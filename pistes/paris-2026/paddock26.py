"""v22 : paddock du Supercross de Paris 2026 d'après les photos de Ryan (pistes/paris-2026/refs/paddock2026) + écran géant refait.

Lecture des photos (validée par Ryan le 2026-11-25) :
  - photo 1 prise depuis le bout côté whoops (z grand), l'écran (mur de scène, x = 879 ft) sur la droite ;
  - allée parallèle au mur ; rangée « mur » : box motos + Triumph, Airstream, Suzuki EN TRAVERS (avant vers la piste) et son stand,
    zone Honda (bâtiment à étage + 3 baies, la 3e = Shimoda 30), Yamaha / Monster + YCF ;
  - rangée « piste » : van blanc, 2 canettes Monster géantes, van KTM (Iveco, porte latérale ouverte, servante Beta) + 2 tentes KTM,
    passage « ACCÈS PISTE », tente Monster, semi Bud Racing (Kawasaki).
  - AUCUNE personne (ni sur les bannières, ni sur l'écran).
Formes CRÉÉES d'après les photos (pas des mesures) : tout sauf la semi-remorque (JGSX2026Scuttle semi_1.jm, peau repeinte, comme v19).
Dimensions : valeurs courantes des objets réels (tente pliante 3 x 3 / 3 x 4,5 m, van 7,2 m, Airstream 27 ft, barrière Vauban 2 m)
-> ESTIMÉES. Pas de collision (comme les camions d'avant : hors piste).

  py -3.15 -I pistes/paris-2026/paddock26.py [dossier_piste]   -> applique au track déjà construit (idempotent) + rendus de contrôle
Appelé aussi par build_zion.export_zion (à la place de semis_jgsx).
"""
import os
import re
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [HERE]
import hab_kit as K                                                     # noqa: E402

REF = os.path.join(HERE, "refs", "paddock2026")
LG = os.path.join(REF, "logos")
SUB = "statue/paris/pad"
LIT, GLOSS, SHINY, UNLIT = "0 0 0 0 0", "16 0.5 1 1 1", "40 1 1 1 1", "-2 0 1 1 1"
PX = 40                                                                  # px / ft sur les faces avec logo


# ================================================================= maillage
class M(K.Mesh):
    def face(self, P, UV, out=None, N=None):
        """triangle orienté : si out est donné, la face regarde du côté de out."""
        P = [np.asarray(p, float) for p in P]; UV = list(UV)
        if out is not None and np.dot(np.cross(P[1] - P[0], P[2] - P[0]), out) < 0:
            P = [P[0], P[2], P[1]]; UV = [UV[0], UV[2], UV[1]]; N = None if N is None else [N[0], N[2], N[1]]
        self.tri(P, UV, N)

    def q(self, P, UV, out=None, N=None):
        self.face([P[0], P[1], P[2]], [UV[0], UV[1], UV[2]], out, None if N is None else [N[0], N[1], N[2]])
        self.face([P[0], P[2], P[3]], [UV[0], UV[2], UV[3]], out, None if N is None else [N[0], N[2], N[3]])

    def panel(self, c, n, w, h, y0, r, two=None):
        """rectangle vertical : base au centre c = (x, z), normale horizontale n, largeur w, hauteur h, bas à y0 ; r = rect UV
        (u vers la droite de celui qui regarde la face). two = rect UV de la face arrière (ou None)."""
        n = np.array([n[0], 0.0, n[1]]); n /= np.linalg.norm(n); rt = np.array([n[2], 0.0, -n[0]]); c = np.array([c[0], 0.0, c[1]])
        bl, br = c - rt * w / 2 + [0, y0, 0], c + rt * w / 2 + [0, y0, 0]; tl, tr = bl + [0, h, 0], br + [0, h, 0]
        self.q([bl, br, tr, tl], ruv(r), n)
        if two is not None:
            self.q([br, bl, tl, tr], ruv(two), -n)

    def tub(self, a, b, rad, r, seg=8, caps=True):
        self.tube(a, b, rad, r, seg, caps)


def ruv(r):
    u0, v0, u1, v1 = r
    return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]


def lerp_uv(r, s, t):
    return (r[0] + (r[2] - r[0]) * s, r[1] + (r[3] - r[1]) * t)


