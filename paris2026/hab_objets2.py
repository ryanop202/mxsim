"""v9 de l'habillage de Paris (retours de Ryan du 2026-11-10 : « tout en beaucoup mieux, plus réaliste, là on dirait du Roblox »).
Formes nouvelles (créées ici, pas des mesures), d'après les photos du Supercross de Paris 2025 (paris2026/refs/photos2025) :

  tuff_arc      tuff block PLEIN (bloc de mousse arrondi, bouts fermés) au lieu du demi-tonneau creux (« à moitié faits »)
  mur           virages : rangée de ballots ronds sous bâche grise (photo 12 « moto verte ») + coussin du sponsor posé dessus ;
                jupe de bâche jusqu'à 3 ft sous l'origine (plus jamais en l'air sur la pente du berm)
  amv_bache     bâche AMV du saut du milieu dessinée sur le VRAI profil du terrain (bord du dessus relevé dans le terrain)
  minerva       portique Minerva Oil : volumes fermés (plus de faces manquantes : « il est transparent à moitié »)
  arche_50      arche 50 Factory : poteaux et poutre fermés, arêtes chanfreinées (« à moitié faite en haut, carrée »)
  semi          camions du paddock : tracteur (cabine arrondie, déflecteur, vitres, rétros), remorque à jupes, vraies roues, auvent

Toutes les pièces sont fermées et orientées vers l'extérieur (contrôle automatique : end_part). Non testé en jeu.
"""
import os
import numpy as np
from PIL import Image, ImageDraw
import hab_kit as K
from hab_kit import Mesh, R, logo, fit

MAT_MAT = (0, 0, 0, 0, 0)
MAT_BACHE = (20, 0.35, 0.4, 0.4, 0.4)
MAT_CAR = (40, 0.6, 1, 1, 1)


def _save(img, path, alpha=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    (img if alpha else img.convert('RGB')).save(path)


# ---------------------------------------------------------------- maillage : pièces fermées, faces vers l'extérieur
class M(Mesh):
    def begin(self):
        self._p0 = len(self.I)

    def end(self, center=None, smooth=0.0):
        """oriente les triangles de la pièce (depuis begin) vers l'extérieur de son centre (pièces convexes) ;
        smooth > 0 : normales lissées entre faces voisines faisant moins de smooth degrés."""
        I = np.array(self.I[self._p0:], int).reshape(-1, 3)
        if not len(I):
            return
        P = np.array([v[:3] for v in self.V])
        c = P[np.unique(I)].mean(0) if center is None else np.asarray(center, float)
        g = np.cross(P[I[:, 1]] - P[I[:, 0]], P[I[:, 2]] - P[I[:, 0]])
        bad = np.einsum('ij,ij->i', g, P[I].mean(1) - c) < 0
        I[bad] = I[bad][:, ::-1]; g[bad] *= -1
        n = g / np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-12)
        for k, tri in enumerate(I):
            for q in tri:
                self.V[q][3:6] = list(n[k])
        if smooth:
            cs = np.cos(np.radians(smooth)); grp = {}
            for q in np.unique(I):
                grp.setdefault(tuple(np.round(P[q], 3)), []).append(q)
            N0 = {q: np.array(self.V[q][3:6]) for q in np.unique(I)}
            for qs in grp.values():
                for q in qs:
                    acc = sum(N0[r] for r in qs if np.dot(N0[r], N0[q]) > cs)
                    self.V[q][3:6] = list(acc / (np.linalg.norm(acc) or 1))
        self.I[self._p0:] = I.ravel().tolist()

    def poly(self, P, uv):
        """polygone convexe (éventail) ; uv = un point ou une liste."""
        P = [np.asarray(p, float) for p in P]
        uvs = uv if isinstance(uv, list) else [uv] * len(P)
        for k in range(1, len(P) - 1):
            self.tri([P[0], P[k], P[k + 1]], [uvs[0], uvs[k], uvs[k + 1]])

    def prism_y(self, pts, y0, y1, uv_sides, uv_cap, caps=(True, True)):
        """prisme vertical sur un polygone convexe (x, z) ; uv_sides[i] = rectangle de la face i (ou un seul)."""
        n = len(pts)
        for i in range(n):
            (xa, za), (xb, zb) = pts[i], pts[(i + 1) % n]
            r = uv_sides[i] if isinstance(uv_sides, list) else uv_sides
            self.quad([(xa, y0, za), (xb, y0, zb), (xb, y1, zb), (xa, y1, za)], r)
        if caps[1]:
            self.poly([(x, y1, z) for x, z in pts], uv_cap)
        if caps[0]:
            self.poly([(x, y0, z) for x, z in pts], uv_cap)

    def prism_x(self, pts, x0, x1, uv_sides, uv_cap):
        """prisme horizontal (le long de x) sur un polygone convexe (z, y)."""
        n = len(pts)
        for i in range(n):
            (za, ya), (zb, yb) = pts[i], pts[(i + 1) % n]
            r = uv_sides[i] if isinstance(uv_sides, list) else uv_sides
            self.quad([(x0, ya, za), (x1, ya, za), (x1, yb, zb), (x0, yb, zb)], r)
        self.poly([(x0, y, z) for z, y in pts], uv_cap); self.poly([(x1, y, z) for z, y in pts], uv_cap)


def cen(r):
    """centre d'un rectangle UV (couleur unie : jamais sur le bord, où l'on tombe sur le pixel voisin)."""
    return ((r[0] + r[2]) / 2, (r[1] + r[3]) / 2)


