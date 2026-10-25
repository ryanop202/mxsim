"""v12 own models (made from scratch, nothing copied from JGSX): hospitality, pickups, finish arch, start grates, banners.
Formes nouvelles (pas mesurées) : d'après les photos de référence envoyées (docs/img/refs_paddock/) et des dimensions réelles.
- hospitality_usland.jm + .png : remorque hospitality 2 niveaux façon team usine (photos de référence 1-2-3) : 44 x 8,4 x 14 ft,
  module d'entrée avancé avec porte vitrée, escalier, tapis rouge et cordons. Logos USLAND (texte + icône U), sponsors RBT / FOX + étoile,
  noms des pilotes et du coach sur le module (TEAM ci-dessous).
- pickup_usland.jm + .png : pick-up double cabine surélevé noir (photo 8), nœud papillon jaune (calandre + hayon),
  crochets rouges, jantes noires.
- banner.jm + banner_<sponsor>.png : bannières 12 x 3 ft (USLAND, icône U, RBT, FOX).
- finish_arch.jm + finish_arch.png : portique carré en treillis alu (section 2,6 ft), piliers à +-ARCH_X du centre du
  couloir, bâche « FINISH » + damiers des deux côtés. Pas de collision (null).
- start_grate.jm + start_grate.png : grate en métal déployé derrière chaque grille (photo de référence) : partie étroite
  contre la grille puis partie large. Plaque de 0,08 ft posée au sol, pas de collision.
Convention : l'avant des véhicules / le sens de la course = axe z local (+z), y vers le haut.
Faces : sommets dans le sens direct vus de l'extérieur, cross(b-a, c-a) le long de la normale (comme tuff_usland.jm).
Texte des côtés : même sens des UV que le tuff USLAND (copié du van JGSX) -> à vérifier en jeu (miroir = inverser u).
Police : police libre intégrée à Pillow (ImageFont.load_default), en gras + italique -> même rendu sur tous les PC.
Run: python3 scripts/props_usland.py [dossier]   (par défaut assets/props/, copié dans les pistes par dress_sx.py)"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

OUTD = f'{ROOT}/assets/props'
TEAM = dict(riders=['B.PIGOIS', 'R.OPPLIGER', 'M.SONNERAT', 'E.VIDALENC'], coach='T.TESSERON', tag='RIDE BY RAOUL.')
NAVY, RED, WHITE = (22, 27, 58), (225, 30, 60), (250, 250, 250)
GOLD = (246, 190, 0)
ARCH_X = 22.0          # pillar centre, ft from the lane centre: past the 4 ft side walls of the finish jumps (flat ground on SX1-3)
GRATE = dict(parts=[(1.5, 3.2), (2.7, 3.8), (1.5, 2.4)], gap=2.5, t=0.06)   # cross shape (width, length) ft, from the gate backwards; v13b: gap 0.4 -> 2.5 = fallen gate (2.375 ft) + 0.125, the gate lands against the grate, not on it

# ------------------------------------------------------------------ mesh builder
class Mesh:
    def __init__(self, tex_w, tex_h):
        self.V, self.I, self.W, self.H = [], [], tex_w, tex_h
    def uv_px(self, px, py):                       # image pixel -> (u, v), v = 0 at the bottom row
        return px / self.W, 1.0 - py / self.H
    def _shade(self, UV, P, N):
        """solid palette colour -> baked shade sub-square (top / side / side near the ground / underside)."""
        u0, v0 = UV[0]
        if any(abs(u - u0) > 1e-9 or abs(v - v0) > 1e-9 for u, v in UV): return UV
        px, py = u0 * self.W, (1 - v0) * self.H
        if not (self.H - 128 <= py <= self.H - 64): return UV
        x0 = 8 + int((px - 8) // 72) * 72; y0 = self.H - 128
        if abs(px - (x0 + 32)) > 1 or abs(py - (y0 + 32)) > 1: return UV
        ny = N[1] / (np.linalg.norm(N) + 1e-12); low = np.mean(np.asarray(P, float)[:, 1]) < 0.9
        q = 0 if ny > 0.6 else (3 if ny < -0.3 else (2 if low else 1))
        return [self.uv_px(x0 + 16 + 32 * (q % 2), y0 + 16 + 32 * (q // 2))] * len(UV)
    def tri_fan(self, P, N, UV):
        a = len(self.V)
        UV = self._shade(list(UV), P, N)
        P = np.asarray(P, float)
        if np.dot(np.cross(P[1] - P[0], P[2] - P[0]), N) < 0:
            P, UV = P[::-1], UV[::-1]
        for p, t in zip(P, UV): self.V.append((*p, *N, *t))
        for k in range(1, len(P) - 1): self.I += [a, a + k, a + k + 1]
    def quad(self, P, N, uvf):
        self.tri_fan(P, np.asarray(N, float), [uvf(np.asarray(p, float)) for p in P])

    def box(self, x0, x1, y0, y1, z0, z1, faces):
        """faces: dict face -> uv source; face in +x -x +y -y +z -z, missing -> faces['*'].
        A uv source is ('c', (px, py)) solid palette colour, or ('r', (px0, py0, px1, py1)) image rect mapped on the face
        (u along the viewer's right, v up; top/bottom: u along x, v along z)."""
        C = {'+x': ((1, 0, 0), [(x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1)]),
             '-x': ((-1, 0, 0), [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)]),
             '+y': ((0, 1, 0), [(x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)]),
             '-y': ((0, -1, 0), [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)]),
             '+z': ((0, 0, 1), [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]),
             '-z': ((0, 0, -1), [(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)])}
        for f, (n, pts) in C.items():
            src = faces.get(f, faces.get('*'))
            if src is None: continue
            self.quad(pts, n, self._uvf(src, f, (x0, x1, y0, y1, z0, z1)))

    def _uvf(self, src, f, ext):
        kind, d = src
        if kind == 'c':
            uv = self.uv_px(*d); return lambda p: uv
        x0, x1, y0, y1, z0, z1 = ext; px0, py0, px1, py1 = d
        right = {'+x': (2, -1), '-x': (2, 1), '+z': (0, 1), '-z': (0, -1)}
        if f in right:
            ax, sg = right[f]; lo, hi = ((x0, x1), (y0, y1), (z0, z1))[ax]
            def g(p):
                s = (p[ax] - lo) / (hi - lo); s = s if sg > 0 else 1 - s; t = (p[1] - y0) / (y1 - y0)
                return self.uv_px(px0 + s * (px1 - px0), py1 - t * (py1 - py0))
            return g
        def g(p):                                   # top / bottom: image top row = front (+z)
            s = (p[0] - x0) / (x1 - x0); t = (p[2] - z0) / (z1 - z0)
            return self.uv_px(px0 + s * (px1 - px0), py1 - t * (py1 - py0))
        return g

    def tube(self, p0, p1, h, src):
        """square bar of half-thickness h from p0 to p1 (any direction), one solid colour."""
        p0, p1 = np.asarray(p0, float), np.asarray(p1, float); d = p1 - p0; L = np.linalg.norm(d); d /= L
        a = np.array([0, 1.0, 0]) if abs(d[1]) < 0.9 else np.array([1.0, 0, 0])
        e1 = np.cross(d, a); e1 /= np.linalg.norm(e1); e2 = np.cross(d, e1)
        uv = self.uv_px(*src[1]); g = lambda p: uv
        c = [(+1, +1), (-1, +1), (-1, -1), (+1, -1)]
        ring = lambda p: [p + h * (s1 * e1 + s2 * e2) for s1, s2 in c]
        A, B = ring(p0), ring(p1)
        for k in range(4):
            j = (k + 1) % 4; n = (A[k] + A[j]) / 2 - p0; n /= np.linalg.norm(n)
            self.quad([A[k], A[j], B[j], B[k]], n, g)
        self.quad(A, -d, g); self.quad(B, d, g)

    def cylinder(self, c, axis, r, w, side_src, cap_rect, seg=16):
        """wheel / tank: axis 0 = x, 2 = z; caps get cap_rect (image rect with the rim drawing), side a solid colour."""
        c = np.asarray(c, float); ax = np.zeros(3); ax[axis] = 1
        u_ = np.array([0, 1.0, 0]); v_ = np.cross(ax, u_)
        ang = np.linspace(0, 2 * np.pi, seg + 1)[:-1]
        rim = [c + r * (np.cos(t) * u_ + np.sin(t) * v_) for t in ang]
        A = [p - ax * w / 2 for p in rim]; B = [p + ax * w / 2 for p in rim]
        sc = self.uv_px(*side_src[1])
        for k in range(seg):
            j = (k + 1) % seg; n = (rim[k] + rim[j]) / 2 - c; n /= np.linalg.norm(n)
            self.quad([A[k], A[j], B[j], B[k]], n, lambda p: sc)
        px0, py0, px1, py1 = cap_rect
        cuv = lambda t: self.uv_px((px0 + px1) / 2 + np.cos(t) * (px1 - px0) / 2, (py0 + py1) / 2 - np.sin(t) * (py1 - py0) / 2)
        self.tri_fan(B, ax, [cuv(t) for t in ang]); self.tri_fan(A[::-1], -ax, [cuv(t) for t in ang[::-1]])

    def rbox(self, x0, x1, y0, y1, z0, z1, r, axis, faces, corner, seg=5):
        """box with its 4 edges parallel to `axis` rounded (radius r). faces as in box() (flat parts only, a missing face
        is skipped); corner = uv source of the rounded strips. The two caps (faces +-axis) are flat."""
        lo, hi = np.array([x0, y0, z0], float), np.array([x1, y1, z1], float)
        p, q = [k for k in range(3) if k != axis]; nm = 'xyz'
        cs = [((hi[p] - r, hi[q] - r), 0), ((lo[p] + r, hi[q] - r), 90), ((lo[p] + r, lo[q] + r), 180), ((hi[p] - r, lo[q] + r), 270)]
        prof = []
        for (cp, cq), a0 in cs:
            for t in np.radians(np.linspace(a0, a0 + 90, seg)): prof.append((cp + r * np.cos(t), cq + r * np.sin(t), np.cos(t), np.sin(t)))
        def P3(pp, qq, c):
            v = np.zeros(3); v[p], v[q], v[axis] = pp, qq, c; return v
        n = len(prof)
        for i in range(n):
            a, b = prof[i], prof[(i + 1) % n]
            N = np.zeros(3); N[p], N[q] = a[2] + b[2], a[3] + b[3]; N /= np.linalg.norm(N)
            flat = abs(abs(N[p]) - 1) < 1e-6 or abs(abs(N[q]) - 1) < 1e-6
            pts = [P3(a[0], a[1], lo[axis]), P3(b[0], b[1], lo[axis]), P3(b[0], b[1], hi[axis]), P3(a[0], a[1], hi[axis])]
            if flat:
                k = p if abs(N[p]) > 0.5 else q; f = ('+' if N[k] > 0 else '-') + nm[k]
                src = faces.get(f, faces.get('*'))
                if src is None: continue
                e = [x0, x1, y0, y1, z0, z1]; o = q if k == p else p
                e[2 * o] += r; e[2 * o + 1] -= r
                self.quad(pts, N, self._uvf(src, f, tuple(e)))
            else:
                self.quad(pts, N, self._uvf(corner, '+y', (x0, x1, y0, y1, z0, z1)))
        for c, sg in ((lo[axis], -1), (hi[axis], 1)):
            f = ('+' if sg > 0 else '-') + nm[axis]; src = faces.get(f, faces.get('*'))
            if src is None: continue
            N = np.zeros(3); N[axis] = sg; g = self._uvf(src, f, (x0, x1, y0, y1, z0, z1))
            pts = [P3(a[0], a[1], c) for a in prof]
            self.tri_fan(pts, N, [g(pt) for pt in pts])

    def wheel(self, c, axis, R, w, tread_rect, rim_rect, side_src, seg=24):
        """turned wheel along x (axis 0) or z (2): rounded tyre (tread strip textured), dished rim face with the rim drawing,
        same on both sides."""
        c = np.asarray(c, float); ax = np.zeros(3); ax[axis] = 1
        u_ = np.array([0, 1.0, 0]); v_ = np.cross(ax, u_)
        Rr = R * 0.64; h = w / 2
        ring = [(Rr * 0.97, h - 0.10), (Rr, h - 0.02), (R - 0.16, h), (R - 0.04, h - 0.09), (R, h - 0.24),
                (R, -h + 0.24), (R - 0.04, -h + 0.09), (R - 0.16, -h), (Rr, -h + 0.02), (Rr * 0.97, -h + 0.10)]
        ang = np.linspace(0, 2 * np.pi, seg + 1)
        dirn = lambda t: np.cos(t) * u_ + np.sin(t) * v_
        sc = self.uv_px(*side_src[1]); tx0, ty0, tx1, ty1 = tread_rect
        for i in range(len(ring) - 1):
            (ra, oa), (rb, ob) = ring[i], ring[i + 1]
            tread = (ra == R and rb == R)
            for k in range(seg):
                t0, t1 = ang[k], ang[k + 1]
                pts = [c + dirn(t0) * ra + ax * oa, c + dirn(t1) * ra + ax * oa, c + dirn(t1) * rb + ax * ob, c + dirn(t0) * rb + ax * ob]
                tm = (t0 + t1) / 2; dr, do = rb - ra, ob - oa
                N = dirn(tm) * (-do) + ax * dr                       # profile normal, pointing out of the tyre
                if np.dot(N, (pts[0] + pts[2]) / 2 - c - ax * (oa + ob) / 2) < 0: N = -N
                N /= np.linalg.norm(N)
                if tread:
                    uvs = [self.uv_px(tx0 + (tx1 - tx0) * s, ty0 + (ty1 - ty0) * (h - o) / w) for s, o in
                           ((k / seg, oa), ((k + 1) / seg, oa), ((k + 1) / seg, ob), (k / seg, ob))]
                    self.tri_fan(pts, N, uvs)
                else:
                    self.quad(pts, N, lambda p_: sc)
        px0, py0, px1, py1 = rim_rect
        for sg in (1, -1):                                          # dished rim faces
            o = sg * (h - 0.10); ctr = c + ax * (o - sg * 0.12)
            rimp = [c + dirn(t) * Rr * 0.97 + ax * o for t in ang[:-1]]
            uvs = [self.uv_px((px0 + px1) / 2 + np.cos(t) * (px1 - px0) / 2 * sg, (py0 + py1) / 2 - np.sin(t) * (py1 - py0) / 2) for t in ang[:-1]]
            for k in range(seg):
                j = (k + 1) % seg
                self.tri_fan([ctr, rimp[k], rimp[j]], ax * sg, [self.uv_px((px0 + px1) / 2, (py0 + py1) / 2), uvs[k], uvs[j]])

    def write(self, path, material=(0, 0, 0, 0, 0)):
        """material = 2nd line of the .jm, read from the JGSX models: specular power, strength, colour (r g b).
        e.g. transit / semi 50 1 1 1 1 (glossy), gate01 16 1 0.35 0.35 0.35, bobcat 0 0 0 0 0 (matte)."""
        lines = ['JM1', ' '.join(f'{v:.6f}' for v in material), f'{len(self.V)} {len(self.I) // 3}']
        lines += [' '.join(f'{v:.6f}' for v in row) for row in self.V] + [str(i) for i in self.I] + ['']
        open(path, 'w', newline='\n').write('\n'.join(lines))           # LF, as the rest of the repo / the game files
        return len(self.V), len(self.I) // 3

# ------------------------------------------------------------------ texture helpers
SHADES = (1.0, 0.84, 0.66, 0.48)   # baked light: top, side, side near the ground, underside
def palette(img, names, colours):
    """solid squares at the bottom of the texture; returns name -> ('c', centre pixel). Each 64 px square holds the colour in
    4 baked shades (2 x 2 sub-squares, SHADES) picked per face by Mesh.tri_fan from its normal and height."""
    d = ImageDraw.Draw(img); W, H = img.size; out = {}; y0 = H - 128
    for k, (nm, col) in enumerate(zip(names, colours)):
        x0 = 8 + k * 72
        for q, f in enumerate(SHADES):
            sx, sy = x0 + 32 * (q % 2), y0 + 32 * (q // 2)
            d.rectangle([sx, sy, sx + 31, sy + 31], fill=tuple(int(min(255, c * f)) for c in col))
        out[nm] = ('c', (x0 + 32, y0 + 32))
    return out

def rim_drawing(img, rect, rim=(200, 200, 205), tyre=(25, 25, 25)):
    d = ImageDraw.Draw(img); x0, y0, x1, y1 = rect; cx, cy, R = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2
    d.ellipse([x0, y0, x1, y1], fill=tyre); r = R * 0.62
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=rim); r2 = R * 0.18
    for k in range(8):
        t = k * np.pi / 4; px, py = cx + np.cos(t) * R * 0.42, cy + np.sin(t) * R * 0.42
        d.ellipse([px - R * 0.05, py - R * 0.05, px + R * 0.05, py + R * 0.05], fill=(90, 90, 95))
    d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], fill=(150, 150, 155))