def write_jm(path, blocks):
    """plusieurs blocs (matériau, maillage) dans un .jm (même texture) ; un indice par ligne comme hab_kit."""
    L = ["JM1"]; nt_ = 0
    for mat, m in blocks:
        if not m.V:
            continue
        V = np.array(m.V); L += [mat, "%d %d" % (len(V), len(m.I) // 3)]
        L += [" ".join("%.5f" % v for v in row) for row in V] + [str(i) for i in m.I]; nt_ += len(m.I) // 3
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", newline="\n").write("\n".join(L) + "\n")
    return nt_


class Atlas:
    """texture carrée (puissance de 2) : on y range les images (rangées) ; couleurs unies = petits carrés."""
    def __init__(self, W=2048, bg=(120, 120, 120)):
        self.im = Image.new("RGB", (W, W), bg); self.W = W; self.x = self.y = self.rh = 0; self.sol = {}

    def put(self, img):
        w, h = img.size
        if self.x + w > self.W:
            self.x = 0; self.y += self.rh + 2; self.rh = 0
        assert w <= self.W and self.y + h <= self.W, "atlas plein (%dx%d)" % (w, h)
        self.im.paste(img.convert("RGB"), (self.x, self.y)); r = K.R((self.x, self.y, self.x + w, self.y + h), self.W, self.W)
        self.x += w + 2; self.rh = max(self.rh, h); return r

    def s(self, col):
        col = tuple(int(c) for c in col)
        if col not in self.sol:
            r = self.put(Image.new("RGB", (8, 8), col)); cu, cv = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2; e = 1.0 / self.W
            self.sol[col] = (cu - e, cv - e, cu + e, cv + e)
        return self.sol[col]

    def save(self, path):
        self.im.save(path, optimize=True)


def box(m, lo, hi, r, faces="xXyYzZ", rs=None):
    m.box(lo, hi, r, faces, rs)


def cyl(m, c, rad, y0, y1, r, seg=16, top=None, bot=None):
    """cylindre vertical (centre c = (x, z)) ; r = rect UV autour, top / bot = rect des disques."""
    cx, cz = c
    for k in range(seg):
        a0, a1 = 2 * np.pi * k / seg, 2 * np.pi * (k + 1) / seg
        p = lambda a, y: (cx + rad * np.sin(a), y, cz + rad * np.cos(a))
        n0, n1 = np.array([np.sin(a0), 0, np.cos(a0)]), np.array([np.sin(a1), 0, np.cos(a1)])
        m.q([p(a0, y0), p(a1, y0), p(a1, y1), p(a0, y1)], ruv(r), (n0 + n1), N=[n0, n1, n1, n0])
        if top is not None:
            cc = lerp_uv(top, 0.5, 0.5); m.face([(cx, y1, cz), p(a0, y1), p(a1, y1)], [cc, cc, cc], (0, 1, 0))
        if bot is not None:
            cc = lerp_uv(bot, 0.5, 0.5); m.face([(cx, y0, cz), p(a0, y0), p(a1, y0)], [cc, cc, cc], (0, -1, 0))


def wheel(m, A, cx, cy, cz, rad, w, axis="x", tire=(28, 28, 30), rim=(170, 172, 176), hub=(70, 70, 74), seg=18):
    """roue : bande du pneu, flancs, jante (anneau), voile (disque) ; axe horizontal x ou z."""
    T, Rm, H = A.s(tire), A.s(rim), A.s(hub)
    def P(a, off, rr):
        if axis == "x":
            return np.array([cx + off, cy + rr * np.cos(a), cz + rr * np.sin(a)])
        return np.array([cx + rr * np.sin(a), cy + rr * np.cos(a), cz + off])
    ax = np.array([1.0, 0, 0]) if axis == "x" else np.array([0, 0, 1.0])
    for k in range(seg):
        a0, a1 = 2 * np.pi * k / seg, 2 * np.pi * (k + 1) / seg
        c0, c1 = P(a0, 0, 1) - P(a0, 0, 0), P(a1, 0, 1) - P(a1, 0, 0)
        m.q([P(a0, -w / 2, rad), P(a1, -w / 2, rad), P(a1, w / 2, rad), P(a0, w / 2, rad)], ruv(T), c0 + c1, N=[c0, c1, c1, c0])
        for sd in (-1, 1):
            o = sd * w / 2
            m.q([P(a0, o, rad), P(a1, o, rad), P(a1, o, rad * 0.72), P(a0, o, rad * 0.72)], ruv(T), sd * ax)
            m.q([P(a0, o * 0.8, rad * 0.72), P(a1, o * 0.8, rad * 0.72), P(a1, o * 0.8, rad * 0.6), P(a0, o * 0.8, rad * 0.6)], ruv(Rm), sd * ax)
            cc = lerp_uv(H, 0.5, 0.5)
            m.face([P(a0, o * 0.6, 0), P(a0, o * 0.6, rad * 0.6), P(a1, o * 0.6, rad * 0.6)], [cc, cc, cc], sd * ax)


# ================================================================= logos (fichiers de Ryan, refs/paddock2026/logos)
_LC = {}


def _key_bg(im, bg, tol=40, soft=40):
    a = np.asarray(im.convert("RGB"), float); d = np.linalg.norm(a - np.array(bg, float), axis=-1)
    al = np.clip((d - tol) / soft, 0, 1)
    out = Image.fromarray(np.dstack([a, al * 255]).astype(np.uint8), "RGBA"); return out.crop(out.getbbox())


def _key_border_white(im, thr=232):
    """fond blanc relié au bord -> transparent (garde le blanc à l'intérieur des lettres)."""
    from scipy import ndimage as ndi
    a = np.asarray(im.convert("RGB"), float); wh = a.min(-1) > thr
    lab, _ = ndi.label(wh); edge = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
    bgm = np.isin(lab, list(edge)); bgm = ndi.binary_dilation(bgm, iterations=1) & (a.min(-1) > thr - 25)
    out = Image.fromarray(np.dstack([a, (~bgm) * 255]).astype(np.uint8), "RGBA"); return out.crop(out.getbbox())


def lg(name):
    if name in _LC:
        return _LC[name]
    f = lambda n: Image.open(os.path.join(LG, n))
    if name == "redbull":                         # taureaux + soleil + « Red Bull » (fond marine retiré)
        im = _key_bg(f("redbull_ktm.png").crop((0, 0, 2000, 610)), (40, 34, 72))
    elif name == "ktm_orange":
        im = _key_bg(f("redbull_ktm.png").crop((0, 640, 2000, 1017)), (40, 34, 72))
    elif name == "redbull_ktm_badge":             # le visuel entier (fond marine), tel quel
        im = f("redbull_ktm.png").convert("RGBA")
    elif name == "ktm_black":
        im = K.tint(lg("ktm_orange"), (14, 14, 14))
    elif name == "triumph_tri":                   # triangle noir, T et TRIUMPH blancs (fond transparent)
        im = f("triumph_triangle.png").convert("RGBA"); im = im.crop(im.getbbox())
    elif name == "triumph_word_w":
        im = K.tint(f("triumph_long.webp").convert("RGBA").crop((0, 0, 1560, 1125)), (255, 255, 255)); im = im.crop(im.getbbox())
    elif name == "suzuki_s":
        im = _key_border_white(f("suzuki.webp").crop((700, 80, 1300, 580)))
    elif name == "suzuki_word":
        im = _key_border_white(f("suzuki.webp").crop((80, 590, 1920, 920)))
    elif name == "suzuki_h":                      # S + SUZUKI côte à côte (comme sur le camion)
        im = K.hstack([lg("suzuki_s"), lg("suzuki_word").resize((int(lg("suzuki_word").size[0] * 0.55), int(lg("suzuki_word").size[1] * 0.55)), Image.LANCZOS)], 40)
    elif name == "ycf":
        im = _key_border_white(f("ycf.png"))
    elif name == "bud":                           # le badge entier (fond noir arrondi)
        a = f("bud_racing.webp").convert("RGB"); im = _key_bg(a, (0, 0, 0), 12, 10)
    elif name == "monster":                       # griffe + MONSTER ENERGY (sur noir)
        im = _key_bg(f("monster_energy.png"), (0, 0, 0), 25, 30)
    elif name == "monster_claw":
        im = _key_bg(f("monster_energy.png").crop((0, 0, 150, 266)), (0, 0, 0), 25, 30)
    elif name == "monster_yamaha":
        im = _key_border_white(f("monster_yamaha.png"))
    elif name == "honda_red":
        im = f("honda.webp").convert("RGBA"); im = im.crop(im.getbbox())
    elif name == "honda_white":
        im = K.tint(lg("honda_red"), (255, 255, 255))
    elif name == "motul":                         # boîte rouge + MOTUL blanc
        im = f("motul.png").convert("RGBA"); im = im.crop(im.getbbox())
    elif name == "stark":                         # logo or (fond blanc retiré)
        im = _key_border_white(f("stark.png"))
    elif name == "milwaukee":                     # blanc sur rouge : on garde le blanc
        a = np.asarray(f("milwaukee.webp").convert("RGB"), float); al = np.clip((a.min(-1) - 90) / 120, 0, 1)
        im = Image.fromarray(np.dstack([np.full(a.shape, 255.0), al * 255]).astype(np.uint8), "RGBA"); im = im.crop(im.getbbox())
    elif name in ("sedna", "rfn"):                # v22e : logos envoyés par Ryan (fond transparent)
        im = f(name + ".png").convert("RGBA"); im = im.crop(im.getbbox())
    elif name == "gsm":                           # badge Team GSM sur fond bleu : pris tel quel
        im = f("gsm.png").convert("RGBA").crop((90, 95, 510, 260))
    elif name == "sxparis":
        im = f("supercross_paris.webp").convert("RGBA"); im = im.crop(im.getbbox())
    else:
        raise KeyError(name)
    _LC[name] = im
    return im


def txt(s, px, col, font="ariblk.ttf", italic=0.0, squeeze=1.0, stroke=0, sf=None):
    return K.text_img(s, px, col, font, italic=italic, squeeze=squeeze, stroke=stroke, stroke_fill=sf)


def canvas(w_ft, h_ft, col, px=PX):
    return Image.new("RGBA", (max(8, int(w_ft * px)), max(8, int(h_ft * px))), tuple(col) + (255,))


def fitc(img, logo, box, pad=0.06, rot=0):
    K.fit(img, logo, box, pad, rot)


# ================================================================= tentes pliantes
TENTS = {   # toit, intérieur, bavolet, logos (pentes longues, pentes courtes), logos du bavolet
    "ktm": dict(roof=(236, 108, 18), under=(150, 70, 14), val=(36, 32, 74), legs=(60, 60, 64)),
    "triumph": dict(roof=(22, 22, 24), under=(14, 14, 16), val=(20, 20, 22), legs=(40, 40, 44)),
    "ycf": dict(roof=(24, 120, 200), under=(16, 70, 120), val=(18, 18, 20), legs=(150, 150, 155)),
    "monster": dict(roof=(18, 18, 20), under=(10, 10, 12), val=(16, 16, 18), legs=(40, 40, 44)),
    "blanc": dict(roof=(236, 236, 238), under=(170, 170, 174), val=(225, 225, 228), legs=(150, 150, 155)),   # sans marque
    "sedna": dict(roof=(0, 150, 166), under=(0, 90, 100), val=(14, 14, 16), legs=(40, 40, 44)),
    "rfn": dict(roof=(18, 18, 20), under=(10, 10, 12), val=(240, 240, 240), legs=(40, 40, 44)),
    "gsm": dict(roof=(21, 58, 156), under=(14, 36, 96), val=(21, 58, 156), legs=(150, 150, 155)),
    "stark": dict(roof=(18, 18, 20), under=(10, 10, 12), val=(18, 18, 20), legs=(40, 40, 44)),
    "milwaukee": dict(roof=(214, 1, 26), under=(130, 0, 16), val=(214, 1, 26), legs=(150, 150, 155)),
}


def _slope_img(kind, w_ft, h_ft, tri):
    c = TENTS[kind]; im = canvas(w_ft, h_ft, c["roof"]); W, H = im.size
    # la zone utile d'une pente : trapèze / triangle ; logo dans le bas, centré
    bx = (int(W * (0.3 if tri else 0.2)), int(H * 0.25), int(W * (0.7 if tri else 0.8)), int(H * 0.92))
    if kind == "ktm":
        if tri:
            fitc(im, lg("ktm_black"), bx, 0.04)
        else:
            for k in (0.3, 0.7):
                cx = int(W * k); fitc(im, lg("redbull_ktm_badge"), (cx - int(H * 0.45), int(H * 0.3), cx + int(H * 0.45), int(H * 0.9)), 0.05)
    elif kind == "triumph":
        fitc(im, lg("triumph_tri"), (int(W * 0.3), int(H * 0.22), int(W * 0.7), int(H * 0.9)), 0.04)
    elif kind == "ycf":
        fitc(im, lg("ycf"), bx, 0.05)
    elif kind == "monster":
        fitc(im, lg("monster"), bx, 0.04)
    elif kind in ("sedna", "gsm", "stark", "milwaukee"):
        fitc(im, lg(kind), bx, 0.05)
    elif kind == "rfn":
        fitc(im, K.tint(lg("rfn"), (240, 240, 240)), bx, 0.05)
    return im


def _valance_img(kind, L_ft):
    c = TENTS[kind]; im = canvas(L_ft, 0.9, c["val"]); W, H = im.size; n = max(1, int(round(L_ft / 7.5)))
    for k in range(n):
        x0, x1 = int(W * k / n), int(W * (k + 1) / n); b = (x0 + 6, 3, x1 - 6, H - 3)
        if kind == "ktm":
            fitc(im, lg("redbull") if k % 2 == 0 else lg("ktm_orange"), b, 0.1)
        elif kind == "triumph":
            fitc(im, K.hstack([lg("triumph_word_w"), lg("triumph_tri").resize((int(lg("triumph_word_w").size[1] * 1.35), int(lg("triumph_word_w").size[1] * 0.76)))], 40), b, 0.1)
        elif kind == "ycf":
            fitc(im, lg("ycf"), b, 0.08)
        elif kind == "monster":
            fitc(im, lg("monster"), b, 0.08)
        elif kind in ("sedna", "gsm", "rfn", "stark", "milwaukee"):
            fitc(im, lg(kind), b, 0.1)
    return im


def tent(D, kind, w=10.0, d=10.0):
    """tente pliante w (x) x d (z) ft : 4 (ou 6) pieds, toit à 4 pans (faîtage si d > w), bavolet imprimé autour.
    Hauteurs d'une tente pliante courante : bas du bavolet 6,0 ft, gouttière 6,9 ft, sommet 10,2 ft (ESTIMÉ)."""
    c = TENTS[kind]; A = Atlas(2048); m = M(); eave, peak, vb = 6.9, 10.2, 6.0
    hx, hz = w / 2, d / 2; rl = max(0.0, (d - w) / 2)                          # demi-faîtage
    E = {"Z": [(-hx, hz), (hx, hz)], "X": [(hx, hz), (hx, -hz)], "z": [(hx, -hz), (-hx, -hz)], "x": [(-hx, -hz), (-hx, hz)]}
    ridge = {"Z": [(0, rl), (0, rl)], "X": [(0, rl), (0, -rl)], "z": [(0, -rl), (0, -rl)], "x": [(0, -rl), (0, rl)]}
    out = {"Z": (0, 0, 1), "X": (1, 0, 0), "z": (0, 0, -1), "x": (-1, 0, 0)}
    UND = A.s(c["under"])
    for f, ((ax, az), (bx_, bz)) in E.items():
        L = np.hypot(bx_ - ax, bz - az); tri = rl == 0 or f in "Zz"
        hs = np.hypot(hx if f in "Xx" else 0, hz - rl if f in "Zz" else 0) if not tri or rl == 0 else hx
        slope_len = np.hypot(peak - eave, hx if f in "Xx" else (hz - rl))
        r = A.put(_slope_img(kind, L, slope_len, tri))
        (rx0, rz0), (rx1, rz1) = ridge[f]
        P = [np.array([ax, eave, az]), np.array([bx_, eave, bz]), np.array([rx1, peak, rz1]), np.array([rx0, peak, rz0])]
        o = np.array(out[f]) * 1.0 + np.array([0, 1.4, 0])
        def uv(p):
            s = np.dot(p[[0, 2]] - P[0][[0, 2]], (P[1] - P[0])[[0, 2]]) / L ** 2
            return lerp_uv(r, s, (p[1] - eave) / (peak - eave))
        if np.allclose(P[2], P[3]):
            m.face([P[0], P[1], P[2]], [uv(P[0]), uv(P[1]), uv(P[2])], o)
            cc = lerp_uv(UND, .5, .5); m.face([P[0], P[1], P[2]], [cc] * 3, -o)
        else:
            m.q(P, [uv(p) for p in P], o); cc = lerp_uv(UND, .5, .5); m.q(P, [cc] * 4, -o)
        # bavolet
        rv = A.put(_valance_img(kind, L)); n_ = np.array(out[f])
        m.panel(((ax + bx_) / 2, (az + bz) / 2), (n_[0], n_[2]), L, eave - vb, vb, rv, two=A.s(c["under"]))
    LEG = A.s(c["legs"]); legs = [(-hx, -hz), (hx, -hz), (hx, hz), (-hx, hz)]
    if d > 14:
        legs += [(-hx, 0), (hx, 0)]
    for (x, z) in legs:
        sx, sz = -np.sign(x) * 0.13, -np.sign(z) * 0.13 if z else 0.065
        box(m, (min(x, x + sx), 0, min(z, z + sz) if z else -0.065), (max(x, x + sx), eave, max(z, z + sz) if z else 0.065), LEG)
    name = "tente_%s_%dx%d" % (kind, w, d)
    nt = write_jm(os.path.join(D, name + ".jm"), [(LIT, m)]); A.save(os.path.join(D, name + ".png")); return name + ".jm", name + ".png", nt


# ================================================================= flammes (beach flags)
FLAGS = {"triumph": (18, 18, 20), "ycf": (24, 120, 200), "honda": (204, 16, 26), "automoto": (204, 16, 26), "bud": (14, 14, 14)}
FW, FH, FB = 2.4, 11.6, 1.6                                              # largeur, hauteur de voile, bas de la voile (ft)


def _flag_logo(brand):
    if brand == "triumph":
        return K.vstack([lg("triumph_word_w").rotate(90, expand=True), lg("triumph_tri").rotate(0, expand=True)], 60)
    if brand == "ycf":
        return lg("ycf").rotate(90, expand=True)
    if brand == "honda":
        return lg("honda_white").rotate(90, expand=True)
    if brand == "automoto":
        return txt("AUTOMOTO", 200, (255, 255, 255), "ariblk.ttf", italic=0.12).rotate(90, expand=True)
    if brand == "bud":
        return lg("bud").rotate(90, expand=True)


def _flag_outline(s):
    """bord haut et bas de la voile à l'abscisse s (0 = mât) : haut arrondi (quart d'ellipse), bas en biais (photo de Ryan)."""
    top = FB + FH - 0.0 - (FH * 0.30) * (1 - np.sqrt(max(0.0, 1 - (s / FW) ** 2)))
    top = min(top, FB + FH)
    bot = FB + 0.9 * (s / FW)
    return top, bot


def flag(D, brand):
    A = Atlas(1024); m = M(); col = FLAGS[brand]
    W, H = int(FW * 80), int(FH * 80)
    base = Image.new("RGBA", (W, H), col + (255,)); d = ImageDraw.Draw(base); d.rectangle([0, 0, int(W * 0.07), H], fill=(12, 12, 12, 255))
    front = base.copy(); fitc(front, _flag_logo(brand), (int(W * 0.12), int(H * 0.16), W - 8, int(H * 0.92)), 0.05)
    back = base.transpose(Image.FLIP_LEFT_RIGHT); fitc(back, _flag_logo(brand), (8, int(H * 0.16), W - int(W * 0.12), int(H * 0.92)), 0.05)
    rf, rb = A.put(front), A.put(back)
    POLE, BASE = A.s((150, 152, 156)), A.s((120, 122, 126))
    n = 10
    for i in range(n):
        s0, s1 = FW * i / n, FW * (i + 1) / n; t0, b0 = _flag_outline(s0); t1, b1 = _flag_outline(s1)
        bend = lambda s: 0.22 * np.sin(np.pi * s / FW)                    # voile un peu galbée
        P = [np.array([s0, b0, bend(s0)]), np.array([s1, b1, bend(s1)]), np.array([s1, t1, bend(s1)]), np.array([s0, t0, bend(s0)])]
        v = lambda y: (y - FB) / FH
        m.q(P, [lerp_uv(rf, s0 / FW, v(b0)), lerp_uv(rf, s1 / FW, v(b1)), lerp_uv(rf, s1 / FW, v(t1)), lerp_uv(rf, s0 / FW, v(t0))], (0, 0, 1))
        m.q(P, [lerp_uv(rb, 1 - s0 / FW, v(b0)), lerp_uv(rb, 1 - s1 / FW, v(b1)), lerp_uv(rb, 1 - s1 / FW, v(t1)), lerp_uv(rb, 1 - s0 / FW, v(t0))], (0, 0, -1))
    m.tub((0, 0.15, 0), (0, FB + FH + 0.1, 0), 0.07, POLE, 6)
    box(m, (-0.9, 0, -0.9), (0.9, 0.15, 0.9), BASE)
    name = "flamme_%s" % brand
    nt = write_jm(os.path.join(D, name + ".jm"), [(LIT, m)]); A.save(os.path.join(D, name + ".png")); return name + ".jm", name + ".png", nt


# ================================================================= barrières Vauban (2 m) : nues ou bâchées
def barrier(D, cover=None):
    A = Atlas(1024 if cover else 64); m = M(); G = A.s((168, 170, 172)); L, Hh = 6.6, 3.6
    box(m, (-L / 2, 3.35, -0.06), (L / 2, 3.5, 0.06), G); box(m, (-L / 2, 0.5, -0.06), (L / 2, 0.62, 0.06), G)
    for x in (-L / 2, L / 2 - 0.12):
        box(m, (x, 0.35, -0.06), (x + 0.12, Hh, 0.06), G)
    for k in range(1, 14):
        x = -L / 2 + L * k / 14; box(m, (x - 0.03, 0.62, -0.03), (x + 0.03, 3.35, 0.03), G)
    for x in (-L / 2 + 0.3, L / 2 - 0.3):
        box(m, (x - 0.06, 0, -1.0), (x + 0.06, 0.35, 1.0), G)
    if cover:
        col, logo = {"honda": ((204, 16, 26), lg("honda_white")), "triumph": ((18, 18, 20), lg("triumph_word_w"))}[cover]
        im = canvas(L, 3.0, col); fitc(im, logo, (int(im.size[0] * 0.12), 8, int(im.size[0] * 0.88), im.size[1] - 8), 0.12)
        r = A.put(im)
        m.panel((0, 0.09), (0, 1), L, 3.0, 0.5, r); m.panel((0, -0.09), (0, -1), L, 3.0, 0.5, r)
    name = "barriere_%s" % (cover or "vauban")
    nt = write_jm(os.path.join(D, name + ".jm"), [(LIT, m)]); A.save(os.path.join(D, name + ".png")); return name + ".jm", name + ".png", nt


# ================================================================= canette Monster géante (photo de Ryan plaquée)
def can(D):
    A = Atlas(1024); m = M(); R_, Hc = 4.4, 24.0                       # v22e : 2,7 m x 7,3 m, plus haute que les camions (ESTIMÉ)
    ph = Image.open(os.path.join(LG, "canette_monster.png")).convert("RGB"); a = np.asarray(ph, float)
    cols = np.nonzero((a[300:700].min(-1) < 200).mean(0) > 0.6)[0]; x0, x1 = cols.min() + 3, cols.max() - 3
    rows = np.nonzero((a[:, x0:x1].min(-1) < 200).mean(1) > 0.6)[0]; y0, y1 = rows.min(), rows.max()
    body = ph.crop((x0, y0 + 40, x1, y1 - 25)).resize((512, 900), Image.LANCZOS); r = A.put(body)
    TOP, RIM = A.s((176, 178, 182)), A.s((205, 207, 210))
    seg = 32
    for k in range(seg):
        a0, a1 = 2 * np.pi * k / seg, 2 * np.pi * (k + 1) / seg
        def u(aa):                                                         # projection orthographique de la photo (avant et arrière)
            s = np.sin(aa); front = np.cos((a0 + a1) / 2) >= 0
            return 0.5 + 0.5 * s if front else 0.5 - 0.5 * s
        p = lambda aa, y: (R_ * np.sin(aa), y, R_ * np.cos(aa))
        n0, n1 = np.array([np.sin(a0), 0, np.cos(a0)]), np.array([np.sin(a1), 0, np.cos(a1)])
        ua, ub = u(a0), u(a1)
        m.q([p(a0, 0.6), p(a1, 0.6), p(a1, Hc - 0.7), p(a0, Hc - 0.7)], [lerp_uv(r, ua, 0), lerp_uv(r, ub, 0), lerp_uv(r, ub, 1), lerp_uv(r, ua, 1)], n0 + n1, N=[n0, n1, n1, n0])
        # épaulement et fond (alu), couvercle
        q_ = lambda aa, y, rr: (rr * np.sin(aa), y, rr * np.cos(aa))
        m.q([q_(a0, Hc - 0.7, R_), q_(a1, Hc - 0.7, R_), q_(a1, Hc - 0.15, R_ * 0.86), q_(a0, Hc - 0.15, R_ * 0.86)], ruv(RIM), n0 + n1 + np.array([0, 1.2, 0]))
        m.q([q_(a0, Hc - 0.15, R_ * 0.86), q_(a1, Hc - 0.15, R_ * 0.86), q_(a1, Hc, R_ * 0.86), q_(a0, Hc, R_ * 0.86)], ruv(RIM), n0 + n1)
        m.face([(0, Hc - 0.1, 0), q_(a0, Hc, R_ * 0.86), q_(a1, Hc, R_ * 0.86)], [lerp_uv(TOP, .5, .5)] * 3, (0, 1, 0))
        m.q([q_(a0, 0, R_ * 0.9), q_(a1, 0, R_ * 0.9), q_(a1, 0.6, R_), q_(a0, 0.6, R_)], ruv(RIM), n0 + n1 - np.array([0, 0.5, 0]))
    nt = write_jm(os.path.join(D, "canette_geante.jm"), [(GLOSS, m)]); A.save(os.path.join(D, "canette_geante.png"))
    return "canette_geante.jm", "canette_geante.png", nt


# ================================================================= vans (Iveco Daily KTM porte ouverte, MAN TGE blanc / noir)
VANBODY = {"ktm": (22, 42, 118), "blanc": (236, 237, 238), "noir": (16, 16, 18), "bus_noir": (16, 16, 18),
           "sedna": (0, 150, 166), "rfn": (18, 18, 20), "gsm": (21, 58, 156), "ycf": (240, 240, 242), "stark": (20, 20, 22),
           "honda": (240, 240, 242), "vhr": (21, 58, 156)}
VW, VL = 6.6, 23.6                                                        # largeur, longueur (ft) ; hauteur 9,0 (toit haut)
Y0, YT = 1.15, 9.0
DOOR = (-0.2, 4.0, 1.5, 7.4)                                              # porte latérale (+x) : z0, z1, y0, y1
CAB = 5.6                                                                 # haut du pare-brise


def _prof(top, w=VW, y0=Y0, rt=1.15, rb=0.35, nseg=4):
    """section arrondie (vue de +z, sens trigo) : liste de points + étiquette de chaque arête."""
    rt = min(rt, (top - y0) / 3); hw = w / 2; P, tag = [], []
    def arc(cx, cy, r, a0, a1, t):
        for k in range(nseg + 1):
            a = a0 + (a1 - a0) * k / nseg; P.append((cx + r * np.cos(a), cy + r * np.sin(a))); tag.append(t)
    arc(hw - rb, y0 + rb, rb, -np.pi / 2, 0, "c")
    arc(hw - rt, top - rt, rt, 0, np.pi / 2, "R")                          # l'arête qui arrive ici = flanc +x
    arc(-hw + rt, top - rt, rt, np.pi / 2, np.pi, "T")
    arc(-hw + rb, y0 + rb, rb, np.pi, 3 * np.pi / 2, "L")
    return P, tag


def _van_side(kind, front_left):
    """image d'un flanc (longueur x hauteur), avant à gauche (flanc +x) ou à droite (flanc -x)."""
    W, H = int(VL * PX), int(YT * PX)
    X = lambda zf: int(W * (1 - zf)) if front_left else int(W * zf)        # zf = 0 arrière, 1 avant
    Yp = lambda y: int(H * (1 - y / YT))
    body = VANBODY[kind]
    im = Image.new("RGBA", (W, H), body + (255,)); d = ImageDraw.Draw(im)
    d.rectangle([0, Yp(1.9), W, H], fill=(44, 46, 50, 255))               # bas de caisse
    if kind == "ktm":
        d.rectangle([0, 0, W, Yp(8.75)], fill=(236, 108, 18, 255))           # galerie orange sur le toit
        poly = [(0.0, 8.75), (0.21, 8.75), (0.12, 1.9), (0.0, 1.9)]          # arrière orange en biais
        d.polygon([(X(zf), Yp(y)) for zf, y in poly], fill=(236, 108, 18, 255))
        poly2 = [(0.0, 5.0), (0.15, 5.0), (0.13, 3.4), (0.0, 3.4)]
        d.polygon([(X(zf), Yp(y)) for zf, y in poly2], fill=(22, 42, 118, 255))
        zc = 0.33; r = int(2.3 * PX); cx, cy = X(zc + 0.07), Yp(6.0)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 205, 0, 255))   # soleil jaune
        bull = lg("redbull").crop((0, 0, lg("redbull").size[0], int(lg("redbull").size[1] * 0.97)))
        b0 = X(0.15), X(0.48)
        fitc(im, bull, (min(b0), Yp(8.4), max(b0), Yp(3.4)), 0.02)
        fitc(im, lg("ktm_black"), (min(X(0.005), X(0.15)), Yp(8.3), max(X(0.005), X(0.15)), Yp(5.6)), 0.04)
        fitc(im, txt("READY TO RACE", 90, (255, 255, 255), "arialbi.ttf"), (min(X(0.2), X(0.42)), Yp(3.3), max(X(0.2), X(0.42)), Yp(2.3)), 0.05)
        fitc(im, lg("ktm_orange"), (min(X(0.69), X(0.81)), Yp(4.8), max(X(0.69), X(0.81)), Yp(3.5)), 0.04)
    elif kind == "noir":
        fitc(im, lg("monster_yamaha"), (min(X(0.30), X(0.62)), Yp(8.0), max(X(0.30), X(0.62)), Yp(2.4)), 0.04)
    elif kind == "ycf":                                                    # v22f : vidéo YCF de Ryan (« ENJOY YOUR RIDE »)
        d.polygon([(X(0.0), Yp(8.8)), (X(0.45), Yp(8.8)), (X(0.3), Yp(4.0)), (X(0.0), Yp(4.0))], fill=(20, 110, 200, 255))
        d.polygon([(X(0.45), Yp(8.8)), (X(0.6), Yp(8.8)), (X(0.45), Yp(4.0)), (X(0.3), Yp(4.0))], fill=(210, 30, 40, 255))
        fitc(im, lg("ycf"), (min(X(0.05), X(0.42)), Yp(7.8), max(X(0.05), X(0.42)), Yp(4.4)), 0.04)
        fitc(im, txt("ENJOY YOUR RIDE", 90, (20, 20, 22), "ariblk.ttf", italic=0.15), (min(X(0.45), X(0.75)), Yp(3.9), max(X(0.45), X(0.75)), Yp(2.9)), 0.04)
    elif kind == "stark":
        fitc(im, lg("stark"), (min(X(0.2), X(0.66)), Yp(7.4), max(X(0.2), X(0.66)), Yp(4.6)), 0.05)
    elif kind == "vhr":                                                    # bus VHR Yamaha (vidéo / photo de Ryan) : bleu, toit blanc
        d.rectangle([0, 0, W, Yp(8.2)], fill=(240, 240, 242, 255))
        fitc(im, lg("monster_claw"), (min(X(0.08), X(0.3)), Yp(7.9), max(X(0.08), X(0.3)), Yp(3.0)), 0.04)
        fitc(im, K.vstack([txt("VHR", 220, (255, 255, 255), "ariblk.ttf", italic=0.15), K.logo("yamaha")], 30),
             (min(X(0.34), X(0.64)), Yp(7.8), max(X(0.34), X(0.64)), Yp(3.2)), 0.05)
    elif kind == "honda":
        d.rectangle([0, Yp(1.95), W, Yp(1.6)], fill=(255, 40, 40, 255))
        for k_ in range(4):                                                # minibus : vitres latérales
            z0_, z1_ = 0.1 + k_ * 0.14, 0.21 + k_ * 0.14
            d.rounded_rectangle([min(X(z0_), X(z1_)), Yp(7.5), max(X(z0_), X(z1_)), Yp(5.4)], 14, fill=(34, 38, 46, 255))
        d.rectangle([0, Yp(3.6), W, Yp(1.9)], fill=(204, 16, 26, 255))
        fitc(im, lg("honda_red"), (min(X(0.12), X(0.6)), Yp(5.2), max(X(0.12), X(0.6)), Yp(3.8)), 0.05)
        fitc(im, txt("HRC", 160, (255, 255, 255), "ariblk.ttf", italic=0.15), (min(X(0.25), X(0.47)), Yp(3.5), max(X(0.25), X(0.47)), Yp(2.0)), 0.05)
    elif kind in ("sedna", "rfn", "gsm"):                                 # v22e : vans aux couleurs du logo (dessin de Ryan)
        if kind == "sedna":
            d.rectangle([0, Yp(3.4), W, Yp(1.9)], fill=(14, 14, 16, 255))
        if kind == "rfn":
            d.rectangle([0, Yp(3.2), W, Yp(2.7)], fill=(240, 240, 240, 255))
        bx = (min(X(0.2), X(0.66)), Yp(8.2), max(X(0.2), X(0.66)), Yp(3.6))
        if kind == "rfn":
            d.rounded_rectangle(bx, 30, fill=(242, 242, 242, 255))
        fitc(im, lg(kind), bx, 0.06)
    # vitre de la portière avant, poignées, passages de roue
    win = [(0.69, 7.6), (0.80, 7.6), (0.84, 5.2), (0.69, 5.2)]
    d.polygon([(X(zf), Yp(y)) for zf, y in win], fill=(34, 38, 46, 255))
    for zf in (0.7,):
        d.rectangle([X(zf) - 10, Yp(4.6) - 4, X(zf) + 10, Yp(4.6) + 4], fill=(20, 20, 22, 255))
    for za in (-5.8, 7.6):
        zf = (za + VL / 2) / VL; r = int(1.45 * PX); cx = X(zf)
        d.pieslice([cx - r, Yp(1.2) - r, cx + r, Yp(1.2) + r], 180, 360, fill=(14, 14, 16, 255))
    return K.shade_v(im, (0, 0, W, H), 1.0, 0.86)