def _bx(m, p, q, r, faces):
    """boîte entre deux coins quelconques (min / max par axe)."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    m.box(tuple(np.minimum(p, q)), tuple(np.maximum(p, q)), r, faces)


def chamfer(w, d, c):
    """rectangle 2w x 2d aux coins coupés de c (8 points, sens direct)."""
    return [(-w + c, -d), (w - c, -d), (w, -d + c), (w, d - c), (w - c, d), (-w + c, d), (-w, d - c), (-w, -d + c)]


def superellipse(W, H, n=16, p=3.0):
    """demi-section arrondie (z, y) de z = -W à +W par le haut ; p grand = plus carré."""
    t = np.linspace(0, np.pi, n + 1); c, s = np.cos(t), np.sin(t)
    return np.c_[-W * np.sign(c) * np.abs(c) ** (2 / p), H * np.abs(s) ** (2 / p)]


# ---------------------------------------------------------------- tuff blocks pleins
TUFF = dict(yamaha=((24, 52, 140), 'yamaha', None, (12, 12, 14)), honda=((214, 22, 28), 'honda', None, (150, 14, 18)),
            seong=((0, 160, 172), 'seong', (10, 10, 10), (0, 120, 130)), amv=((245, 245, 242), 'amv', None, (0, 150, 64)),
            monster=((14, 14, 15), 'monster', None, (30, 30, 32)), motul=((214, 22, 28), 'motul', None, (150, 12, 16)),
            venum=((14, 14, 15), 'venum', None, (40, 40, 42)), thor=((120, 122, 126), 'thor', None, (80, 80, 84)),
            gris=((128, 130, 134), None, None, (96, 98, 102)))
ARC_L, ARC_W, ARC_H = 1.95, 1.2, 1.5


def tuff_arc(out):
    """bloc de mousse arrondi (photos 3 et 6) : 3,9 x 2,4 x 1,5 ft, dessus bombé, bouts arrondis, plein. Même nom de fichier
    que l'ancien demi-tonneau (même place, même collision)."""
    m = M(); W = H = 512
    pan, endr, bot = R((0, 0, 512, 262), W, H), (300 / W, 1 - 300 / H), (60 / W, 1 - 300 / H)
    sec = superellipse(ARC_W, ARC_H, 16, 3.4)
    b = 0.32; xs = [-ARC_L, -ARC_L + b * 0.35, -ARC_L + b, ARC_L - b, ARC_L - b * 0.35, ARC_L]
    ks = [0.72, 0.93, 1.0, 1.0, 0.93, 0.72]
    rings = [np.c_[np.full(len(sec), x), sec[:, 1] * (0.6 + 0.4 * k), sec[:, 0] * k] for x, k in zip(xs, ks)]
    seg = np.hypot(np.diff(sec[:, 0]), np.diff(sec[:, 1])); s = np.r_[0, np.cumsum(seg)]; half = s[-1] / 2
    m.begin()
    for j in range(len(xs) - 1):
        A, B = rings[j], rings[j + 1]
        for i in range(len(sec) - 1):
            P = [A[i], B[i], B[i + 1], A[i + 1]]
            if j == 2:                                                       # corps : le panneau du sponsor, un par côté
                a_side = sec[i + 1, 0] <= 1e-9
                f0, f1 = (s[i] / half, s[i + 1] / half) if a_side else ((s[-1] - s[i]) / half, (s[-1] - s[i + 1]) / half)
                v0, v1 = pan[1] + (pan[3] - pan[1]) * min(f0, 1), pan[1] + (pan[3] - pan[1]) * min(f1, 1)
                ua, ub = (pan[2], pan[0]) if a_side else (pan[0], pan[2])     # u à x = -L et x = +L (texte à l'endroit des 2 côtés)
                m.tri([P[0], P[1], P[2]], [(ua, v0), (ub, v0), (ub, v1)]); m.tri([P[0], P[2], P[3]], [(ua, v0), (ub, v1), (ua, v1)])
            else:
                m.quad(P, (endr[0], endr[1], endr[0] + 0.001, endr[1] + 0.001))
    for A in (rings[0], rings[-1]):
        m.poly(list(A), endr)
    m.quad([rings[0][0], rings[-1][0], rings[-1][-1], rings[0][-1]], (bot[0], bot[1], bot[0] + 0.001, bot[1] + 0.001))   # dessous
    m.end(center=(0, ARC_H * 0.4, 0), smooth=50)
    m.write(os.path.join(out, 'tuff_arc.jm'), MAT_BACHE)
    K.shp(os.path.join(out, 'tuff_arc.shp'), [(-1.15, 0.72, 0), (0, 0.72, 0), (1.15, 0.72, 0)], 0.78)
    for name, (bg, lg, ink, end) in TUFF.items():
        im = Image.new('RGB', (W, H), bg); d = ImageDraw.Draw(im)
        if name == 'amv':
            d.rectangle([0, 0, 511, 261], fill=(0, 150, 64)); d.rounded_rectangle([14, 14, 497, 247], 18, fill=bg)
        if name == 'seong':
            d.rectangle([0, 60, 511, 200], fill=(10, 10, 10))
            fit(im, K.hstack([logo('seong_icon').resize((120, 134)), logo('seong')], 40), (20, 60, 492, 200), 0.12)
        elif name == 'monster':
            fit(im, K.hstack([logo('monster_claw'), logo('monster_text')], 30), (20, 30, 492, 232), 0.06)
        elif lg is not None:
            fit(im, logo(lg) if ink is None else K.tint(logo(lg), ink), (20, 30, 492, 232), 0.08)
        im = K.shade_v(im, (0, 0, 512, 262), 1.0, 0.8)
        d = ImageDraw.Draw(im); d.rectangle([0, 266, 255, 340], fill=(16, 16, 18)); d.rectangle([256, 266, 511, 340], fill=end)
        _save(K.grain(im, 2.0), os.path.join(out, 'tuff_arc_%s.png' % name))
    return list(TUFF)