def rim_face(img, rect, metal=(200, 202, 206), dark=(40, 40, 44), spokes=6):
    """rim face drawing filling the square rect (= the rim disc): lip, spokes, holes, centre cap."""
    d = ImageDraw.Draw(img); x0, y0, x1, y1 = rect; cx, cy, R = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2
    d.ellipse([x0, y0, x1, y1], fill=dark)
    d.ellipse([x0 + R * 0.04, y0 + R * 0.04, x1 - R * 0.04, y1 - R * 0.04], fill=metal)        # lip
    d.ellipse([x0 + R * 0.12, y0 + R * 0.12, x1 - R * 0.12, y1 - R * 0.12], fill=dark)        # well
    for k in range(spokes):
        t = k * 2 * np.pi / spokes; n = np.array([-np.sin(t), np.cos(t)])
        a = np.array([np.cos(t), np.sin(t)])
        pts = [(cx, cy) + a * R * 0.25 + n * R * 0.10, (cx, cy) + a * R * 0.9 + n * R * 0.12,
               (cx, cy) + a * R * 0.9 - n * R * 0.12, (cx, cy) + a * R * 0.25 - n * R * 0.10]
        d.polygon([tuple(p) for p in pts], fill=metal)
    d.ellipse([cx - R * 0.30, cy - R * 0.30, cx + R * 0.30, cy + R * 0.30], fill=metal)
    for k in range(spokes):
        t = (k + 0.5) * 2 * np.pi / spokes; px, py = cx + np.cos(t) * R * 0.2, cy + np.sin(t) * R * 0.2
        d.ellipse([px - R * 0.035, py - R * 0.035, px + R * 0.035, py + R * 0.035], fill=dark)
    d.ellipse([cx - R * 0.11, cy - R * 0.11, cx + R * 0.11, cy + R * 0.11], fill=tuple(int(v * 0.8) for v in metal))

def tread_strip(img, rect, blocks=36, rubber=(28, 28, 30), groove=(12, 12, 13)):
    """tyre tread unrolled: u = around the tyre, v = across; staggered blocks."""
    d = ImageDraw.Draw(img); x0, y0, x1, y1 = rect; W, H = x1 - x0, y1 - y0
    d.rectangle([x0, y0, x1, y1], fill=groove); bw = W / blocks
    for k in range(blocks):
        bx = x0 + k * bw
        for j, (va, vb) in enumerate(((0.04, 0.30), (0.36, 0.64), (0.70, 0.96))):
            off = bw * 0.3 * ((k + j) % 2)
            d.rectangle([bx + off * 0.2 + 1, y0 + H * va, bx + bw * 0.78 + off * 0.2, y0 + H * vb], fill=rubber)

_LOGO = None
def logo_mask():
    """alpha mask of the USLAND logo (navy text) + mask of its red marks, cropped to the ink."""
    global _LOGO
    if _LOGO is None:
        lg = np.array(Image.open(f'{ROOT}/assets/usland_logo.png').convert('RGB')).astype(float)
        ink = lg.min(2) < 150; ys, xs = np.nonzero(ink)
        c = lg[ys.min() - 4:ys.max() + 5, xs.min() - 4:xs.max() + 5]
        red = (c[..., 0] > 150) & (c[..., 1] < 110)
        a = np.clip((235 - c.min(2)) / 160, 0, 1); a[red] = 1
        _LOGO = (a, red)
    return _LOGO

def blend(img, rgba, ox, oy):
    """alpha-paste an RGBA numpy array (float 0..1 alpha in [..., 3]) onto an RGB PIL image, clipped to the image."""
    base = np.array(img).astype(float); h, w = rgba.shape[:2]; H, W = base.shape[:2]
    x0, y0, x1, y1 = max(ox, 0), max(oy, 0), min(ox + w, W), min(oy + h, H)
    if x1 <= x0 or y1 <= y0: return
    s = rgba[y0 - oy:y1 - oy, x0 - ox:x1 - ox]; A = s[..., 3:4]
    base[y0:y1, x0:x1] = base[y0:y1, x0:x1] * (1 - A) + s[..., :3] * A
    img.paste(Image.fromarray(base.astype(np.uint8)))

def paste_logo(img, box, colour, accent=RED):
    """logo filling box (x0, y0, x1, y1) keeping its aspect, in `colour`, red marks in `accent`."""
    a, red = logo_mask(); x0, y0, x1, y1 = box; h, w = a.shape
    s = min((x1 - x0) / w, (y1 - y0) / h); W_, H_ = int(w * s), int(h * s)
    A = np.array(Image.fromarray((a * 255).astype(np.uint8)).resize((W_, H_), Image.LANCZOS)) / 255.0
    R = np.array(Image.fromarray(red.astype(np.uint8) * 255).resize((W_, H_), Image.LANCZOS)) > 127
    col = np.where(R[..., None], np.array(accent, float), np.array(colour, float))
    blend(img, np.dstack([col, A]), int((x0 + x1 - W_) / 2), int((y0 + y1 - H_) / 2))

def text_rgba(txt, h_px, fill, bold=0.07, italic=0.22, outline=None):
    """text rendered with Pillow's built-in font, bold (stroke) and slanted like team graphics; returns RGBA float array."""
    size = int(h_px * 1.45); f = ImageFont.load_default(size=size); sw = max(1, int(size * bold))
    l, t, r, b = f.getbbox(txt, stroke_width=sw); pad = int(h_px * italic) + sw + 4
    im = Image.new('L', (r - l + 2 * pad, b - t + 2 * pad), 0)
    ImageDraw.Draw(im).text((pad - l, pad - t), txt, font=f, fill=255, stroke_width=sw, stroke_fill=255)
    if italic: im = im.transform(im.size, Image.AFFINE, (1, italic, -italic * im.size[1] / 2, 0, 1, 0), Image.BICUBIC)
    a = np.array(im) / 255.0; ys, xs = np.nonzero(a > 0.02); a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    k = h_px / a.shape[0]                         # ink height = h_px exactly (capitals)
    a = np.array(Image.fromarray((a * 255).astype(np.uint8)).resize((max(1, int(a.shape[1] * k)), h_px), Image.LANCZOS)) / 255.0
    rgb = np.ones(a.shape + (3,)) * np.array(fill, float)
    if outline is not None:                       # thin outline in another colour
        o = np.array(Image.fromarray((a * 255).astype(np.uint8)).filter(__import__('PIL.ImageFilter', fromlist=['x']).MaxFilter(5))) / 255.0
        rgb = np.where((a < 0.5)[..., None], np.array(outline, float), rgb); a = np.maximum(a, o)
    return np.dstack([rgb, a])