def _van_front(kind):
    W, H = int(VW * PX), int(4.0 * PX); body = VANBODY[kind]
    im = Image.new("RGBA", (W, H), body + (255,)); d = ImageDraw.Draw(im)
    d.rectangle([0, int(H * 0.72), W, H], fill=(40, 42, 46, 255))          # pare-chocs
    d.rounded_rectangle([int(W * 0.25), int(H * 0.28), int(W * 0.75), int(H * 0.66)], 12, fill=(24, 24, 26, 255))   # calandre
    for x0 in (0.04, 0.78):
        d.rounded_rectangle([int(W * x0), int(H * 0.22), int(W * (x0 + 0.18)), int(H * 0.42)], 10, fill=(225, 228, 232, 255))
    fitc(im, txt("IVECO" if kind == "ktm" else "MAN", 60, (225, 228, 232), "arialbd.ttf"), (int(W * 0.35), int(H * 0.36), int(W * 0.65), int(H * 0.56)), 0.1)
    return im


def _van_rear(kind):
    W, H = int(VW * PX), int((YT - Y0) * PX); body = (236, 108, 18) if kind == "ktm" else VANBODY[kind]
    im = Image.new("RGBA", (W, H), body + (255,)); d = ImageDraw.Draw(im)
    d.line([(W // 2, int(H * 0.06)), (W // 2, int(H * 0.9))], fill=(60, 60, 64, 255), width=3)
    d.rectangle([0, int(H * 0.88), W, H], fill=(40, 42, 46, 255))
    for x0 in (0.02, 0.9):
        d.rectangle([int(W * x0), int(H * 0.55), int(W * (x0 + 0.08)), int(H * 0.8)], fill=(190, 20, 20, 255))
    if kind == "ktm":
        fitc(im, lg("redbull_ktm_badge"), (int(W * 0.12), int(H * 0.12), int(W * 0.88), int(H * 0.62)), 0.03)
    elif kind == "noir":
        fitc(im, lg("monster_claw"), (int(W * 0.3), int(H * 0.15), int(W * 0.7), int(H * 0.6)), 0.05)
    elif kind in ("ycf", "stark", "honda", "vhr"):
        fitc(im, lg({"ycf": "ycf", "stark": "stark", "honda": "honda_red", "vhr": "monster_claw"}[kind]), (int(W * 0.12), int(H * 0.2), int(W * 0.88), int(H * 0.5)), 0.06)
    elif kind in ("sedna", "rfn", "gsm"):
        if kind == "rfn":
            d.rounded_rectangle([int(W * 0.12), int(H * 0.2), int(W * 0.88), int(H * 0.5)], 16, fill=(242, 242, 242, 255))
        fitc(im, lg(kind), (int(W * 0.12), int(H * 0.2), int(W * 0.88), int(H * 0.5)), 0.06)
    return im


def _interior(A):
    """intérieur de l'Iveco KTM (photo de Ryan) : murs blancs, placards gris clair filet orange, réglette LED."""
    W, H = int(17.0 * PX), int(6.8 * PX); im = Image.new("RGBA", (W, H), (226, 228, 230, 255)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, int(H * 0.36)], fill=(210, 206, 198, 255))
    for k in range(9):
        x = int(W * k / 9); d.line([(x, 0), (x, int(H * 0.36))], fill=(236, 108, 18, 255), width=3)
        d.ellipse([x + 40, int(H * 0.2), x + 52, int(H * 0.2) + 12], fill=(40, 40, 40, 255))
    d.rectangle([0, int(H * 0.36), W, int(H * 0.36) + 10], fill=(236, 108, 18, 255))
    d.rectangle([0, int(H * 0.42), W, int(H * 0.45)], fill=(170, 172, 176, 255))   # rail aluminium
    return A.put(im)


def _beta(A):
    W, H = int(2.6 * PX), int(2.2 * PX); im = Image.new("RGBA", (W, H), (58, 60, 64, 255)); d = ImageDraw.Draw(im)
    for k in range(5):
        y0 = int(H * (0.08 + k * 0.17)); d.rectangle([10, y0, W - 10, y0 + int(H * 0.13)], fill=(240, 110, 20, 255))
    fitc(im, txt("Beta", 60, (250, 250, 250), "arialbi.ttf"), (int(W * 0.3), int(H * 0.44), int(W * 0.6), int(H * 0.56)), 0.1)
    return A.put(im)


def van(D, kind, door_open=False):
    """kind : 'ktm' (Iveco Daily Red Bull KTM, photos de Ryan), 'blanc' (MAN TGE blanc), 'noir' (MAN TGE noir Monster Yamaha).
    Repère : +z = avant, flanc porte latérale = +x."""
    A = Atlas(2048); m = M(); col = VANBODY[kind]
    BODY, GLASS, DARK = A.s(col), A.s((30, 34, 42)), A.s((24, 24, 26))
    ROOF = A.s((236, 108, 18)) if kind == "ktm" else BODY
    rP, rM = A.put(_van_side(kind, True)), A.put(_van_side(kind, False))
    rF, rR = A.put(_van_front(kind)), A.put(_van_rear(kind))
    zr, zf = -VL / 2, VL / 2
    secs = [(zr, YT), (CAB, YT), (CAB + 0.4, YT - 0.35), (CAB + 3.0, 4.6), (zf - 0.25, 3.95), (zf, 3.85)]
    profs = [_prof(t) for _, t in secs]; npt = len(profs[0][0]); tag = profs[0][1]
    def side_uv(p, sgn):
        r = rP if sgn > 0 else rM; s = (zf - p[2]) / VL if sgn > 0 else (p[2] - zr) / VL
        return lerp_uv(r, s, p[1] / YT)
    for i in range(len(secs) - 1):
        (za, _), (zb, _) = secs[i], secs[i + 1]; Pa, Pb = profs[i][0], profs[i + 1][0]
        for j in range(npt):
            j2 = (j + 1) % npt
            a0, a1 = np.array([Pa[j][0], Pa[j][1], za]), np.array([Pa[j2][0], Pa[j2][1], za])
            b0, b1 = np.array([Pb[j][0], Pb[j][1], zb]), np.array([Pb[j2][0], Pb[j2][1], zb])
            mid = (a0 + a1 + b0 + b1) / 4; nrm = np.array([mid[0], mid[1] - 4.5, 0.0])
            if i >= 2:
                nrm = nrm + np.array([0, 0, 2.0])
            P = [a0, a1, b1, b0]
            # flanc +x de la partie caisse : fait à la main (trou de la porte)
            if door_open and i == 0 and tag[j] == "T" and tag[j2] == "L":
                continue
            edge_x = (abs(a0[0]) + abs(a1[0])) / 2
            if edge_x > VW / 2 - 0.3 and abs(a0[0] - a1[0]) < 0.05:          # flanc plat
                sg = np.sign(a0[0]); m.q(P, [side_uv(p, sg) for p in P], nrm)
            elif mid[1] < Y0 + 0.2:
                m.q(P, ruv(DARK), nrm)
            elif i == 2 and abs(mid[0]) < VW / 2 - 0.4:                       # pare-brise
                m.q(P, ruv(GLASS), nrm)
            elif abs(mid[0]) < VW / 2 - 0.3:
                m.q(P, ruv(ROOF if i == 0 else BODY), nrm)
            else:
                sg = np.sign(mid[0]); m.q(P, [side_uv(p, sg) for p in P], nrm)
    # bouts : arrière (portes) et avant (calandre)
    for (z_, pr, r, o) in ((zr, profs[0][0], rR, -1), (zf, profs[-1][0], rF, 1)):
        top = max(p[1] for p in pr); c = np.array([0, (Y0 + top) / 2, z_])
        def uv(p):
            s = (p[0] + VW / 2) / VW if o > 0 else (VW / 2 - p[0]) / VW
            return lerp_uv(r, s, (p[1] - Y0) / (top - Y0))
        cuv = uv(c)
        for j in range(npt):
            p0, p1 = np.array([pr[j][0], pr[j][1], z_]), np.array([pr[(j + 1) % npt][0], pr[(j + 1) % npt][1], z_])
            m.face([c, p0, p1], [cuv, uv(p0), uv(p1)], (0, 0, o))
    if door_open:                                                           # porte coulissante côté -x local = droite du véhicule
        dz0, dz1, dy0, dy1 = DOOR; x = -VW / 2; yb, yt = Y0 + 0.25, YT - 0.7
        def S(z0_, z1_, y0_, y1_):
            P = [np.array([x, y0_, z0_]), np.array([x, y0_, z1_]), np.array([x, y1_, z1_]), np.array([x, y1_, z0_])]
            m.q(P, [side_uv(p, -1) for p in P], (-1, 0, 0))
        S(zr, dz0, yb, yt); S(dz1, CAB, yb, yt); S(dz0, dz1, dy1, yt); S(dz0, dz1, yb, dy0)
        # intérieur (vu par la porte) : sol, plafond, fond, cloisons
        ri = _interior(A); FL, WH = A.s((70, 72, 76)), A.s((226, 228, 230))
        xo_, xb_, zi0, zi1, yf, yc = -VW / 2 + 0.02, VW / 2 - 0.15, zr + 0.3, CAB - 0.3, dy0 + 0.05, YT - 0.75
        m.q([(xo_, yf, zi0), (xb_, yf, zi0), (xb_, yf, zi1), (xo_, yf, zi1)], ruv(FL), (0, 1, 0))
        m.q([(xo_, yc, zi0), (xb_, yc, zi0), (xb_, yc, zi1), (xo_, yc, zi1)], ruv(WH), (0, -1, 0))
        P = [np.array([xb_, yf, zi0]), np.array([xb_, yf, zi1]), np.array([xb_, yc, zi1]), np.array([xb_, yc, zi0])]
        m.q(P, [lerp_uv(ri, (p[2] - zi0) / (zi1 - zi0), (p[1] - yf) / (yc - yf)) for p in P], (-1, 0, 0))
        for zz, o in ((zi0, 1), (zi1, -1)):
            m.q([(xo_, yf, zz), (xb_, yf, zz), (xb_, yc, zz), (xo_, yc, zz)], ruv(WH), (0, 0, o))
        for zz, o in ((dz0, 1), (dz1, -1)):                                  # chants de la baie
            m.q([(x, dy0, zz), (xo_, dy0, zz), (xo_, dy1, zz), (x, dy1, zz)], ruv(BODY), (0, 0, o))
        m.q([(x, dy1, dz0), (xo_, dy1, dz0), (xo_, dy1, dz1), (x, dy1, dz1)], ruv(BODY), (0, -1, 0))
        # servante Beta contre la paroi du fond, face à la porte + étagère bois et caisson alu au-dessus
        rb = _beta(A); zc = (dz0 + dz1) / 2; bx1 = xb_ - 0.2
        box(m, (bx1 - 1.6, yf, zc - 1.3), (bx1, yf + 2.2, zc + 1.3), A.s((58, 60, 64)), faces="xzZY", rs={"x": rb})
        box(m, (bx1 - 2.4, yf + 2.2, zc - 1.5), (bx1, yf + 2.35, zc + 1.5), A.s((205, 178, 130)), faces="xzZYy")
        box(m, (bx1 - 1.9, yf + 2.35, zc - 1.4), (bx1, yf + 2.9, zc + 1.4), A.s((196, 198, 202)), faces="xzZY")
        box(m, (bx1 - 0.25, yf, zc + 1.6), (bx1, yf + 1.2, zc + 1.85), A.s((30, 30, 32)))  # support de roue
        # porte coulissante ouverte : décalée vers l'arrière, contre le flanc (même livrée)
        sh = (dz1 - dz0) * 0.95; xo = x - 0.14
        P = [np.array([xo, dy0, dz0 - sh]), np.array([xo, dy0, dz1 - sh]), np.array([xo, dy1, dz1 - sh]), np.array([xo, dy1, dz0 - sh])]
        m.q(P, [side_uv(p + np.array([0, 0, sh]), -1) for p in P], (-1, 0, 0))
        m.q(P, ruv(A.s((90, 92, 96))), (1, 0, 0))
        box(m, (xo, dy1, dz0 - sh), (x, dy1 + 0.08, dz1 - sh), BODY, faces="Yzz")
    # roues (un peu dehors : passage de roue dessiné sur le flanc), rétroviseurs, galerie
    for za in (-5.8, 7.6):
        for sx in (-1, 1):
            wheel(m, A, sx * (VW / 2 - 0.12), 1.2, za, 1.2, 0.75)
    for sx in (-1, 1):
        box(m, (sx * VW / 2 + (0 if sx > 0 else -0.55), 5.6, CAB + 0.2), (sx * VW / 2 + (0.55 if sx > 0 else 0), 6.7, CAB + 0.45), DARK)
    name = "van_%s%s" % (kind, "_ouvert" if door_open else "")
    nt = write_jm(os.path.join(D, name + ".jm"), [(GLOSS, m)]); A.save(os.path.join(D, name + ".png")); return name + ".jm", name + ".png", nt


# ================================================================= Airstream (loueur Eden Street, photo 7)
AL, AW, AY0, AH = 27.0, 8.0, 1.3, 8.3                                     # longueur, largeur, bas de caisse, hauteur de caisse


def _air_side(front_left, door):
    W, H = int(AL * PX), int((AY0 + AH) * PX)
    a = np.linspace(214, 176, H)[:, None] * np.ones((1, W)); a += np.random.default_rng(4).normal(0, 2.0, (H, W))
    im = Image.fromarray(np.dstack([a, a + 2, a + 6, np.full_like(a, 255)]).clip(0, 255).astype(np.uint8), "RGBA"); d = ImageDraw.Draw(im)
    X = lambda zf: int(W * (1 - zf)) if front_left else int(W * zf); Yp = lambda y: int(H * (1 - y / (AY0 + AH)))
    for k in range(1, 9):
        x = X(k / 9); d.line([(x, 0), (x, H)], fill=(150, 152, 158, 255), width=2)          # joints des tôles
    for y in (2.4, 4.9, 7.4):
        d.line([(0, Yp(y)), (W, Yp(y))], fill=(160, 162, 168, 255), width=2)
    d.rectangle([0, Yp(2.3), W, Yp(2.0)], fill=(150, 152, 158, 255))
    for (z0, z1) in ((0.08, 0.2), (0.4, 0.5), (0.74, 0.92)):                  # fenêtres
        d.rounded_rectangle([min(X(z0), X(z1)), Yp(7.6), max(X(z0), X(z1)), Yp(5.5)], 14, fill=(38, 42, 52, 255), outline=(120, 122, 128, 255), width=4)
    if door:
        d.rounded_rectangle([min(X(0.27), X(0.36)), Yp(8.0), max(X(0.27), X(0.36)), Yp(1.6)], 16, outline=(110, 112, 118, 255), width=5)
        d.rounded_rectangle([min(X(0.29), X(0.34)), Yp(7.4), max(X(0.29), X(0.34)), Yp(6.0)], 8, fill=(38, 42, 52, 255))
        bx = (min(X(0.5), X(0.72)), Yp(5.1), max(X(0.5), X(0.72)), Yp(3.3))   # décal Eden Street (redessiné en texte)
        d.rounded_rectangle(bx, 40, fill=(28, 30, 34, 255))
        es = txt("ES", 140, (235, 235, 235), "arialbd.ttf"); nm = K.vstack([txt("EDEN STREET", 70, (235, 235, 235), "arial.ttf"),
                                                                           txt("Airstreams - Événementiel", 40, (210, 210, 210), "arial.ttf")], 10)
        fitc(im, K.hstack([es, nm], 30), bx, 0.12)
    return im


def airstream(D):
    A = Atlas(2048); m = M(); rP, rM = A.put(_air_side(True, True)), A.put(_air_side(False, False))
    BELLY, AF = A.s((60, 62, 66)), A.s((40, 40, 42)); n_sec, n_pr = 36, 14
    zs = np.linspace(-AL / 2, AL / 2, n_sec)
    f = lambda z: max(0.0, 1 - abs(2 * z / AL) ** 3.2) ** (1 / 3.2)
    def pt(z, t, half):
        # demi-section : t de 0 (bas) à 1 (haut, x = 0) ; superellipse n = 3
        th = t * np.pi / 2; n = 3.0
        x = (AW / 2) * f(z) * np.cos(th) ** (2 / n) * half; y = AY0 + AH * f(z) ** 0.9 * np.sin(th) ** (2 / n)
        return np.array([x, y, z])
    for half, r in ((1, rP), (-1, rM)):
        ts = np.linspace(0, 1, n_pr)
        G = np.array([[pt(z, t, half) for t in ts] for z in zs])
        def uv(p):
            s = (AL / 2 - p[2]) / AL if half > 0 else (p[2] + AL / 2) / AL
            return lerp_uv(r, s, p[1] / (AY0 + AH))
        for i in range(n_sec - 1):
            for j in range(n_pr - 1):
                P = [G[i, j], G[i + 1, j], G[i + 1, j + 1], G[i, j + 1]]
                o = np.array([P[0][0] * 0.5 + 0.001 * half, P[0][1] - AY0 - 1.0, P[0][2] * 0.6])
                m.q(P, [uv(p) for p in P], o)
        for i in range(n_sec - 1):                                          # fond
            a0, a1 = G[i, 0], G[i + 1, 0]
            m.q([a0, a1, np.array([0, AY0, a1[2]]), np.array([0, AY0, a0[2]])], ruv(BELLY), (0, -1, 0))
    for za in (-2.0, 0.6):                                                  # 2 essieux
        for sx in (-1, 1):
            wheel(m, A, sx * (AW / 2 - 0.55), 1.15, za, 1.15, 0.7)
    for sx in (-1, 1):                                                      # flèche (timon en A), cric, coffre à bouteilles
        m.tub((sx * 2.6, 1.0, AL / 2 - 1.5), (0, 1.0, AL / 2 + 3.6), 0.12, AF, 6)
    box(m, (-0.25, 0.8, AL / 2 + 3.4), (0.25, 1.25, AL / 2 + 4.1), AF)
    m.tub((0, 0.0, AL / 2 + 2.6), (0, 1.1, AL / 2 + 2.6), 0.12, AF, 6)
    box(m, (-1.6, 1.0, AL / 2 + 0.1), (1.6, 3.0, AL / 2 + 2.0), A.s((200, 203, 208)))
    # marchepied tôle larmée sous la porte (+x, z = 0,27-0,36 de l'avant) + comptoir bois avec machine à café (photo 7)
    zd = -AL / 2 + AL * 0.315; TL = A.s((150, 152, 156))
    box(m, (AW / 2 - 0.2, 0, zd - 1.4), (AW / 2 + 1.2, 0.65, zd + 1.4), TL); box(m, (AW / 2 - 0.2, 0.65, zd - 1.4), (AW / 2 + 0.55, 1.3, zd + 1.4), TL)
    WOOD = A.s((176, 132, 84)); zc = zd - 4.5
    box(m, (AW / 2 + 0.3, 0, zc - 2.2), (AW / 2 + 1.8, 3.4, zc + 2.2), WOOD)
    box(m, (AW / 2 + 0.6, 3.4, zc + 0.8), (AW / 2 + 1.4, 4.4, zc + 1.6), A.s((20, 20, 22)))
    nt = write_jm(os.path.join(D, "airstream.jm"), [(SHINY, m)]); A.save(os.path.join(D, "airstream.png")); return "airstream.jm", "airstream.png", nt


# ================================================================= moto (cross) sur béquille
BIKES = {   # plastiques, selle, béquille, plaque (fond, chiffres)
    "suzuki": ((250, 210, 0), (18, 18, 20), (250, 210, 0), ((250, 210, 0), (16, 16, 16))),
    "honda": ((206, 18, 28), (206, 18, 28), (206, 18, 28), ((255, 255, 255), (16, 16, 16))),
    "ktm": ((240, 112, 18), (20, 20, 22), (240, 112, 18), ((255, 255, 255), (16, 16, 16))),
    "yamaha": ((22, 60, 170), (22, 22, 26), (22, 22, 26), ((255, 255, 255), (16, 16, 16))),
    "kawa": ((60, 170, 40), (20, 20, 22), (20, 20, 22), ((255, 255, 255), (16, 16, 16))),
    "blanc": ((236, 236, 236), (20, 20, 22), (60, 60, 64), ((255, 255, 255), (16, 16, 16))),
    "triumph": ((24, 24, 26), (24, 24, 26), (24, 24, 26), ((255, 255, 255), (16, 16, 16))),
    "stark": ((28, 28, 30), (20, 20, 22), (28, 28, 30), ((255, 255, 255), (16, 16, 16))),
    "ycf": ((240, 240, 242), (20, 20, 22), (20, 20, 22), ((255, 255, 255), (16, 16, 16))),
    "ycf_jaune": ((24, 24, 26), (24, 24, 26), (250, 200, 0), ((250, 200, 0), (16, 16, 16))),
}


def bike(D, team, number=None, sc=1.0, name=None):
    """moto cross ~ 450 (empattement 4,9 ft, roues 21 / 19 pouces) sur béquille ; +z = avant. Forme créée (simplifiée).
    sc < 1 : pit bike (YCF, vidéo de Ryan : x 0,72)."""
    A = Atlas(512); m = M(); pl, seat, stand, (pbg, pfg) = BIKES[team]
    P_, S_, ST, AL_, EN, GO, BK = A.s(pl), A.s(seat), A.s(stand), A.s((175, 178, 182)), A.s((70, 72, 76)), A.s((214, 170, 50)), A.s((22, 22, 24))
    plate = Image.new("RGBA", (220, 180), pbg + (255,))
    if number:
        fitc(plate, txt(str(number), 150, pfg, "impact.ttf"), (10, 10, 210, 170), 0.05)
    rPl = A.put(plate)
    lift = 0.15; zr, zf = -2.45, 2.45; rr, rf = 1.08, 1.15
    wheel(m, A, 0, rr + lift, zr, rr, 0.42, tire=(26, 26, 28), rim=(30, 30, 32), hub=(120, 122, 126), seg=16)
    wheel(m, A, 0, rf + lift, zf, rf, 0.32, tire=(26, 26, 28), rim=(30, 30, 32), hub=(120, 122, 126), seg=16)
    for sx in (-1, 1):
        m.tub((sx * 0.27, rf + lift, zf), (sx * 0.27, 3.55, 1.55), 0.09, GO, 6)                     # fourche
        m.tub((sx * 0.25, 3.15, 1.35), (sx * 0.3, 1.35, -0.55), 0.07, AL_, 6)                     # cadre
        m.tub((sx * 0.3, 1.75, -0.5), (sx * 0.22, rr + lift, zr), 0.08, AL_, 6)                  # bras oscillant
        box(m, (0.12 if sx > 0 else -0.42, 2.5, 0.3), (0.42 if sx > 0 else -0.12, 3.2, 1.3), P_)   # ouïes
        box(m, (sx * 0.2 if sx > 0 else -0.46, 2.35, -1.75), (0.46 if sx > 0 else -0.2, 3.05, -0.55), P_)  # plaques latérales
    m.tub((-1.25, 3.85, 1.35), (1.25, 3.85, 1.35), 0.06, BK, 6)                                    # guidon
    box(m, (-0.3, 3.5, 1.35), (0.3, 3.75, 1.7), BK)
    box(m, (-0.36, 1.05, -0.5), (0.36, 2.45, 0.95), EN)                                             # moteur
    box(m, (-0.27, 3.05, -2.3), (0.27, 3.35, 0.6), S_)                                              # selle
    box(m, (-0.3, 2.75, 0.3), (0.3, 3.2, 1.25), P_)                                                 # réservoir
    m.q([(-0.33, 3.15, -2.0), (0.33, 3.15, -2.0), (0.22, 3.35, -3.2), (-0.22, 3.35, -3.2)], ruv(P_), (0, 1, 0))   # garde-boue arrière
    m.q([(-0.33, 3.15, -2.0), (0.33, 3.15, -2.0), (0.22, 3.35, -3.2), (-0.22, 3.35, -3.2)], ruv(P_), (0, -1, 0))
    m.q([(-0.25, rf + lift + rf + 0.18, 1.7), (0.25, rf + lift + rf + 0.18, 1.7), (0.2, rf + lift + rf + 0.05, 3.5), (-0.2, rf + lift + rf + 0.05, 3.5)], ruv(P_), (0, 1, 0))
    m.q([(-0.25, rf + lift + rf + 0.18, 1.7), (0.25, rf + lift + rf + 0.18, 1.7), (0.2, rf + lift + rf + 0.05, 3.5), (-0.2, rf + lift + rf + 0.05, 3.5)], ruv(P_), (0, -1, 0))
    pP = [np.array([-0.42, 2.85, 1.78]), np.array([0.42, 2.85, 1.78]), np.array([0.38, 3.55, 1.6]), np.array([-0.38, 3.55, 1.6])]
    m.q(pP, ruv(rPl), (0, 0.3, 1)); m.q(pP, ruv(P_), (0, -0.3, -1))                               # plaque avant
    m.tub((0.42, 2.0, 0.2), (0.38, 3.0, -2.6), 0.16, AL_, 8)                                        # silencieux
    box(m, (-0.42, 0, -0.45), (0.42, 1.0, 0.55), ST)                                               # béquille
    if sc != 1.0:
        for v in m.V:
            v[0] *= sc; v[1] *= sc; v[2] *= sc
    name = name or "moto_%s%s" % (team, "_%s" % number if number else "")
    nt = write_jm(os.path.join(D, name + ".jm"), [(GLOSS, m)]); A.save(os.path.join(D, name + ".png")); return name + ".jm", name + ".png", nt


# ================================================================= panneaux (bannières Suzuki, murs Honda, Shimoda, ACCÈS PISTE)
def _rollup_img(first, last, number):
    im = canvas(4.4, 7.6, (252, 210, 0)); W, H = im.size; d = ImageDraw.Draw(im)
    for k in range(7):                                                      # traits obliques plus foncés (photo)
        x = int(W * (k / 6)); d.polygon([(x, 0), (x + 60, 0), (x - 140, H), (x - 200, H)], fill=(238, 190, 0, 255))
    fitc(im, lg("suzuki_h"), (int(W * 0.1), int(H * 0.04), int(W * 0.9), int(H * 0.13)), 0.05)
    fitc(im, txt(first, 80, (20, 20, 20), "impact.ttf", italic=0.12), (int(W * 0.06), int(H * 0.16), int(W * 0.94), int(H * 0.24)), 0.04)
    fitc(im, txt(last, 160, (20, 20, 20), "impact.ttf", italic=0.12), (int(W * 0.04), int(H * 0.24), int(W * 0.96), int(H * 0.38)), 0.03)
    fitc(im, txt("RM-Z450", 70, (20, 20, 20), "arialbi.ttf"), (int(W * 0.25), int(H * 0.39), int(W * 0.75), int(H * 0.44)), 0.04)
    if number:
        fitc(im, txt(str(number), 300, (20, 20, 20), "impact.ttf", italic=0.12), (int(W * 0.15), int(H * 0.5), int(W * 0.85), int(H * 0.85)), 0.04)
    d.rectangle([0, int(H * 0.93), W, H], fill=(20, 20, 22, 255))
    return im


def rollup(D, first, last, number):
    A = Atlas(512); m = M(); r = A.put(_rollup_img(first, last, number)); B = A.s((40, 40, 44)); G = A.s((150, 150, 155))
    m.panel((0, 0.02), (0, 1), 4.4, 7.6, 0.35, r, two=G); box(m, (-2.3, 0, -0.45), (2.3, 0.35, 0.45), B)
    name = "banniere_suzuki_%s" % last.lower().replace("ç", "c")
    nt = write_jm(os.path.join(D, name + ".jm"), [(LIT, m)]); A.save(os.path.join(D, name + ".png")); return name + ".jm", name + ".png", nt


def honda_wall(D):
    """mur rétroéclairé du stand Honda (photos 4-5) : dégradé orange-rouge, HONDA blanc ; face avant non éclairée par le jeu
    (lumineuse), le reste noir."""
    A = Atlas(1024); f = M(); m = M(); W_, H_ = 16.0, 10.0
    im = canvas(W_, H_, (230, 70, 20)); a = np.asarray(im, float).copy(); hh = a.shape[0]
    g = np.linspace(0, 1, hh)[:, None]; a[..., 0] = 250 - 40 * g; a[..., 1] = 120 - 95 * g; a[..., 2] = 40 - 25 * g
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")
    fitc(im, lg("honda_white"), (int(im.size[0] * 0.1), int(hh * 0.3), int(im.size[0] * 0.9), int(hh * 0.62)), 0.04)
    r = A.put(im); BK = A.s((18, 18, 20))
    f.panel((0, 0.31), (0, 1), W_, H_, 0.0, r)
    box(m, (-W_ / 2, 0, -0.3), (W_ / 2, H_, 0.3), BK, faces="xXzY")
    nt = write_jm(os.path.join(D, "mur_honda_lumineux.jm"), [(UNLIT, f), (LIT, m)]); A.save(os.path.join(D, "mur_honda_lumineux.png"))
    return "mur_honda_lumineux.jm", "mur_honda_lumineux.png", nt


def shimoda_panel(D):
    """panneau pilote de la baie Shimoda (photo 6) : blanc + violet, nom et numéro, Honda ; PAS de photo du pilote."""
    A = Atlas(1024); m = M(); W_, H_ = 8.0, 9.0; im = canvas(W_, H_, (245, 245, 248)); W, H = im.size; d = ImageDraw.Draw(im)
    d.polygon([(int(W * 0.45), 0), (W, 0), (W, H), (int(W * 0.2), H)], fill=(88, 46, 150, 255))
    fitc(im, txt("JO", 120, (255, 255, 255), "impact.ttf"), (int(W * 0.5), int(H * 0.06), int(W * 0.95), int(H * 0.16)), 0.05)
    fitc(im, txt("SHIMODA", 160, (255, 255, 255), "impact.ttf"), (int(W * 0.4), int(H * 0.16), int(W * 0.97), int(H * 0.3)), 0.04)
    fitc(im, txt("30", 400, (255, 255, 255), "impact.ttf", italic=0.1), (int(W * 0.5), int(H * 0.36), int(W * 0.95), int(H * 0.74)), 0.04)
    fitc(im, lg("honda_white"), (int(W * 0.55), int(H * 0.82), int(W * 0.95), int(H * 0.92)), 0.04)
    fitc(im, lg("honda_red").rotate(90, expand=True), (int(W * 0.02), int(H * 0.08), int(W * 0.2), int(H * 0.7)), 0.04)
    r = A.put(im); BK = A.s((30, 30, 34))
    m.panel((0, 0.15), (0, 1), W_, H_, 0.2, r); box(m, (-W_ / 2, 0, -0.15), (W_ / 2, H_ + 0.2, 0.15), BK, faces="xXzY")
    nt = write_jm(os.path.join(D, "panneau_shimoda.jm"), [(LIT, m)]); A.save(os.path.join(D, "panneau_shimoda.png"))
    return "panneau_shimoda.jm", "panneau_shimoda.png", nt


def servante(D):
    """servante d'atelier rouge (photos 4-6) : caisson à tiroirs + plateau."""
    A = Atlas(512); m = M(); W_, H_, P_ = 2.6, 3.4, 1.5
    im = canvas(W_, H_, (196, 18, 24)); W, H = im.size; d = ImageDraw.Draw(im)
    for k in range(6):
        y = int(H * (0.12 + k * 0.14)); d.rectangle([8, y, W - 8, y + int(H * 0.12)], fill=(212, 26, 32, 255), outline=(120, 10, 14, 255), width=2)
        d.rectangle([int(W * 0.3), y + 6, int(W * 0.7), y + 11], fill=(200, 202, 206, 255))
    r = A.put(im); RD = A.s((180, 16, 22)); BK = A.s((24, 24, 26))
    box(m, (-W_ / 2, 0.35, -P_ / 2), (W_ / 2, H_, P_ / 2), RD, rs={"Z": r}); box(m, (-W_ / 2 - 0.05, H_, -P_ / 2 - 0.05), (W_ / 2 + 0.05, H_ + 0.12, P_ / 2 + 0.05), BK)
    for sx in (-1, 1):
        for sz in (-1, 1):
            box(m, (sx * 1.1 - 0.1, 0, sz * 0.6 - 0.1), (sx * 1.1 + 0.1, 0.35, sz * 0.6 + 0.1), BK)
    nt = write_jm(os.path.join(D, "servante_rouge.jm"), [(GLOSS, m)]); A.save(os.path.join(D, "servante_rouge.png")); return "servante_rouge.jm", "servante_rouge.png", nt


def acces_piste(D):
    A = Atlas(512); m = M(); W_, H_ = 2.6, 7.0; im = canvas(W_, H_, (238, 238, 240)); W, H = im.size; d = ImageDraw.Draw(im)
    fitc(im, txt("ACCÈS", 120, (20, 20, 24), "arialbd.ttf"), (10, int(H * 0.06), W - 10, int(H * 0.17)), 0.04)
    fitc(im, txt("PISTE", 120, (20, 20, 24), "arialbd.ttf"), (10, int(H * 0.17), W - 10, int(H * 0.28)), 0.04)
    fitc(im, txt("TRACK", 90, (90, 90, 96), "arialbd.ttf"), (10, int(H * 0.31), W - 10, int(H * 0.39)), 0.06)
    fitc(im, txt("ACCESS", 90, (90, 90, 96), "arialbd.ttf"), (10, int(H * 0.39), W - 10, int(H * 0.47)), 0.06)
    c = (W // 2, int(H * 0.7)); s = int(W * 0.3)                              # flèche rouge vers le bas à droite (photos 1 et 4)
    d.line([(c[0] - s, c[1] - s), (c[0] + s, c[1] + s)], fill=(214, 20, 26, 255), width=int(W * 0.08))
    d.polygon([(c[0] + s + 12, c[1] + s + 12), (c[0] + s - int(s * 0.9), c[1] + s + 12), (c[0] + s + 12, c[1] + s - int(s * 0.9))], fill=(214, 20, 26, 255))
    r = A.put(im); BK = A.s((40, 40, 44))
    m.panel((0, 0.08), (0, 1), W_, H_, 0.8, r, two=None); m.panel((0, -0.08), (0, -1), W_, H_, 0.8, r)
    box(m, (-W_ / 2, 0.8, -0.08), (W_ / 2, 0.8 + H_, 0.08), BK, faces="xXY"); box(m, (-0.9, 0, -0.6), (0.9, 0.8, 0.6), BK)
    nt = write_jm(os.path.join(D, "acces_piste.jm"), [(LIT, m)]); A.save(os.path.join(D, "acces_piste.png")); return "acces_piste.jm", "acces_piste.png", nt


def tapis(D, name, w, d_, col, border=(240, 240, 240)):
    A = Atlas(64); m = M(); C, B = A.s(col), A.s(border)
    box(m, (-w / 2, 0, -d_ / 2), (w / 2, 0.1, d_ / 2), C, faces="xXzZY")
    nt = write_jm(os.path.join(D, name + ".jm"), [(LIT, m)]); A.save(os.path.join(D, name + ".png")); return name + ".jm", name + ".png", nt


def auvent(D, L, d_, h0, h1, col=(206, 208, 212), name="auvent_suzuki"):
    """auvent accroché au flanc d'une remorque : toile de L x d_ ft, de h0 (côté remorque, z = 0) à h1 (bord, z = d_), 2 pieds."""
    A = Atlas(64); m = M(); C, U, LEG = A.s(col), A.s(tuple(int(c * 0.7) for c in col)), A.s((150, 152, 156))
    P = [np.array([-L / 2, h0, 0]), np.array([L / 2, h0, 0]), np.array([L / 2, h1, d_]), np.array([-L / 2, h1, d_])]
    m.q(P, ruv(C), (0, 1, 0.3)); m.q(P, ruv(U), (0, -1, -0.3))
    for x in (-L / 2 + 0.3, L / 2 - 0.3):
        box(m, (x - 0.08, 0, d_ - 0.25), (x + 0.08, h1, d_ - 0.09), LEG)
    nt = write_jm(os.path.join(D, name + ".jm"), [(LIT, m)]); A.save(os.path.join(D, name + ".png")); return name + ".jm", name + ".png", nt


def pieds_remorque(D):
    A = Atlas(64); m = M(); C = A.s((40, 40, 44))
    for x in (-3.2, 3.2):
        box(m, (x - 0.2, 0, -0.2), (x + 0.2, 4.2, 0.2), C); box(m, (x - 0.5, 0, -0.5), (x + 0.5, 0.15, 0.5), C)
    box(m, (-3.2, 2.4, -0.1), (3.2, 2.6, 0.1), C)
    nt = write_jm(os.path.join(D, "pieds_remorque.jm"), [(LIT, m)]); A.save(os.path.join(D, "pieds_remorque.png")); return "pieds_remorque.jm", "pieds_remorque.png", nt


# ================================================================= structure Honda à étage (photo 1 : balcon « HONDA », vitres rouges)
def honda_hospitality(D, L=96.0, Dp=28.0):
    """repère : longueur le long de x, +z = façade (côté allée). Rez : vitrage éclairé rouge ; étage en retrait de 6 ft avec terrasse,
    garde-corps à panneaux blancs « HONDA » (photo 1). Forme créée, dimensions ESTIMÉES."""
    A = Atlas(2048); lit, un = M(), M(); hz = Dp / 2
    BK, GR, WH, SL = A.s((22, 22, 24)), A.s((60, 62, 66)), A.s((236, 236, 238)), A.s((200, 202, 206))
    # vitrage rez : panneaux rouges lumineux avec montants
    g = canvas(L, 10.0, (200, 30, 26), px=20); W, H = g.size; a = np.asarray(g, float).copy()
    a[..., 0] = 215 - 60 * np.linspace(0, 1, H)[:, None]; a[..., 1] = 40; a[..., 2] = 32; g = Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA"); d = ImageDraw.Draw(g)
    for k in range(0, int(L / 6) + 1):
        x = int(W * k * 6 / L); d.rectangle([x - 5, 0, x + 5, H], fill=(30, 30, 32, 255))
    for y in (0.12, 0.88):
        d.rectangle([0, int(H * y) - 4, W, int(H * y) + 4], fill=(30, 30, 32, 255))
    for k in range(int(L / 4)):                                             # rangées de lumières (photo 4 : réglettes rouges)
        x = int(W * (k + 0.5) * 4 / L); d.rectangle([x - 20, int(H * 0.2), x + 20, int(H * 0.24)], fill=(255, 120, 100, 255))
    rg = A.put(g)
    un.panel((0, hz + 0.01), (0, 1), L, 10.0, 0.0, rg)
    box(lit, (-L / 2, 0, -hz), (L / 2, 10.0, hz), BK, faces="xXz")
    # dalle (bandeau blanc), étage, toit
    box(lit, (-L / 2, 10.0, -hz), (L / 2, 11.2, hz), WH)
    up = canvas(L, 8.6, (40, 42, 48), px=20); d = ImageDraw.Draw(up); W, H = up.size
    for k in range(0, int(L / 6) + 1):
        x = int(W * k * 6 / L); d.rectangle([x - 4, 0, x + 4, H], fill=(190, 192, 196, 255))
    for k in range(int(L / 4)):
        x = int(W * (k + 0.5) * 4 / L); d.rectangle([x - 16, int(H * 0.45), x + 16, int(H * 0.55)], fill=(230, 60, 50, 255))
    ru = A.put(up)
    box(lit, (-L / 2, 11.2, -hz), (L / 2, 19.8, hz - 6.0), GR, rs={"Z": ru}, faces="xXzZ")
    box(lit, (-L / 2 - 0.3, 19.8, -hz - 0.3), (L / 2 + 0.3, 20.8, hz - 5.7), WH)
    # garde-corps : panneaux blancs « HONDA » rouges, tous les 8 ft
    pn = canvas(8.0, 3.2, (245, 245, 246)); fitc(pn, lg("honda_red"), (20, 14, pn.size[0] - 20, pn.size[1] - 14), 0.12); rp = A.put(pn)
    n = int(L // 8.0)
    for k in range(n):
        x = -L / 2 + 8.0 * (k + 0.5) + (L - 8.0 * n) / 2
        lit.panel((x, hz - 0.1), (0, 1), 7.9, 3.2, 11.3, rp, two=WH)
    for x in (-L / 2 + 0.1, L / 2 - 0.1):
        lit.panel((x, hz - 3.0), (np.sign(x), 0), 6.0, 3.2, 11.3, WH, two=WH)
    # escalier extérieur (bout -x)
    for k in range(10):
        box(lit, (-L / 2 - 4.0, k * 1.1, hz - 4.0 + k * 0.0), (-L / 2, k * 1.1 + 0.25, hz - 1.0), SL)
    nt = write_jm(os.path.join(D, "honda_hospitality.jm"), [(UNLIT, un), (LIT, lit)]); A.save(os.path.join(D, "honda_hospitality.png"))
    return "honda_hospitality.jm", "honda_hospitality.png", nt


# ================================================================= écran géant + 2 écrans verticaux (mur de scène)
# v28 (photo de Ryan de Paris 2026 : grand écran ~3,8:1, 2 écrans de côté couchés ~1,6:1, presque collés, centrés un peu plus bas
# que le grand) : grand 64 x 17 m (bas 11 m, haut 28 m, sous la toiture : l'ancien montait à 30,5 m) ; côtés 15 x 9,1 m à 2,7 m
SCR_W, SCR_Y0, SCR_Y1 = 210.0, 36.1, 91.9
SIDE_W, SIDE_Y0, SIDE_Y1, SIDE_GAP = 49.2, 45.0, 74.9, 8.9                  # v28 : couchés (étaient 9 x 16 m debout)


def _sunset(W, H):
    """fond « coucher de soleil rétro » du visuel Supercross Paris (photo 1) : violet -> rose -> orange, bandes horizontales."""
    t = np.linspace(0, 1, H)[:, None, None]
    c0, c1, c2, c3 = np.array([40, 10, 60.]), np.array([120, 20, 110.]), np.array([235, 60, 120.]), np.array([255, 170, 40.])
    col = np.where(t < 0.45, c0 + (c1 - c0) * (t / 0.45), np.where(t < 0.75, c1 + (c2 - c1) * ((t - 0.45) / 0.3), c2 + (c3 - c2) * ((t - 0.75) / 0.25)))
    a = np.broadcast_to(col, (H, W, 3)).copy()
    for k in range(9):                                                      # bandes sombres en bas (style rétro)
        y = int(H * (0.72 + k * 0.032)); a[y:y + max(2, int(H * 0.006 * (k + 1))), :] = c0
    return Image.fromarray(a.clip(0, 255).astype(np.uint8)).convert("RGBA")


def screen(D):
    A = Atlas(2048); un, lit = M(), M(); BK = A.s((14, 14, 16))
    hW = 2048; hH = int(hW * (SCR_Y1 - SCR_Y0) / SCR_W)
    main = _sunset(hW, hH); fitc(main, lg("sxparis").filter(ImageFilter.SMOOTH), (int(hW * 0.2), int(hH * 0.08), int(hW * 0.8), int(hH * 0.8)), 0.02)
    rM = A.put(main)
    sw = 700; sh = int(sw * (SIDE_Y1 - SIDE_Y0) / SIDE_W)
    side = _sunset(sw, sh); fitc(side, lg("sxparis"), (20, int(sh * 0.25), sw - 20, int(sh * 0.6)), 0.03); rS = A.put(side)
    un.panel((0, 1.02), (0, 1), SCR_W, SCR_Y1 - SCR_Y0, SCR_Y0, rM)
    box(lit, (-SCR_W / 2 - 1.5, SCR_Y0 - 1.5, 0), (SCR_W / 2 + 1.5, SCR_Y1 + 1.5, 1.0), BK, faces="xXyYZ")
    for sx in (-1, 1):
        cx = sx * (SCR_W / 2 + SIDE_GAP + SIDE_W / 2)
        un.panel((cx, 1.02), (0, 1), SIDE_W, SIDE_Y1 - SIDE_Y0, SIDE_Y0, rS)
        box(lit, (cx - SIDE_W / 2 - 1.0, SIDE_Y0 - 1.0, 0), (cx + SIDE_W / 2 + 1.0, SIDE_Y1 + 1.0, 1.0), BK, faces="xXyYZ")
    nt = write_jm(os.path.join(D, "ecran_geant.jm"), [(UNLIT, un), (LIT, lit)]); A.save(os.path.join(D, "ecran_geant.png"))
    return "ecran_geant.jm", "ecran_geant.png", nt


# ================================================================= semi-remorques (JGSX2026Scuttle, peau repeinte)
def _bud_side(W, H, front_right):
    """flanc du semi Bud Racing (photos de Ryan) : noir, double filet vert, BUD racing, Kawasaki, KX. Le grand logo blanc de
    l'arrière (illisible) n'est pas refait."""
    im = Image.new("RGBA", (W, H), (14, 14, 14, 255)); d = ImageDraw.Draw(im)
    X = lambda f: int(W * f) if front_right else int(W * (1 - f))          # f = 0 arrière, 1 avant
    d.rectangle([0, int(H * 0.52), W, int(H * 0.545)], fill=(40, 170, 60, 255)); d.rectangle([0, int(H * 0.57), W, int(H * 0.64)], fill=(40, 170, 60, 255))
    b = (min(X(0.38), X(0.66)), int(H * 0.04), max(X(0.38), X(0.66)), int(H * 0.36)); fitc(im, lg("bud"), b, 0.04)
    fitc(im, K.logo("kawasaki"), (min(X(0.4), X(0.64)), int(H * 0.36), max(X(0.4), X(0.64)), int(H * 0.5)), 0.08)
    fitc(im, txt("KX", 300, (40, 170, 60), "ariblk.ttf", italic=0.2, stroke=6, sf=(255, 255, 255)), (min(X(0.78), X(0.95)), int(H * 0.2), max(X(0.78), X(0.95)), int(H * 0.5)), 0.05)
    return im


def _suzuki_side(W, H, front_right):
    """flanc du semi Suzuki (photo 1) : gris alu, bande lumineuse en haut, bandeau jaune S SUZUKI, boîte MOTUL, bas vitré."""
    a = np.linspace(205, 170, H)[:, None] * np.ones((1, W)); im = Image.fromarray(np.dstack([a, a + 2, a + 6, np.full_like(a, 255)]).astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(im); X = lambda f: int(W * f) if front_right else int(W * (1 - f))
    d.rectangle([0, 0, W, int(H * 0.06)], fill=(250, 250, 245, 255))
    d.rectangle([0, int(H * 0.5), W, int(H * 0.94)], fill=(36, 40, 48, 255))
    for k in range(13):
        x = int(W * k / 12); d.rectangle([x - 4, int(H * 0.5), x + 4, int(H * 0.94)], fill=(150, 152, 158, 255))
    b = (min(X(0.42), X(0.68)), int(H * 0.12), max(X(0.42), X(0.68)), int(H * 0.42)); d.rectangle(b, fill=(252, 210, 0, 255))
    fitc(im, lg("suzuki_h"), b, 0.1)
    fitc(im, lg("motul"), (min(X(0.08), X(0.32)), int(H * 0.1), max(X(0.08), X(0.32)), int(H * 0.44)), 0.02)
    d.rectangle([min(X(0.74), X(0.88)), int(H * 0.16), max(X(0.74), X(0.88)), int(H * 0.36)], fill=(34, 38, 46, 255))   # fenêtre haute
    return im


PLAIN = {"noir": (20, 20, 22), "rouge": (176, 22, 26), "milwaukee": (214, 1, 26), "vhr": (21, 58, 156), "noir_rouge": (20, 20, 22), "rbt": (22, 22, 24), "honda_semi": (240, 240, 242)}
PLAIN_LOGO = {"milwaukee": "milwaukee", "vhr": "vhr", "noir_rouge": "bande_rouge", "rbt": "rbt", "honda_semi": "honda_semi"}


def _plain_side(W, H, col, logo=None):
    im = Image.new("RGBA", (W, H), col + (255,)); d = ImageDraw.Draw(im)
    for k in range(1, 8):
        x = int(W * k / 8); d.line([(x, 0), (x, H)], fill=tuple(int(c * 0.8) for c in col) + (255,), width=3)
    d.rectangle([0, int(H * 0.9), W, H], fill=(18, 18, 20, 255))
    if logo == "rbt":
        a = np.asarray(im, float).copy(); g = np.linspace(1.0, 0.7, H)[:, None, None]; a[..., :3] *= g; im.paste(Image.fromarray(a.astype(np.uint8), "RGBA"))
        d = ImageDraw.Draw(im)
        for k, (c, w_) in enumerate((((200, 20, 26), 0.035), ((240, 240, 240), 0.012), ((200, 20, 26), 0.012))):
            x0 = int(W * (0.62 + 0.05 * k))
            d.polygon([(x0, 0), (x0 + int(W * w_), 0), (x0 + int(W * w_) - int(H * 0.6), H), (x0 - int(H * 0.6), H)], fill=c + (255,))
        d.rectangle([0, int(H * 0.82), W, int(H * 0.84)], fill=(200, 20, 26, 255))
        rbt = Image.open(os.path.join(K.LOGOS, "rbt_wide.png")).convert("RGBA"); rbt = K.tint(rbt.crop(rbt.getbbox()), (245, 245, 245))
        fitc(im, rbt, (int(W * 0.08), int(H * 0.1), int(W * 0.56), int(H * 0.8)), 0.04)
        fitc(im, rbt, (int(W * 0.8), int(H * 0.3), int(W * 0.97), int(H * 0.7)), 0.06)
    if logo == "honda_semi":
        a = np.asarray(im, float).copy(); g = np.linspace(1.0, 0.86, H)[:, None, None]; a[..., :3] *= g; im.paste(Image.fromarray(a.astype(np.uint8), "RGBA"))
        d = ImageDraw.Draw(im)
        for k, (c, w_) in enumerate((((204, 16, 26), 0.035), ((24, 24, 26), 0.012), ((204, 16, 26), 0.012))):
            x0 = int(W * (0.62 + 0.05 * k))
            d.polygon([(x0, 0), (x0 + int(W * w_), 0), (x0 + int(W * w_) - int(H * 0.6), H), (x0 - int(H * 0.6), H)], fill=c + (255,))
        d.rectangle([0, int(H * 0.9), W, H], fill=(255, 40, 40, 255))
        fitc(im, lg("honda_red"), (int(W * 0.08), int(H * 0.12), int(W * 0.56), int(H * 0.56)), 0.04)
        fitc(im, txt("HRC", 260, (24, 24, 26), "ariblk.ttf", italic=0.15), (int(W * 0.2), int(H * 0.58), int(W * 0.44), int(H * 0.86)), 0.05)
    if logo == "bande_rouge":
        d.rectangle([0, int(H * 0.62), W, int(H * 0.72)], fill=(200, 20, 26, 255))
    if logo == "milwaukee":
        fitc(im, lg("milwaukee"), (int(W * 0.25), int(H * 0.08), int(W * 0.75), int(H * 0.86)), 0.04)
    elif logo == "vhr":                           # VHR redessiné en texte (pas de fichier) + Yamaha (texture ZION)
        fitc(im, K.hstack([txt("VHR", 300, (255, 255, 255), "ariblk.ttf", italic=0.15), K.logo("yamaha")], 80), (int(W * 0.2), int(H * 0.12), int(W * 0.8), int(H * 0.8)), 0.04)
    return K.shade_v(im, (0, 0, W, H), 1.0, 0.85)


def semi(D, team, tractor=True):
    import semi_jgsx as SJ
    src = SJ.model(D) and os.path.join(D, "semi_jgsx.jm")
    L = open(src).read().split("\n"); os.remove(src)
    if not tractor:                                                         # remorque seule : triangles dont un sommet dépasse z = -12,3
        out, i = [L[0]], 1
        while i < len(L) - 1 and L[i].strip():
            mat = L[i]; nv, nt = map(int, L[i + 1].split()); V = L[i + 2:i + 2 + nv]; j = i + 2 + nv
            three = len(L[j].split()) == 3; n_idx = nt if three else 3 * nt
            idx = [int(t) for l in L[j:j + n_idx] for t in l.split()]; zz = np.array([float(v.split()[2]) for v in V]); yy = np.array([float(v.split()[1]) for v in V])
            # tracteur : cabine (un sommet en avant de z = -8 ; la face avant de la remorque est vers -12) et essieux moteurs SOUS
            # l'avant de la remorque (triangle entièrement à z > -26 et y < 4,6)
            T_ = np.array(idx).reshape(-1, 3)
            bad = (zz[T_].max(1) > -8.0) | ((zz[T_].min(1) > -26.0) & (yy[T_].max(1) < 4.6))
            keep = [list(t) for t, b_ in zip(T_, bad) if not b_]
            out += [mat, "%d %d" % (nv, len(keep))] + V + [" ".join(map(str, t)) for t in keep]; i = j + n_idx
        L = out + [""]
    if team == "honda_semi":                                                # v22l : sans la rampe ni les portes ouvertes à l'arrière
        out, i = [L[0]], 1
        while i < len(L) - 1 and L[i].strip():
            mat = L[i]; nv, nt = map(int, L[i + 1].split()); V = L[i + 2:i + 2 + nv]; j = i + 2 + nv
            three = len(L[j].split()) == 3; n_idx = nt if three else 3 * nt
            idx = [int(t) for l in L[j:j + n_idx] for t in l.split()]; zz = np.array([float(v.split()[2]) for v in V]); yy = np.array([float(v.split()[1]) for v in V])
            T_ = np.array(idx).reshape(-1, 3); keep = [list(t) for t in T_ if zz[t].min() > -74.6]
            out += [mat, "%d %d" % (nv, len(keep))] + V + [" ".join(map(str, t)) for t in keep]; i = j + n_idx
        L = out + [""]
    name = "semi_%s%s" % (team, "" if tractor else "_remorque")
    open(os.path.join(D, name + ".jm"), "w", newline="\n").write("\n".join(L))
    base = Image.open(SJ._src("ws_semiskin.png")).convert("RGB"); d = ImageDraw.Draw(base)
    fn = {"bud": _bud_side, "suzuki": _suzuki_side}.get(team) or (lambda W, H, fr: _plain_side(W, H, PLAIN[team], PLAIN_LOGO.get(team)))
    for k, (x0, y0, x1, y1) in enumerate(SJ.PANELS):                       # PANELS[0] = flanc -x (avant à droite), [1] = flanc +x
        base.paste(fn(x1 - x0, y1 - y0, k == 0).convert("RGB"), (x0, y0))
    d.rectangle(SJ.ROOF, fill=(200, 202, 206) if team in ("suzuki", "honda_semi") else (18, 18, 20))
    for r_ in SJ.SKIRTS:
        d.rectangle(r_, fill=(18, 18, 20))
    base.save(os.path.join(D, name + ".png"), optimize=True)
    return name + ".jm", name + ".png", None


# ================================================================= objets courants de paddock, SANS marque (remplissage, demandé par Ryan)
def tente_arche(D):
    """tente arche gonflable noire (photo 1, devant les tentes KTM) : 4 pieds gonflés courbes + dôme ; 16 x 16 ft, 11 ft (ESTIMÉ)."""
    A = Atlas(64); m = M(); B, U = A.s((22, 22, 24)), A.s((12, 12, 14)); n = 12; h0, h1, a = 7.6, 11.0, 8.0
    def y(u, v):
        return h0 + (h1 - h0) * (1 - max(abs(u), abs(v)) ** 2)
    for i in range(n):
        for j in range(n):
            us = [-1 + 2 * i / n, -1 + 2 * (i + 1) / n]; vs = [-1 + 2 * j / n, -1 + 2 * (j + 1) / n]
            P = [np.array([a * uu, y(uu, vv), a * vv]) for uu, vv in ((us[0], vs[0]), (us[1], vs[0]), (us[1], vs[1]), (us[0], vs[1]))]
            m.q(P, ruv(B), (0, 1, 0)); m.q(P, ruv(U), (0, -1, 0))
    for sx in (-1, 1):
        for sz in (-1, 1):
            pts = [(sx * 9.0, 0.0, sz * 9.0), (sx * 8.6, 3.5, sz * 8.6), (sx * 8.0, 6.5, sz * 8.0), (sx * 7.0, 8.6, sz * 7.0)]
            for p0, p1 in zip(pts[:-1], pts[1:]):
                m.tub(p0, p1, 0.55, B, 8)
    nt = write_jm(os.path.join(D, "tente_arche.jm"), [(LIT, m)]); A.save(os.path.join(D, "tente_arche.png")); return "tente_arche.jm", "tente_arche.png", nt


def gant_five(D):
    """gant gonflable Five (photo de Ryan) : main rouge, index et majeur levés (V), FIVE sur l'index, logo 5 blanc sur la paume,
    manchette noire ; ~18 ft de haut (ESTIMÉ). Forme créée."""
    A = Atlas(1024); m = M(); R_, BK, WH = A.s((206, 22, 30)), A.s((24, 24, 26)), A.s((240, 240, 240))
    cyl(m, (0, 0), 3.0, 0, 3.2, BK, 20, top=BK)                                  # manchette
    pr = canvas(7.0, 7.0, (206, 22, 30)); fitc(pr, K.tint(K.logo("five"), (255, 255, 255)), (40, 40, pr.size[0] - 40, pr.size[1] - 40), 0.12)
    rp = A.put(pr)
    box(m, (-3.5, 3.2, -1.7), (3.5, 10.2, 1.7), R_, rs={"Z": rp, "z": rp})           # paume
    fn = canvas(1.6, 7.0, (206, 22, 30)); fitc(fn, txt("FIVE", 200, (255, 255, 255), "ariblk.ttf").rotate(90, expand=True), (8, 20, fn.size[0] - 8, fn.size[1] - 20), 0.06)
    rf = A.put(fn)
    for (x0, lean) in ((-1.9, -0.25), (0.2, 0.15)):                              # index (FIVE) et majeur, en V
        a, b = np.array([x0, 10.2, 0.0]), np.array([x0 + lean * 7.5, 17.6, 0.0]); m.tub(a, b, 0.95, R_, 12)
        cyl(m, (b[0], 0.0), 0.95, b[1] - 0.01, b[1] + 0.6, R_, 12, top=R_)
    P = [np.array([-1.9 - 0.8, 10.6, 0.97]), np.array([-1.9 + 0.8, 10.6, 0.97]), np.array([-1.9 + 0.8 - 1.8, 17.0, 0.97]), np.array([-1.9 - 0.8 - 1.8, 17.0, 0.97])]
    m.q(P, ruv(rf), (0, 0, 1))
    for x0 in (1.7, 3.0):                                                        # annulaire et auriculaire repliés
        m.tub((x0, 10.3, -1.4), (x0, 10.3, 1.6), 0.75, R_, 10)
    m.tub((-3.4, 6.5, 0.5), (-1.0, 9.8, 1.9), 0.85, R_, 10)                        # pouce
    nt = write_jm(os.path.join(D, "gant_five.jm"), [(LIT, m)]); A.save(os.path.join(D, "gant_five.png")); return "gant_five.jm", "gant_five.png", nt


def rider_panel(D, first, last, num, bg, accent, ink):
    """panneau pilote du stand Honda (photos 6 et 8) : nom, numéro, HONDA ; PAS de photo du pilote."""
    A = Atlas(1024); m = M(); W_, H_ = 8.0, 9.0; im = canvas(W_, H_, bg); W, H = im.size; d = ImageDraw.Draw(im)
    d.polygon([(int(W * 0.45), 0), (W, 0), (W, H), (int(W * 0.2), H)], fill=accent + (255,))
    fitc(im, txt(first, 120, ink, "impact.ttf"), (int(W * 0.45), int(H * 0.06), int(W * 0.95), int(H * 0.16)), 0.05)
    fitc(im, txt(last, 160, ink, "impact.ttf"), (int(W * 0.38), int(H * 0.16), int(W * 0.97), int(H * 0.3)), 0.04)
    fitc(im, txt(str(num), 400, ink, "impact.ttf", italic=0.1), (int(W * 0.5), int(H * 0.36), int(W * 0.95), int(H * 0.74)), 0.04)
    fitc(im, K.tint(lg("honda_red"), ink), (int(W * 0.55), int(H * 0.82), int(W * 0.95), int(H * 0.92)), 0.04)
    fitc(im, lg("honda_red").rotate(90, expand=True), (int(W * 0.02), int(H * 0.08), int(W * 0.2), int(H * 0.7)), 0.04)
    r = A.put(im); B_ = A.s((30, 30, 34))
    m.panel((0, 0.15), (0, 1), W_, H_, 0.2, r); box(m, (-W_ / 2, 0, -0.15), (W_ / 2, H_ + 0.2, 0.15), B_, faces="xXzY")
    name = "panneau_%s" % last.lower()
    nt = write_jm(os.path.join(D, name + ".jm"), [(LIT, m)]); A.save(os.path.join(D, name + ".png")); return name + ".jm", name + ".png", nt


def camion_porteur(D, name, logo_side, band=(204, 16, 26)):
    """porteur 2 essieux (cabine + caisse 24 ft), blanc, bandeau lumineux rouge en bas de caisse (photo 1, « gros camion » Honda),
    HONDA + HRC sur les flancs. +z = avant (cabine). Forme créée."""
    A = Atlas(2048); lit, un = M(), M(); WH, BK, GL = A.s((240, 240, 242)), A.s((24, 24, 26)), A.s((34, 38, 46))
    L_, W_, y0, y1 = 24.0, 8.2, 3.4, 12.6
    im = canvas(L_, y1 - y0, (240, 240, 242)); d = ImageDraw.Draw(im); Wp, Hp = im.size
    d.rectangle([0, int(Hp * 0.86), Wp, Hp], fill=band + (255,))
    fitc(im, logo_side, (int(Wp * 0.12), int(Hp * 0.12), int(Wp * 0.88), int(Hp * 0.55)), 0.04)
    fitc(im, txt("HRC", 200, band, "ariblk.ttf", italic=0.15), (int(Wp * 0.3), int(Hp * 0.58), int(Wp * 0.7), int(Hp * 0.82)), 0.05)
    rs = A.put(im); rb = A.put(Image.fromarray(np.full((64, 256, 3), band, np.uint8)))
    z0, z1 = -L_ / 2 - 4.0, L_ / 2 - 4.0                                     # caisse (la cabine devant)
    box(lit, (-W_ / 2, y0, z0), (W_ / 2, y1, z1), WH, rs={"x": rs, "X": rs}, faces="xXzZY")
    box(un, (-W_ / 2 - 0.02, y0 - 0.35, z0), (W_ / 2 + 0.02, y0, z1), rb, faces="xXz")          # lumière rouge (non éclairée)
    box(lit, (-3.2, 1.6, z0 + 1.0), (3.2, 2.4, z1 + 7.6), BK)                                    # châssis
    zc0, zc1 = z1 + 0.4, z1 + 7.8                                              # cabine
    box(lit, (-W_ / 2, 2.2, zc0), (W_ / 2, 10.2, zc1 - 1.2), WH, faces="xXzY")
    P = [np.array([-W_ / 2, 6.4, zc1]), np.array([W_ / 2, 6.4, zc1]), np.array([W_ / 2, 10.2, zc1 - 1.2]), np.array([-W_ / 2, 10.2, zc1 - 1.2])]
    lit.q(P, ruv(GL), (0, 0.3, 1))                                            # pare-brise incliné
    box(lit, (-W_ / 2, 2.2, zc1 - 1.2), (W_ / 2, 6.4, zc1), WH, faces="xXZ")
    box(lit, (-W_ / 2 - 0.05, 6.6, zc0 + 2.5), (W_ / 2 + 0.05, 9.2, zc1 - 1.6), GL, faces="xX")   # vitres latérales
    box(lit, (-W_ / 2, 1.6, zc1 - 0.1), (W_ / 2, 2.6, zc1 + 0.4), BK)                            # pare-chocs
    for za in (z1 + 4.2, z0 + 5.0, z0 + 8.4):
        for sx in (-1, 1):
            wheel(lit, A, sx * (W_ / 2 - 0.6), 1.65, za, 1.65, 0.9)
    nt = write_jm(os.path.join(D, name + ".jm"), [(UNLIT, un), (GLOSS, lit)]); A.save(os.path.join(D, name + ".png"))
    return name + ".jm", name + ".png", nt


def camion_vente(D, name, col, logo):
    """camion de vente à 2 niveaux (Ryan : « en 2 fois, tu peux monter, t'as une place pour vendre ») : remorque 48 ft, côté +x
    ouvert sur un comptoir de vente (étagères d'outils, volet relevé en auvent), terrasse sur le toit avec garde-corps à logo et
    escalier à l'arrière. +z = avant. Forme créée."""
    A = Atlas(2048); m = M(); C, BK, GR, WD = A.s(col), A.s((24, 24, 26)), A.s((150, 152, 156)), A.s((60, 60, 64))
    L_, W_, y0, y1 = 48.0, 8.5, 3.6, 13.4; hx, hz = W_ / 2, L_ / 2
    side = canvas(L_, y1 - y0, col, px=36); fitc(side, logo, (int(side.size[0] * 0.15), 20, int(side.size[0] * 0.85), side.size[1] - 20), 0.06)
    rS = A.put(side)
    box(m, (-hx, y0, -hz), (hx, y1, hz), C, faces="xzZ", rs={"x": rS})                                   # côté -x : grand logo
    o0, o1, oy0, oy1 = -17.0, 17.0, 6.6, 12.0                                                            # ouverture de vente (+x)
    for (za, zb_, ya, yb) in ((-hz, o0, y0, y1), (o1, hz, y0, y1), (o0, o1, oy1, y1), (o0, o1, y0, oy0)):
        m.q([np.array([hx, ya, zb_]), np.array([hx, ya, za]), np.array([hx, yb, za]), np.array([hx, yb, zb_])], ruv(C), (1, 0, 0))
    sh = canvas(o1 - o0, oy1 - oy0, (235, 235, 235), px=30); dsh = ImageDraw.Draw(sh); Ws, Hs = sh.size
    for k in range(1, 4):
        y_ = int(Hs * k / 4); dsh.rectangle([0, y_ - 6, Ws, y_ + 6], fill=(40, 40, 44, 255))
        for j in range(18):
            x_ = int(Ws * (j + 0.5) / 18); dsh.rectangle([x_ - 30, y_ - 70, x_ + 30, y_ - 8], fill=(200, 20, 30, 255) if j % 2 else (30, 30, 32, 255))
    rSh = A.put(sh)
    m.q([np.array([hx - 2.5, oy0, o0]), np.array([hx - 2.5, oy0, o1]), np.array([hx - 2.5, oy1, o1]), np.array([hx - 2.5, oy1, o0])], ruv(rSh), (1, 0, 0))
    m.q([np.array([hx - 2.5, oy0, o0]), np.array([hx, oy0, o0]), np.array([hx, oy0, o1]), np.array([hx - 2.5, oy0, o1])], ruv(GR), (0, 1, 0))
    m.q([np.array([hx - 2.5, oy1, o0]), np.array([hx - 2.5, oy1, o1]), np.array([hx, oy1, o1]), np.array([hx, oy1, o0])], ruv(BK), (0, -1, 0))
    for zz, o in ((o0, 1), (o1, -1)):
        m.q([np.array([hx - 2.5, oy0, zz]), np.array([hx - 2.5, oy1, zz]), np.array([hx, oy1, zz]), np.array([hx, oy0, zz])], ruv(C), (0, 0, o))
    box(m, (hx, oy0 - 0.2, o0), (hx + 1.0, oy0 + 0.1, o1), A.s((40, 40, 44)))                             # comptoir
    P = [np.array([hx, oy1 + 0.2, o0]), np.array([hx, oy1 + 0.2, o1]), np.array([hx + 4.5, oy1 - 0.8, o1]), np.array([hx + 4.5, oy1 - 0.8, o0])]
    m.q(P, ruv(C), (0.3, 1, 0)); m.q(P, ruv(WD), (-0.3, -1, 0))                                         # volet relevé
    box(m, (-hx, y1, -hz), (hx, y1 + 0.3, hz), GR, faces="xXzZY")                                       # plancher de la terrasse
    rail = canvas(12.0, 3.4, col, px=30); fitc(rail, logo, (20, 10, rail.size[0] - 20, rail.size[1] - 10), 0.1); rR = A.put(rail)
    for zc in (-18.0, -6.0, 6.0, 18.0):
        m.panel((hx, zc), (1, 0), 12.0, 3.4, y1 + 0.3, rR, two=GR); m.panel((-hx, zc), (-1, 0), 12.0, 3.4, y1 + 0.3, rR, two=GR)
    m.panel((0.0, hz), (0, 1), W_, 3.4, y1 + 0.3, rR, two=GR)
    for k in range(10):                                                                                  # escalier à l'arrière
        yy = y1 * (k + 1) / 10
        box(m, (-1.8, yy - 0.25, -hz - 1.2 * (10 - k)), (1.8, yy, -hz - 1.2 * (9 - k)), GR)
    box(m, (-hx, 1.8, -hz + 2), (hx, y0, hz - 2), BK, faces="xXzZ")                                      # châssis / jupes
    for za in (-hz + 4.5, -hz + 8.5):
        for sx in (-1, 1):
            wheel(m, A, sx * (hx - 0.7), 1.65, za, 1.65, 0.9)
    for sx in (-1, 1):
        box(m, (sx * 3.0 - 0.2, 0, hz - 6.2), (sx * 3.0 + 0.2, y0, hz - 5.8), BK)                       # béquilles avant
    nt = write_jm(os.path.join(D, name + ".jm"), [(GLOSS, m)]); A.save(os.path.join(D, name + ".png")); return name + ".jm", name + ".png", nt


def tapis_imprime(D, name, w, d_, base, logo):
    """moquette imprimée (vidéo YCF : bleu, traits noirs / blancs, logo) ; w (x) x d_ (z) ft."""
    A = Atlas(1024); m = M(); im = canvas(d_, w, base, px=20); dr = ImageDraw.Draw(im); W, H = im.size
    rng = np.random.default_rng(5)
    for _ in range(int(W * H / 900)):
        x, y = rng.uniform(0, W), rng.uniform(0, H); a = rng.uniform(0, np.pi); l_ = rng.uniform(15, 60)
        dr.line([(x, y), (x + l_ * np.cos(a), y + l_ * np.sin(a))], fill=(10, 10, 12, 255) if rng.random() < 0.6 else (235, 240, 245, 255), width=3)
    for k in range(3):
        fitc(im, logo, (int(W * (0.05 + 0.32 * k)), int(H * 0.3), int(W * (0.32 + 0.32 * k)), int(H * 0.7)), 0.08)
    r = A.put(im)
    P = [np.array([-w / 2, 0.1, d_ / 2]), np.array([-w / 2, 0.1, -d_ / 2]), np.array([w / 2, 0.1, -d_ / 2]), np.array([w / 2, 0.1, d_ / 2])]
    m.q(P, ruv(r), (0, 1, 0)); box(m, (-w / 2, 0, -d_ / 2), (w / 2, 0.1, d_ / 2), A.s(base), faces="xXzZ")
    nt = write_jm(os.path.join(D, name + ".jm"), [(LIT, m)]); A.save(os.path.join(D, name + ".png")); return name + ".jm", name + ".png", nt


def podium_noir(D):
    A = Atlas(64); m = M(); B_ = A.s((20, 20, 22))
    box(m, (-4.0, 0, -2.5), (4.0, 1.4, 2.5), B_, faces="xXzZY")
    nt = write_jm(os.path.join(D, "podium_noir.jm"), [(LIT, m)]); A.save(os.path.join(D, "podium_noir.png")); return "podium_noir.jm", "podium_noir.png", nt


def podium_ycf(D):
    """podium noir YCF (vidéo) : caisson 8 x 5 x 1,4 ft, logo YCF blanc sur les côtés, dessus bleu."""
    A = Atlas(512); m = M(); im = canvas(8.0, 1.4, (18, 18, 20)); fitc(im, K.tint(lg("ycf"), (255, 255, 255)), (10, 4, im.size[0] - 10, im.size[1] - 4), 0.1)
    r = A.put(im); B_, BL = A.s((18, 18, 20)), A.s((20, 110, 200))
    box(m, (-4.0, 0, -2.5), (4.0, 1.4, 2.5), B_, faces="xXzZ", rs={"Z": r, "z": r}); box(m, (-4.0, 1.39, -2.5), (4.0, 1.4, 2.5), BL, faces="Y")
    nt = write_jm(os.path.join(D, "podium_ycf.jm"), [(LIT, m)]); A.save(os.path.join(D, "podium_ycf.png")); return "podium_ycf.jm", "podium_ycf.png", nt


def table_haute(D):
    A = Atlas(64); m = M(); B, T_ = A.s((24, 24, 26)), A.s((236, 236, 238))
    cyl(m, (0, 0), 1.0, 0, 0.12, B, 12, top=B); cyl(m, (0, 0), 0.12, 0.12, 3.5, B, 8); cyl(m, (0, 0), 1.35, 3.5, 3.6, T_, 16, top=T_, bot=B)
    nt = write_jm(os.path.join(D, "table_haute.jm"), [(LIT, m)]); A.save(os.path.join(D, "table_haute.png")); return "table_haute.jm", "table_haute.png", nt


def groupe(D):
    """groupe électrogène insonorisé (caisson gris, grilles)."""
    A = Atlas(256); m = M(); im = canvas(6.0, 3.6, (150, 154, 158)); d = ImageDraw.Draw(im); W, H = im.size
    for k in range(10):
        y = int(H * (0.2 + k * 0.06)); d.line([(int(W * 0.55), y), (int(W * 0.95), y)], fill=(70, 72, 76, 255), width=4)
    d.rectangle([int(W * 0.08), int(H * 0.2), int(W * 0.45), int(H * 0.8)], outline=(90, 92, 96, 255), width=4)
    r = A.put(im); G = A.s((140, 144, 148))
    box(m, (-3.0, 0.3, -1.6), (3.0, 3.9, 1.6), G, rs={"Z": r, "z": r}); box(m, (-3.1, 0, -1.7), (3.1, 0.3, 1.7), A.s((40, 40, 44)))
    nt = write_jm(os.path.join(D, "groupe_electrogene.jm"), [(LIT, m)]); A.save(os.path.join(D, "groupe_electrogene.png")); return "groupe_electrogene.jm", "groupe_electrogene.png", nt


def caisses(D):
    """pile de caisses de transport (flight cases) noires à coins alu."""
    A = Atlas(256); m = M(); im = canvas(2.6, 2.0, (26, 26, 28)); d = ImageDraw.Draw(im); W, H = im.size
    d.rectangle([0, 0, W - 1, H - 1], outline=(180, 182, 186, 255), width=6)
    for cx, cy in ((0, 0), (W, 0), (0, H), (W, H)):
        d.rectangle([cx - 14, cy - 14, cx + 14, cy + 14], fill=(190, 192, 196, 255))
    r = A.put(im); B = A.s((26, 26, 28))
    for (x0, y0, z0) in ((-1.4, 0, -1.0), (1.4, 0, -1.0), (-1.4, 2.0, -1.0)):
        box(m, (x0 - 1.3, y0, z0 - 1.0), (x0 + 1.3, y0 + 2.0, z0 + 1.0), B, rs={"Z": r, "z": r})
    nt = write_jm(os.path.join(D, "caisses.jm"), [(LIT, m)]); A.save(os.path.join(D, "caisses.png")); return "caisses.jm", "caisses.png", nt


def barriere_num(D, n):
    """barrière Vauban avec plaque numérotée (photo 1 : 6, 8, 10, 12 au bout du paddock)."""
    A = Atlas(256); m = M(); G = A.s((168, 170, 172)); L = 6.6
    box(m, (-L / 2, 3.35, -0.06), (L / 2, 3.5, 0.06), G); box(m, (-L / 2, 0.5, -0.06), (L / 2, 0.62, 0.06), G)
    for x in (-L / 2, L / 2 - 0.12):
        box(m, (x, 0.35, -0.06), (x + 0.12, 3.6, 0.06), G)
    for k in range(1, 14):
        x = -L / 2 + L * k / 14; box(m, (x - 0.03, 0.62, -0.03), (x + 0.03, 3.35, 0.03), G)
    for x in (-L / 2 + 0.3, L / 2 - 0.3):
        box(m, (x - 0.06, 0, -1.0), (x + 0.06, 0.35, 1.0), G)
    im = canvas(1.4, 1.1, (250, 250, 250)); fitc(im, txt(str(n), 120, (16, 16, 16), "arialbd.ttf"), (4, 4, im.size[0] - 4, im.size[1] - 4), 0.08)
    r = A.put(im); m.panel((0, 0.09), (0, 1), 1.4, 1.1, 2.2, r); m.panel((0, -0.09), (0, -1), 1.4, 1.1, 2.2, r)
    name = "barriere_num_%d" % n
    nt = write_jm(os.path.join(D, name + ".jm"), [(LIT, m)]); A.save(os.path.join(D, name + ".png")); return name + ".jm", name + ".png", nt


# ================================================================= plan (coordonnées du jeu, ft) et pose
import layout_paris as _LP                                              # noqa: E402
X_WALL = _LP.OX + 62.0 * _LP.PLAN_K * _LP.FT                            # v28 : mur de scène (était 879,34 ft pour x1,624)
# v28 (stade x1,52, « essaie que le paddock passe quand même ») : tout le paddock recalé contre le mur de scène (même écart qu'avant)
# et resserré de 4 % en z autour de l'axe de l'arène (le sol fait 449 ft de large au lieu de 480) ; les objets gardent leur taille
PAD_DX = X_WALL - 879.34
# z : le paddock prenait 469 ft (357 -> 826), le sol n'en fait plus que 458 (x1,55) : les 2 bandes vides (passage « croix » 706-715,
# bande 818-824 avant les barrières numérotées) réduites à 4 ft et 1 ft ; le reste quasi intact (< 1 %), chaque stand bouge d'un bloc
PAD_ZK = [357.3, 706.0, 715.0, 818.0, 824.0, 826.0]
MUR_DOWN = 20.0   # v28z (« descends de 15 ft encore ») : 5 -> 20 ft
def pad_z(z):
    o = PAD_ZK; h = 45.0 * _LP.PLAN_K * _LP.FT; lo, hi = _LP.OZ - h + 1.0, _LP.OZ + h - 1.0
    f = min(1.0, ((hi - lo) - 5.0) / ((o[-1] - o[0]) - 15.0))
    n = [lo]; n.append(n[-1] + (o[1] - o[0]) * f); n.append(n[-1] + 4.0); n.append(n[-1] + (o[3] - o[2]) * f); n.append(n[-1] + 1.0); n.append(n[-1] + (o[5] - o[4]) * f)
    return float(np.interp(z, o, n))
YAW = lambda fx, fz: float(np.arctan2(fx, fz))
E, W_, N_, S_ = (1, 0), (-1, 0), (0, -1), (0, 1)                          # +x (vers le mur), -x (vers la piste), -z, +z (bout whoops)


BOX_W, BOX_D, BOX_PATH = 13.2, 13.2, 8.0                                 # box carrés 13,2 x 13,2 ft (2 barrières par côté), chemin de 8 ft
BOX_BIKES = ["vraie_ktm_usland_202", "vraie_honda_151", "vraie_gasgas", "vraie_husqvarna", "vraie_ktm_usland_9", "vraie_ktm_dew",
             "vraie_ktm_evo3", "vraie_crf_troy", "vraie_ryan", "vraie_ktm_usland_47", "vraie_ktm_usland_348", "vraie_ktm_usland_151",
             "vraie_ktm_usland_16", "vraie_honda_16"]                       # v22h : vraies motos du jeu (motos_jeu.py)
VRAIES = sorted(set(b[6:] for b in BOX_BIKES) | {"stark"})
PIT_NUMS = (7, 4, 16, 21, 30, 56, 31, 64)                                  # numéros vus sur les pit bikes YCF (vidéo)


def box_pair(P, x0, z0, n, tag, k0=0):
    """2 rangées de n box CARRÉS face à face (fond + 2 côtés en barrières, ouverts sur le chemin du milieu), moto au milieu."""
    k = k0
    for xs, o in ((x0, 1), (x0 + 2 * BOX_D + BOX_PATH, -1)):
        for i in range(n):
            zb = z0 + BOX_W * i
            P.append(("barriere_vauban", xs, zb + 3.3, (1, 0), tag)); P.append(("barriere_vauban", xs, zb + 9.9, (1, 0), tag))
            P.append((BOX_BIKES[k % len(BOX_BIKES)], xs + o * BOX_D / 2, zb + BOX_W / 2, (o, 0), tag)); k += 1
        for i in range(n + 1):
            for q in (3.3, 9.9):
                P.append(("barriere_vauban", xs + o * q, z0 + BOX_W * i, (0, 1), tag))
    return k


def plan():
    """liste (modèle, x, z, direction du +z local, commentaire).
    v22i (Ryan) : Honda : gros camion blanc (lumière rouge en bas, photo 1) derrière les pilotes, les 2 bus au fond du stand ;
    camion RBT (semi complète, stylée) à la place du camion noir ; Stark : 2 bus alignés + 5 tentes noires collées + vraies Stark
    (modèle du jeu, couleur unie : texture protégée non utilisée) ; YCF refait (moquettes imprimées, 2 rangées serrées de pit bikes
    face à l'allée, podiums) ; moto VHR à l'arrière du bus ; motos Bud dans l'autre sens."""
    P = []
    add = lambda k, x, z, f, c="": P.append((k, x, z, f, c))
    AL_Z = (1, 0)
    AL_X = (0, 1)
    XA = 789.0
    # ======================= rangée MUR, bout whoops (validé : Triumph, Airstream, Suzuki, box)
    for i in range(2):
        for j in range(2):
            add("tente_triumph", 796.0 + 10.2 * i, 786.0 + 10.2 * j, W_, "Triumph")
    for k in range(4):
        P.append(("barriere_triumph", XA, 780.0 + 6.7 * k + 3.3, AL_Z, "Triumph"))
    add("flamme_triumph", XA - 2.0, 776.0, W_, "Triumph"); add("flamme_triumph", XA - 2.0, 810.0, W_, "Triumph")
    add("flamme_triumph", XA - 2.0, 744.0, W_, "Triumph")
    add("table_haute", 800.0, 791.0, S_, "Triumph"); add("table_haute", 806.0, 801.0, S_, "Triumph")
    for z in (750.0, 757.5, 765.0):
        add("moto_triumph", 797.0, z, W_, "Triumph (motos)")
    add("airstream", 812.0, 758.0, N_, "Airstream Eden Street")
    box_pair(P, 820.0, 746.0, 4, "box motos")
    add("semi_suzuki_remorque", 875.0, 735.0, E, "Suzuki"); add("pieds_remorque", 858.0, 735.0, E, "Suzuki (béquilles)")
    add("auvent_suzuki", 841.0, 730.6, N_, "Suzuki (auvent)"); add("tapis_suzuki", 841.0, 722.5, N_, "Suzuki (moquette)")
    for x, bn, mo in ((852.0, "banniere_suzuki_lefrancois", "moto_suzuki_94"), (840.0, "banniere_suzuki_anderson", "moto_suzuki_21"),
                      (828.0, "banniere_suzuki_roczen", "moto_suzuki_94")):
        add(bn, x, 729.3, N_, "Suzuki"); add(mo, x, 721.0, W_, "Suzuki")
    # ======================= passage (croix) z 700-714,5
    # ======================= Honda (z 612-700)
    add("honda_hospitality", 851.0, 656.0, W_, "Honda (bâtiment à étage)")
    add("tapis_honda", 813.5, 660.5, W_, "Honda (moquette rouge)")
    for x, pn, mo in ((812.0, "panneau_soubeyras", "vraie_honda_151"), (822.0, "panneau_vialle", "vraie_honda_16"), (832.0, "panneau_shimoda", "vraie_honda_151")):
        add(pn, x, 689.5, S_, "Honda (pilote)"); add(mo, x, 695.6, S_, "Honda (moto du pilote : l'avant vers les spectateurs)")
    # v22k (Ryan : « le gros camion Honda ressemble plutôt à celui de RBT » ; « les 2 petits camions l'un à côté de l'autre, sans
    # empiéter sur le rouge ») : semi complète Honda (même modèle que RBT, livrée blanche HONDA / HRC) le long du bâtiment ;
    # les 2 bus côte à côte, juste avant la moquette rouge
    add("semi_honda_semi", 800.0, 611.8, N_, "gros camion Honda (semi façon RBT, sans rampe, sur le tapis côté allée)")
    add("servante_rouge", 826.0, 682.0, S_, "Honda"); add("servante_rouge", 830.0, 682.0, S_, "Honda")
    add("table_haute", 816.0, 640.0, S_, "Honda"); add("table_haute", 826.0, 660.0, S_, "Honda")
    add("van_honda", 827.0, 610.9, E, "bus Honda (côte à côte, hors moquette)"); add("van_honda", 827.0, 617.7, E, "bus Honda (côte à côte)")
    for k in range(12):
        P.append(("barriere_honda", XA + 1.0, 622.0 + 6.5 * k + 3.3, AL_Z, "Honda (le long de l'allée)"))
    for k in range(6):
        P.append(("barriere_honda", 791.0 + 6.7 * k + 3.3, 700.0, AL_X, "Honda (face au passage)"))
    add("flamme_honda", XA - 2.0, 618.0, W_, "Honda"); add("flamme_honda", 834.0, 702.0, W_, "Honda")
    add("flamme_automoto", XA - 2.0, 703.0, W_, "Automoto")
    # ======================= après Honda : box, GSM, USLAND, Sedna, VHR, YCF
    box_pair(P, 820.0, 562.0, 3, "box motos (côté photo 2)", 4)
    add("tente_gsm_10x10", 796.0, 600.0, W_, "Yamaha GSM"); add("tente_gsm_10x10", 796.0, 588.0, W_, "Yamaha GSM")
    add("moto_yamaha", 808.0, 600.0, W_, "Yamaha GSM"); add("moto_yamaha", 808.0, 588.0, W_, "Yamaha GSM")
    add("van_gsm", 806.0, 572.0, E, "Yamaha GSM (bus)")
    add("hospitality_usland", 817.1, 544.0, N_, "camion vitré USLAND (entrée, escalier et tapis rouge côté allée)")
    add("tente_sedna_10x10", 796.0, 512.0, W_, "Sedna"); add("van_sedna", 812.0, 510.0, S_, "Sedna (bus)"); add("table_haute", 796.0, 512.0, S_, "Sedna")
    add("van_vhr", 812.0, 490.0, E, "bus VHR Yamaha (en travers, arrière vers la piste)")
    add("moto_yamaha", 795.0, 490.0, W_, "VHR Yamaha (moto à l'arrière du bus)")
    # YCF (vidéo) : 2 moquettes imprimées, 2 rangées serrées de pit bikes face à l'allée, podiums, camion, tentes, flammes
    add("tapis_ycf_imprime", 805.0, 454.0, S_, "YCF (moquette imprimée)"); add("tapis_ycf_imprime", 805.0, 414.0, S_, "YCF (moquette imprimée)")
    k = 0
    for x in (799.0, 806.5):
        for j in range(22):
            z = 397.0 + 3.4 * j
            if 432.0 < z < 436.0:
                continue
            add("pitbike_ycf_jaune" if k % 6 == 5 else "pitbike_ycf_%d" % PIT_NUMS[k % len(PIT_NUMS)], x, z, W_, "YCF (pit bikes)"); k += 1
    for z, b in ((468.0, "pitbike_ycf_rouge"), (452.0, "pitbike_ycf_7"), (436.0, "pitbike_ycf_jaune"), (420.0, "pitbike_ycf_56")):
        add("podium_ycf", 822.0, z, S_, "YCF (podium)"); add(b, 822.0, z, W_, "YCF (moto exposée)")
    add("van_ycf", 840.0, 440.0, S_, "YCF (camion ENJOY YOUR RIDE)")
    add("tente_ycf", 822.0, 404.0, W_, "YCF"); add("tente_ycf", 834.0, 404.0, W_, "YCF")
    for z in (396.0, 434.0, 472.0):
        add("flamme_ycf", XA - 2.0, z, W_, "YCF")
    # ======================= rangée PISTE : bout whoops -> KTM (validé)
    for k, n in enumerate((None, None, 6, 8, 10, 12, None, None, None)):
        P.append(("barriere_num_%d" % n if n else "barriere_vauban", 741.3 + 6.7 * k, 825.0, AL_X, "barrière numérotée"))
    add("gant_five", 739.0, 808.0, S_, "gant gonflable Five")
    add("van_blanc", 750.0, 806.0, N_, "van blanc")
    add("tente_arche", 763.5, 806.0, S_, "tente arche noire")
    add("van_bus_noir", 746.5, 770.0, N_, "bus noir à côté du KTM")
    add("van_ktm_ouvert", 755.0, 770.0, N_, "KTM")
    add("tente_ktm_10x15", 764.0, 772.0, S_, "KTM"); add("tente_ktm_10x15", 764.0, 788.0, S_, "KTM")
    add("canette_geante", 740.0, 744.0, S_, "Monster"); add("canette_geante", 740.0, 730.0, S_, "Monster")
    add("table_haute", 763.0, 750.0, S_, "KTM"); add("caisses", 763.0, 738.0, S_, "KTM"); add("table_haute", 763.0, 726.0, S_, "KTM")
    add("acces_piste", 767.0, 716.5, S_, "ACCÈS PISTE (croix)")
    # ---- après la croix, file A (x 741-750) : RBT | Milwaukee | 2 bus Stark | Bud ; file B (x 755-769) : stands
    add("semi_rbt", 745.0, 611.8, N_, "camion RBT (semi complète)")
    add("caisses", 760.0, 690.0, S_, "RBT"); add("table_haute", 760.0, 678.0, S_, "RBT"); add("table_haute", 760.0, 666.0, S_, "RBT")
    add("podium_noir", 760.0, 650.0, S_, "RBT (moto exposée)"); add("vraie_ktm_usland_9", 760.0, 650.0, E, "RBT (moto exposée)")
    add("camion_milwaukee", 745.25, 553.0, S_, "camion de vente Milwaukee (2 niveaux, comptoir côté allée)")
    add("groupe_electrogene", 745.0, 592.0, S_, ""); add("caisses", 745.0, 582.0, S_, "")
    add("tente_milwaukee_10x10", 760.0, 560.0, S_, "Milwaukee"); add("tente_milwaukee_10x10", 760.0, 548.0, S_, "Milwaukee")
    add("vraie_crf_troy", 760.0, 560.0, E, "Milwaukee (moto)"); add("vraie_gasgas", 760.0, 548.0, E, "Milwaukee (moto)")
    add("tente_monster_10x20", 762.0, 590.0, S_, "Monster (collé derrière Milwaukee)")
    add("podium_noir", 762.0, 590.0, S_, "Monster (jeu)"); add("moto_kawa", 762.0, 590.0, W_, "Monster (moto du jeu)")
    add("van_stark", 745.5, 492.0, N_, "Stark Varg (bus 1)"); add("van_stark", 745.5, 467.0, N_, "Stark Varg (bus 2, aligné)")
    for zc in (500.0, 490.0, 480.0, 470.0, 460.0):
        add("tente_stark_10x10", 760.0, zc, S_, "Stark Varg (tentes collées)"); add("vraie_stark", 760.0, zc, E, "Stark Varg (moto, vers l'allée)")
    add("table_haute", 760.0, 530.0, S_, "")
    add("semi_bud", 745.0, 366.8, N_, "Bud Racing (au fond)")
    add("flamme_bud", 767.0, 450.0, W_, "Bud Racing")
    for z in (418.0, 427.0, 436.0):
        add("moto_kawa", 759.0, z, E, "Bud Racing (motos, vers l'allée)")
    add("caisses", 760.0, 404.0, S_, "Bud Racing")
    # ======================= écran
    # v28 : recalé (PAD_DX, pad_z) ; chaque stand (1er mot du commentaire) bouge d'un bloc : rien ne se resserre à l'intérieur d'un stand
    #   (Ryan, v22k : les bus Honda ne doivent pas empiéter sur la moquette rouge)
    KW_ = ('Honda', 'Suzuki', 'Triumph', 'YCF', 'Stark', 'KTM', 'RBT', 'Milwaukee', 'Monster', 'Bud', 'GSM', 'Sedna', 'VHR', 'USLAND', 'Airstream',
           'box motos (côté photo 2)', 'box motos', 'barrière numérotée')
    grp = lambda k, c: next((w for w in KW_ if w in c), c or k)
    zc = {}
    for k, x, z, f, c in P:
        zc.setdefault(grp(k, c), []).append(z)
    dz = {g: pad_z(float(np.mean(v))) - float(np.mean(v)) for g, v in zc.items()}
    # v28y (croquis : « pousse cette partie vers le bas pour garder le passage entre Honda et Suzuki ») : rangée du fond (x >= 785),
    #   de Honda à YCF, MUR_DOWN ft plus bas : le passage « croix » retrouve ses 9 ft de ce côté
    P = [(k, x + PAD_DX, z + dz[grp(k, c)] - (MUR_DOWN if (x >= 785.0 and z < 706.0) else 0.0), f, c) for k, x, z, f, c in P]
    # v28 : la remorque Suzuki dépassait de 5 ft dans le mur de scène (déjà 5 ft avant) : stand Suzuki
    #   5,5 ft plus près de l'allée
    P = [(k, x - (5.5 if c.startswith('Suzuki') else 0.0), z, f, c) for k, x, z, f, c in P]
    # v28z2 (« le box du bas, décale-le un peu sur la gauche pour que ça ne touche pas ») : ses barrières touchaient le camion
    #   vitré USLAND (6 ft) : box 8 ft vers le mur de scène
    P = [(k, x + (8.0 if c.startswith('box motos (côté photo 2)') else 0.0), z, f, c) for k, x, z, f, c in P]
    # v28z3 (« tout le stand Honda sans rien oublier, monte-le de 5 ft ») : tout ce qui porte « Honda » (bâtiment, semi, bus, moquette,
    #   pilotes, motos, servantes, tables, barrières, flammes) 5 ft vers Suzuki
    P = [(k, x, z + (5.0 if 'Honda' in c else 0.0), f, c) for k, x, z, f, c in P]
    add("ecran_geant", X_WALL - 2.5, _LP.OZ, W_, "écran géant")
    return P


def build_models(D):
    import shutil
    os.makedirs(D, exist_ok=True); out = {}
    def reg(r):
        out[r[0][:-3]] = r
    for k, w, d in (("triumph", 10, 10), ("ktm", 10, 15), ("ycf", 10, 10), ("monster", 10, 20), ("sedna", 10, 10), ("gsm", 10, 10),
                    ("stark", 10, 10), ("milwaukee", 10, 10)):
        jm, png, nt = tent(D, k, w, d); out[jm[:-3]] = (jm, png, nt)
        if w == d:
            out["tente_%s" % k] = (jm, png, nt)
    for b in FLAGS:
        reg(flag(D, b))
    reg(barrier(D)); reg(barrier(D, "honda")); reg(barrier(D, "triumph"))
    for n in (6, 8, 10, 12):
        reg(barriere_num(D, n))
    reg(can(D)); reg(van(D, "ktm", True)); reg(airstream(D))
    for k in ("blanc", "bus_noir", "sedna", "gsm", "ycf", "stark", "honda", "vhr"):
        reg(van(D, k))
    for t in ("suzuki", "honda", "ktm", "yamaha", "kawa", "blanc", "triumph", "stark"):
        reg(bike(D, t))
    reg(bike(D, "suzuki", 21)); reg(bike(D, "suzuki", 94)); reg(bike(D, "honda", 30)); reg(bike(D, "honda", 16)); reg(bike(D, "honda", 85))
    for n in PIT_NUMS:
        reg(bike(D, "ycf", n, 0.62, "pitbike_ycf_%d" % n))
    reg(bike(D, "ycf_jaune", None, 0.62, "pitbike_ycf_jaune")); reg(bike(D, "honda", None, 0.62, "pitbike_ycf_rouge"))
    for first, last, n in (("CHARLES", "LEFRANÇOIS", None), ("JASON", "ANDERSON", 21), ("KEN", "ROCZEN", 94)):
        reg(rollup(D, first, last, n))
    reg(honda_wall(D)); reg(shimoda_panel(D)); reg(servante(D)); reg(acces_piste(D))
    reg(rider_panel(D, "TOM", "VIALLE", 16, (245, 245, 248), (204, 16, 26), (255, 255, 255)))
    reg(rider_panel(D, "CEDRIC", "SOUBEYRAS", 85, (245, 245, 248), (204, 16, 26), (255, 255, 255)))
    reg(tapis(D, "tapis_suzuki", 38.0, 16.0, (24, 60, 160))); reg(tapis(D, "tapis_honda", 77.0, 45.0, (190, 16, 24)))
    reg(tapis_imprime(D, "tapis_ycf_imprime", 20.0, 38.0, (20, 110, 200), lg("ycf")))
    reg(camion_vente(D, "camion_milwaukee", (214, 1, 26), lg("milwaukee")))
    reg(auvent(D, 40.0, 16.0, 13.0, 10.0)); reg(pieds_remorque(D)); reg(honda_hospitality(D, L=68.0, Dp=26.0)); reg(screen(D))
    reg(tente_arche(D)); reg(table_haute(D)); reg(groupe(D)); reg(caisses(D)); reg(gant_five(D)); reg(podium_ycf(D)); reg(podium_noir(D))
    reg(semi(D, "bud", True)); reg(semi(D, "suzuki", False)); reg(semi(D, "rbt", True)); reg(semi(D, "honda_semi", True))
    # vraies motos (modèles moddés du jeu à texture en clair ; Stark : modèle du jeu, couleur unie) ; repli : nos motos
    try:
        import motos_jeu as MJ
        for n in VRAIES:
            reg(MJ.build(n, D))
    except Exception as e:
        print("motos du jeu indisponibles (%s) : motos simplifiées" % e)
        for k_, n in enumerate(VRAIES):
            jm_, png_, nt_ = bike(D, ["ktm", "honda", "kawa", "blanc", "yamaha"][k_ % 5], None, 1.0, "vraie_" + n); out["vraie_" + n] = (jm_, png_, nt_)
    src = os.path.join(ROOT, "tracks", "USLAND2026SX1", "statue")
    for f in ("hospitality_usland.jm", "hospitality_usland.png", "hospitality_usland_spec.png"):
        shutil.copy(os.path.join(src, f), os.path.join(D, f))
    out["hospitality_usland"] = ("hospitality_usland.jm", "hospitality_usland.png", None)
    return out


DROP = ("/statue/paris/semi.jm ", "/statue/paris/semi_jgsx.jm ", "stage__screen_main", "stage__screen_side", "/%s/" % SUB)


def apply(OUT, FOLDER):
    """pose le paddock dans la piste construite : retire les anciens camions et l'ancien écran, (re)crée les modèles, ajoute les
    lignes aux statues (jour et nuit). Idempotent."""
    import shutil
    D = os.path.join(OUT, *SUB.split("/"))
    if os.path.isdir(D):
        shutil.rmtree(D)
    models = build_models(D); lines = []; missing = []
    for k, x, z, f, c in plan():
        if k not in models:
            missing.append(k); continue
        jm, png, _ = models[k]
        lines.append("[%.6f 0.000000 %.6f] %.6f @%s/%s/%s @%s/%s/%s null" % (x, z, YAW(*f), FOLDER, SUB, jm, FOLDER, SUB, png))
    assert not missing, "modèles manquants : %s" % sorted(set(missing))
    for f in ["statues"] + ["variants/" + v for v in os.listdir(os.path.join(OUT, "variants")) if v.startswith("statues")]:
        p = os.path.join(OUT, f); L = [l for l in open(p).read().splitlines() if l.strip() and not any(k in l for k in DROP)]
        for essai in range(8):                                             # le fichier est parfois pris par un autre programme (Errno 22)
            try:
                with open(p, "w", newline="\n") as fh:
                    fh.write("\n".join(L + lines) + "\n")
                break
            except OSError:
                if essai == 7:
                    raise
                import time
                time.sleep(1.5)
    sd = os.path.join(OUT, "statue", "paris")
    for fn in os.listdir(sd):                                              # anciens camions (v19-v21) : plus utilisés
        if fn.startswith("semi_jgsx") or fn == "semi.jm" or (fn.startswith("semi_") and fn.endswith(".png")):
            os.remove(os.path.join(sd, fn))
    files = os.listdir(D)
    for fn in files:                                                       # contrôles de format
        if fn.endswith(".png"):
            im = Image.open(os.path.join(D, fn)); assert im.size[0] == im.size[1] and im.size[0] & (im.size[0] - 1) == 0, fn
    return dict(lignes=len(lines), modeles=len(models), fichiers=len(files),
                triangles=sum(v[2] or 0 for v in models.values()))


if __name__ == "__main__":
    T = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "tracks", "USLAND2026SupercrossParisZion")
    print(apply(T, os.path.basename(os.path.normpath(T))))