# ---------------------------------------------------------------- virages : ballots ronds bâchés + coussin du sponsor
MUR = dict(honda=((214, 22, 28), 'honda', None, 2), seong=((0, 160, 172), 'seong', (10, 10, 10), 1), amv=((245, 245, 242), 'amv', None, 2),
           five=((245, 245, 242), 'five', None, 2), automoto=((16, 16, 18), 'automoto', None, 1), motoverte=((240, 240, 238), 'motoverte', None, 2),
           venum=((16, 16, 18), 'venum', None, 2))
MUR_L, MUR_D, MUR_H, MUR_SKIRT = 4.0, 2.1, 3.3, 3.0


def mur(out):
    """pièce de 8 ft : 2 ballots ronds sous bâche grise (bosses tous les 4 ft) + coussin de 8 x 2,3 ft du sponsor posé à l'arrière
    du dessus (logo côté piste ET côté tribunes). +z = côté piste. Jupe de bâche jusqu'à y = -3 ft (pente du berm)."""
    W, H = 1024, 512; m = M()
    ban, tarp = R((0, 0, 1024, 256), W, H), R((0, 262, 1024, 470), W, H)
    bgc = (40 / W, 1 - 490 / H)
    xs = np.linspace(-MUR_L, MUR_L, 33); sec = superellipse(MUR_D, MUR_H, 14, 2.3)
    sc = lambda x: 0.9 + 0.1 * np.cos(np.pi * x / 2) ** 2                   # 2 ballots par pièce (joints à x = ±2)
    m.begin()
    for i in range(len(xs) - 1):
        xa, xb = xs[i], xs[i + 1]; ka, kb = sc(xa), sc(xb)
        ua, ub = tarp[0] + (tarp[2] - tarp[0]) * (xa + MUR_L) / (2 * MUR_L), tarp[0] + (tarp[2] - tarp[0]) * (xb + MUR_L) / (2 * MUR_L)
        for j in range(len(sec) - 1):
            (za, ya), (zb, yb) = sec[j], sec[j + 1]
            va, vb = tarp[1] + (tarp[3] - tarp[1]) * ya / MUR_H, tarp[1] + (tarp[3] - tarp[1]) * yb / MUR_H   # v = hauteur (les 2 faces pareilles)
            m.tri([(xa, ya * ka, za * ka), (xb, ya * kb, za * kb), (xb, yb * kb, zb * kb)], [(ua, va), (ub, va), (ub, vb)])
            m.tri([(xa, ya * ka, za * ka), (xb, yb * kb, zb * kb), (xa, yb * ka, zb * ka)], [(ua, va), (ub, vb), (ua, vb)])
        for zs in (-1, 1):                                                   # jupe (devant / derrière)
            m.quad([(xa, -MUR_SKIRT, zs * MUR_D * ka), (xb, -MUR_SKIRT, zs * MUR_D * kb), (xb, 0.0, zs * MUR_D * kb), (xa, 0.0, zs * MUR_D * ka)],
                   (ua, tarp[1], ub, tarp[1] + 0.02))
    for x in (-MUR_L, MUR_L):                                                # bouts fermés
        k = sc(x); m.poly([(x, y * k, z * k) for z, y in sec] + [(x, -MUR_SKIRT, MUR_D * k), (x, -MUR_SKIRT, -MUR_D * k)], cen(tarp))
    m.end(center=(0, 0.6, 0), smooth=40)
    # coussin du sponsor : section arrondie 0,8 x 2,3 ft, posé à l'arrière du dessus
    cz, y0, y1, t = -0.55, MUR_H * 0.82, MUR_H * 0.82 + 2.3, 0.4
    cs = superellipse(t, (y1 - y0) / 2, 10, 4.0)
    ring = np.r_[np.c_[cs[:, 0], y0 + (y1 - y0) / 2 + cs[:, 1]][::-1], np.c_[-cs[1:-1, 0], y0 + (y1 - y0) / 2 - cs[1:-1, 1]][::-1]]
    ring[:, 0] += cz
    m.begin()
    n = len(ring)
    for j in range(n):
        (za, ya), (zb, yb) = ring[j], ring[(j + 1) % n]
        front = za > cz + t * 0.9 and zb > cz + t * 0.9                      # face côté piste : logo à l'endroit vu de +z
        back = za < cz - t * 0.9 and zb < cz - t * 0.9
        if front or back:
            va, vb = ban[1] + (ban[3] - ban[1]) * (ya - y0) / (y1 - y0), ban[1] + (ban[3] - ban[1]) * (yb - y0) / (y1 - y0)
            u_m, u_p = (ban[0], ban[2]) if front else (ban[2], ban[0])
            m.tri([(-MUR_L, ya, za), (MUR_L, ya, za), (MUR_L, yb, zb)], [(u_m, va), (u_p, va), (u_p, vb)])
            m.tri([(-MUR_L, ya, za), (MUR_L, yb, zb), (-MUR_L, yb, zb)], [(u_m, va), (u_p, vb), (u_m, vb)])
        else:
            m.quad([(-MUR_L, ya, za), (MUR_L, ya, za), (MUR_L, yb, zb), (-MUR_L, yb, zb)], (bgc[0], bgc[1], bgc[0] + 0.001, bgc[1] + 0.001))
    m.poly([(-MUR_L, y, z) for z, y in ring], bgc); m.poly([(MUR_L, y, z) for z, y in ring], bgc)
    m.end(center=(0, (y0 + y1) / 2, cz), smooth=35)
    m.write(os.path.join(out, 'mur.jm'), MAT_BACHE)
    K.shp(os.path.join(out, 'mur.shp'), [(x, y, 0) for x in (-3, -1, 1, 3) for y in (1.2, 2.6)] + [(x, 4.2, cz) for x in (-3, -1, 1, 3)], 1.3, (1.5, 1000, 200))
    rng = np.random.default_rng(4)
    for name, (bg, lg, ink, nlg) in MUR.items():
        im = Image.new('RGB', (W, H), (150, 152, 156)); d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 1024, 256], fill=bg)
        if name == 'amv':
            d.rectangle([0, 0, 1023, 255], outline=(0, 150, 64), width=14)
        lgo = logo(lg) if ink is None else K.tint(logo(lg), ink)
        if name == 'seong':
            lgo = K.hstack([logo('seong_icon').resize((120, 134)), lgo], 40)
        for k in range(nlg):
            fit(im, lgo, (k * 1024 / nlg, 24, (k + 1) * 1024 / nlg, 232), 0.12)
        im = K.shade_v(im, (0, 0, 1024, 256), 1.0, 0.9)
        a = np.asarray(im, float)                                            # bâche grise : plis + plus sombre vers le sol
        xs_ = np.arange(1024); fold = sum(np.sin(xs_ / p + rng.uniform(0, 6)) * q for p, q in ((17, 4), (47, 6), (113, 5)))
        a[262:470, :, :] += fold[None, :, None]; a[262:470, :, :] *= np.linspace(1.04, 0.62, 208)[:, None, None]
        for xj in (256, 768):                                                # joints entre ballots
            a[262:470, xj - 6:xj + 6, :] *= 0.72
        im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
        ImageDraw.Draw(im).rectangle([0, 476, 130, 512], fill=bg)
        _save(K.grain(im, 2.5), os.path.join(out, 'mur_%s.png' % name))
    return list(MUR)