def put_text(img, txt, h_px, fill, x, y, anchor='l', max_w=None, **kw):
    t = text_rgba(txt, h_px, fill, **kw)
    if max_w and t.shape[1] > max_w:              # shrink to fit
        k = max_w / t.shape[1]; sz = (int(t.shape[1] * k), int(t.shape[0] * k))
        a = np.array(Image.fromarray((t[..., 3] * 255).astype(np.uint8)).resize(sz, Image.LANCZOS)) / 255.0
        t = np.dstack([np.ones(a.shape + (3,)) * t[0, 0, :3], a])
    w = t.shape[1]; ox = x if anchor == 'l' else (x - w if anchor == 'r' else x - w // 2)
    blend(img, t, int(ox), int(y)); return w

def panel(size_ft, px_w, draw_fn, ao=0.22):
    """draw at the real aspect of the face (no stretching); the caller resizes it into its texture rect.
    ao: baked shading, the lower part of the face darkens towards the ground (no shadows in MX Simulator)."""
    w_ft, h_ft = size_ft; ph = int(px_w * h_ft / w_ft)
    im = Image.new('RGB', (px_w, ph)); draw_fn(im)
    if ao:
        a = np.array(im).astype(float); t = np.linspace(0, 1, ph)[:, None, None]
        k = 1 - ao * np.clip((t - 0.55) / 0.45, 0, 1) ** 1.5 + 0.04 * np.clip((0.15 - t) / 0.15, 0, 1)
        im = Image.fromarray(np.clip(a * k, 0, 255).astype(np.uint8))
    return im

def bowtie(img, box, fill=GOLD, edge=(150, 150, 155)):
    """yellow bow-tie emblem (pickup grille / tailgate) in box (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = box; W, H = x1 - x0, y1 - y0
    P = [(0.00, 0.30), (0.36, 0.30), (0.38, 0.06), (0.64, 0.06), (0.62, 0.30), (1.00, 0.30), (0.95, 0.72), (0.61, 0.72),
         (0.59, 0.94), (0.33, 0.94), (0.35, 0.72), (0.03, 0.72)]
    pts = [(x0 + W * u, y0 + H * v) for u, v in P]
    d = ImageDraw.Draw(img); d.polygon(pts, fill=edge)
    c = (x0 + W / 2, y0 + H / 2); inner = [(c[0] + (p[0] - c[0]) * 0.86, c[1] + (p[1] - c[1]) * 0.80) for p in pts]
    d.polygon(inner, fill=fill)

# ------------------------------------------------------------------ logos (vrais fichiers fournis, assets/logos/)
# icône U d'USLAND (l1_*.jpg), RBT, FOX, étoile : détourés depuis leur fond (alpha) et posés sans déformation.
SPONSORS = ['RBT', 'FOX', 'STAR']
LOGO_FILES = {('ICON', 'dark'): ('l1_white.jpg', 'black'), ('ICON', 'light'): ('l1_black.jpg', 'white'),
              ('RBT', 'any'): ('rbt_wide.png', None), ('FOX', 'any'): ('fox_white.png', None), ('STAR', 'any'): ('star.png', None),
              ('U', 'dark'): ('u_monogram.jpg', 'black')}
_LCACHE = {}
def logo_rgba(fname, bg):
    """RGBA float array of a logo file: its own alpha if it has one, else alpha from the distance to its plain background."""
    if (fname, bg) not in _LCACHE:
        im = Image.open(f'{ROOT}/assets/logos/{fname}')
        if bg is None:
            a = np.array(im.convert('RGBA')).astype(float) / 255.0; A = a[..., 3]; rgb = a[..., :3] * 255
        else:
            c = np.array(im.convert('RGB')).astype(float)
            if bg == 'white': A = np.clip(((255 - c).max(2) - 25) / 110, 0, 1)
            else: A = np.clip((c.max(2) - 25) / 110, 0, 1)
            rgb = c
        ys, xs = np.nonzero(A > 0.1)
        sl = (slice(ys.min(), ys.max() + 1), slice(xs.min(), xs.max() + 1))
        _LCACHE[(fname, bg)] = np.dstack([rgb[sl], A[sl]])
    return _LCACHE[(fname, bg)]

def paste_rgba(img, rgba, box, colour=None):
    """fit rgba in box (aspect kept, centred); colour = recolour all the ink, None = original colours."""
    x0, y0, x1, y1 = box; h, w = rgba.shape[:2]; s = min((x1 - x0) / w, (y1 - y0) / h)
    W_, H_ = max(1, int(w * s)), max(1, int(h * s))
    ch = [np.array(Image.fromarray(np.clip(rgba[..., k] * (255 if k == 3 else 1), 0, 255).astype(np.uint8)).resize((W_, H_), Image.LANCZOS)).astype(float) for k in range(4)]
    A = ch[3] / 255.0; rgb = np.dstack(ch[:3]) if colour is None else np.ones(A.shape + (3,)) * np.array(colour, float)
    blend(img, np.dstack([rgb, A]), int((x0 + x1 - W_) / 2), int((y0 + y1 - H_) / 2))

def logo(img, name, box, on='dark', ink=None):
    """draw a logo by name: USLAND (wordmark), ICON (U icon), U (monogram), RBT, FOX, STAR.
    on = 'dark' / 'light' background (picks the white or the black version); ink = recolour (single-colour logos)."""
    if name == 'USLAND': paste_logo(img, box, WHITE if on == 'dark' else NAVY); return
    key = (name, on) if (name, on) in LOGO_FILES else (name, 'any')
    f, bg = LOGO_FILES[key]
    if name in ('RBT', 'FOX') and ink is None: ink = WHITE if on == 'dark' else (12, 12, 12)
    paste_rgba(img, logo_rgba(f, bg), box, ink)

def sponsor(img, name, box, ink=(10, 10, 10)):
    logo(img, name, box, on='dark' if sum(ink) > 600 else 'light')


# ------------------------------------------------------------------ hospitality trailer (reference photos 1-2-3, HRC-style unit)
# Remorque hospitality 2 niveaux : cadre blanc arrondi, toit noir, côtés entièrement ouverts (extensions sur toute la longueur des
# deux côtés), module d'entrée centré avec porte vitrée, escalier, tapis rouge et cordons.
# Vitres : fond gris, logos noirs centrés (USLAND, icône U, RBT, FOX). Étoile au-dessus du USLAND de la porte.
HW, HY0, HY1, HL = 4.2, 3.6, 13.8, 44.0          # main box: half width, floor / roof height, length (z from -HL/2 to HL/2)
SO = dict(depth=3.5, z=19.0, y0=3.9, y1=13.5)     # slide-outs on both sides, z from -SO.z to SO.z
MOD = dict(half=8.0, depth=2.0)                    # entrance module in the middle of the +x slide-out
GLASS_HI, GLASS_LO, FRAME, CHAR, ROOF = (95, 100, 108), (48, 52, 58), (240, 241, 243), (36, 38, 42), (22, 22, 24)
INK = (16, 16, 18)                                 # black logos on the grey glass

def glass(d, box, top, bot, streak=True):
    x0, y0, x1, y1 = box; n = max(2, int(y1 - y0))
    for i in range(n):
        t = i / (n - 1); c = tuple(int(top[k] + (bot[k] - top[k]) * t) for k in range(3))
        d.line([x0, y0 + i, x1, y0 + i], fill=c)
    if streak:                                                                   # sky reflection band
        d.polygon([(x0, y0 + (y1 - y0) * 0.18), (x1, y0 + (y1 - y0) * 0.05), (x1, y0 + (y1 - y0) * 0.14), (x0, y0 + (y1 - y0) * 0.27)],
                  fill=tuple(min(255, int(v * 1.25)) for v in top))

def centered_logo(im, name, cx, cy, w, h):
    """logo centred on (cx, cy), fitted in w x h, in black (window panels)."""
    box = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
    if name == 'USLAND': paste_logo(im, box, INK, accent=INK)
    else: logo(im, name, box, on='light', ink=INK)

SIDE_LOGOS = ['FOX', 'USLAND', 'ICON', 'RBT', 'USLAND', 'USLAND', 'RBT', 'ICON', 'USLAND', 'FOX']   # symmetric
def hosp_side(length):
    """slide-out face (length x 9.6 ft): white frame, upper row of light-grey glass panels with black logos centred,
    lower row of dark glass."""
    W = 2032; ppf = W / length; H = int((SO['y1'] - SO['y0']) * ppf); im = Image.new('RGB', (W, H), CHAR); d = ImageDraw.Draw(im)
    f = lambda ft: int(ft * ppf)
    top, mid, bot = f(0.3), f(4.8), H - f(0.45)
    d.rectangle([0, 0, W, top], fill=FRAME); d.rectangle([0, bot, W, H], fill=FRAME)
    d.rectangle([0, 0, f(0.4), H], fill=FRAME); d.rectangle([W - f(0.4), 0, W, H], fill=FRAME)
    n = len(SIDE_LOGOS); x0 = f(0.4); pw = (W - 2 * x0) / n
    for i, lg in enumerate(SIDE_LOGOS):
        a, b = x0 + i * pw + 3, x0 + (i + 1) * pw - 3
        glass(d, (a, top + 3, b, mid - 3), (150, 154, 160), (124, 128, 135), streak=False)
        glass(d, (a, mid + f(0.12), b, bot - 3), GLASS_HI, GLASS_LO)
        cx, cy = (a + b) / 2, (top + mid) / 2
        if lg in ('ICON',): centered_logo(im, lg, cx, cy, pw * 0.42, (mid - top) * 0.42)
        else: centered_logo(im, lg, cx, cy, pw * 0.70, (mid - top) * 0.30)
    d.rectangle([0, mid - 2, W, mid + f(0.12)], fill=(150, 154, 160))            # metal belt line
    return im

def hosp_front():
    """entrance module face, 16 x 10.2 ft: white frame; side columns (black glass / white panel with a small RBT / black
    panel with the names, centred); centre: star, white panel with the USLAND logo in colour, double glass door."""
    W = 1008; Lm = 2 * MOD['half']; ppf = W / Lm; H = int((HY1 - HY0) * ppf); im = Image.new('RGB', (W, H), FRAME); d = ImageDraw.Draw(im)
    f = lambda ft: int(ft * ppf)
    fr = f(0.4); c0, c1 = f(5.0), W - f(5.0); ytop, ypan, ylow = f(2.6), f(5.2), H - fr
    for x0, x1 in ((fr, c0 - f(0.15)), (c1 + f(0.15), W - fr)):
        glass(d, (x0, fr, x1, ytop), (30, 32, 36), (18, 19, 22))
        d.rectangle([x0, ytop, x1, ypan], fill=WHITE)
        logo(im, 'RBT', ((x0 + x1) / 2 - (x1 - x0) * 0.27, ytop + (ypan - ytop) * 0.28, (x0 + x1) / 2 + (x1 - x0) * 0.27, ypan - (ypan - ytop) * 0.28), on='light')
        d.rectangle([x0, ypan + 4, x1, ylow], fill=(22, 23, 26))
    glass(d, (c0, fr, c1, ytop), (30, 32, 36), (18, 19, 22))
    logo(im, 'STAR', ((c0 + c1) / 2 - f(0.8), fr + f(0.25), (c0 + c1) / 2 + f(0.8), ytop - f(0.25)), ink=(150, 154, 160))  # star (light grey) above the USLAND
    d.rectangle([c0, ytop, c1, f(4.6)], fill=WHITE)
    paste_logo(im, (c0 + f(0.5), ytop + f(0.35), c1 - f(0.5), f(4.6) - f(0.35)), NAVY, accent=RED)
    d.rectangle([c0, f(4.6), c1, ylow], fill=(60, 62, 66))                       # door frame
    for x0, x1 in ((c0 + f(0.25), (c0 + c1) / 2 - f(0.08)), ((c0 + c1) / 2 + f(0.08), c1 - f(0.25))):
        glass(d, (x0, f(4.85), x1, ylow - f(0.15)), (70, 74, 82), (28, 30, 34))
    for x in ((c0 + c1) / 2 - f(0.3), (c0 + c1) / 2 + f(0.22)): d.rectangle([x, f(7.0), x + f(0.08), f(8.4)], fill=(200, 200, 205))
    # names, centred in the lower black panels
    grey = (150, 154, 160)
    def block(x0, x1, lines):                     # lines: (text, height_ft, colour); vertically centred block
        gap = f(0.22); tot = sum(f(h) for _, h, _ in lines) + gap * (len(lines) - 1); y = (ypan + ylow) / 2 - tot / 2
        for t, h, c in lines:
            if t: put_text(im, t, f(h), c, (x0 + x1) / 2, y, anchor='c', max_w=(x1 - x0) * 0.86)
            y += f(h) + gap
    block(fr, c0 - f(0.15), [('PILOTES', 0.26, grey)] + [(nm, 0.34, WHITE) for nm in TEAM['riders']])
    block(c1 + f(0.15), W - fr, [('COACH', 0.26, grey), (TEAM['coach'], 0.34, WHITE), ('', 0.2, WHITE), (TEAM['tag'], 0.30, RED)])
    return im

def hosp_end(width_ft, height_ft, with_logo=True, tag=False):
    """end faces: white frame, grey glass with the black U icon centred, dark glass below (rear: RIDE BY RAOUL. on it)."""
    W = 512; ppf = W / width_ft; H = int(height_ft * ppf); im = Image.new('RGB', (W, H), FRAME); d = ImageDraw.Draw(im)
    fr = int(0.4 * ppf); mid = int(H * 0.47)
    glass(d, (fr, fr, W - fr, mid), (150, 154, 160), (124, 128, 135), streak=False)
    glass(d, (fr, mid + 6, W - fr, H - int(0.5 * ppf)), (40, 43, 48), (20, 21, 24))
    if with_logo: centered_logo(im, 'ICON', W / 2, (fr + mid) / 2, (W - 2 * fr) * 0.45, (mid - fr) * 0.55)
    if tag:
        lo = H - int(0.5 * ppf)
        put_text(im, TEAM['tag'], int(0.42 * ppf), WHITE, W / 2, (mid + lo) / 2 - 0.21 * ppf, anchor='c', italic=0.22, max_w=int((W - 2 * fr) * 0.86))
    return im

def hospitality_texture():
    img = Image.new('RGB', (2048, 2048), CHAR)
    img.paste(hosp_side(2 * SO['z']).resize((2032, 472), Image.LANCZOS), (8, 8))
    img.paste(hosp_front().resize((1008, 642), Image.LANCZOS), (8, 496))
    img.paste(hosp_end(2 * HW, HY1 - HY0).resize((496, 600), Image.LANCZOS), (1032, 496))
    img.paste(hosp_end(2 * HW, HY1 - HY0, tag=True).resize((496, 600), Image.LANCZOS), (8, 1160))   # rear (-z, wheel end)
    img.paste(hosp_end(SO['depth'], SO['y1'] - SO['y0'], False).resize((240, 520), Image.LANCZOS), (1544, 496))
    def carpet(im):
        d = ImageDraw.Draw(im); W, H = im.size; d.rectangle([0, 0, W, H], fill=(178, 22, 30))
        d.rectangle([0, 0, W, 6], fill=(120, 12, 18)); d.rectangle([0, H - 6, W, H], fill=(120, 12, 18))
    img.paste(panel((8, 12), 256, carpet).resize((256, 384)), (1032, 1160))
    rim_face(img, (1304, 1160, 1560, 1416), metal=(190, 192, 196), dark=(50, 52, 56), spokes=8)
    tread_strip(img, (1032, 1560, 2040, 1640))
    pal = palette(img, ['frame', 'char', 'steel', 'tyre', 'glass', 'white', 'red', 'rope', 'chrome', 'roof'],
                  [FRAME, CHAR, (88, 92, 98), (26, 26, 28), (30, 32, 36), WHITE, (200, 20, 20), (190, 20, 30), (205, 208, 214), ROOF])
    pal.update(side=('r', (8, 8, 2040, 480)), front=('r', (8, 496, 1016, 1138)), end=('r', (1032, 496, 1528, 1096)),
               soside=('r', (1544, 496, 1784, 1016)), rear=('r', (8, 1160, 504, 1760)), carpet=('r', (1032, 1160, 1288, 1544)), rim=(1304, 1160, 1560, 1416),
               tread=(1032, 1560, 2040, 1640))
    return img, pal

def hospitality_model(pal):
    m = Mesh(2048, 2048); P = pal; z0, z1 = -HL / 2, HL / 2
    # main box: long edges rounded (roof + floor), black roof, white rounded edges
    m.rbox(-HW, HW, HY0, HY1, z0, z1, 0.7, 2, {'+x': P['end'], '-x': P['end'], '+z': P['end'], '-z': P['rear'], '+y': P['roof'], '-y': P['char']}, P['frame'])
    # slide-outs on both sides over the whole length (outer vertical edges rounded)
    d, sz, sy0, sy1 = SO['depth'], SO['z'], SO['y0'], SO['y1']
    m.rbox(HW - 0.5, HW + d, sy0, sy1, -sz, sz, 0.6, 1, {'+x': P['side'], '+z': P['soside'], '-z': P['soside'], '+y': P['roof'], '-y': P['char']}, P['frame'])
    m.rbox(-HW - d, -HW + 0.5, sy0, sy1, -sz, sz, 0.6, 1, {'-x': P['side'], '+z': P['soside'], '-z': P['soside'], '+y': P['roof'], '-y': P['char']}, P['frame'])
    for s in (-1, 1):                                                                               # white sills
        xa, xb = sorted((s * (HW - 0.5), s * (HW + d + 0.1)))
        m.rbox(xa, xb, sy0 - 0.35, sy0, -sz - 0.1, sz + 0.1, 0.15, 2, {'*': P['frame']}, P['frame'])
    # entrance module, centred on the +x slide-out
    xm0, xm1, hz = HW + d - 0.3, HW + d + MOD['depth'], MOD['half']
    m.rbox(xm0, xm1, HY0, HY1, -hz, hz, 0.45, 1, {'+x': P['front'], '+z': P['frame'], '-z': P['frame'], '+y': P['roof'], '-y': P['char']}, P['frame'])
    m.rbox(xm0, xm1 + 0.25, HY1, HY1 + 0.35, -hz - 0.25, hz + 0.25, 0.3, 1, {'*': P['frame'], '+y': P['roof']}, P['frame'])
    # running gear: tri-axle, support legs
    for zc in (-12.0, -15.6, -19.2):
        for s in (-1, 1): m.wheel((s * 3.4, 1.55, zc), 0, 1.55, 1.05, P['tread'], P['rim'], P['tyre'])
    m.box(-3.0, 3.0, 1.5, HY0, -20.5, -10.5, {'*': P['char']})
    for zc in (8.0, -6.0):
        for s in (-1, 1): m.box(s * 3.2 - 0.25, s * 3.2 + 0.25, 0, HY0, zc - 0.25, zc + 0.25, {'*': P['steel']}); m.box(s * 3.2 - 0.7, s * 3.2 + 0.7, 0, 0.1, zc - 0.7, zc + 0.7, {'*': P['char']})
    # stairs to the door, 5 steps, railings
    xs = xm1; rise = (HY0 - 0.05) / 5; run = 1.0; w = 2.2
    for k in range(5):
        y = rise * (k + 1); x = xs + (4 - k) * run
        m.box(x, x + run + 0.05, y - 0.12, y, -w, w, {'*': P['steel']})
    m.box(xs, xs + 1.0, HY0 - 0.15, HY0 - 0.05, -w, w, {'*': P['steel']})
    for s in (-1, 1):
        zr = s * (w - 0.05)
        m.tube((xs + 5 * run + 0.2, 0, zr), (xs + 5 * run + 0.2, 3.2, zr), 0.06, P['steel'])
        m.tube((xs + 0.2, HY0, zr), (xs + 0.2, HY0 + 3.2, zr), 0.06, P['steel'])
        m.tube((xs + 5 * run + 0.2, 3.2, zr), (xs + 0.2, HY0 + 3.2, zr), 0.06, P['steel'])
        m.tube((xs + 5 * run + 0.2, 1.6, zr), (xs + 0.2, HY0 + 1.6, zr), 0.05, P['steel'])
        m.box(xs + 0.5 * run, xs + 5 * run + 0.3, 0, 0.12, zr - 0.1, zr + 0.1, {'*': P['steel']})
    # red carpet + rope line (photo 2)
    cx0 = xs + 5 * run + 0.4
    m.box(cx0, cx0 + 12.0, 0.0, 0.04, -4.0, 4.0, {'+y': P['carpet'], '*': P['rope']})
    posts = [(cx0 + 1.0, -4.6), (cx0 + 6.0, -4.6), (cx0 + 11.0, -4.6), (cx0 + 1.0, 4.6), (cx0 + 6.0, 4.6), (cx0 + 11.0, 4.6)]
    for x, z in posts:
        m.tube((x, 0, z), (x, 3.0, z), 0.08, P['chrome']); m.box(x - 0.45, x + 0.45, 0, 0.08, z - 0.45, z + 0.45, {'*': P['chrome']})
    for (xa, za), (xb, zb) in zip(posts[:2] + posts[3:5], posts[1:3] + posts[4:6]):
        m.tube((xa, 2.8, za), ((xa + xb) / 2, 2.3, za), 0.06, P['rope']); m.tube(((xa + xb) / 2, 2.3, za), (xb, 2.8, zb), 0.06, P['rope'])
    return m


# ------------------------------------------------------------------ pickup (photo 8: black crew-cab off-road pickup, gold bow-tie)
# Carrosserie « lissée » : sections arrondies (super-ellipses) reliées entre elles (loft), pavillon trapézoïdal, benne longue
# et creuse (plancher, parois, ridelle), élargisseurs d'ailes en arc, marchepieds, pare-chocs arrondis, crochets rouges.
PK_BODY = (24, 24, 27)
PK = dict(zf=10.0, zr=-10.3, zcab=-3.7, zbed=-3.85, wf=6.4, wr=-6.6, R=1.6)   # front, rear, cab back, bed front, wheel z, wheel radius
BODY_Z, BODY_Y = (-3.7, 10.0), (1.85, 4.98)          # side texture range of the cab + front body
BED_Z, BED_Y = (-10.2, -3.85), (1.95, 4.62)
WIN_Z, WIN_Y = (-3.6, 4.05), (4.55, 6.75)

def _arch_cut(d, W, H, z0, z1, y0, y1, zw, R):
    """dark wheel-arch shape on a side texture (u = z from z0 at left, v = y)."""
    cx = (zw - z0) / (z1 - z0) * W; cy = H - (PK['R'] - y0) / (y1 - y0) * H; rr = R / (z1 - z0) * W; ry = R / (y1 - y0) * H
    d.ellipse([cx - rr, cy - ry, cx + rr, cy + ry], fill=(6, 6, 7))

def gloss(im, ya, yb, amp):
    """soft horizontal reflection band between rows ya and yb (glossy paint), strongest in the middle."""
    a = np.array(im).astype(float); H = a.shape[0]; y = np.arange(H)[:, None, None]
    lo, hi = min(ya, yb), max(ya, yb); c = (lo + hi) / 2; w = max(1.0, (hi - lo) / 2)
    a += amp * np.exp(-((y - c) / w) ** 2)
    im.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))

def pickup_texture():
    img = Image.new('RGB', (1024, 1024), PK_BODY)
    def body_side(im):                                                     # z from BODY_Z[0] (left) to BODY_Z[1] (right)
        d = ImageDraw.Draw(im); W, H = im.size; d.rectangle([0, 0, W, H], fill=PK_BODY)
        Z = lambda z: (z - BODY_Z[0]) / (BODY_Z[1] - BODY_Z[0]) * W; Y = lambda y: H - (y - BODY_Y[0]) / (BODY_Y[1] - BODY_Y[0]) * H
        _arch_cut(d, W, H, *BODY_Z, *BODY_Y, PK['wf'], 2.0)
        for z in (-3.45, 0.45, 4.0): d.line([Z(z), Y(4.6), Z(z), Y(2.05)], fill=(52, 52, 56), width=3)       # door gaps
        d.line([Z(-3.45), Y(2.05), Z(4.0), Y(2.05)], fill=(52, 52, 56), width=3)
        for z in (-0.4, 3.4): d.rounded_rectangle([Z(z), Y(4.35), Z(z + 0.55), Y(4.22)], radius=3, fill=(58, 58, 62))  # handles
        d.line([0, Y(3.95), W, Y(3.95)], fill=(38, 38, 42), width=2)                                          # body crease
        gloss(im, Y(4.75), Y(4.05), 18); gloss(im, Y(3.6), Y(3.1), 8)                                        # glossy black paint reflections
        d.rectangle([0, Y(2.05), W, H], fill=(14, 14, 15))                                                     # rocker (black plastic)
        _arch_cut(d, W, H, *BODY_Z, *BODY_Y, PK['wf'], 2.0)
    img.paste(panel((BODY_Z[1] - BODY_Z[0], BODY_Y[1] - BODY_Y[0]), 1008, body_side).resize((1008, 240), Image.LANCZOS), (8, 8))
    def bed_side(im):
        d = ImageDraw.Draw(im); W, H = im.size; d.rectangle([0, 0, W, H], fill=PK_BODY)
        d.line([0, H - (3.95 - BED_Y[0]) / (BED_Y[1] - BED_Y[0]) * H, W, H - (3.95 - BED_Y[0]) / (BED_Y[1] - BED_Y[0]) * H], fill=(38, 38, 42), width=2)
        gloss(im, H * 0.05, H * 0.30, 18); gloss(im, H * 0.42, H * 0.55, 8)
        _arch_cut(d, W, H, *BED_Z, *BED_Y, PK['wr'], 2.0)
    img.paste(panel((BED_Z[1] - BED_Z[0], BED_Y[1] - BED_Y[0]), 504, bed_side).resize((504, 160), Image.LANCZOS), (8, 264))
    def windows(im):                                                       # side glass strip, z from WIN_Z[0] (left)
        d = ImageDraw.Draw(im); W, H = im.size; d.rectangle([0, 0, W, H], fill=(10, 10, 11))
        Z = lambda z: (z - WIN_Z[0]) / (WIN_Z[1] - WIN_Z[0]) * W; Y = lambda y: H - (y - WIN_Y[0]) / (WIN_Y[1] - WIN_Y[0]) * H
        for za, zb in ((-3.1, 0.2), (0.7, 3.5)):
            d.rounded_rectangle([Z(za), Y(6.35), Z(zb), Y(4.85)], radius=10, fill=(30, 38, 48))
            d.polygon([(Z(za), Y(6.0)), (Z(za + 0.9), Y(6.35)), (Z(za + 1.4), Y(6.35)), (Z(za), Y(5.7))], fill=(55, 64, 76))   # reflection
    img.paste(panel((WIN_Z[1] - WIN_Z[0], WIN_Y[1] - WIN_Y[0]), 496, windows).resize((496, 160), Image.LANCZOS), (520, 264))
    def grille(im):                                                        # front face 6.1 x 2.4 ft
        d = ImageDraw.Draw(im); W, H = im.size; d.rectangle([0, 0, W, H], fill=(8, 8, 9))
        d.rounded_rectangle([W * 0.18, H * 0.30, W * 0.82, H * 0.95], radius=14, fill=(16, 16, 18))
        for y in np.arange(H * 0.36, H * 0.92, H * 0.075):                 # honeycomb-ish mesh
            for x in np.arange(W * 0.2 + (int(y) // 7 % 2) * 7, W * 0.8, 14): d.rectangle([x, y, x + 8, y + 4], fill=(34, 34, 37))
        d.rectangle([W * 0.04, H * 0.52, W * 0.96, H * 0.64], fill=PK_BODY)                       # body-colour bar
        bowtie(im, (W * 0.43, H * 0.44, W * 0.57, H * 0.72))
        for x0 in (W * 0.02, W * 0.79):                                     # LED headlights + light bar
            d.rounded_rectangle([x0, H * 0.10, x0 + W * 0.19, H * 0.30], radius=6, fill=(28, 28, 30))
            d.rectangle([x0 + 4, H * 0.12, x0 + W * 0.19 - 4, H * 0.17], fill=(235, 240, 250))
            d.rectangle([x0 + W * 0.06, H * 0.20, x0 + W * 0.16, H * 0.27], fill=(200, 210, 225))
    img.paste(panel((6.1, 2.4), 512, grille).resize((496, 196), Image.LANCZOS), (520, 520))
    def tail(im):                                                          # tailgate 6.6 x 2.65 ft
        d = ImageDraw.Draw(im); W, H = im.size; d.rectangle([0, 0, W, H], fill=PK_BODY)
        d.line([0, H * 0.22, W, H * 0.22], fill=(40, 40, 44), width=3)
        bowtie(im, (W * 0.445, H * 0.30, W * 0.555, H * 0.48))
        d.rounded_rectangle([W * 0.42, H * 0.58, W * 0.58, H * 0.66], radius=4, fill=(14, 14, 15))
    img.paste(panel((6.6, 2.65), 512, tail).resize((496, 160), Image.LANCZOS), (520, 728))
    def shield(im):                                                        # windshield / rear window: tinted glass, soft reflection
        from PIL import ImageFilter
        W, H = im.size; a = np.zeros((H, W, 3))
        t = np.linspace(0, 1, H)[:, None]
        for k, (c0, c1) in enumerate(((62, 26), (72, 30), (86, 36))): a[..., k] = c0 + (c1 - c0) * t
        refl = Image.new('L', (W, H), 0); ImageDraw.Draw(refl).polygon([(W * 0.18, H), (W * 0.46, 0), (W * 0.60, 0), (W * 0.32, H)], fill=60)
        r = np.array(refl.filter(ImageFilter.GaussianBlur(W * 0.05))).astype(float)[..., None]
        a = np.clip(a + r, 0, 255); b = max(2, int(H * 0.05))
        a[:b] = a[-b:] = 10; a[:, :b] = a[:, -b:] = 10                        # thin black frit all around
        im.paste(Image.fromarray(a.astype(np.uint8)))
    img.paste(panel((6.2, 2.2), 232, shield, ao=0).resize((232, 150), Image.LANCZOS), (280, 440))
    def paint_top(im):                                                     # hood / roof: glossy black paint, soft reflection
        d = ImageDraw.Draw(im); W, H = im.size; d.rectangle([0, 0, W, H], fill=PK_BODY)
        a = np.array(im).astype(float); x = np.linspace(-1, 1, W)[None, :, None]; y = np.linspace(0, 1, H)[:, None, None]
        a += 16 * np.exp(-(x / 0.35) ** 2) * (0.6 + 0.4 * np.cos(y * 6.0)) + 5 * np.exp(-((x - 0.7) / 0.12) ** 2)
        im.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
    img.paste(panel((6.6, 14.0), 232, paint_top, ao=0).resize((232, 170), Image.LANCZOS), (280, 600))
    rim_face(img, (8, 520, 264, 776), metal=(36, 36, 39), dark=(12, 12, 13), spokes=6)
    tread_strip(img, (8, 790, 512, 860), blocks=30)
    pal = palette(img, ['body', 'chrome', 'dark', 'tyre', 'glass', 'white', 'red', 'amber', 'bed', 'hook', 'plastic'],
                  [PK_BODY, (205, 208, 214), (20, 20, 22), (28, 28, 28), (24, 30, 38), (245, 245, 245), (190, 15, 20),
                   (240, 150, 20), (16, 16, 17), (220, 25, 30), (14, 14, 15)])
    pal.update(bodyside=(8, 8, 1016, 248), bedside=('r', (8, 264, 512, 424)), win=(520, 264, 1016, 424), rim=(8, 520, 264, 776),
               tread=(8, 790, 512, 860), grille=(520, 520, 1016, 716), tail=('r', (520, 728, 1016, 888)),
               shield=(280, 440, 512, 590), ptop=(280, 600, 512, 770))
    return img, pal

def _sec(z, y0, y1, wb, wt, e, n=32):
    """rounded section (super-ellipse of exponent e), half width wb at the bottom, wt at the top."""
    pts = []
    for k in range(n):
        t = 2 * np.pi * k / n; c, s = np.cos(t), np.sin(t)
        px = np.sign(c) * abs(c) ** (2 / e); py = np.sign(s) * abs(s) ** (2 / e)
        w = wb + (wt - wb) * (py + 1) / 2
        pts.append(np.array([px * w, (y0 + y1) / 2 + py * (y1 - y0) / 2, z]))
    return pts

def _loft(m, secs, uvf, cap_first=None, cap_last=None):
    """connect consecutive sections with quads; uvf(point, normal) -> uv. Caps: uv function or None."""
    S = [_sec(*s) for s in secs]; n = len(S[0])
    for a, b in zip(S[:-1], S[1:]):
        for k in range(n):
            j = (k + 1) % n; P = [a[k], a[j], b[j], b[k]]
            N = np.cross(P[1] - P[0], P[3] - P[0])
            if np.linalg.norm(N) < 1e-9: N = np.cross(P[2] - P[1], P[3] - P[1])
            if np.linalg.norm(N) < 1e-9: continue
            N = N / np.linalg.norm(N); ctr = np.mean(P, 0); ax = np.array([0, np.mean([p[1] for p in a + b]), ctr[2]])
            if np.dot(N, ctr - ax) < 0: N = -N
            m.tri_fan(P, N, [uvf(p, N) for p in P])
    for sec, f, sg in ((S[0], cap_first, -1), (S[-1], cap_last, 1)):
        if f is None: continue
        dz = sg * np.sign(S[-1][0][2] - S[0][0][2]); N = np.array([0, 0, dz])
        m.tri_fan(sec, N, [f(p) for p in sec])

def _planar(m, rect, z0, z1, y0, y1, side):
    """side texture lookup: u along z (z0 = left of the image) on both sides (no text there, so no mirroring needed)."""
    px0, py0, px1, py1 = rect
    def g(p):
        s = np.clip((p[2] - z0) / (z1 - z0), 0, 1); t = np.clip((p[1] - y0) / (y1 - y0), 0, 1)
        return m.uv_px(px0 + s * (px1 - px0), py1 - t * (py1 - py0))
    return g

def pickup_model(pal):
    """lifted crew-cab long box, front = +z (z from -10.3 to +10.0), 6.9 ft wide, 6.75 ft tall."""
    m = Mesh(1024, 1024); P = pal; col = lambda nm: m.uv_px(*P[nm][1])
    side_r = _planar(m, P['bodyside'], *BODY_Z, *BODY_Y, 1); side_l = _planar(m, P['bodyside'], *BODY_Z, *BODY_Y, -1)
    tx0, ty0, tx1, ty1 = P['ptop']
    top_uv = lambda p: m.uv_px(tx0 + (p[0] + 3.35) / 6.7 * (tx1 - tx0), ty0 + (10.0 - p[2]) / 13.8 * (ty1 - ty0))   # glossy paint, same on hood + roof
    def body_uv(p, N):
        if N[0] > 0.45: return side_r(p)
        if N[0] < -0.45: return side_l(p)
        if N[1] > 0.45: return top_uv(p)
        return col('body') if p[1] > 2.3 else col('plastic')
    gx0, gy0, gx1, gy1 = P['grille']
    grille_uv = lambda p: m.uv_px(gx0 + (p[0] + 3.05) / 6.1 * (gx1 - gx0), gy1 - (p[1] - 1.95) / 2.4 * (gy1 - gy0))
    body = [(10.0, 1.95, 4.35, 3.05, 2.95, 6), (9.8, 1.85, 4.70, 3.22, 3.12, 6), (8.6, 1.85, 4.86, 3.30, 3.20, 6),
            (5.0, 1.85, 4.95, 3.32, 3.22, 6), (4.15, 1.85, 4.98, 3.32, 3.22, 6), (4.05, 1.85, 4.62, 3.32, 3.24, 6),
            (-3.55, 1.85, 4.62, 3.32, 3.24, 6), (-3.70, 1.95, 4.45, 3.22, 3.12, 6)]
    _loft(m, body, body_uv, cap_first=grille_uv, cap_last=lambda p: col('dark'))
    win_r = _planar(m, P['win'], *WIN_Z, *WIN_Y, 1); win_l = _planar(m, P['win'], *WIN_Z, *WIN_Y, -1)
    sx0, sy0, sx1, sy1 = P['shield']
    def shield_uv(p, N):                                                   # windshield (+z) / rear window (-z), readable gradient + reflections
        u = (p[0] + 3.1) / 6.2; u = u if N[2] < 0 else 1 - u
        return m.uv_px(sx0 + u * (sx1 - sx0), sy1 - (p[1] - 4.55) / 2.2 * (sy1 - sy0))
    def cab_uv(p, N):
        if abs(N[2]) > 0.2 and N[1] < 0.9 and abs(N[0]) < 0.6: return col('plastic')    # glass frame (the glass is a separate pane)
        if N[1] > 0.75: return top_uv(p)
        if N[0] > 0.5: return win_r(p)
        if N[0] < -0.5: return win_l(p)
        if abs(N[2]) > 0.3: return shield_uv(p, N)
        return col('glass')
    cab = [(4.10, 4.55, 4.70, 3.18, 3.10, 4), (3.05, 4.55, 6.25, 3.12, 2.80, 4), (2.05, 4.55, 6.74, 3.08, 2.72, 5),
           (-2.95, 4.55, 6.75, 3.08, 2.72, 5), (-3.45, 4.55, 6.62, 3.10, 2.78, 5), (-3.62, 4.55, 4.65, 3.12, 3.06, 5)]
    _loft(m, cab, cab_uv)
    def pane(y0, y1, z_of_y, hw0, hw1, out):
        """flat glass pane laid on the cab slope (trapezoid, half widths hw0 at y0 / hw1 at y1), pushed `out` along its normal."""
        A, B = np.array([0, y0, z_of_y(y0)]), np.array([0, y1, z_of_y(y1)])
        up = (B - A) / np.linalg.norm(B - A); N = np.cross(np.array([1.0, 0, 0]), up)
        if np.sign(N[2]) != np.sign(out): N = -N
        pts = [A + np.array([-hw0, 0, 0]), A + np.array([hw0, 0, 0]), B + np.array([hw1, 0, 0]), B + np.array([-hw1, 0, 0])]
        pts = [q + N * 0.03 for q in pts]
        flip = out > 0                                                       # viewer's right is -x on the front, +x at the back
        uv = [m.uv_px(sx0 if not flip else sx1, sy1), m.uv_px(sx1 if not flip else sx0, sy1),
              m.uv_px(sx1 if not flip else sx0, sy0), m.uv_px(sx0 if not flip else sx1, sy0)]
        m.tri_fan(pts, N, uv)
    pane(4.78, 6.12, lambda y: 4.10 - (y - 4.70) / 1.55 * 1.05, 2.78, 2.30, 1)          # windshield, inside the frame
    pane(5.15, 6.20, lambda y: -3.62 + (y - 4.65) / 1.97 * 0.17, 1.85, 1.60, -1)         # rear window, smaller
    # long, hollow bed: floor, rounded side walls, bulkhead, tailgate
    m.box(-2.86, 2.86, 2.30, 2.55, PK['zr'] + 0.2, PK['zbed'], {'*': P['bed']})
    for s in (-1, 1):
        x0, x1 = sorted((s * 2.86, s * 3.30))
        bs = ('r', (512, 264, 8, 424)) if s > 0 else P['bedside']                   # +x face runs right-to-left: mirrored rect
        m.rbox(x0, x1, BED_Y[0], BED_Y[1], *BED_Z, 0.18, 2, {('+x' if s > 0 else '-x'): bs, ('-x' if s > 0 else '+x'): P['bed'],
               '+z': P['body'], '-z': P['body'], '-y': P['plastic']}, P['body'])
    m.rbox(-2.86, 2.86, 2.55, BED_Y[1], PK['zbed'], PK['zbed'] + 0.15, 0.12, 0, {'*': P['body'], '-z': P['bed']}, P['body'])
    m.rbox(-3.20, 3.20, 2.33, 2.55, PK['zr'] - 2.62, PK['zr'] + 0.05, 0.1, 0, {'+y': P['bed'], '-y': P['tail'], '*': P['body']}, P['body'])   # tailgate open (lowered flat)
    for s in (-1, 1): m.tube((s * 3.0, BED_Y[1] - 0.3, PK['zr'] + 0.1), (s * 3.0, 2.5, PK['zr'] - 2.4), 0.025, P['dark'])                   # support cables
    m.box(-2.86, 2.86, BED_Y[0], 2.30, PK['zr'] + 0.2, PK['zbed'], {'*': P['plastic']})                   # under the floor
    for s in (-1, 1):                                                                                   # wheel wells inside the bed
        x0, x1 = sorted((s * 2.86, s * 1.95))
        m.rbox(x0, x1, 2.4, 3.45, PK['wr'] - 2.0, PK['wr'] + 2.0, 0.35, 0, {'*': P['bed']}, P['bed'])
    # bumpers, skid plate, tow hooks, lights
    m.rbox(-3.20, 3.20, 1.30, 2.20, 9.75, 10.55, 0.3, 0, {'*': P['plastic']}, P['plastic'])
    m.rbox(-1.9, 1.9, 1.05, 1.40, 8.6, 10.3, 0.12, 0, {'*': P['plastic']}, P['plastic'])
    for s in (-1, 1): m.rbox(s * 2.25 - 0.2, s * 2.25 + 0.2, 1.75, 2.15, 10.45, 10.75, 0.08, 1, {'*': P['hook']}, P['hook'])
    m.rbox(-3.25, 3.25, 1.55, 2.20, PK['zr'] - 0.45, PK['zr'] + 0.05, 0.2, 0, {'*': P['plastic']}, P['plastic'])
    for s in (-1, 1):
        m.rbox(s * 3.0 - 0.28, s * 3.0 + 0.28, 3.05, 4.45, PK['zr'] - 0.04, PK['zr'] + 0.02, 0.08, 2, {'*': P['red']}, P['red'])   # tail lights
        m.rbox(min(s * 3.12, s * 3.85), max(s * 3.12, s * 3.85), 5.0, 5.75, 3.25, 3.75, 0.12, 2, {'*': P['plastic']}, P['plastic'])  # mirrors
        m.tube((s * 3.48, 1.72, -3.4), (s * 3.48, 1.72, 3.7), 0.11, P['plastic'])                                                 # side steps
        for z in (-2.4, 0.4, 2.9): m.tube((s * 3.2, 1.95, z), (s * 3.48, 1.72, z), 0.06, P['plastic'])
        for zw in (PK['wf'], PK['wr']):
            m.wheel((s * 2.92, PK['R'], zw), 0, PK['R'], 1.1, P['tread'], P['rim'], P['tyre'])
            arc = [(zw + 2.05 * np.cos(t), PK['R'] + 2.05 * np.sin(t)) for t in np.radians(np.linspace(8, 172, 12))]
            for (za, ya), (zb, yb) in zip(arc[:-1], arc[1:]):                                       # fender flares
                m.tube((s * 3.36, ya, za), (s * 3.36, yb, zb), 0.16, P['plastic'])
    return m


# ------------------------------------------------------------------ cut-out signs (plate following the logo outline, like real sponsor signs)
_CUT = {}       # name -> (PIL crop of the texture rect, rect) filled by the texture functions, used by the model functions

def _ear_clip(poly):
    """triangulate a simple polygon (list of (x, y)), counter-clockwise or not; returns index triples."""
    P = [np.array(p, float) for p in poly]; n = len(P)
    area = sum(P[i][0] * P[(i + 1) % n][1] - P[(i + 1) % n][0] * P[i][1] for i in range(n)) / 2
    idx = list(range(n)) if area > 0 else list(range(n))[::-1]; tris = []
    def inside(p, a, b, c):
        d1 = (p[0] - b[0]) * (a[1] - b[1]) - (a[0] - b[0]) * (p[1] - b[1]); d2 = (p[0] - c[0]) * (b[1] - c[1]) - (b[0] - c[0]) * (p[1] - c[1])
        d3 = (p[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (p[1] - a[1])
        return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))
    guard = 0
    while len(idx) > 3 and guard < 20000:
        guard += 1; m_ = len(idx)
        for k in range(m_):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % m_]; a, b, c = P[i0], P[i1], P[i2]
            if (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) <= 1e-9: continue      # reflex
            if any(inside(P[j], a, b, c) for j in idx if j not in (i0, i1, i2)): continue
            tris.append((i0, i1, i2)); idx.pop(k); break
        else: break
    if len(idx) == 3: tris.append(tuple(idx))
    return tris

def sign_mask(crop, margin=0.06, join=False, base=0.0):
    """plate mask (bool, pixel grid) of the logo drawn on black in `crop`: grown by `margin` x height, pieces joined by a
    centre strip (join), solid base bar under the lettering (base x H), holes filled."""
    from scipy import ndimage as ndi_
    a = np.array(crop.convert('L')).astype(float) > 60
    r = max(1, int(margin * a.shape[0]))
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]; disk = xx ** 2 + yy ** 2 <= r * r
    mk = ndi_.binary_dilation(a, structure=disk)
    rows, cols = np.nonzero(mk); top, bot = rows.min(), rows.max(); c0, c1 = cols.min(), cols.max()
    if join:
        sw = max(2, int(0.06 * mk.shape[1])); cx = mk.shape[1] // 2; mk[top:bot + 1, cx - sw:cx + sw] = True
    if base:
        bh = max(2, int(base * mk.shape[0])); mk[max(0, bot - bh):bot + 1, c0:c1 + 1] = True
    return ndi_.binary_fill_holes(mk)

def cut_outline(mk, tol=1.2, min_area=0.01):
    """outer contours (row, col) of a plate mask."""
    from skimage import measure
    p = np.pad(mk, 2); out = []
    for c in measure.find_contours(p.astype(float), 0.5):
        c = measure.approximate_polygon(c, tol)[:-1] - 2
        if len(c) < 3: continue
        ar = abs(sum(c[i][1] * c[(i + 1) % len(c)][0] - c[(i + 1) % len(c)][1] * c[i][0] for i in range(len(c)))) / 2
        if ar > min_area * mk.size: out.append(c)
    return out

def cutout(m, name, xc, yb, width, z0, thick, black, facing=-1, join=True, base=0.07):
    """one plate following the logo outline, printed on the face looking `facing` (-1 = -z, +1 = +z) and readable from
    there; other face and edges black. xc = centre, yb = bottom of the plate (it sits on its support), z0..z0+thick."""
    crop, (px0, py0, px1, py1) = _CUT[name]; W, H = crop.size; hgt = H * width / W
    bl = m.uv_px(*black[1]); mk = sign_mask(crop, join=join, base=base); outs = cut_outline(mk)
    rmax = max(c[:, 0].max() for c in outs); y0 = yb - (1 - rmax / H) * hgt
    for c in outs:
        # the viewer's right is -x for a face looking -z, +x for a face looking +z
        pts = [(xc + facing * (col / W - 0.5) * width, y0 + (1 - row / H) * hgt) for row, col in c]
        uvs = [m.uv_px(px0 + col / W * (px1 - px0), py0 + row / H * (py1 - py0)) for row, col in c]
        tris = _ear_clip(pts); zf, zb = z0, z0 + thick
        for i, j, l in tris:
            for zz, nz in ((zf, -1.0), (zb, 1.0)):
                tri = [np.array([pts[q][0], pts[q][1], zz]) for q in (i, j, l)]
                m.tri_fan(tri, np.array([0, 0, nz]), [uvs[q] for q in (i, j, l)] if nz == facing else [bl] * 3)
        n = len(pts); area = sum(pts[q][0] * pts[(q + 1) % n][1] - pts[(q + 1) % n][0] * pts[q][1] for q in range(n)) / 2
        for q in range(n):
            a, b = pts[q], pts[(q + 1) % n]
            e = np.array([b[0] - a[0], b[1] - a[1]]); N = np.array([e[1], -e[0], 0.0]) * (1 if area > 0 else -1)
            if np.linalg.norm(N) < 1e-9: continue
            N /= np.linalg.norm(N)
            m.quad([np.array([a[0], a[1], zf]), np.array([b[0], b[1], zf]), np.array([b[0], b[1], zb]), np.array([a[0], a[1], zb])], N, lambda p: bl)
    return mk, y0, hgt

def sign_pair(m, name, xc, yb, width, gap, thick, black, metal, step=1.6):
    """double-sided sign = two separate cut plates (front readable from -z, back readable from +z) `gap` ft apart,
    tied together by metal rods (+ diagonal braces) where both plates overlap."""
    mk, y0, hgt = cutout(m, name, xc, yb, width, -gap / 2 - thick, thick, black, facing=-1)
    cutout(m, name, xc, yb, width, gap / 2, thick, black, facing=1)
    H, W = mk.shape; both = mk & mk[:, ::-1]                       # front col c and back col W-1-c sit at the same x
    from scipy import ndimage as ndi_
    both = ndi_.binary_erosion(both, iterations=max(1, int(0.05 * H)))
    pts = []
    for y in np.arange(y0 + 0.5, y0 + hgt, step):
        row = int((1 - (y - y0) / hgt) * H)
        if not (0 <= row < H): continue
        line = []
        for x in np.arange(xc - width / 2 + step / 2, xc + width / 2, step):
            col = int((0.5 - (x - xc) / width) * W)
            if 0 <= col < W and both[row, col]: line.append((x, y))
        pts.append(line)
    z_a, z_b = -gap / 2, gap / 2
    for line in pts:
        for k, (x, y) in enumerate(line):
            m.tube((x, y, z_a), (x, y, z_b), 0.05, metal)                     # rods across the gap
            if k and abs(line[k - 1][0] - x) < step * 1.5:                     # braces between neighbours
                xa, ya = line[k - 1]
                m.tube((xa, ya, z_a), (x, y, z_b), 0.035, metal) if k % 2 else m.tube((xa, ya, z_b), (x, y, z_a), 0.035, metal)
    return y0, hgt


# ------------------------------------------------------------------ finish arch v3 (épurée : volumes arrondis, peu de logos, proportions)
# Socles inclinés lisses, poteaux épais à arêtes arrondies (étoile au milieu, petit RBT en haut, faces avant/arrière seulement),
# poutre arrondie « FINISH » + icône U de chaque côté, enseigne pleine (pas de treillis) : USLAND puis icône U.
ARCH_CLEAR = 30.0      # beam bottom above the statue base
AP = 2.1               # pillar half size (4.2 ft square)
BEAM = (30.0, 37.5)    # beam y range
TORCH = 2.85          # v13b: flame torch on the beam above each pillar (base 0.3 + stick + cup), flames start at its top
BLK, SEAM, GREY = (14, 15, 17), (44, 46, 50), (150, 154, 160)

def _rot(im, draw, box, angle=90):
    """draw(tmp, (0, 0, w, h)) on a black canvas, rotate it and blend it centred in box (alpha = brightness)."""
    x0, y0, x1, y1 = box; w, h = int(y1 - y0), int(x1 - x0)
    tmp = Image.new('RGB', (w, h), (0, 0, 0)); draw(tmp, (0, 0, w, h)); tmp = tmp.rotate(angle, expand=True)
    c = np.array(tmp).astype(float); A = np.clip(c.max(2) / 140.0, 0, 1)
    blend(im, np.dstack([c, A]), int((x0 + x1 - c.shape[1]) / 2), int((y0 + y1 - c.shape[0]) / 2))

def finish_word(im, box):
    """FINISH: white letters, blue outline (as the reference), centred."""
    from PIL import ImageFilter
    x0, y0, x1, y1 = box; t = text_rgba('FINISH', int((y1 - y0) * 0.78), WHITE, italic=0.0, bold=0.05)
    if t.shape[1] > x1 - x0:
        k = (x1 - x0) / t.shape[1]; a_ = Image.fromarray((t[..., 3] * 255).astype(np.uint8)).resize((int(t.shape[1] * k), int(t.shape[0] * k)), Image.LANCZOS)
        t = np.dstack([np.ones((a_.size[1], a_.size[0], 3)) * 250, np.array(a_) / 255.0])
    a = t[..., 3]; A8 = Image.fromarray((a * 255).astype(np.uint8))
    o = np.array(A8.filter(ImageFilter.MaxFilter(11))) / 255.0; o2 = np.array(A8.filter(ImageFilter.MaxFilter(17))) / 255.0
    ox, oy = int((x0 + x1 - t.shape[1]) / 2), int((y0 + y1 - t.shape[0]) / 2)
    for col, al in ((WHITE, o2), ((28, 78, 200), o), (WHITE, a)):
        blend(im, np.dstack([np.ones(a.shape + (3,)) * np.array(col, float), al]), ox, oy)

def arch_texture(pcol=None):
    """pcol: colour of the whole structure (beam, bases, pillars, sign backs). Default black; SX2 trial: USLAND navy."""
    pcol = pcol or BLK
    img = Image.new('RGB', (2048, 2048), pcol)
    L = 2 * (ARCH_X + AP)
    def beam(im):                                                            # beam front/back: FINISH + U icons, nothing else
        d = ImageDraw.Draw(im); W, H = im.size; d.rectangle([0, 0, W, H], fill=pcol)
        d.rectangle([0, int(H * 0.06), W, int(H * 0.06) + 3], fill=SEAM); d.rectangle([0, int(H * 0.94) - 3, W, int(H * 0.94)], fill=SEAM)
        finish_word(im, (W * 0.30, H * 0.16, W * 0.70, H * 0.84))
        for cx in (W * 0.215, W * 0.785): logo(im, 'ICON', (cx - H * 0.30, H * 0.22, cx + H * 0.30, H * 0.78))
    img.paste(panel((L, BEAM[1] - BEAM[0]), 2032, beam).resize((2032, 290), Image.LANCZOS), (8, 8))
    def pillar(im):                                                          # pillar front/back 4.2 x 23.5: RBT top, star middle
        d = ImageDraw.Draw(im); W, H = im.size; d.rectangle([0, 0, W, H], fill=pcol)
        for y in (H / 3, 2 * H / 3): d.rectangle([0, y - 2, W, y + 2], fill=SEAM)
        logo(im, 'RBT', (W * 0.06, H / 6 - W * 0.3, W * 0.94, H / 6 + W * 0.3), on='dark', ink=GREY)
        logo(im, 'STAR', (W * 0.25, H / 2 - W * 0.25, W * 0.75, H / 2 + W * 0.25), ink=GREY)
    img.paste(panel((2 * AP, BEAM[0] - 6.0), 256, pillar).resize((240, 1344), Image.LANCZOS), (8, 320))
    def plain(im):                                                           # plain pillar side with the two seams
        d = ImageDraw.Draw(im); W, H = im.size; d.rectangle([0, 0, W, H], fill=pcol)
        for y in (H / 3, 2 * H / 3): d.rectangle([0, y - 2, W, y + 2], fill=SEAM)
    img.paste(panel((2 * AP, BEAM[0] - 6.0), 256, plain).resize((240, 1344), Image.LANCZOS), (264, 320))
    def base(im):                                                            # base inner face (16 x 6): USLAND only
        d = ImageDraw.Draw(im); W, H = im.size; d.rectangle([0, 0, W, H], fill=pcol)
        paste_logo(im, (W * 0.30, H * 0.40, W * 0.70, H * 0.62), GREY, accent=GREY)
    img.paste(panel((16, 6), 1016, base).resize((1016, 380), Image.LANCZOS), (520, 320))
    def sign(im):                                                            # sign 22 x 13: U icon over USLAND (one plate)
        d = ImageDraw.Draw(im); W, H = im.size; d.rectangle([0, 0, W, H], fill=pcol)
        logo(im, 'ICON', (W * 0.31, H * 0.04, W * 0.69, H * 0.52))
        paste_logo(im, (W * 0.04, H * 0.60, W * 0.96, H * 0.90), WHITE)
    sp = panel((22, 13), 1016, sign).resize((1016, 600), Image.LANCZOS); img.paste(sp, (520, 720)); _CUT['arch_sign'] = (sp, (520, 720, 1536, 1320))
    pal = palette(img, ['black', 'seam', 'metal', 'pcol'], [pcol, SEAM, (120, 123, 128), pcol])
    pal.update(beam=('r', (8, 8, 2040, 298)), pillar=('r', (8, 320, 248, 1664)), plain=('r', (264, 320, 504, 1664)),
               base=('r', (520, 320, 1536, 700)))
    return img, pal

def _prism_x(m, poly, x0, x1, side_src, cap_src):
    """polygon in (z, y), extruded along x from x0 to x1: edges get side_src (u along x, v up the edge), caps cap_src
    (a uv source, or a dict {-1: src, +1: src} for the -x / +x caps)."""
    P = [np.array(p, float) for p in poly]; n = len(P); ctr = np.mean(P, 0)
    zs, ys = [p[0] for p in P], [p[1] for p in P]
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]; e = b - a
        nz, ny = e[1], -e[0]
        if nz * ((a[0] + b[0]) / 2 - ctr[0]) + ny * ((a[1] + b[1]) / 2 - ctr[1]) < 0: nz, ny = -nz, -ny
        N = np.array([0.0, ny, nz]); N /= np.linalg.norm(N)
        pts = [np.array([x0, a[1], a[0]]), np.array([x1, a[1], a[0]]), np.array([x1, b[1], b[0]]), np.array([x0, b[1], b[0]])]
        src = side_src(i) if callable(side_src) else side_src
        if src[0] == 'c': m.quad(pts, N, lambda p, s_=src: m.uv_px(*s_[1]))
        else:
            px0, py0, px1, py1 = src[1]; L = np.linalg.norm(e); lo_ = a if a[1] <= b[1] else b
            if N[2] < 0: px0, px1 = px1, px0                                 # face looking -z: viewer's right is -x
            g = lambda p, lo_=lo_, L=L, px0=px0, px1=px1: m.uv_px(px0 + (p[0] - x0) / (x1 - x0) * (px1 - px0),
                                                py1 - np.linalg.norm(np.array([p[2], p[1]]) - lo_) / L * (py1 - py0))
            m.quad(pts, N, g)
    for x, sg in ((x0, -1), (x1, 1)):
        src = cap_src[sg] if isinstance(cap_src, dict) else cap_src
        if src[0] == 'c': g = lambda p, s_=src: m.uv_px(*s_[1])
        else:
            px0, py0, px1, py1 = src[1]
            if sg < 0: px0, px1 = px1, px0                                    # viewer's right on the -x cap is +z
            g = lambda p, px0=px0, px1=px1, py0=py0, py1=py1: m.uv_px(px0 + (max(zs) - p[2]) / (max(zs) - min(zs)) * (px1 - px0),
                                                                     py1 - (p[1] - min(ys)) / (max(ys) - min(ys)) * (py1 - py0))
        pts = [np.array([x, p[1], p[0]]) for p in P]
        m.tri_fan(pts, np.array([sg, 0, 0.0]), [g(p) for p in pts])

def _bevel(poly, r=0.35, seg=3):
    """round every corner of a convex polygon (z, y) with radius r."""
    P = [np.array(p, float) for p in poly]; n = len(P); out = []
    for i in range(n):
        a, b, c = P[i - 1], P[i], P[(i + 1) % n]
        u, v = (a - b) / np.linalg.norm(a - b), (c - b) / np.linalg.norm(c - b)
        p0, p1 = b + u * r, b + v * r
        for t in np.linspace(0, 1, seg + 2):                                  # quadratic Bézier through the corner
            out.append(tuple((1 - t) ** 2 * p0 + 2 * (1 - t) * t * b + t ** 2 * p1))
    return out

def arch_model(pal):
    m = Mesh(2048, 2048); P = pal; X = ARCH_X
    base = _bevel([(-8.0, -2.0), (8.0, -2.0), (8.0, 0.6), (AP + 0.4, 6.0), (-AP - 0.4, 6.0), (-8.0, 0.6)], 0.45)
    for s in (-1, 1):
        cx = s * X; inner = -s                                                # the cap facing the lane gets the logo
        _prism_x(m, base, cx - AP - 0.4, cx + AP + 0.4, P['black'], {inner: P['base'], -inner: P['black']})
        m.rbox(cx - AP, cx + AP, 5.9, BEAM[0] + 0.1, -AP, AP, 0.35, 1,
               {'-z': P['pillar'], '+z': P['pillar'], '+x': P['plain'], '-x': P['plain'], '+y': P['pcol'], '-y': P['pcol']}, P['pcol'])
    m.rbox(-X - AP - 0.6, X + AP + 0.6, BEAM[0], BEAM[1], -2.4, 2.4, 0.5, 0,
           {'-z': P['beam'], '+z': P['beam'], '*': P['black']}, P['black'])
    sign_pair(m, 'arch_sign', 0.0, BEAM[1] - 0.05, 22.0, 1.6, 0.3, P['black'], P['metal'])   # two cut plates (front / back) tied by rods, on the beam
    for s in (-1, 1):                                                         # v13b: flame torches on the beam, above each pillar
        cx, y = s * X, BEAM[1]                                                # (the finish flames of pyro_chalk.py come out of them)
        m.rbox(cx - 0.45, cx + 0.45, y, y + 0.3, -0.45, 0.45, 0.15, 1, {'*': P['black']}, P['black'])                 # base plate
        m.rbox(cx - 0.22, cx + 0.22, y + 0.3, y + TORCH - 0.35, -0.22, 0.22, 0.2, 1, {'*': P['metal']}, P['metal'])   # stick
        m.rbox(cx - 0.36, cx + 0.36, y + TORCH - 0.35, y + TORCH, -0.36, 0.36, 0.3, 1, {'*': P['black']}, P['black'])  # nozzle cup
    for i, v in enumerate(m.V): m.V[i] = (v[0] + ARCH_X,) + tuple(v[1:])            # v12b: origin = foot of the -x pillar (flat ground)
    return m


# ------------------------------------------------------------------ start gantry (reference image: truss over the gate row, flags)
# Treillis au-dessus de la grille, posé sur 2 socles en trapèze, bâches noires (USLAND / RBT / FOX) sur la face avant,
# drapeaux israéliens en fanions le long du treillis, enseigne au centre (icône U, USLAND). Pas de collision.
GANTRY = dict(half=46.0, y=7.5, sec=1.4, n_flags=14)

def pennant_flag(im):
    """Israeli flag laid out for the pennant (u = along the flag, v = across the band between its edges): stripes follow
    the edges, the star sits in the tall part (u = 0.30) with pre-compensated proportions so it looks round on the shape."""
    W, H = im.size; d = ImageDraw.Draw(im); blue = (0, 56, 184)
    d.rectangle([0, 0, W, H], fill=WHITE)
    d.rectangle([0, H * 0.10, W, H * 0.24], fill=blue); d.rectangle([0, H * 0.76, W, H * 0.90], fill=blue)
    cx, cy, ru, rv = W * 0.30, H * 0.50, W * 0.11, H * 0.27
    for r in (-np.pi / 2, np.pi / 2):
        P = [(cx + ru * np.cos(r + i * 2 * np.pi / 3), cy + rv * np.sin(r + i * 2 * np.pi / 3)) for i in range(3)]
        d.polygon(P, outline=blue, width=max(3, int(H * 0.035)))

def israel_flag(im, box):
    x0, y0, x1, y1 = box; W, H = x1 - x0, y1 - y0; d = ImageDraw.Draw(im)
    blue = (0, 56, 184); d.rectangle([x0, y0, x1, y1], fill=WHITE)
    d.rectangle([x0, y0 + H * 0.10, x1, y0 + H * 0.25], fill=blue); d.rectangle([x0, y1 - H * 0.25, x1, y1 - H * 0.10], fill=blue)
    cx, cy, R = (x0 + x1) / 2, (y0 + y1) / 2, H * 0.21
    for r in (-np.pi / 2, np.pi / 2):
        Pp = [(cx + R * np.cos(r + i * 2 * np.pi / 3), cy + R * np.sin(r + i * 2 * np.pi / 3)) for i in range(3)]
        d.polygon(Pp, outline=blue, width=max(2, int(R * 0.18)))

def gantry_texture():
    img = Image.new('RGB', (2048, 2048), BLK)
    seq = ['USLAND', 'RBT', 'FOX', 'RBT', 'USLAND', 'FOX', 'RBT', 'USLAND']
    def strip(im):                                                           # truss banner strip 8 panels of 10 ft x 1.4
        dd = ImageDraw.Draw(im); W, H = im.size; dd.rectangle([0, 0, W, H], fill=BLK); pw = W / len(seq)
        for i, nm in enumerate(seq):
            dd.rectangle([i * pw, 0, i * pw + 2, H], fill=(60, 60, 64))
            bx = (i * pw + pw * 0.15, H * 0.15, (i + 1) * pw - pw * 0.15, H * 0.85)
            if nm == 'USLAND': paste_logo(im, bx, WHITE)
            else: logo(im, nm, bx, on='dark')
    img.paste(panel((80, 1.4), 2032, strip).resize((2032, 120), Image.LANCZOS), (8, 8))
    def ped(im):                                                             # pedestal faces (5.5 x 7.5)
        dd = ImageDraw.Draw(im); W, H = im.size; dd.rectangle([0, 0, W, H], fill=BLK)
        logo(im, 'ICON', (W * 0.30, H * 0.12, W * 0.70, H * 0.38))
        paste_logo(im, (W * 0.12, H * 0.45, W * 0.88, H * 0.58), WHITE)
        logo(im, 'RBT', (W * 0.2, H * 0.66, W * 0.8, H * 0.80), on='dark')
        logo(im, 'FOX', (W * 0.25, H * 0.84, W * 0.75, H * 0.94), on='dark')
    img.paste(panel((5.5, 7.5), 512, ped).resize((496, 676), Image.LANCZOS), (8, 140))
    def sign(im):                                                            # centre sign 12 x 8: U icon over USLAND
        dd = ImageDraw.Draw(im); W, H = im.size; dd.rectangle([0, 0, W, H], fill=BLK)
        logo(im, 'ICON', (W * 0.3, H * 0.06, W * 0.7, H * 0.62))
        paste_logo(im, (W * 0.06, H * 0.68, W * 0.94, H * 0.94), WHITE)
    sg = panel((12, 8), 512, sign).resize((496, 330), Image.LANCZOS); img.paste(sg, (520, 140)); _CUT['gantry_sign'] = (sg, (520, 140, 1016, 470))
    flag = Image.new('RGB', (440, 320)); pennant_flag(flag); img.paste(flag, (1032, 140))
    pal = palette(img, ['black', 'metal', 'metal_dark', 'white'], [(14, 15, 17), (190, 193, 198), (110, 113, 118), WHITE])
    pal.update(strip=('r', (8, 8, 2040, 128)), ped=('r', (8, 140, 504, 816)), sign=('r', (520, 140, 1016, 470)),
               flag=(1032, 140, 1472, 460))
    return img, pal

def gantry_model(pal):
    """local x = along the gate row, z = riding direction, gate row at z = 0."""
    m = Mesh(2048, 2048); P = pal; H, y, a = GANTRY['half'], GANTRY['y'], GANTRY['sec'] / 2
    ped = [(-2.75, -1.5), (2.75, -1.5), (1.6, y), (-1.6, y)]                  # tapered pedestal profile (z, y)
    for s in (-1, 1):
        cx = s * (H + 1.0); m_ = ped
        _prism_x(m, [(z, yy) for z, yy in m_], cx - 2.4, cx + 2.4, P['ped'], P['ped'])
    # box truss along x
    C = [(y + 0.2, -a), (y + 0.2, a), (y + 0.2 + 2 * a, -a), (y + 0.2 + 2 * a, a)]
    for yy, zz in C: m.tube((-H - 1, yy, zz), (H + 1, yy, zz), 0.08, P['metal'])
    for k, x in enumerate(np.arange(-H - 1, H + 1.01, 2.0)):
        for (ya, za), (yb, zb) in (((y + 0.2, -a), (y + 0.2, a)), ((y + 0.2 + 2 * a, -a), (y + 0.2 + 2 * a, a)),
                                   ((y + 0.2, -a), (y + 0.2 + 2 * a, -a)), ((y + 0.2, a), (y + 0.2 + 2 * a, a))):
            m.tube((x, ya, za), (x, yb, zb), 0.05, P['metal'])
            if x + 2.0 <= H + 1.01: m.tube((x, ya, za) if k % 2 else (x, yb, zb), (x + 2.0, yb, zb) if k % 2 else (x + 2.0, ya, za), 0.045, P['metal'])
    # banner strip on the front face of the truss (both sides printed)
    m.box(-40.0, 40.0, y + 0.2, y + 0.2 + 2 * a, -a - 0.08, -a - 0.04, {'-z': P['strip'], '+z': P['strip'], '*': P['black']})
    m.box(-40.0, 40.0, y + 0.2, y + 0.2 + 2 * a, a + 0.04, a + 0.08, {'-z': P['strip'], '+z': P['strip'], '*': P['black']})
    # pennant flags standing on the truss, leaning back (as the reference): pole + triangle (flag texture), double sided
    px0, py0, px1, py1 = P['flag']; top = y + 0.2 + 2 * a
    for x in np.linspace(-H + 3, H - 3, GANTRY['n_flags']):
        if abs(x) < 2.0: continue                                                       # only inside the sign tower itself (the sign is raised above the flags)
        base = np.array([x, top, 0.0]); tip = base + np.array([0.0, 3.4, 0.45])         # pole (flags ~20 % smaller)
        m.tube(base, tip, 0.05, P['metal_dark'])
        far = base + np.array([0.0, 0.8, 4.5])                                          # point forwards (towards the track)
        b0 = base + np.array([0, 0.3, 0.1])
        bow = -(tip - b0) / np.linalg.norm(tip - b0) * 0.08 * np.linalg.norm(far - tip)  # gentle concave arc on the top edge
        n_ = 16; strip = []
        for k in range(n_ + 1):
            t = k / n_
            top_p = tip + (far - tip) * t + bow * np.sin(np.pi * t)
            bot_p = b0 + (far - b0) * t
            u = px0 + t * (px1 - px0)
            strip.append((bot_p, top_p, u))
        nrm = np.cross(tip - b0, far - b0); nrm /= np.linalg.norm(nrm)
        rows = 6                                                                          # fine grid: no zig-zag on the stripes
        for (ba, ta, ua), (bb, tb, ub) in zip(strip[:-1], strip[1:]):
            for r_ in range(rows):
                v0, v1 = r_ / rows, (r_ + 1) / rows
                q = [ba + (ta - ba) * v0, bb + (tb - bb) * v0, bb + (tb - bb) * v1, ba + (ta - ba) * v1]
                uv = [m.uv_px(ua, py1 - v0 * (py1 - py0)), m.uv_px(ub, py1 - v0 * (py1 - py0)),
                      m.uv_px(ub, py1 - v1 * (py1 - py0)), m.uv_px(ua, py1 - v1 * (py1 - py0))]
                m.tri_fan(q, nrm, uv); m.tri_fan(q[::-1], -nrm, uv[::-1])
        m.tube(far, np.array([x + 0.4, top, a]), 0.015, P['metal_dark'])                  # small cable holding the point down to the truss
    # centre sign on a small tower
    th, bx, bz = 4.4, 1.6, 0.7                                                       # truss tower: 3.2 x 1.4 ft, 4.4 ft tall
    C = [(-bx, -bz), (bx, -bz), (bx, bz), (-bx, bz)]
    for cx, cz in C: m.tube((cx, top, cz), (cx, top + th, cz), 0.07, P['metal'])
    for k, yy in enumerate(np.linspace(top + 0.15, top + th, 4)):
        for i in range(4):
            (ax_, az), (bx_, bz_) = C[i], C[(i + 1) % 4]
            m.tube((ax_, yy, az), (bx_, yy, bz_), 0.05, P['metal'])
            if k < 3:
                y2 = np.linspace(top + 0.15, top + th, 4)[k + 1]
                m.tube((ax_, yy, az), (bx_, y2, bz_), 0.035, P['metal']) if (i + k) % 2 else m.tube((bx_, yy, bz_), (ax_, y2, az), 0.035, P['metal'])
    sign_pair(m, 'gantry_sign', 0.0, top + th - 0.05, 12.0, 0.9, 0.22, P['black'], P['metal'])   # two cut plates on the tower, above the flags
    return m


# ------------------------------------------------------------------ start grate (reference photo: thin cross-shaped steel grating)
# Fine (0,06 ft), en croix : étroite contre la grille (roue avant), plus large au niveau des pieds, de nouveau étroite derrière.
# Grillage à mailles carrées + cadre plat légèrement surélevé.
PXF = 80   # texture pixels per ft
def grate_outline():
    """cross outline (x, z) of the one-piece grate, gate at z = 0, running backwards; small chamfers at the steps."""
    z = -GRATE['gap']; right = []
    for w, L in GRATE['parts']:
        right += [(w / 2, z - 0.06), (w / 2, z - L + 0.06)]; z -= L
    zend = z; ch = 0.12
    pts = [(-x, zz) for x, zz in right[::-1]] if False else None
    R = [(GRATE['parts'][0][0] / 2 - ch, -GRATE['gap'])] + right + [(GRATE['parts'][-1][0] / 2 - ch, zend)]
    L_ = [(-x, zz) for x, zz in R[::-1]]
    return R + L_, zend

def grate_texture():
    img = Image.new('RGB', (1024, 1024), (110, 86, 60)); d = ImageDraw.Draw(img)
    steel, edge, hole = (178, 182, 186), (206, 209, 213), (92, 72, 52)
    poly, zend = grate_outline(); wmax = max(w for w, _ in GRATE['parts']); L = -zend - GRATE['gap']   # sheet only (not the gap)
    x0, y0 = 8, 8; x1, y1 = x0 + int(wmax * PXF), y0 + int(L * PXF)
    d.rectangle([x0, y0, x1, y1], fill=steel); cw, chh = 13, 8                 # small diamonds (expanded metal), one continuous sheet
    for j, y in enumerate(np.arange(y0 + 2, y1 - 2, chh / 2)):
        off = cw / 2 * (j % 2)
        for xx in np.arange(x0 + 2 + off - cw, x1, cw):
            d.polygon([(xx + 2, y + chh / 2), (xx + cw / 2, y + 1.2), (xx + cw - 2, y + chh / 2), (xx + cw / 2, y + chh - 1.2)], fill=hole)
    P_ = [(x0 + (x + wmax / 2) * PXF, y0 + (-zz - GRATE['gap']) * PXF) for x, zz in poly]
    d.line(P_ + [P_[0]], fill=edge, width=9, joint='curve')                    # flat border following the cut outline
    pal = palette(img, ['steel', 'edge', 'dark'], [steel, edge, (70, 70, 72)])
    assert y1 < 1024 - 128, 'grate sheet runs into the palette squares'
    pal.update(top=(x0, y0, x1, y1), wmax=wmax, L=L)
    return img, pal

def grate_model(pal):
    """one grate per gate, cut from one sheet (cross outline), local z = riding direction, gate at z = 0, runs backwards."""
    m = Mesh(1024, 1024); P = pal; t = GRATE['t']; poly, zend = grate_outline()
    x0, y0, x1, y1 = P['top']; wmax, L = P['wmax'], P['L']
    uv = lambda x, z: m.uv_px(x0 + (x + wmax / 2) / wmax * (x1 - x0), y0 + (-z - GRATE['gap']) / L * (y1 - y0))   # v13b: from the sheet front
    tris = _ear_clip(poly); ed = m.uv_px(*P['edge'][1])
    for i, j, k in tris:
        m.tri_fan([np.array([poly[q][0], t, poly[q][1]]) for q in (i, j, k)], np.array([0, 1.0, 0]), [uv(*poly[q]) for q in (i, j, k)])
        m.tri_fan([np.array([poly[q][0], 0.0, poly[q][1]]) for q in (i, j, k)], np.array([0, -1.0, 0]), [ed] * 3)
    n = len(poly)
    for q in range(n):
        (ax_, az), (bx, bz) = poly[q], poly[(q + 1) % n]; e = np.array([bx - ax_, bz - az])
        N = np.array([e[1], 0, -e[0]]); N /= np.linalg.norm(N)
        if np.dot(N[[0, 2]], np.array([(ax_ + bx) / 2, (az + bz) / 2 - zend / 2])) < 0: N = -N
        m.quad([np.array([ax_, 0, az]), np.array([bx, 0, bz]), np.array([bx, t, bz]), np.array([ax_, t, az])], N, lambda p: ed)
    return m

# ------------------------------------------------------------------ start gate (reference photo): solid black plate with the U icon, red round tube frame
# Même encombrement que la grille JGSX gate01 (3,1 ft de large, pas de 4 ft) ; charnière en bas (y = 0, z = 0), face au pilote = -z.
# À vérifier en jeu : point de pivot / sens de chute identiques à gate01 (le jeu anime la grille ; forme de collision @startgate.shp gardée).
GATE = dict(w=3.75, h=2.30, r_tube=0.075, pitch=4.0)   # gate01 convention (modelled flat, hinge at the origin); wider than gate01 (3.14): 0.25 ft gap between gates
def pipe(m, pts, r, src, closed=False, seg=10):
    """round tube swept along a polyline (closed = loop)."""
    P = [np.asarray(p, float) for p in pts]; n = len(P); uv = m.uv_px(*src[1]); rings = []
    for i in range(n):
        a = P[i - 1] if (closed or i > 0) else P[i]; b = P[(i + 1) % n] if (closed or i < n - 1) else P[i]
        tg = b - a; tg /= np.linalg.norm(tg)
        ref = np.array([0, 0, 1.0]) if abs(tg[2]) < 0.9 else np.array([1.0, 0, 0])
        e1 = np.cross(tg, ref); e1 /= np.linalg.norm(e1); e2 = np.cross(tg, e1)
        rings.append([(P[i] + r * (np.cos(t) * e1 + np.sin(t) * e2), np.cos(t) * e1 + np.sin(t) * e2) for t in np.linspace(0, 2 * np.pi, seg + 1)[:-1]])
    for i in range(n if closed else n - 1):
        A, B = rings[i], rings[(i + 1) % n]
        for k in range(seg):
            j = (k + 1) % seg; N = A[k][1] + A[j][1] + B[k][1] + B[j][1]; N /= np.linalg.norm(N)
            m.tri_fan([A[k][0], A[j][0], B[j][0], B[k][0]], N, [uv] * 4)

def gate_texture():
    img = Image.new('RGB', (1024, 1024), (14, 14, 16))
    def plate(im):
        d = ImageDraw.Draw(im); W, H = im.size; d.rectangle([0, 0, W, H], fill=(14, 14, 16))
        logo(im, 'ICON', (W / 2 - H * 0.36, H * 0.14, W / 2 + H * 0.36, H * 0.86))
    img.paste(panel((GATE['w'] - 0.26, GATE['h'] - 0.3), 1008, plate).resize((1008, 464), Image.LANCZOS), (8, 8))
    pal = palette(img, ['black', 'red'], [(14, 14, 16), (205, 24, 34)])
    pal.update(plate=('r', (8, 8, 1016, 472)))
    return img, pal

def gate_model(pal):
    m = Mesh(1024, 1024); P = pal; w, h, r = GATE['w'], GATE['h'], GATE['r_tube']
    yh = 0.0                                                                  # hinge tube axis = base of every gate (at the origin, as gate01)
    # plate: square bottom hanging on the hinge tube, rounded top corners only
    hw, top, rc = w / 2 - 0.13, h - 0.13, 0.26
    poly = [(-hw, yh), (hw, yh)]
    for t in np.radians(np.linspace(0, 90, 10)): poly.append((hw - rc + rc * np.cos(t), top - rc + rc * np.sin(t)))
    for t in np.radians(np.linspace(90, 180, 10)): poly.append((-hw + rc + rc * np.cos(t), top - rc + rc * np.sin(t)))
    px0, py0, px1, py1 = P['plate'][1]; bl = m.uv_px(*P['black'][1])
    for zz, nz in ((-0.04, -1.0), (0.04, 1.0)):
        for i, j, k in _ear_clip(poly):
            pts = [np.array([poly[q][0], poly[q][1], zz]) for q in (i, j, k)]
            # -z face: viewer's right is -x ; +z face: +x
            uv = [m.uv_px(px0 + (0.5 + poly[q][0] / (2 * hw)) * (px1 - px0), py1 - (poly[q][1] - yh) / (top - yh) * (py1 - py0))
                  for q in (i, j, k)] if nz > 0 else [bl] * 3                         # logo on the outer (track) side only
            m.tri_fan(pts, np.array([0, 0, nz]), uv)
    n = len(poly)
    for q in range(n):
        (ax_, ay), (bx, by) = poly[q], poly[(q + 1) % n]; N = np.array([by - ay, -(bx - ax_), 0.0])
        if np.linalg.norm(N) < 1e-9: continue
        N /= np.linalg.norm(N)
        if np.dot(N[:2], np.array([(ax_ + bx) / 2, (ay + by) / 2 - (yh + top) / 2])) < 0: N = -N
        m.quad([np.array([ax_, ay, -0.04]), np.array([bx, by, -0.04]), np.array([bx, by, 0.04]), np.array([ax_, ay, 0.04])], N, lambda p: bl)
    # frame: inverted U, the two uprights go straight down into the hinge tube, rounded top corners only
    cr = 0.34; x0, x1, y1 = -w / 2 + r, w / 2 - r, h
    path = [(x0, yh, 0.0)]
    for t in np.radians(np.linspace(180, 90, 12)): path.append((x0 + cr + cr * np.cos(t), y1 - cr + cr * np.sin(t), 0.0))
    for t in np.radians(np.linspace(90, 0, 12)): path.append((x1 - cr + cr * np.cos(t), y1 - cr + cr * np.sin(t), 0.0))
    path.append((x1, yh, 0.0))
    pipe(m, path, r, P['red'], closed=False, seg=12)
    pipe(m, [(-GATE['pitch'] / 2, yh, 0.0), (GATE['pitch'] / 2, yh, 0.0)], r * 1.15, P['red'], seg=12)   # hinge tube, gate to gate (pitch 4 ft): one continuous tube along the row
    # built upright, then laid flat towards +z like gate01 (rotation +90 deg about x): the rider-facing face becomes +y
    for i, v in enumerate(m.V):
        m.V[i] = (v[0], -v[2], v[1], v[3], -v[5], v[4], v[6], v[7])
    return m


# ------------------------------------------------------------------ road bike on a direct-drive trainer (reference photos)
# Vélo de route aéro rouge (géométrie taille 54 : empattement 3,25 ft, roues 700c), cadre en tubes ovales profilés,
# haubans plongeants qui rejoignent le tube de selle bas, cintre route à drops, selle courte, roue avant à jante haute
# et flancs beige, pédalier + plateau, disque avant. La roue arrière est remplacée par un home-trainer à transmission
# directe (corps noir, carter rond, cassette orange, pieds repliables en X). « S-WORKS » sur le tube diagonal (2 côtés).
# Origine = axe arrière (sur le trainer) au sol ; +z = avant du vélo. Posé dans la benne des pick-ups, tête-bêche.
BK = dict(R=1.115, wb=3.25, bb=(1.34, 0.88), ht_top=(2.60, 2.70), ht_bot=(2.74, 2.22), cluster=(0.92, 2.46),
          saddle=(0.66, 3.18), stays=(1.02, 2.12))
RED, RED_D, CARBON, TAN = (168, 14, 30), (110, 8, 20), (22, 22, 24), (196, 160, 110)

def bike_texture():
    img = Image.new('RGB', (1024, 1024), RED)
    def decal(im):                                                           # down-tube decal 1.6 x 0.3 ft, wrapped on the tube
        d = ImageDraw.Draw(im); W, H = im.size; d.rectangle([0, 0, W, H], fill=RED)
        put_text(im, 'S-WORKS', int(H * 0.56), WHITE, W / 2, H * 0.22, anchor='c', italic=0.28, bold=0.09, max_w=int(W * 0.94))
    img.paste(panel((1.6, 0.30), 1008, decal).resize((1008, 188), Image.LANCZOS), (8, 8))
    def rimd(im):                                                            # deep rim side, 1 turn unrolled: black + small grey logos
        d = ImageDraw.Draw(im); W, H = im.size; d.rectangle([0, 0, W, H], fill=CARBON)
        d.rectangle([0, H * 0.82, W, H], fill=(60, 60, 64))                      # brake track
    img.paste(panel((7.0, 0.17), 1008, rimd).resize((1008, 40), Image.LANCZOS), (8, 210))
    pal = palette(img, ['red', 'red_d', 'carbon', 'black', 'tan', 'silver', 'orange', 'grey', 'tyre', 'blue'],
                  [RED, RED_D, CARBON, (10, 10, 11), TAN, (175, 178, 184), (240, 90, 20), (60, 62, 66), (24, 24, 25), (60, 120, 255)])
    pal.update(decal=(8, 8, 1016, 196), rim=(8, 210, 1016, 250))
    return img, pal

def epipe(m, pts, rx, ry, src, seg=10, side=(1.0, 0, 0)):
    """elliptical tube along a polyline: rx across the bike (x), ry in the frame plane (aero tubes)."""
    P = [np.asarray(p, float) for p in pts]; n = len(P); uv = m.uv_px(*src[1]); rings = []
    sx = np.asarray(side, float)
    for i in range(n):
        a = P[max(i - 1, 0)]; b = P[min(i + 1, n - 1)]; tg = b - a; tg /= np.linalg.norm(tg)
        e1 = sx - np.dot(sx, tg) * tg; e1 /= np.linalg.norm(e1); e2 = np.cross(tg, e1)
        rings.append([(P[i] + rx * np.cos(t) * e1 + ry * np.sin(t) * e2, np.cos(t) / rx * e1 + np.sin(t) / ry * e2)
                      for t in np.linspace(0, 2 * np.pi, seg + 1)[:-1]])
    for i in range(n - 1):
        A, B = rings[i], rings[i + 1]
        for k in range(seg):
            j = (k + 1) % seg; N = A[k][1] + A[j][1] + B[k][1] + B[j][1]; N /= np.linalg.norm(N)
            m.tri_fan([A[k][0], A[j][0], B[j][0], B[k][0]], N, [uv] * 4)
    for i, sg in ((0, -1), (n - 1, 1)):                                       # end caps
        ring = [p for p, _ in rings[i]]; tg = P[min(i + 1, n - 1)] - P[max(i - 1, 0)]; tg /= np.linalg.norm(tg)
        m.tri_fan(ring, tg * sg, [uv] * len(ring))

def _curve(p0, p1, p2, n=8):
    """quadratic Bézier from p0 to p2 through control p1."""
    p0, p1, p2 = (np.asarray(p, float) for p in (p0, p1, p2))
    return [(1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2 for t in np.linspace(0, 1, n)]

def _lathe(m, c, axis_x, prof, src, seg=36, uvrect=None):
    """surface of revolution around the x axis through c: prof = [(radius, x offset)], solid colour or unrolled rect."""
    c = np.asarray(c, float); ang = np.linspace(0, 2 * np.pi, seg + 1)
    d = lambda t: np.array([0, np.cos(t), np.sin(t)])
    for i in range(len(prof) - 1):
        (ra, oa), (rb, ob) = prof[i], prof[i + 1]
        for k in range(seg):
            t0, t1 = ang[k], ang[k + 1]
            pts = [c + d(t0) * ra + np.array([oa, 0, 0]), c + d(t1) * ra + np.array([oa, 0, 0]),
                   c + d(t1) * rb + np.array([ob, 0, 0]), c + d(t0) * rb + np.array([ob, 0, 0])]
            tm = (t0 + t1) / 2; N = d(tm) * (ob - oa) * -1 + np.array([rb - ra, 0, 0])
            if np.linalg.norm(N) < 1e-9: N = d(tm)
            N /= np.linalg.norm(N)
            if np.dot(N, d(tm)) < -1e-6 and abs(ob - oa) > 1e-6: N = -N
            if uvrect is None: m.quad(pts, N, lambda p: m.uv_px(*src[1]))
            else:
                x0, y0, x1, y1 = uvrect
                m.tri_fan(pts, N, [m.uv_px(x0 + (x1 - x0) * s, y1 if q else y0) for s, q in ((k / seg, 0), ((k + 1) / seg, 0), ((k + 1) / seg, 1), (k / seg, 1))])

def bike_wheel(m, c, P, spokes=24):
    R = BK['R']; c = np.asarray(c, float)
    _lathe(m, c, 0, [(R - 0.06, 0.045), (R - 0.02, 0.05), (R, 0.0), (R - 0.02, -0.05), (R - 0.06, -0.045)], P['tyre'], seg=40)
    _lathe(m, c, 0, [(R - 0.06, 0.044), (R - 0.07, 0.046)], P['tan'], seg=40)                    # tan sidewall
    _lathe(m, c, 0, [(R - 0.07, 0.046), (R - 0.24, 0.03)], P['carbon'], seg=40, uvrect=P['rim'])   # deep rim, drive side
    _lathe(m, c, 0, [(R - 0.24, -0.03), (R - 0.07, -0.046)], P['carbon'], seg=40, uvrect=P['rim'])
    _lathe(m, c, 0, [(R - 0.24, 0.03), (R - 0.24, -0.03)], P['carbon'], seg=40)
    _lathe(m, c, 0, [(0.05, 0.16), (0.07, 0.12), (0.07, -0.12), (0.05, -0.16)], P['black'], seg=12)   # hub
    for k in range(spokes):
        t = 2 * np.pi * k / spokes; dd = np.array([0, np.cos(t), np.sin(t)]); sx = 0.11 if k % 2 else -0.11
        m.tube(c + np.array([sx, 0, 0]) + dd * 0.07, c + dd * (R - 0.24), 0.008, P['black'])
    _lathe(m, c + np.array([-0.17, 0, 0]), 0, [(0.0, 0.0), (0.26, 0.0), (0.26, -0.01), (0.0, -0.01)], P['silver'], seg=24)   # disc rotor

def bike_model(pal):
    m = Mesh(1024, 1024); P = pal; R = BK['R']
    ax = np.array([0, R, 0.0]); bb = np.array([0, BK['bb'][1], BK['bb'][0]])
    fa = np.array([0, R, BK['wb']]); ht_t = np.array([0, BK['ht_top'][1], BK['ht_top'][0]]); ht_b = np.array([0, BK['ht_bot'][1], BK['ht_bot'][0]])
    cl = np.array([0, BK['cluster'][1], BK['cluster'][0]]); st = np.array([0, BK['stays'][1], BK['stays'][0]])
    # frame: aero tubes (thin across, deep in the frame plane)
    epipe(m, [ht_b + (ht_t - ht_b) * t for t in np.linspace(-0.05, 1.05, 4)], 0.10, 0.13, P['red'])            # head tube
    epipe(m, _curve(ht_b + (ht_t - ht_b) * 0.15, (ht_b + bb) / 2 + np.array([0, 0.05, 0.05]), bb), 0.11, 0.17, P['red'])   # down tube
    epipe(m, _curve(ht_t + (ht_b - ht_t) * 0.12, (ht_t + cl) / 2 + np.array([0, 0.03, 0]), cl), 0.075, 0.09, P['red'])     # top tube
    epipe(m, [bb, bb + (cl - bb) * 0.5, cl + (cl - bb) * 0.06], 0.085, 0.13, P['red'])                          # seat tube
    for s in (-1, 1):
        o = np.array([s * 0.2, 0, 0])
        epipe(m, _curve(bb + o * 0.4, (bb + ax) / 2 + o + np.array([0, -0.02, 0]), ax + o * 0.9), 0.05, 0.075, P['red'])   # chainstays
        epipe(m, _curve(st + o * 0.25, (st + ax) / 2 + o * 0.9, ax + o * 0.9), 0.035, 0.05, P['red'])             # dropped seatstays
        fk = _curve(ht_b + o * 0.35, ht_b + (fa - ht_b) * 0.5 + o + np.array([0, 0, 0.05]), fa + o * 0.6)
        epipe(m, fk, 0.05, 0.09, P['red'])                                                                         # fork legs
    epipe(m, [bb + np.array([-0.22, 0, 0]), bb + np.array([0.22, 0, 0])], 0.11, 0.11, P['red_d'], side=(0, 1.0, 0))   # BB shell
    # S-WORKS on both sides of the down tube, wrapped on the oval tube (big, as on the real frame)
    dtp = _curve(ht_b + (ht_t - ht_b) * 0.15, (ht_b + bb) / 2 + np.array([0, 0.05, 0.05]), bb, 24)[3:21]
    px0, py0, px1, py1 = P['decal']; rx, ry = 0.11 + 0.004, 0.17 + 0.004
    for s in (-1, 1):
        rows = []
        for i, c in enumerate(dtp):
            tg = dtp[min(i + 1, len(dtp) - 1)] - dtp[max(i - 1, 0)]; tg /= np.linalg.norm(tg)
            e1 = np.array([1.0, 0, 0]); e2 = np.cross(tg, e1)                  # e2 points down (towards the BB side)
            ring = []
            for j, ph in enumerate(np.linspace(-1.05, 1.05, 7)):
                p = c + s * rx * np.cos(ph) * e1 + ry * np.sin(ph) * e2
                nrm = s * np.cos(ph) / rx * e1 + np.sin(ph) / ry * e2; nrm /= np.linalg.norm(nrm)
                uu = i / (len(dtp) - 1); uu = uu if s > 0 else 1 - uu
                ring.append((p, nrm, m.uv_px(px0 + uu * (px1 - px0), py0 + j / 6 * (py1 - py0))))
            rows.append(ring)
        for i in range(len(rows) - 1):
            for j in range(6):
                q = [rows[i][j], rows[i + 1][j], rows[i + 1][j + 1], rows[i][j + 1]]
                N = sum(v[1] for v in q); N /= np.linalg.norm(N)
                m.tri_fan([v[0] for v in q], N, [v[2] for v in q])
    # aero seatpost + saddle
    sd = np.array([0, BK['saddle'][1], BK['saddle'][0]])
    epipe(m, [cl, sd - np.array([0, 0.08, 0])], 0.06, 0.1, P['carbon'])
    secs = [(sd[2] - 0.40, sd[1], sd[1] + 0.10, 0.22, 0.20, 3), (sd[2] - 0.30, sd[1] - 0.02, sd[1] + 0.12, 0.24, 0.22, 3),
            (sd[2] - 0.05, sd[1] - 0.02, sd[1] + 0.10, 0.17, 0.15, 3), (sd[2] + 0.20, sd[1] - 0.01, sd[1] + 0.08, 0.09, 0.08, 3),
            (sd[2] + 0.38, sd[1], sd[1] + 0.06, 0.06, 0.05, 3)]
    _loft(m, secs, lambda p, N: m.uv_px(*P['black'][1]), cap_first=lambda p: m.uv_px(*P['black'][1]), cap_last=lambda p: m.uv_px(*P['black'][1]))
    # one-piece cockpit: spacer, stem, drop bar (tops -> hoods -> drops), levers
    stem_end = ht_t + np.array([0, 0.06, 0.36])
    epipe(m, [ht_t, ht_t + np.array([0, 0.06, 0])], 0.10, 0.10, P['carbon'], side=(1.0, 0, 0))
    epipe(m, [ht_t + np.array([0, 0.06, 0]), stem_end], 0.06, 0.07, P['carbon'])
    for s in (-1, 1):
        x = s * 0.69
        bar = [stem_end, stem_end + np.array([s * 0.35, 0, 0.0]), np.array([x, stem_end[1], stem_end[2] + 0.02]),
               np.array([x, stem_end[1] + 0.01, stem_end[2] + 0.18])]
        bar += _curve(np.array([x, stem_end[1] - 0.02, stem_end[2] + 0.30]), np.array([x, stem_end[1] - 0.25, stem_end[2] + 0.48]),
                      np.array([x, stem_end[1] - 0.42, stem_end[2] + 0.15]), 7)
        epipe(m, bar, 0.04, 0.05, P['carbon'], side=(0, 1.0, 0))
        hood = np.array([x, stem_end[1] + 0.03, stem_end[2] + 0.24])
        m.rbox(x - 0.05, x + 0.05, hood[1] - 0.05, hood[1] + 0.09, hood[2] - 0.06, hood[2] + 0.16, 0.04, 0, {'*': P['black']}, P['black'])
        epipe(m, _curve(hood + np.array([0, 0, 0.12]), hood + np.array([0, -0.25, 0.2]), hood + np.array([0, -0.48, 0.05]), 6), 0.02, 0.03, P['black'])
    # crankset, chainring, pedals, chain (drive side = +x)
    _lathe(m, bb + np.array([0.25, 0, 0]), 0, [(0.0, 0.0), (0.34, 0.0), (0.34, -0.02), (0.0, -0.02)], P['black'], seg=36)
    for s, t in ((1, -0.6), (-1, 2.55)):
        pd = bb + np.array([s * 0.29, 0.56 * np.sin(t), 0.56 * np.cos(t)])
        m.tube(bb + np.array([s * 0.27, 0, 0]), pd, 0.035, P['black'])
        m.rbox(pd[0] + s * 0.02 - 0.06, pd[0] + s * 0.02 + 0.06 + s * 0.12, pd[1] - 0.03, pd[1] + 0.03, pd[2] - 0.1, pd[2] + 0.1, 0.02, 2, {'*': P['black']}, P['black'])
    for yo in (0.33, -0.33):
        m.tube(bb + np.array([0.25, yo, 0]), ax + np.array([0.25, yo * 0.4, 0]), 0.012, P['silver'])
    bike_wheel(m, fa, P)
    bike_wheel(m, ax, P)                                                                                   # natural rear wheel
    _lathe(m, ax + np.array([0.2, 0, 0]), 0, [(0.0, 0.0), (0.17, 0.0), (0.17, -0.1), (0.0, -0.1)], P['silver'], seg=18)   # cassette
    lift = 0.17                                                                                            # bike raised: wheel on the trainer roller
    for i in range(len(m.V)): m.V[i] = (m.V[i][0], m.V[i][1] + lift) + tuple(m.V[i][2:])
    # small wheel-on trainer unit under the rear wheel (roller + resistance box), riser block under the front wheel
    m.rbox(-0.42, 0.42, 0.0, 0.16, -0.75, 0.30, 0.07, 0, {'*': P['black']}, P['black'])
    m.rbox(0.10, 0.48, 0.0, 0.34, -0.70, -0.20, 0.08, 0, {'*': P['black']}, P['black'])                  # resistance unit
    _lathe(m, np.array([0, 0.17, 0.0]), 0, [(0.0, 0.2), (0.07, 0.2), (0.07, -0.2), (0.0, -0.2)], P['grey'], seg=12)   # roller
    for s in (-1, 1): m.rbox(s * 0.55 - 0.1, s * 0.55 + 0.1, 0.0, 0.06, -0.75, 0.25, 0.03, 2, {'*': P['grey']}, P['grey'])
    m.box(0.18, 0.30, 0.34, 0.36, -0.5, -0.42, {'*': P['blue']})                                         # status LED
    m.rbox(-0.22, 0.22, 0.0, 0.17, BK['wb'] - 0.45, BK['wb'] + 0.45, 0.08, 0, {'*': P['black']}, P['black'])   # front riser block
    return m


# ------------------------------------------------------------------ pop-up tent (EZ-up type, replaces the JGSX ezup)
# 10 x 10 ft, toit en pyramide bleu marine USLAND, bandeau (0,8 ft) tout autour : USLAND devant et derrière, RBT et FOX sur
# les côtés (un logo par face, centré, blanc). Pieds alu carrés avec lests, ciseaux sous le bandeau. Pas de collision.
TENT = dict(half=5.0, eave=7.0, peak=9.6, val=0.8)
ROOF = NAVY           # roof and valance: same navy

def tent_texture():
    img = Image.new('RGB', (1024, 1024), NAVY)
    H_, V_ = TENT['half'], TENT['val']
    for k, nm in enumerate(('USLAND', 'RBT', 'FOX')):                       # valance strips (10 x 0.8 ft each)
        def val(im, nm=nm):
            d = ImageDraw.Draw(im); W, H = im.size; d.rectangle([0, 0, W, H], fill=NAVY)
            d.rectangle([0, H - 6, W, H], fill=RED)
            box = (W * 0.25, H * 0.16, W * 0.75, H * 0.80)
            if nm == 'USLAND': paste_logo(im, box, WHITE)
            else: logo(im, nm, box, on='dark')
        img.paste(panel((2 * H_, V_), 1008, val, ao=0).resize((1008, 96), Image.LANCZOS), (8, 8 + k * 104))
    def roof(im):                                                           # roof panel: plain navy (as seen and approved, v12b)
        d = ImageDraw.Draw(im); W, H = im.size; d.rectangle([0, 0, W, H], fill=ROOF)
    img.paste(panel((10, 10), 400, roof, ao=0).resize((400, 400), Image.LANCZOS), (8, 330))
    def plain(im):
        d = ImageDraw.Draw(im); W, H = im.size; d.rectangle([0, 0, W, H], fill=ROOF)
    img.paste(panel((10, 10), 400, plain, ao=0).resize((400, 400), Image.LANCZOS), (420, 330))
    pal = palette(img, ['navy', 'alu', 'dark', 'red'], [NAVY, (190, 193, 198), (22, 22, 24), RED])
    pal.update(v_usland=('r', (8, 8, 1016, 104)), v_rbt=('r', (8, 112, 1016, 208)), v_fox=('r', (8, 216, 1016, 312)),
               roof_logo=(8, 330, 408, 730), roof_plain=(420, 330, 820, 730))
    return img, pal

def tent_model(pal):
    """local +z = front of the tent (USLAND side), y up, origin at the centre of the footprint on the ground."""
    m = Mesh(1024, 1024); P = pal; h, e, pk, v = TENT['half'], TENT['eave'], TENT['peak'], TENT['val']
    for sx in (-1, 1):                                                       # legs (telescopic: thicker lower part) + weights
        for sz in (-1, 1):
            x, z = sx * (h - 0.1), sz * (h - 0.1)
            m.rbox(x - 0.09, x + 0.09, 0.0, 3.6, z - 0.09, z + 0.09, 0.03, 1, {'*': P['alu']}, P['alu'])
            m.rbox(x - 0.07, x + 0.07, 3.6, e, z - 0.07, z + 0.07, 0.025, 1, {'*': P['alu']}, P['alu'])
            m.rbox(x - 0.45, x + 0.45, 0.0, 0.25, z - 0.45, z + 0.45, 0.1, 1, {'*': P['dark']}, P['dark'])
    C = [(-h + 0.1, -h + 0.1), (h - 0.1, -h + 0.1), (h - 0.1, h - 0.1), (-h + 0.1, h - 0.1)]
    for i in range(4):                                                       # scissor truss under the valance
        (ax_, az), (bx, bz) = C[i], C[(i + 1) % 4]
        m.tube((ax_, e - v + 0.05, az), (bx, e - 0.05, bz), 0.035, P['alu']); m.tube((ax_, e - 0.05, az), (bx, e - v + 0.05, bz), 0.035, P['alu'])
    # valance: 4 printed strips outside the frame (USLAND front + back, RBT left, FOX right), readable from outside
    m.box(-h, h, e - v, e, h, h + 0.03, {'+z': P['v_usland'], '-z': P['navy'], '*': P['navy']})
    m.box(-h, h, e - v, e, -h - 0.03, -h, {'-z': P['v_usland'], '+z': P['navy'], '*': P['navy']})
    m.box(-h - 0.03, -h, e - v, e, -h, h, {'-x': P['v_rbt'], '+x': P['navy'], '*': P['navy']})
    m.box(h, h + 0.03, e - v, e, -h, h, {'+x': P['v_fox'], '-x': P['navy'], '*': P['navy']})
    # pyramid roof, slightly overhanging; front and back panels carry the U icon
    o = 0.15; apex = np.array([0.0, pk, 0.0])
    corners = [np.array([-h - o, e, h + o]), np.array([h + o, e, h + o]), np.array([h + o, e, -h - o]), np.array([-h - o, e, -h - o])]
    for i in range(4):
        a_, b_ = corners[i], corners[(i + 1) % 4]; N = np.cross(b_ - a_, apex - a_); N /= np.linalg.norm(N)
        if N[1] < 0: N = -N
        rx0, ry0, rx1, ry1 = P['roof_logo'] if i in (0, 2) else P['roof_plain']
        uv = [m.uv_px(rx0, ry1), m.uv_px(rx1, ry1), m.uv_px((rx0 + rx1) / 2, ry0)]
        m.tri_fan([a_, b_, apex], N, uv)
        dn = np.array([0.0, 0.06, 0.0])                                     # underside 0.06 ft lower: no z-fighting with the roof
        m.tri_fan([b_ - dn, a_ - dn, apex - dn], -N, [m.uv_px(*P['navy'][1])] * 3)
    return m


# ------------------------------------------------------------------ track banners (on the inner side of the fences)
BANNER_FT = (12.0, 3.0, 0.6)    # width, height, bottom above the ground
BANNERS = ['ICON', 'RBT', 'FOX', 'USLAND']          # USLAND at the far end, never next to the U icon
def banner_texture(name):
    W, H = 1024, 256; im = Image.new('RGB', (W, H), WHITE)
    if name == 'USLAND': paste_logo(im, (W * 0.08, H * 0.18, W * 0.92, H * 0.82), (12, 12, 14))
    else: logo(im, name, (W * 0.22, H * 0.14, W * 0.78, H * 0.86), on='light')
    d = ImageDraw.Draw(im); d.rectangle([0, 0, W, 10], fill=RED); d.rectangle([0, H - 11, W, H], fill=RED)
    img = Image.new('RGB', (1024, 1024), (40, 40, 44))
    img.paste(im.resize((1008, 248)), (8, 8)); img.paste(im.resize((1008, 248)), (8, 264))
    pal = palette(img, ['frame'], [(60, 60, 64)]); pal.update(front=('r', (8, 8, 1016, 256)), back=('r', (8, 264, 1016, 512)))
    return img, pal

def banner_model(pal):
    """12 x 3 ft banner printed on both sides, hung 0.6 ft above the ground (one model, one texture per sponsor)."""
    m = Mesh(1024, 1024); P = pal; w, h, b = BANNER_FT
    m.box(-w / 2, w / 2, b, b + h, -0.03, 0.03, {'-z': P['front'], '+z': P['back'], '*': P['frame']})
    return m

# ------------------------------------------------------------------ specs (docs/12_objets_usland.md) : contrôlés à chaque génération
BUDGET = {'tent_usland': 2500, 'hospitality_usland': 8000, 'pickup_usland': 6000, 'finish_arch': 3000, 'start_gantry': 12000, 'start_grate': 200, 'start_gate': 1500, 'bike_trainer': 8000, 'banner': 100}
def check_specs(outd):
    """JM + PNG checks: triangle budget, indices, UV in [0, 1], unit normals, texture size (power of two, <= 2048, RGB),
    model sizes. Returns the rows printed by build(); raises on any failure."""
    rows, bad = [], []
    for name, budget in BUDGET.items():
        L = open(f'{outd}/{name}.jm').read().splitlines(); nv, nt = map(int, L[2].split())
        V = np.array([[float(t) for t in l.split()] for l in L[3:3 + nv]]); I = np.array([int(l) for l in L[3 + nv:3 + nv + 3 * nt]])
        lo, hi = V[:, :3].min(0), V[:, :3].max(0); nl = np.linalg.norm(V[:, 3:6], axis=1)
        if L[0] != 'JM1' or len(L[1].split()) != 5: bad.append((name, 'en-tête'))
        if nt > budget: bad.append((name, f'{nt} triangles > {budget}'))
        if I.min() < 0 or I.max() >= nv: bad.append((name, 'indices'))
        if V[:, 6:8].min() < -1e-6 or V[:, 6:8].max() > 1 + 1e-6: bad.append((name, 'UV hors [0,1]'))
        if np.abs(nl - 1).max() > 1e-3: bad.append((name, 'normales'))
        rows.append((name, nt, tuple(np.round(hi - lo, 1))))
    for f in sorted(os.listdir(outd)):
        if not f.endswith('.png'): continue
        im = Image.open(f'{outd}/{f}'); w, h = im.size
        if im.mode != 'RGB' or w != h or w > 2048 or (w & (w - 1)): bad.append((f, f'texture {w}x{h} {im.mode}'))
    if bad: raise SystemExit(f'specs KO : {bad}')
    return rows

# grain only on matte materials (raw steel, fabric covers). Paint, glass, chrome, printed banners stay clean.
MATTE = {'tent_usland': dict(grain=1.2, mottle=0.03), 'start_grate': dict(grain=2.5, mottle=0.05), 'start_gate': dict(grain=1.0, mottle=0.02),
         'start_gantry': dict(grain=1.2, mottle=0.025), 'finish_arch': dict(grain=1.0, mottle=0.025)}   # light: barely visible
def weather(img, seed=7, grain=4.0, mottle=0.06):
    """realistic surface: fine grain + large soft mottling (dust, wear). Palette squares are kept flat."""
    rg = np.random.default_rng(seed); a = np.array(img).astype(float); H, W = a.shape[:2]
    n = np.round(np.repeat(np.repeat(rg.normal(0, grain, (H // 2, W // 2, 1)), 2, 0), 2, 1) / 2) * 2   # 2 px grain, quantised (smaller files)
    low = np.array(Image.fromarray((rg.random((H // 64 + 2, W // 64 + 2)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)) / 255.0
    a = a * (1 - mottle / 2 + mottle * low[..., None]) + n
    a[H - 128:H - 64] = np.array(img).astype(float)[H - 128:H - 64]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

# materials: glossy paint / glass / carbon vs matte steel, fabric, rubber. spec = (base level, {palette name: level})
MATERIAL = {'tent_usland': (4, 0.3, 0.3, 0.3, 0.3), 'hospitality_usland': (50, 1, 1, 1, 1), 'pickup_usland': (24, 0.45, 0.6, 0.6, 0.6),   # v12b: less shiny (seen in game)
             'bike_trainer': (50, 1, 1, 1, 1),
            'start_gate': (16, 1, 0.35, 0.35, 0.35), 'start_grate': (16, 0.6, 0.35, 0.35, 0.35), 'finish_arch': (6, 0.5, 0.3, 0.3, 0.3),
            'start_gantry': (5, 0.5, 0.3, 0.3, 0.3), 'banner': (0, 0, 0, 0, 0)}
SPEC = {'pickup_usland': (120, {'tyre': 10, 'plastic': 25, 'dark': 30, 'bed': 15, 'hook': 60}),
        'hospitality_usland': (150, {'tyre': 10, 'rope': 20, 'char': 40, 'steel': 90}),
        'bike_trainer': (170, {'tyre': 10, 'black': 30, 'tan': 20, 'grey': 40}),
        'start_gate': (110, {'black': 50})}
def spec_map(name, img, pal):
    base, over = SPEC[name]; W, H = img.size
    sp = Image.new('RGB', (W, H), (base,) * 3); d = ImageDraw.Draw(sp)
    for nm, lvl in over.items():
        if nm in pal and pal[nm][0] == 'c':
            cx, cy = pal[nm][1]; d.rectangle([cx - 32, cy - 32, cx + 31, cy + 31], fill=(lvl,) * 3)
    return sp

# ------------------------------------------------------------------ main
def build(outd=OUTD):
    os.makedirs(outd, exist_ok=True); info = {}
    for name, tex, model in (('hospitality_usland', hospitality_texture, hospitality_model), ('pickup_usland', pickup_texture, pickup_model),
                             ('finish_arch', arch_texture, arch_model), ('start_grate', grate_texture, grate_model), ('start_gate', gate_texture, gate_model), ('bike_trainer', bike_texture, bike_model), ('tent_usland', tent_texture, tent_model),
                             ('start_gantry', gantry_texture, gantry_model)):
        img, pal = tex(); (weather(img, **MATTE[name]) if name in MATTE else img).save(f'{outd}/{name}.png', optimize=True)
        if name in SPEC: spec_map(name, img, pal).save(f'{outd}/{name}_spec.png', optimize=True)
        info[name] = model(pal).write(f'{outd}/{name}.jm', MATERIAL.get(name, (0, 0, 0, 0, 0)))
    for nm in BANNERS:
        img, pal = banner_texture(nm); img.save(f'{outd}/banner_{nm.lower()}.png', optimize=True)
    info['banner'] = banner_model(pal).write(f'{outd}/banner.jm', MATERIAL['banner'])
    check_specs(outd)
    return info

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else OUTD
    build(out)
    for name, nt, size in check_specs(out): print(f'{name:20s} {nt:6d} triangles  {size[0]:5.1f} x {size[1]:5.1f} x {size[2]:5.1f} ft (x, y, z)')
    print('specs OK')