# ---------------------------------------------------------------- bâche AMV sur le vrai profil du saut du milieu
def _mascotte(d, cx, cy, s, G=(0, 150, 64)):
    d.ellipse([cx - s, cy - 2.2 * s, cx + s, cy - 0.2 * s], fill=G)
    d.rounded_rectangle([cx - 0.7 * s, cy - 1.5 * s, cx + 0.7 * s, cy - 0.95 * s], int(0.2 * s), fill=(250, 250, 250))
    d.ellipse([cx - 0.28 * s, cy - 1.4 * s, cx - 0.08 * s, cy - 1.1 * s], fill=(20, 20, 20)); d.ellipse([cx + 0.08 * s, cy - 1.4 * s, cx + 0.28 * s, cy - 1.1 * s], fill=(20, 20, 20))
    d.rounded_rectangle([cx - 0.55 * s, cy - 0.15 * s, cx + 0.55 * s, cy + 1.5 * s], int(0.25 * s), fill=(25, 25, 28))
    d.line([(cx - 0.5 * s, cy + 0.2 * s), (cx - 1.3 * s, cy + 0.9 * s)], fill=(25, 25, 28), width=int(0.3 * s))
    d.line([(cx + 0.5 * s, cy + 0.2 * s), (cx + 1.3 * s, cy - 0.3 * s)], fill=(25, 25, 28), width=int(0.3 * s))


def amv_bache(out, name, xs, top, head=2.6, flat_tol=0.4):
    """xs (x local croissant, ft) / top (hauteur du BORD du dessus du saut relevée dans le terrain) : panneau vertical qui épouse
    exactement le saut, du pied amont au pied aval, avec le panneau central qui dépasse de head ft sur le dessus plat.
    Texture dessinée sur ce profil (aucune déformation). Vu de +z : image de gauche à droite = x croissant."""
    xs, top = np.asarray(xs, float), np.maximum(np.asarray(top, float), 0.0)
    G = (0, 150, 64); Hm = float(top.max()); flat = top >= Hm - flat_tol; xf0, xf1 = xs[flat][0], xs[flat][-1]
    teff = np.where((xs >= xf0) & (xs <= xf1), Hm + head, top + 0.25)
    W, H = 2048, 512; span = xs[-1] - xs[0]; px = min((H - 8) / (Hm + head), (W - 8) / span)
    X = lambda x: 4 + (x - xs[0]) * px; Y = lambda y: H - 2 - y * px
    im = Image.new('RGB', (W, H), (40, 40, 40)); d = ImageDraw.Draw(im)
    pts = [(X(x), Y(t)) for x, t in zip(xs, teff)]
    d.polygon(pts + [(X(xs[-1]), H), (X(xs[0]), H)], fill=(248, 248, 246))
    d.line(pts, fill=G, width=max(8, int(0.35 * px)))
    bx0, bx1 = X(xf0), X(xf1); hy = Y(Hm + head)
    d.rectangle([bx0, hy, bx1, H], outline=G, width=max(8, int(0.3 * px)))   # panneau central
    hh = head * px; cw = bx1 - bx0
    for k in range(3):
        fit(im, logo('amv'), (bx0 + 10 + k * (cw - 20) / 3, hy + 6, bx0 + 10 + (k + 1) * (cw - 20) / 3, hy + hh - 6), 0.16)
    d.line([(bx0, hy + hh), (bx1, hy + hh)], fill=G, width=6)
    yb = hy + hh + 0.6 * px
    d.rounded_rectangle([bx0 + cw * 0.28, yb, bx1 - cw * 0.28, yb + 1.9 * px], 8, fill=G)
    fit(im, K.tint(logo('amv_fr'), (255, 255, 255)), (bx0 + cw * 0.28, yb, bx1 - cw * 0.28, yb + 1.9 * px), 0.12); yb += 2.6 * px
    for line in ("L'ASSURANCE", "DES DEUX-ROUES", "QUI COMPREND", "LES DEUX-ROUES !"):
        t = K.text_img(line, 40, (30, 60, 40), 'arialbd.ttf'); fit(im, t, (bx0 + 20, yb, bx1 - 20, yb + 1.6 * px), 0.02); yb += 1.75 * px
    for xa, xb in ((xs[0], xf0), (xf1, xs[-1])):                             # pentes : bonhomme + AMV.fr au milieu du triangle
        if xb - xa < 4:
            continue
        xc = xa + (xb - xa) * (0.62 if xa == xs[0] else 0.38); hc = float(np.interp(xc, xs, top))
        s_ = min(hc * 0.12, (xb - xa) * 0.1) * px
        _mascotte(d, X(xc), Y(hc * 0.5), s_)
        fit(im, logo('amv_fr'), (X(xc) - 2.6 * s_, Y(hc * 0.5) + 1.7 * s_, X(xc) + 2.6 * s_, Y(hc * 0.5) + 3.2 * s_), 0.05)
    im = K.shade_v(im, (0, 0, W, H), 1.0, 0.88)
    _save(K.grain(im, 2.0), os.path.join(out, name + '.png'))
    m = M(); u = lambda x: X(x) / W; v = lambda y: 1 - Y(max(y, 0.0)) / H
    white = (u((xf0 + xf1) / 2), v(1.0))
    yb_ = -0.8                                                               # bas de la bâche un peu sous le sol
    for i in range(len(xs) - 1):
        xa, xb, ta, tb = xs[i], xs[i + 1], teff[i], teff[i + 1]
        if (xa < xf0 <= xb) or (xa < xf1 <= xb):                              # marche du panneau central : 2 quads verticaux
            ta = tb = min(ta, tb) if xa < xf0 <= xb else max(ta, tb)
        P = [(xa, yb_, 0), (xb, yb_, 0), (xb, tb, 0), (xa, ta, 0)]
        m.tri([P[0], P[1], P[2]], [(u(xa), v(0)), (u(xb), v(0)), (u(xb), v(tb))]); m.tri([P[0], P[2], P[3]], [(u(xa), v(0)), (u(xb), v(tb)), (u(xa), v(ta))])
        m.tri([P[1], P[0], P[3]], [white] * 3); m.tri([P[1], P[3], P[2]], [white] * 3)   # dos (blanc)
    m.write(os.path.join(out, name + '.jm'), MAT_BACHE)
    return dict(span=round(float(span), 1), h=round(Hm + head, 1))


# ---------------------------------------------------------------- portique Minerva Oil (volumes fermés)
def _steel(d, box, dark=(58, 60, 64), light=(96, 99, 104)):
    x0, y0, x1, y1 = box; d.rectangle(box, fill=dark)
    for y in range(y0, y1, 10):
        d.line([(x0, y), (x1, y)], fill=light, width=2)
    for x in range(x0, x1, 22):
        d.line([(x, y0), (x, y1)], fill=(40, 41, 44), width=2)


def minerva(out):
    G = (0, 150, 64); W = H = 1024; im = Image.new('RGB', (W, H), (14, 14, 15)); d = ImageDraw.Draw(im)
    hd = (0, 0, 1024, 250)
    d.rectangle([0, 0, 1023, 14], fill=G); d.rectangle([0, 236, 1023, 250], fill=(240, 240, 238))
    fit(im, logo('minerva'), (150, 24, 874, 226), 0.04)
    for x0 in (30, 910):
        for k in range(3):
            xx = x0 + k * 28; pts = [(xx, 70), (xx + 30, 125), (xx, 180)] if x0 < 500 else [(xx + 30, 70), (xx, 125), (xx + 30, 180)]
            d.line(pts, fill=(240, 240, 238), width=10)
    pb = (0, 256, 190, 1024)
    d.rectangle(pb, fill=G); d.rectangle([pb[0] + 8, pb[1] + 8, pb[2] - 8, pb[3] - 8], outline=(240, 240, 238), width=5)
    fit(im, logo('minerva_v'), (pb[0] + 20, pb[1] + 40, pb[2] - 20, pb[3] - 40), 0.0, rot=90)
    _steel(d, (200, 256, 712, 768)); st = R((200, 256, 712, 768), W, H); blk = R((730, 300, 1000, 500), W, H)
    _save(K.grain(im, 2.0), os.path.join(out, 'minerva.png'))
    m = M(); hw, pw, ph, hh, dz = 4.0, 2.2, 9.0, 3.0, 3.0
    for sx in (-1, 1):                                                       # piliers pleins sur toute la profondeur
        x0, x1 = sorted((sx * hw, sx * (hw + pw)))
        m.begin(); m.box((x0, 0, -dz), (x1, ph, dz), blk, 'xXzZYy', {'Z': R(pb, W, H), 'z': R(pb, W, H)}); m.end()
    m.begin(); m.box((-hw - pw, ph, -dz), (hw + pw, ph + hh, dz), blk, 'xXzZYy', {'Z': R(hd, W, H), 'z': R(hd, W, H)}); m.end()
    yp, lr = 2.4, 9.0                                                        # podium acier + 2 rampes (on roule dessus)
    m.begin(); m.box((-hw, 0, -dz), (hw, yp, dz), st, 'xXYy'); m.end()
    for sg in (-1, 1):
        m.begin()
        a, b = sg * dz, sg * (dz + lr)
        m.quad([(-hw, yp, a), (hw, yp, a), (hw, 0, b), (-hw, 0, b)], st)
        for sx in (-1, 1):
            m.tri([(sx * hw, 0, a), (sx * hw, 0, b), (sx * hw, yp, a)], [cen(blk)] * 3)
        m.quad([(-hw, 0, a), (hw, 0, a), (hw, 0, b), (-hw, 0, b)], blk)
        m.end(center=(0, yp * 0.3, sg * (dz + lr * 0.3)))
    m.write(os.path.join(out, 'minerva.jm'), MAT_MAT)
    sp = []; r = 1.0
    for z in np.arange(-dz - lr, dz + lr + 0.01, 0.75):
        y = yp if abs(z) <= dz else yp * (1 - (abs(z) - dz) / lr)
        ny = 1.0 if abs(z) <= dz else lr / np.hypot(lr, yp)
        for x in np.arange(-hw + 0.6, hw - 0.59, 0.75):
            sp.append((x, y - r * ny, z))
    for sx in (-1, 1):
        for z in (-dz + 1.0, 0.0, dz - 1.0):
            sp += [(sx * (hw + pw / 2), y, z) for y in (1.1, 3.3, 5.5, 7.7)]
    K.shp(os.path.join(out, 'minerva.shp'), sp, r, (1.5, 1000, 200))
    return dict(n_boules=len(sp))


# ---------------------------------------------------------------- arche 50 Factory (photo 8 : poteaux jaunes, poutre, pieds en biais)
def arche_50(out, drop=0.0, half=21.0, leg=3.0, hleg=17.0, hbeam=4.6):
    Y = (250, 224, 22); W, H = 1024, 512; im = Image.new('RGB', (W, H), Y); d = ImageDraw.Draw(im)
    bw = 2 * half + leg; bb = (0, 0, 1024, int(1024 * hbeam / bw))
    fit(im, logo('50factory'), (bb[0] + 230, bb[1], bb[2] - 230, bb[3]), 0.12)
    d.line([(0, 2), (1024, 2)], fill=(30, 30, 30), width=4); d.line([(0, bb[3] - 2), (1024, bb[3] - 2)], fill=(30, 30, 30), width=4)
    lb = (0, 130, int(380 * leg / hleg), 510)
    fit(im, logo('50factory'), (lb[0], lb[1] + 30, lb[2], lb[3] - 30), 0.14, rot=90)
    pl = (700 / W, 1 - 400 / H); dk = (900 / W, 1 - 480 / H)
    d.rectangle([860, 450, 1000, 510], fill=(36, 36, 38))
    im = K.shade_v(im, (0, 0, W, bb[3]), 1.0, 0.92); _save(K.grain(im, 1.5), os.path.join(out, 'arche_50.png'))
    m = M(); y0 = -drop; c = 0.35
    rl = R(lb, W, H); rb = R(bb, W, H); plr = (pl[0], pl[1], pl[0] + 0.001, pl[1] + 0.001)
    for sx in (-1, 1):
        pts = [(sx * half + x, z) for x, z in chamfer(leg / 2, leg / 2, c)]
        rlf = (rl[2], rl[1], rl[0], rl[3])                                  # faces avant / arrière : logo vertical (pas en miroir)
        sides = [plr] * 8; sides[0] = rlf; sides[4] = rlf
        m.begin(); m.prism_y(pts, y0 - 0.5, y0 + hleg, sides, pl); m.end(center=(sx * half, y0 + hleg / 2, 0))
        for sz in (-1, 1):                                                   # pieds en biais (cales pleines) devant / derrière
            m.begin()
            zf = sz * (leg / 2 + 4.5); w_ = leg / 2 - 0.3
            A = [(sx * half - w_, y0, sz * leg / 2), (sx * half + w_, y0, sz * leg / 2)]
            B = [(sx * half - w_, y0, zf), (sx * half + w_, y0, zf)]
            Tt = [(sx * half - w_, y0 + 5.5, sz * leg / 2), (sx * half + w_, y0 + 5.5, sz * leg / 2)]
            m.quad([B[0], B[1], Tt[1], Tt[0]], plr); m.quad([A[0], A[1], B[1], B[0]], dk + (dk[0] + 0.001, dk[1] + 0.001))
            m.tri([A[0], B[0], Tt[0]], [pl] * 3); m.tri([A[1], B[1], Tt[1]], [pl] * 3)
            m.end(center=(sx * half, y0 + 1.5, sz * (leg / 2 + 1.5)))
    pts = [(z, y) for z, y in chamfer(leg / 2 + 0.2, hbeam / 2, 0.45)]      # poutre (section z, y) chanfreinée
    pts = [(z, y0 + hleg + hbeam / 2 + y) for z, y in pts]
    # côtés : 0 = dessous, 4 = dessus ; 2 = face +z, 6 = face -z (logo)
    m.begin()
    x0, x1 = -half - leg / 2 - 0.2, half + leg / 2 + 0.2
    n = len(pts)
    for i in range(n):
        (za, ya), (zb, yb) = pts[i], pts[(i + 1) % n]
        if abs(za - zb) < 1e-6 and abs(abs(za) - (leg / 2 + 0.2)) < 1e-6:   # faces verticales avant / arrière : le logo
            yl, yh = min(ya, yb), max(ya, yb)
            va = rb[1] + (rb[3] - rb[1]) * (yl - (y0 + hleg)) / hbeam; vb = rb[1] + (rb[3] - rb[1]) * (yh - (y0 + hleg)) / hbeam
            u0, u1 = (rb[0], rb[2]) if za > 0 else (rb[2], rb[0])
            m.tri([(x0, yl, za), (x1, yl, za), (x1, yh, za)], [(u0, va), (u1, va), (u1, vb)])
            m.tri([(x0, yl, za), (x1, yh, za), (x0, yh, za)], [(u0, va), (u1, vb), (u0, vb)])
        else:
            m.quad([(x0, ya, za), (x1, ya, za), (x1, yb, zb), (x0, yb, zb)], plr)
    m.poly([(x0, y, z) for z, y in pts], pl); m.poly([(x1, y, z) for z, y in pts], pl)
    m.end(center=(0, y0 + hleg + hbeam / 2, 0))
    m.write(os.path.join(out, 'arche_50.jm'), MAT_BACHE)
    return dict(clear=hleg, half=half)


# ---------------------------------------------------------------- camions du paddock
SEMIS = dict(honda=((205, 20, 26), 'honda', None), yamaha=((22, 50, 140), 'yamaha', None), monster=((16, 16, 18), 'monster', None),
             kawasaki=((70, 160, 30), 'kawasaki', None), ktm=((236, 104, 8), 'ktm', None), triumph=((20, 20, 22), 'triumph', None),
             ducati=((200, 16, 22), None, 'DUCATI'), blanc=((235, 235, 232), 'sxparis', None))


def _wheel(m, cx, cy, cz, r, w, tire, rim, side):
    """roue : pneu (cylindre) + jante (disque gris + moyeu) côté extérieur (side = ±1 en x)."""
    seg = 16; xo, xi = cx + side * w / 2, cx - side * w / 2
    m.begin()
    for k in range(seg):
        a0, a1 = 2 * np.pi * k / seg, 2 * np.pi * (k + 1) / seg
        p = lambda a, x, rr: (x, cy + rr * np.cos(a), cz + rr * np.sin(a))
        m.quad([p(a0, xi, r), p(a1, xi, r), p(a1, xo, r), p(a0, xo, r)], tire)
        m.tri([p(a0, xo, r), p(a1, xo, r), p(a1, xo, r * 0.62)], [cen(tire)] * 3)
        m.tri([p(a0, xo, r), p(a1, xo, r * 0.62), p(a0, xo, r * 0.62)], [cen(tire)] * 3)
        m.tri([p(a0, xo, r * 0.62), p(a1, xo, r * 0.62), (xo + side * 0.05, cy, cz)], [rim] * 3)
        m.tri([p(a1, xi, r), p(a0, xi, r), (xi, cy, cz)], [cen(tire)] * 3)
    m.end(center=(cx, cy, cz))


def semi(out):
    """semi-remorque d'équipe (photos du paddock de Paris) : remorque 48 x 8,5 x 13,5 ft (angles arrondis, jupes latérales,
    portes arrière), tracteur à cabine longue (déflecteur de toit, pare-brise, vitres, rétroviseurs, pare-chocs, réservoirs),
    10 vraies roues (pneu + jante), auvent sur le côté +x. +z = l'avant ; origine = avant de la remorque."""
    W = H = 1024; m = M()
    side, rear = R((0, 0, 1024, 250), W, H), R((0, 260, 200, 520), W, H)
    dark = R((320, 270, 400, 330), W, H); awn = R((420, 260, 1000, 520), W, H)
    cab, glass, chrome = R((0, 540, 400, 800), W, H), R((420, 540, 700, 700), W, H), R((720, 540, 800, 620), W, H)
    tire, rim = R((820, 540, 900, 620), W, H), (950 / W, 1 - 580 / H)
    blk = (360 / W, 1 - 300 / H); col = (200 / W, 1 - 660 / H)
    hw, y0, y1, L = 4.25, 4.0, 13.5, 48.0
    # remorque : section chanfreinée (angles arrondis), faces latérales = image du sponsor
    sec = [(hw - 0.35, y0), (hw, y0 + 0.35), (hw, y1 - 0.45), (hw - 0.45, y1), (-hw + 0.45, y1), (-hw, y1 - 0.45), (-hw, y0 + 0.35), (-hw + 0.35, y0)]
    m.begin()
    for i in range(len(sec)):
        (xa, ya), (xb, yb) = sec[i], sec[(i + 1) % len(sec)]
        if abs(xa - xb) < 1e-6 and abs(abs(xa) - hw) < 1e-6:                 # flancs : logo à l'endroit des deux côtés
            va, vb = side[1] + (side[3] - side[1]) * (ya - y0) / (y1 - y0), side[1] + (side[3] - side[1]) * (yb - y0) / (y1 - y0)
            u_back, u_front = (side[2], side[0]) if xa > 0 else (side[0], side[2])
            m.tri([(xa, ya, -L), (xa, ya, 0), (xb, yb, 0)], [(u_back, va), (u_front, va), (u_front, vb)])
            m.tri([(xa, ya, -L), (xb, yb, 0), (xb, yb, -L)], [(u_back, va), (u_front, vb), (u_back, vb)])
        else:
            m.quad([(xa, ya, -L), (xa, ya, 0), (xb, yb, 0), (xb, yb, -L)], dark)
    rr_ = rear; uvb = lambda x, y: (rr_[0] + (rr_[2] - rr_[0]) * (hw - x) / (2 * hw), rr_[1] + (rr_[3] - rr_[1]) * (y - y0) / (y1 - y0))
    m.poly([(x, y, -L) for x, y in sec], [uvb(x, y) for x, y in sec])        # portes arrière
    m.poly([(x, y, 0) for x, y in sec], cen(dark))
    m.end(center=(0, (y0 + y1) / 2, -L / 2))
    for sx in (-1, 1):                                                       # jupes latérales + châssis
        m.begin(); _bx(m, (sx * (hw - 0.1), 1.6, -34.0), (sx * (hw - 0.3), 4.0, -10.0), dark, 'xXzZy'); m.end()
    m.begin(); m.box((-3.6, 2.6, -46.5), (3.6, 4.0, -36.0), dark, 'xXzZy'); m.end()
    for z in (-44.0, -40.0):                                                 # essieux remorque (jumelés)
        for sx in (-1, 1):
            _wheel(m, sx * 3.25, 1.75, z, 1.75, 1.7, tire, rim, sx)
    # tracteur : cabine à couchette, capot, déflecteur
    zc0, zc1 = 1.5, 9.0                                                      # cabine (arrière -> pare-brise)
    m.begin()
    m.box((-4.0, 3.0, zc0), (4.0, 10.6, zc1), cab, 'xXzY', {'Y': dark})
    m.end()
    m.begin()                                                                # déflecteur de toit (rampe)
    m.quad([(-4.0, 10.6, zc1 - 0.2), (4.0, 10.6, zc1 - 0.2), (4.0, 13.2, zc0 + 1.5), (-4.0, 13.2, zc0 + 1.5)], cab)
    m.quad([(4.0, 10.6, zc0), (-4.0, 10.6, zc0), (-4.0, 13.2, zc0 + 1.5), (4.0, 13.2, zc0 + 1.5)], dark)
    for sx in (-1, 1):
        m.tri([(sx * 4.0, 10.6, zc0), (sx * 4.0, 10.6, zc1 - 0.2), (sx * 4.0, 13.2, zc0 + 1.5)], [col] * 3)
    m.quad([(-4.0, 10.6, zc0), (4.0, 10.6, zc0), (4.0, 10.6, zc1 - 0.2), (-4.0, 10.6, zc1 - 0.2)], dark)
    m.end(center=(0, 11.5, zc0 + 2.5))
    m.begin()                                                                # pare-brise incliné + capot
    m.quad([(-3.9, 7.0, zc1), (3.9, 7.0, zc1), (3.9, 10.4, zc1 - 0.7), (-3.9, 10.4, zc1 - 0.7)], glass)
    m.quad([(-3.9, 7.0, zc1), (3.9, 7.0, zc1), (3.9, 6.4, zc1 + 0.6), (-3.9, 6.4, zc1 + 0.6)], cab)
    for sx in (-1, 1):
        m.poly([(sx * 3.9, 3.0, zc1), (sx * 3.9, 7.0, zc1), (sx * 3.9, 10.4, zc1 - 0.7)], col)
    m.end(center=(0, 6.0, zc1 - 1.0))
    m.begin()
    m.box((-3.6, 2.4, zc1), (3.6, 6.4, zc1 + 5.2), cab, 'xXZY')             # capot
    m.end()
    m.begin(); m.box((-4.1, 1.4, zc1 + 5.0), (4.1, 2.6, zc1 + 5.6), chrome, 'xXzZYy'); m.end()   # pare-chocs
    m.begin(); m.box((-3.4, 2.6, zc1 + 5.2), (3.4, 5.8, zc1 + 5.3), chrome, 'Z'); m.end()        # calandre
    for sx in (-1, 1):
        m.begin(); _bx(m, (sx * 4.0, 6.6, zc1 - 0.3), (sx * 4.4, 8.6, zc1 + 0.1), dark, 'xXzZYy'); m.end()   # rétros
        m.begin(); _bx(m, (sx * 3.2, 1.7, zc0 + 0.2), (sx * 4.0, 3.0, zc0 + 4.0), chrome, 'xXzZYy'); m.end()  # réservoirs
        m.begin(); _bx(m, (sx * 4.02, 7.4, zc0 + 3.6), (sx * 4.05, 9.6, zc1 - 0.6), glass, 'xX'); m.end()   # vitres
    m.begin(); m.box((-3.2, 2.2, -2.0), (3.2, 3.0, zc0), dark, 'xXYy'); m.end()   # sellette / châssis
    for z, w in ((zc1 + 2.6, 1.1), (-0.5, 1.7), (-4.6, 1.7)):               # roues tracteur
        for sx in (-1, 1):
            _wheel(m, sx * 3.35, 1.75, z, 1.75, w, tire, rim, sx)
    for x, z in ((4.4, -42), (4.4, -6), (25, -42), (25, -6), (14.7, -42), (14.7, -6)):   # auvent
        m.tube((x, 0, z), (x, 11.6, z), 0.12, dark, 6, caps=False)
    m.quad([(4.25, 12.7, -44), (25.4, 11.4, -44), (25.4, 11.4, -4), (4.25, 12.7, -4)][::-1], awn, two=True)
    m.write(os.path.join(out, 'semi.jm'), MAT_CAR)
    for name, (bg, lg, txt) in SEMIS.items():
        im = Image.new('RGB', (W, H), bg); d = ImageDraw.Draw(im)
        ink = (20, 20, 22) if sum(bg) > 600 else (255, 255, 255)
        lgo = logo(lg) if lg else K.text_img(txt, 180, ink, 'ariblk.ttf', italic=0.15)
        if name == 'ktm':
            lgo = K.tint(lgo, (12, 12, 12))
        d.rectangle([0, 196, 1024, 250], fill=(18, 18, 20)); d.rectangle([0, 190, 1024, 196], fill=tuple(int(c * 0.6) for c in bg))
        fit(im, lgo, (240, 18, 784, 186), 0.1)
        fit(im, K.tint(logo('sxparis'), (255, 255, 255)) if sum(bg) < 600 else logo('sxparis'), (820, 200, 1010, 246), 0.05)
        fit(im, lgo, (16, 300, 184, 480), 0.06)                              # portes arrière
        d.line([(100, 262), (100, 518)], fill=tuple(int(c * 0.5) for c in bg), width=3)
        d.rectangle([420, 260, 1000, 520], fill=tuple(int(c * 0.85) for c in bg))      # auvent
        for k in range(8):
            d.line([(420 + k * 72, 260), (420 + k * 72, 520)], fill=tuple(int(c * 0.7) for c in bg), width=2)
        d.rectangle([0, 540, 400, 800], fill=bg); d.rectangle([0, 760, 400, 800], fill=(25, 25, 27))   # cabine
        fit(im, lgo, (40, 590, 360, 740), 0.12)
        d.rectangle([420, 540, 700, 700], fill=(34, 44, 56)); d.polygon([(440, 690), (560, 548), (630, 548), (510, 690)], fill=(70, 86, 104))
        d.rectangle([720, 540, 800, 620], fill=(176, 178, 182)); d.rectangle([820, 540, 900, 620], fill=(22, 22, 24))
        d.ellipse([910, 540, 990, 620], fill=(170, 172, 176)); d.ellipse([938, 568, 962, 592], fill=(60, 60, 62))
        d.rectangle([180, 640, 220, 680], fill=bg)
        d.rectangle([310, 262, 410, 340], fill=(26, 26, 28))
        im = K.shade_v(im, (0, 0, 1024, 196), 1.0, 0.86)
        _save(im, os.path.join(out, 'semi_%s.png' % name))
    return list(SEMIS)
