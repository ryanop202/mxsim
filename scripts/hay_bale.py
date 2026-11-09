"""Real-looking small square hay bale + hay wall (user: the yellow bale_paille bale "looks flat, like compacted hay: it should
look like a real hay bale, two strings around it across the width, more ruffled / fluffy"; also a ruffled "hay wall").
Made from scratch (doc 12: 1 unit = 1 ft, y up, origin on the ground, one texture per model, matte 0 0 0 0 0).

bale_hay.jm / .png / .shp : one bale, SAME size and frame as stt_props.bale() (long axis = local x, L 4.6, W 1.75 (z),
  H 1.6 ft, origin = ground under the centre, bottom sunk 0.22 ft). Shape: a lofted tube along x around a rounded y-z
  section, every vertex pushed along the section normal by: a low bulge on each face, compressed slices ("flakes", ~0.3 ft
  thick across the length, each a bit proud or sunk, a V crease between them), small noise (looser near the ends), and a
  pinch under the two twines; rounded fluffy ends (domed caps). Two orange polypropylene twines wrap the y-z section at
  x = +-L/4, slightly sunk in the hay (dark edge = the hay shadow). Loose straw: alpha cut-out cards (fringe along the
  edges, a few tufts on the faces), two-sided. Texture: thousands of drawn straw stems (shadow + body + highlight, 2x
  super-sampled) over dark crevices, flakes across the top, stems along the length on the sides, messy stems and cut straw
  ends on the end faces, golden / pale / grey-brown patches, baked shadow near the ground and beside the twines.
hay_wall.jm / .png / .shp : ~17 x 3.3 x 1.75 ft wall (long axis local x, origin ground centre): 2 rows of bales laid like
  bricks (4 bales below, 3 + two half bales above), each bale slightly different (length, offset, tiny yaw / roll, bulge),
  2 or 3 twines per bale, same ruffled look at lower resolution (hidden bottoms not built).
hay_block.jm / .png / .shp (v2, user: one straw wall, not stacked bales): ONE monolithic block 8.5 x 4.9 (above the ground) x
  2.0 ft, origin ground centre, built like bale_hay (bulging faces, ~0.4 ft compressed layers, fringe + tufts), only two twines
  at x = -1.2 / +1.2 ft round the y-z section; 2048 atlas; collision 3 rows of spheres (y 0.9, 2.6, 3.9).
Collision: stt_props.BALE_SHP values (firm: r 0.9, every 1.0 ft, spring 150, damping 8, friction 0.6); the wall has 2 rows.
Run: python scripts/hay_bale.py [--preview]  -> assets/props/ (+ ../apercus_sgm/hay_3d.png with --preview)"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, map_coordinates
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
from props_usland import Mesh, OUTD
import stt_props as SP

BALE = dict(L=SP.BALE['L'], W=SP.BALE['W'], H=SP.BALE['H'], sink=SP.BALE['sink'], r=0.22, px=150)
WALL = dict(L=17.0, W=1.75, bh=1.72, sink=0.10, sit=0.04, r=0.2, px=128)    # 2 x 1.72 - 0.10 - 0.04 = 3.30 ft high
SHP = dict(SP.BALE_SHP, spring=270, damping=18)   # v33 (user): harder to ride through (Saint-Thibery bales: 150 / 8)
TW = dict(w=0.085, lift=0.018, edge=0.004, pinch=0.05, pinch_w=0.07)    # twine ribbon width (incl. dark hay-shadow edges)
MAT = (0, 0, 0, 0, 0)
TEX = 1024
# v2 (user: "un mur de paille, pas plusieurs ballots empilés"): ONE monolithic straw block, half the wall, one bale taller,
# only two twines near the middle. H includes the sunk part: 5.0 - 0.1 = 4.9 ft above the ground.
BLOCK = dict(L=8.5, W=2.0, H=5.0, sink=0.1, r=0.25, px=140, twines=(-1.2, 1.2), tex=2048)

CREV = (70, 50, 24)                                                               # dark gaps between the stems
DEEP = [(150, 118, 62), (165, 130, 70), (140, 112, 60), (172, 140, 78), (150, 126, 80)]
MID = [(214, 172, 88), (224, 184, 98), (204, 164, 84), (232, 196, 112), (196, 160, 90), (220, 188, 118), (186, 160, 104)]
GOLD = (204, 168, 92)                                                             # mean colour (bale_paille: 208 174 95)
TOP = [(244, 214, 138), (250, 228, 166), (238, 202, 118), (230, 194, 108), (214, 192, 140), (246, 222, 156), (200, 172, 112)]


# ------------------------------------------------------------------ texture painting
def _smooth_noise(shape, sigma, rg, mode='wrap'):
    n = gaussian_filter(rg.normal(0, 1, shape), sigma, mode=mode); return n / (n.std() + 1e-9)

def _stems(d, rg, n, W2, H2, ang_fn, Lm, wr, cols, shadow, sc, root=None):
    """n straw stems: soft cast shadow, coloured body, thin highlight on one side; slightly bent 3-segment polylines."""
    if n <= 0: return
    if root is None: x, y = rg.uniform(0, W2, n), rg.uniform(0, H2, n)
    else: x, y = root(n)
    a = ang_fn(x, y); L = Lm * rg.uniform(0.45, 1.6, n); w = rg.integers(wr[0], wr[1] + 1, n)
    bend = rg.normal(0, 0.10, n); ci = rg.integers(0, len(cols), n); br = rg.uniform(0.88, 1.1, n)
    for k in range(n):
        px_, py_, ang = x[k], y[k], a[k]; pts = [(px_, py_)]
        for _ in range(3):
            ang += bend[k]; px_ += L[k] / 3 * np.cos(ang); py_ += L[k] / 3 * np.sin(ang); pts.append((px_, py_))
        c = tuple(int(min(255, v * br[k])) for v in cols[ci[k]])
        if shadow: d.line([(p + 1.0 * sc, q + 1.5 * sc) for p, q in pts], fill=(30, 20, 8, shadow), width=int(w[k] + sc))
        d.line(pts, fill=c + (255,), width=int(w[k]))
        ox, oy = -np.sin(a[k]) * w[k] * 0.28, np.cos(a[k]) * w[k] * 0.28
        hl = tuple(int(min(255, v * 1.16 + 10)) for v in c)
        d.line([(p - ox, q - oy) for p, q in pts], fill=hl + (170,), width=max(1, int(w[k]) // 3))

def paint_hay(h, w, px_ft, seed, ang_fn, cover=(1.7, 1.3, 0.55), crev=None, cut_ends=0, sc=2):
    """(h, w, 3) float straw surface: dark crevice base, deep / mid stem layers, optional crevice mask (flake gaps), top layer."""
    rg = np.random.default_rng(seed); H2, W2 = h * sc, w * sc
    nz = _smooth_noise((H2, W2), 3 * sc, rg)
    base = np.array(CREV, float)[None, None] * (1 + 0.3 * nz[..., None])
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im, 'RGBA')
    Lm = 0.27 * px_ft * sc; wm = 2.25 * sc
    cnt = lambda c: int(c * H2 * W2 / (Lm * wm))
    _stems(d, rg, cnt(cover[0]), W2, H2, ang_fn, Lm, (int(1.5 * sc), int(3 * sc)), DEEP, 0, sc)
    _stems(d, rg, cnt(cover[1]), W2, H2, ang_fn, Lm, (int(1.5 * sc), int(3 * sc)), MID, 60, sc)
    if crev is not None:
        a = np.asarray(im).astype(float); m = crev(H2, W2)[..., None]
        a = a * (1 - m) + np.array(CREV, float) * 0.85 * m
        im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im, 'RGBA')
    _stems(d, rg, cnt(cover[2]), W2, H2, ang_fn, Lm, (int(1.5 * sc), int(2.5 * sc)), TOP, 90, sc)
    if cut_ends:                                                      # cut stems seen end-on: pale ring, dark hollow
        xs, ys = rg.uniform(0, W2, cut_ends), rg.uniform(0, H2, cut_ends); rr = rg.uniform(1.2, 2.6, cut_ends) * sc
        for x, y, r in zip(xs, ys, rr):
            e = rg.uniform(0.6, 1.0); c = TOP[rg.integers(len(TOP))]
            d.ellipse([x - r, y - r * e, x + r, y + r * e], fill=(120, 92, 48, 255), outline=c + (255,), width=max(1, int(r * 0.6)))
    a = np.asarray(im).astype(float)
    return a.reshape(h, sc, w, sc, 3).mean((1, 3))

def variation(arr, px_ft, rg):
    """golden / pale / grey-brown patches + fine grain."""
    h, w = arr.shape[:2]
    n1 = _smooth_noise((h, w), 0.45 * px_ft, rg); n2 = _smooth_noise((h, w), 0.3 * px_ft, rg); n3 = _smooth_noise((h, w), 0.08 * px_ft, rg)
    arr = arr * (1 + 0.11 * n1 + 0.10 * n3)[..., None]   # v33 (user): more texture (v28 0.06 / 0.04)
    pale = np.clip(n1 - 0.6, 0, 1)[..., None] * 0.35; grey = np.clip(n2 - 0.8, 0, 1)[..., None] * 0.4
    lum = arr.mean(2, keepdims=True)
    arr = arr * (1 - pale) + (arr * 0.6 + np.array([250, 236, 190.0]) * 0.4) * pale
    arr = arr * (1 - grey) + (lum * np.array([0.95, 0.88, 0.72])) * grey
    arr = arr * (np.array(GOLD) / arr.reshape(-1, 3).mean(0))[None, None]   # same mean golden colour as bale_paille (far view)
    return arr + rg.normal(0, 6.5, arr.shape)

def strip_texture(h, w, px_ft, seed, ny_row, ao_row, bnd_px=(), twine_px=(), crease=1.0):
    """the unrolled tube (u = along x, v = around the section). ny_row: section normal y per image row (top = 1);
    bnd_px: flake gaps (image columns) matching the geometry, or random every ~flake_px ft if empty; twine_px: baked shadow."""
    rg = np.random.default_rng(seed)
    wt = np.clip(ny_row, 0, 1) ** 2; wb = np.clip(-ny_row, 0, 1) ** 2
    if not len(bnd_px):
        b, bl = [], rg.uniform(0, 0.3) * px_ft
        while bl < w: b.append(bl); bl += rg.uniform(0.27, 0.42) * px_ft
        bnd_px = b
    def ang(x, y):
        r = np.clip((y / 2).astype(int), 0, h - 1); u = rg.random(len(x))
        top = u < wt[r]; bot = (~top) & (u < wt[r] + wb[r])
        a = np.where(rg.random(len(x)) < 0.75, rg.normal(0, 0.3, len(x)), np.pi / 2 + rg.normal(0, 0.5, len(x)))   # sides
        a = np.where(top, np.pi / 2 + rg.normal(0, 0.33, len(x)), a)                                                  # flakes across
        return np.where(bot, rg.uniform(0, np.pi, len(x)), a) + np.where(rg.random(len(x)) < 0.5, 0, np.pi)
    strength = (0.2 + 0.7 * wt + 0.15 * np.clip(1 - np.abs(ny_row) * 1.4, 0, 1)) * crease   # top creases strongest
    cr = [(b, _smooth_noise((h,), 7, rg) * 2.5, 1.3 + 1.8 * np.abs(_smooth_noise((h,), 5, rg)), rg.uniform(0.65, 1.0)) for b in bnd_px]
    def crev(H2, W2):                                                    # gap between two flakes (under the top stems)
        X = np.arange(W2)[None, :]; m = np.zeros((H2, W2))
        for b, wig, wid, k in cr:
            s = np.repeat(strength * k, 2); c = b * 2 + np.repeat(wig, 2) * 2; ww = np.repeat(wid, 2) * 2
            m = np.maximum(m, s[:, None] * np.exp(-((X - c[:, None]) / ww[:, None]) ** 2))
        return np.clip(m, 0, 0.92)
    arr = paint_hay(h, w, px_ft, seed + 1, ang, crev=crev)
    X = np.arange(w)[None, :]; sh = np.zeros((h, w))                     # shadow in the gap + flake edges rolling into it
    for b, wig, wid, k in cr:
        dx = X - (b + wig[:, None]); s = (strength * k)[:, None]
        sh = np.maximum(sh, s * (0.55 * np.exp(-(dx / (wid[:, None] * 0.9)) ** 2) + 0.22 * np.exp(-(dx / (0.05 * px_ft)) ** 2)))
    arr = arr * (1 - np.clip(sh, 0, 0.75))[..., None]
    edges = np.r_[0, np.sort(np.asarray(bnd_px, float)), w]            # per-flake tone (some slices paler / browner)
    tone = np.ones(w)
    for a_, b_ in zip(edges[:-1], edges[1:]): tone[int(max(a_, 0)):int(min(b_, w))] = rg.uniform(0.86, 1.1)
    arr = arr * tone[None, :, None]
    arr = variation(arr, px_ft, rg)
    arr = arr * ao_row[:, None, None]
    U = np.arange(w)
    for t in twine_px: arr = arr * (1 - 0.38 * np.exp(-((U - t) / (0.075 * px_ft)) ** 2))[None, :, None]
    return arr

def end_texture(h, w, px_ft, seed, ao_rows):
    rg = np.random.default_rng(seed)
    arr = paint_hay(h, w, px_ft, seed + 1, lambda x, y: rg.uniform(0, 2 * np.pi, len(x)), cover=(1.3, 0.95, 0.55),
                    cut_ends=int(h * w / 160))
    arr = variation(arr, px_ft, rg)
    return arr * ao_rows[:, None, None]

def twine_texture(h, w, seed):
    """orange polypropylene twine along the image x: dark hay-shadow edge rows, twisted orange core, highlight."""
    rg = np.random.default_rng(seed); Y, X = np.mgrid[0:h, 0:w].astype(float)
    t = np.abs(Y - (h - 1) / 2) / (h / 2)                                  # 0 centre .. 1 edge
    core = t < 0.62
    tw = 0.78 + 0.22 * np.sin(2 * np.pi * (X + Y * 0.9) / 6.0)
    orange = np.array([228, 104, 26.0]) * (tw * (1.08 - 0.4 * t ** 2))[..., None]
    orange = orange * (1 + 0.06 * _smooth_noise((h, w), (1, 30), rg))[..., None]
    shadow = np.array([46, 32, 16.0]) * (0.9 + 0.2 * rg.random((h, w)))[..., None]
    a = np.where(core[..., None], orange, shadow)
    fuzz = (~core) & (rg.random((h, w)) < 0.12)                            # a few frayed fibres
    a[fuzz] = np.array([200, 96, 30.0])
    return a

def sprite(w, h, seed, kind, sc=2):
    """RGBA loose-straw sprite, root along the bottom edge; alpha cut-out (0 / 255)."""
    rg = np.random.default_rng(seed); W2, H2 = w * sc, h * sc
    im = Image.new('RGBA', (W2, H2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if kind == 'fringe':
        n = int(w / 2.2); x = rg.uniform(0.02, 0.98, n) * W2; y = np.full(n, H2 - 1.0)
        a = -np.pi / 2 + rg.normal(0, 0.8, n); L = rg.uniform(0.25, 1.0, n) ** 0.7 * H2 * 1.05
    else:
        n = 46; x = W2 / 2 + rg.normal(0, 0.08, n) * W2; y = np.full(n, H2 - 1.0)
        a = -np.pi / 2 + rg.normal(0, 0.5, n); L = rg.uniform(0.35, 1.0, n) * H2 * 0.98
    order = np.argsort(rg.random(n))
    for k in order:
        bend = rg.normal(0, 0.12); px_, py_, ang = x[k], y[k], a[k]; pts = [(px_, py_)]
        for _ in range(3):
            ang += bend; px_ += L[k] / 3 * np.cos(ang); py_ += L[k] / 3 * np.sin(ang); pts.append((px_, py_))
        wd = int(rg.integers(2, 4)) * sc // 2 + 1; c = (MID + TOP)[rg.integers(len(MID) + len(TOP))]
        d.line(pts, fill=(120, 92, 48, 255), width=wd + 2)
        d.line(pts, fill=c + (255,), width=wd)
    if kind == 'fringe':                                                  # root band: stems lying along the edge
        for _ in range(int(w * 0.8)):
            x0 = rg.uniform(0, W2); y0 = H2 - rg.uniform(0, 0.16) * H2; L = rg.uniform(10, 40) * sc; aa = rg.normal(0, 0.25) + (0 if rg.random() < .5 else np.pi)
            c = MID[rg.integers(len(MID))]
            d.line([(x0, y0), (x0 + L * np.cos(aa), y0 + L * np.sin(aa))], fill=c + (255,), width=sc + 1)
    A = np.asarray(im).astype(float).reshape(h, sc, w, sc, 4)
    al = A[..., 3].mean((1, 3)) / 255
    rgb = (A[..., :3] * A[..., 3:4]).sum((1, 3)) / (A[..., 3:4].sum((1, 3)) + 1e-6)
    rgb[al < 0.05] = (196, 160, 90)                                       # straw colour under the cut-out (no dark mip halo)
    return np.dstack([rgb, np.where(al >= 0.42, 255.0, 0.0)])


# ------------------------------------------------------------------ geometry
class HMesh:
    """triangles on shared positions (smooth area-weighted normals, UV seams allowed) + explicit-normal extras."""
    def __init__(self, W, H):
        self.W, self.H = W, H; self.P = []; self.T = []; self.X = []
    def uv(self, px, py): return (px / self.W, 1.0 - py / self.H)
    def pt(self, p): self.P.append(np.asarray(p, float)); return len(self.P) - 1
    def tri(self, ids, uvs, out):
        a, b, c = (self.P[i] for i in ids)
        if np.dot(np.cross(b - a, c - a), out) < 0: ids, uvs = ids[::-1], uvs[::-1]
        self.T.append((tuple(ids), tuple(uvs)))
    def quad(self, ids, uvs, out):
        self.tri([ids[0], ids[1], ids[2]], [uvs[0], uvs[1], uvs[2]], out); self.tri([ids[0], ids[2], ids[3]], [uvs[0], uvs[2], uvs[3]], out)
    def raw(self, P, N, UV, two_sided=False):
        """explicit vertices (polygon fan); front = side of the mean normal; two_sided adds the back (same normals)."""
        P = [np.asarray(p, float) for p in P]
        if np.dot(np.cross(P[1] - P[0], P[2] - P[0]), sum(np.asarray(n, float) for n in N)) < 0: P, N, UV = P[::-1], N[::-1], UV[::-1]
        for k in range(1, len(P) - 1):
            self.X.append(([P[0], P[k], P[k + 1]], [N[0], N[k], N[k + 1]], [UV[0], UV[k], UV[k + 1]]))
            if two_sided: self.X.append(([P[0], P[k + 1], P[k]], [N[0], N[k + 1], N[k]], [UV[0], UV[k + 1], UV[k]]))
    def to_mesh(self):
        m = Mesh(self.W, self.H); P = np.array(self.P); N = np.zeros_like(P)
        for ids, _ in self.T:
            a, b, c = P[list(ids)]; n = np.cross(b - a, c - a)
            for i in ids: N[i] += n
        N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
        key = {}
        for ids, uvs in self.T:
            for i, t in zip(ids, uvs):
                k = (i, round(t[0], 6), round(t[1], 6))
                if k not in key: key[k] = len(m.V); m.V.append((*P[i], *N[i], *t))
                m.I.append(key[k])
        for Ps, Ns, UVs in self.X:
            for p, n, t in zip(Ps, Ns, UVs):
                n = np.asarray(n, float); n = n / np.linalg.norm(n); m.I.append(len(m.V)); m.V.append((*p, *n, *t))
        return m

def section(hz, hy, r, nb, nc, ns, nt, open_bottom=False, bot_bit=0.1):
    """rounded y-z section, bottom centre -> +z side -> top -> -z side; returns arrays z, y, nz, ny, face, tf, s, P (perimeter)."""
    pts = []; cz, cy = hz - r, hy - r
    def line(z0, y0, z1, y1, n, face, nz, ny, tf):
        for k in range(n):
            t = k / n; z, y = z0 + (z1 - z0) * t, y0 + (y1 - y0) * t; pts.append((z, y, nz, ny, face, tf(z, y)))
    def arc(cx, cy_, a0, a1, n):
        for k in range(n):
            a = np.radians(a0 + (a1 - a0) * k / n); pts.append((cx + r * np.cos(a), cy_ + r * np.sin(a), np.cos(a), np.sin(a), 3, 1.0))
    tz = lambda z, y: z / cz; ty = lambda z, y: y / cy
    if open_bottom: line(cz - bot_bit, -hy, cz, -hy, 1, 0, 0, -1, tz)
    else: line(0, -hy, cz, -hy, nb, 0, 0, -1, tz)
    arc(cz, -cy, -90, 0, nc); line(hz, -cy, hz, cy, ns, 1, 1, 0, ty)
    arc(cz, cy, 0, 90, nc); line(cz, hy, -cz, hy, nt, 2, 0, 1, tz)
    arc(-cz, cy, 90, 180, nc); line(-hz, cy, -hz, -cy, ns, 1, -1, 0, ty)
    arc(-cz, -cy, 180, 270, nc)
    if open_bottom: line(-cz, -hy, -cz + bot_bit, -hy, 1, 0, 0, -1, tz); pts.append((-cz + bot_bit, -hy, 0, -1, 0, -1.0))
    else: line(-cz, -hy, 0, -hy, nb, 0, 0, -1, tz)
    A = np.array(pts, float); z, y = A[:, 0], A[:, 1]
    seg = np.hypot(np.diff(z), np.diff(y)); s = np.r_[0, np.cumsum(seg)]
    P = s[-1] + (0 if open_bottom else np.hypot(z[0] - z[-1], y[0] - y[-1]))
    return dict(z=z, y=y, nz=A[:, 2], ny=A[:, 3], face=A[:, 4].astype(int), tf=A[:, 5], s=s, P=P, closed=not open_bottom)

def rot(yaw, roll):
    cy, sy, cr, sr = np.cos(yaw), np.sin(yaw), np.cos(roll), np.sin(roll)
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]); Rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    return Ry @ Rx

HI = dict(nb=2, nc=4, ns=4, nt=4, ends=[(0.16, 0.0), (0.06, -0.035), (0.0, -0.11)], cap=(0.74, 0.46, 0.2), flakes=True,
          interior=None, tw_nb=0.09, tent=True, noise=0.013, flake_amp=0.022, bulge=0.05, cards=1.0, tufts=7)
BQ = dict(HI, nb=1, nc=3, ns=5, nt=3, bulge=0.09, tufts=10, flake=(0.34, 0.46))   # big block: thicker layers (triangle budget)
LO = dict(nb=1, nc=2, ns=2, nt=2, ends=[(0.14, 0.0), (0.0, -0.08)], cap=(0.5,), flakes=False,
          interior=0.75, tw_nb=None, tent=False, noise=0.012, flake_amp=0.0, bulge=0.045, cards=0.55, tufts=1)

def bale_geo(hm, spec, Q):
    """one bale into hm. spec: L W H r seed centre(box centre, world) yaw roll twines open caps(-x,+x: 'full'|'fan')
    strip=(px0, py0, px_ft, margin, flip) end_uv=[(px0, py0), (..)] twine_uv=(px0, py0, h) spr=dict(fringe=[rects], tuft=[rects])
    cardmask(x, j)->bool; Q = HI / LO resolution. Returns the local surface grid info (for the shapes)."""
    L, W, H, r = spec['L'], spec['W'], spec['H'], spec['r']; hx, hz, hy = L / 2, W / 2, H / 2
    rg = np.random.default_rng(spec['seed']); R = rot(spec.get('yaw', 0), spec.get('roll', 0)); C = np.asarray(spec['centre'], float)
    S = section(hz, hy, r, Q['nb'], Q['nc'], Q['ns'], Q['nt'], open_bottom=spec.get('open', False))
    nr = len(S['z']); tw_x = list(spec['twines'])
    # stations along x: (x, inset, kind, boundary index)
    st = []
    for sg in (-1, 1):
        for e, ins in Q['ends']: st.append((sg * (hx - e), ins, 'e', -1))
    bnd = []
    if Q['flakes']:
        b = -hx + 0.16 + rg.uniform(0.18, 0.3); fl = Q.get('flake', (0.26, 0.36))
        while b < hx - 0.3:
            if all(abs(b - t) > 0.07 for t in tw_x): bnd.append(b)
            b += rg.uniform(*fl)
        prev = -hx + 0.16
        for i, b in enumerate(bnd):
            st.append((b, 0.0, 'b', i)); st.append(((prev + b) / 2, 0.0, 'm', -1)); prev = b
        st.append(((prev + hx - 0.16) / 2, 0.0, 'm', -1))
    else:
        n = max(1, int(round((L - 0.3) / Q['interior'])))
        for k in range(1, n): st.append((-hx + 0.14 + (L - 0.28) * k / n, 0.0, 'm', -1))
    for t in tw_x:
        st.append((t, 0.0, 't', -1))
        if Q['tw_nb']: st += [(t - Q['tw_nb'], 0.0, 'm', -1), (t + Q['tw_nb'], 0.0, 'm', -1)]
    pri = {'t': 0, 'e': 1, 'b': 2, 'm': 3}; keep = []
    for s_ in sorted(st, key=lambda q: pri[q[2]]):
        if all(abs(s_[0] - k[0]) > 0.045 for k in keep): keep.append(s_)
    st = sorted(keep, key=lambda q: q[0]); xs = np.array([q[0] for q in st])
    # displacement field
    NG = _smooth_noise((int((L + 1) / 0.05), int(S['P'] / 0.05) + 2), 1.6, rg)
    def noise(x, s): return map_coordinates(NG, [np.full_like(s, (x + hx + 0.5) / 0.05), s / 0.05], order=1, mode='wrap')
    foff = rg.normal(0, Q['flake_amp'], len(bnd) + 1); ftilt = rg.normal(0, 1, len(bnd) + 1); gdep = rg.uniform(0.03, 0.06, len(bnd))
    bul = np.array([0.0, Q['bulge'] * rg.uniform(0.7, 1.3), Q['bulge'] * rg.uniform(0.6, 1.1), 0.0])[S['face']]
    gfac = np.array([0.15, 0.7, 1.0, 1.0])[S['face']]
    ang_s = 2 * np.pi * S['s'] / S['P']
    def disp(x, kind, bi):
        xr = min(abs(x) / hx, 1.0)
        d = bul * (1 - S['tf'] ** 2) * (1 - xr ** 4)
        if Q['flakes']:
            k = int(np.searchsorted(bnd, x))
            if kind == 'b': d = d + ((foff[bi] + foff[bi + 1]) / 2 - gdep[bi]) * gfac
            else: d = d + (foff[k] + 0.012 * ftilt[k] * np.sin(ang_s + ftilt[k])) * gfac
        for t in tw_x: d = d - TW['pinch'] * np.exp(-((x - t) / TW['pinch_w']) ** 2) * np.where(S['face'] == 0, 0.3, 1.0)
        d = d + Q['noise'] * noise(x, S['s']) * (1 + 2.0 * xr ** 8) * np.where(S['face'] == 3, 1.8, 1.0)
        return d * np.where(S['face'] == 0, 0.3, 1.0)
    G = np.zeros((len(st), nr, 3))
    for i, (x, ins, kind, bi) in enumerate(st):
        d = disp(x, kind, bi) + ins
        xx = x + (0.018 * noise(x * 1.7, S['s'] * 1.3) if kind == 'e' and ins < -0.05 else 0)
        G[i] = np.stack([np.broadcast_to(xx, S['z'].shape), S['y'] + S['ny'] * d, S['z'] + S['nz'] * d], 1)
    W_ = lambda p: C + R @ p
    ids = [[hm.pt(W_(G[i, j])) for j in range(nr)] for i in range(len(st))]
    px0, py0, pf, mg, flip = spec['strip']
    def suv(x, s):
        u = (hx - x if flip else x + hx) + mg
        return hm.uv(px0 + u * pf, py0 + s * pf)
    segs = [(j, j + 1, S['s'][j], S['s'][j + 1]) for j in range(nr - 1)]
    if S['closed']: segs.append((nr - 1, 0, S['s'][-1], S['P']))
    for i in range(len(st) - 1):
        for j0, j1, s0, s1 in segs:
            out = R @ np.array([0, S['ny'][j0] + S['ny'][j1], S['nz'][j0] + S['nz'][j1]])
            hm.quad([ids[i][j0], ids[i + 1][j0], ids[i + 1][j1], ids[i][j1]],
                    [suv(xs[i], s0), suv(xs[i + 1], s0), suv(xs[i + 1], s1), suv(xs[i], s1)], out)
    # end caps (domed, fluffy)
    ring_ids = list(range(nr))
    for side, kind in zip((-1, 1), spec['caps']):
        i_end = 0 if side < 0 else len(st) - 1; E = G[i_end]; ex0, ey0 = spec['end_uv'][(0 if side < 0 else 1) % len(spec['end_uv'])]
        cen = np.array([side * (hx + 0.06 * rg.uniform(0.6, 1.3)), E[:, 1].mean() * 0.5, 0.0])
        def euv(p, ex0=ex0, ey0=ey0, side=side):
            zz = (p[2] + hz) if side > 0 else (hz - p[2])
            return hm.uv(ex0 + np.clip(zz, 0, W) * pf, ey0 + np.clip(hy - p[1], 0, H) * pf)
        outv = R @ np.array([side, 0, 0.0])
        rings = [[ids[i_end][j] for j in ring_ids]]; rpts = [E]
        fs = Q['cap'] if kind == 'full' else ()
        for f in fs:
            P_ = cen + (E - cen) * f
            P_[:, 0] = side * (hx + (cen[0] * side - hx) * (1 - f ** 2)) + side * 0.02 * rg.normal(0, 1, nr) * f
            P_[:, 1:] += rg.normal(0, 0.012, (nr, 2))
            rings.append([hm.pt(W_(p)) for p in P_]); rpts.append(P_)
        c_id = hm.pt(W_(cen))
        for k in range(len(rings) - 1):
            for j in range(nr):
                j2 = (j + 1) % nr
                hm.quad([rings[k][j], rings[k + 1][j], rings[k + 1][j2], rings[k][j2]],
                        [euv(rpts[k][j]), euv(rpts[k + 1][j]), euv(rpts[k + 1][j2]), euv(rpts[k][j2])], outv)
        for j in range(nr):
            j2 = (j + 1) % nr
            hm.tri([rings[-1][j], c_id, rings[-1][j2]], [euv(rpts[-1][j]), euv(cen), euv(rpts[-1][j2])], outv)
    # twines: tent ribbon over the pinched surface, dark edges = shadow in the hay
    def surf(x, j):
        i = int(np.clip(np.searchsorted(xs, x) - 1, 0, len(xs) - 2)); t = (x - xs[i]) / (xs[i + 1] - xs[i])
        return G[i, j] * (1 - t) + G[i + 1, j] * t
    tx0, ty0, th = spec['twine_uv']
    tsegs = [(j, j + 1, S['s'][j], S['s'][j + 1]) for j in range(nr - 1)] + ([(nr - 1, 0, S['s'][-1], S['P'])] if S['closed'] else [])
    for t in tw_x:
        for j0, j1, s0, s1 in tsegs:
            pts = {}
            for j, s_ in ((j0, s0), (j1, s1)):
                n = np.array([0, S['ny'][j], S['nz'][j]])
                pts[j] = (W_(surf(t - TW['w'] / 2, j) + n * TW['edge']), W_(surf(t, j) + n * TW['lift']), W_(surf(t + TW['w'] / 2, j) + n * TW['edge']), R @ n, s_)
            (a0, c0, b0, n0, s0_), (a1, c1, b1, n1, s1_) = pts[j0], pts[j1]
            ex = R @ np.array([1.0, 0, 0])
            uvf = lambda row, s_: hm.uv(tx0 + s_ * pf, ty0 + row)
            if Q['tent']:
                hm.raw([a0, c0, c1, a1], [n0 - 0.4 * ex, n0, n1, n1 - 0.4 * ex], [uvf(0, s0_), uvf(th / 2, s0_), uvf(th / 2, s1_), uvf(0, s1_)])
                hm.raw([c0, b0, b1, c1], [n0, n0 + 0.4 * ex, n1 + 0.4 * ex, n1], [uvf(th / 2, s0_), uvf(th, s0_), uvf(th, s1_), uvf(th / 2, s1_)])
            else:
                lift0, lift1 = (c0 - (a0 + b0) / 2) * 0.6, (c1 - (a1 + b1) / 2) * 0.6
                hm.raw([a0 + lift0, b0 + lift0, b1 + lift1, a1 + lift1], [n0, n0, n1, n1], [uvf(0, s0_), uvf(th, s0_), uvf(th, s1_), uvf(0, s1_)])
    # loose straw: fringe cards along the exposed edges, tufts on the faces
    spr = spec['spr']; cm = spec.get('cardmask', lambda x, j: True)
    def card(base, e_dir, up, wd, ht, rect, nrm):
        e_dir = e_dir / np.linalg.norm(e_dir); up = up / np.linalg.norm(up)
        a, b = base - e_dir * wd / 2, base + e_dir * wd / 2
        P_ = [W_(a), W_(b), W_(b + up * ht), W_(a + up * ht)]
        x0, y0, x1, y1 = rect; nn = R @ (nrm / np.linalg.norm(nrm))
        hm.raw(P_, [nn] * 4, [hm.uv(x0, y1), hm.uv(x1, y1), hm.uv(x1, y0), hm.uv(x0, y0)], two_sided=True)
    corners = [j for j in range(nr) if S['face'][j] == 3 and S['ny'][j] > 0.3 and S['ny'][j] < 0.95]   # top long edges
    cz_top = [j for j in corners if abs(S['nz'][j]) > 0.3]
    for sgz in (1, -1):
        js = [j for j in cz_top if np.sign(S['nz'][j]) == sgz]
        if not js: continue
        x = -hx + 0.25 + rg.uniform(0, 0.2)
        while x < hx - 0.3:
            wd = rg.uniform(0.45, 0.75) * (1 if Q['cards'] >= 1 else 1.4)
            xc = x + wd / 2
            if all(abs(xc - t) > 0.15 for t in tw_x) and rg.random() < Q['cards'] and cm(xc, sgz):
                j = js[rg.integers(len(js))]; n = np.array([0, S['ny'][j], S['nz'][j]])
                up = n + np.array([rg.normal(0, 0.2), -0.1, 0]) + rg.normal(0, 0.15, 3)
                base = surf(xc, j) - n * 0.035
                e_dir = np.array([1.0, 0, 0]) + np.array([0, 0, rg.normal(0, 0.08)])
                card(base, e_dir, up, wd, rg.uniform(0.1, 0.18), spr['fringe'][rg.integers(len(spr['fringe']))], n + np.array([0, 0.5, 0]))
            x += wd * rg.uniform(0.85, 1.1)
    for side, kind in zip((-1, 1), spec['caps']):                         # around the exposed end rims (not the sunk bottom)
        if kind != 'full': continue
        i_end = 0 if side < 0 else len(st) - 1; E = G[i_end]
        j = 0; acc = 0.0
        order = [jj for jj in range(nr) if S['y'][jj] > -hy + r * 0.8 + spec.get('rim_min', 0)]
        for jj in order[::max(1, int(round(0.42 / (S['P'] / nr))))]:
            if rg.random() > Q['cards']: continue
            n = np.array([0, S['ny'][jj], S['nz'][jj]]); tang = np.array([0, -S['nz'][jj], S['ny'][jj]])
            up = n * 0.75 + np.array([side * 0.75, 0, 0]) + rg.normal(0, 0.15, 3)
            base = E[jj] - n * 0.03 - np.array([side * 0.03, 0, 0])
            card(base, tang, up, rg.uniform(0.35, 0.55), rg.uniform(0.1, 0.2), spr['fringe'][rg.integers(len(spr['fringe']))], n + np.array([side * 0.6, 0.4, 0]))
    nt_ = Q['tufts']
    for _ in range(nt_):                                                  # tufts stuck in the top / sides
        for _try in range(20):
            x = rg.uniform(-hx + 0.3, hx - 0.3); j = rg.integers(nr)
            if S['ny'][j] > -0.2 and S['y'][j] > -hy + 0.45 and all(abs(x - t) > 0.15 for t in tw_x) and cm(x, int(np.sign(S['nz'][j]) or 0)): break
        n = np.array([0, S['ny'][j], S['nz'][j]]); tg = rg.normal(0, 1, 3); tg -= n * np.dot(tg, n); tg /= np.linalg.norm(tg)
        up = n * 0.45 + tg * 0.9                                         # loose straw lying on the bale, half raised
        base = surf(x, j) - n * 0.03; ht = rg.uniform(0.14, 0.24); rect = spr['tuft'][rg.integers(len(spr['tuft']))]
        a0 = rg.uniform(0, np.pi)
        for a in (a0, a0 + np.pi / 2):
            e = np.array([np.cos(a), 0, np.sin(a)]); e = e - up * np.dot(e, up) / np.dot(up, up)
            card(base, e, up, ht * 1.0, ht, rect, n + np.array([0, 0.6, 0]))
    return dict(xs=xs, G=G, S=S, bnd=bnd)


# ------------------------------------------------------------------ atlases
def put(img, arr, x0, y0):
    h, w = arr.shape[:2]; img[y0:y0 + h, x0:x0 + w, :arr.shape[2]] = arr
    if arr.shape[2] == 3: img[y0:y0 + h, x0:x0 + w, 3] = 255

def row_ao(hy, sink, s_rows_y, strength=0.45, reach=0.4):
    """baked shadow by height above the ground (or above the bale under it)."""
    hgt = s_rows_y + hy - sink
    return 1 - strength * (1 - np.clip(hgt / reach, 0, 1)) ** 1.5

def section_rows(S, pf, h):
    """section normal y and local y per image row of the strip (row = s * pf)."""
    s = (np.arange(h) + 0.5) / pf
    ss = np.r_[S['s'], S['P']]; ny = np.r_[S['ny'], S['ny'][0]]; y = np.r_[S['y'], S['y'][0]]
    return np.interp(s, ss, ny), np.interp(s, ss, y)

def sprites_into(img, x0, y0, w, seed, fh=96, ts=None):
    """two fringe strips (w x fh) and two tufts (ts x ts) stacked from (x0, y0); returns rects."""
    out = dict(fringe=[], tuft=[]); y = y0
    for k in range(2):
        a = sprite(w, fh, seed + k, 'fringe'); put(img, a, x0, y); out['fringe'].append((x0 + 1, y + 1, x0 + w - 1, y + fh - 1)); y += fh + 4
    tw_ = ts or (w - 8) // 2
    for k in range(2):
        a = sprite(tw_, tw_, seed + 10 + k, 'tuft'); xx = x0 + k * (tw_ + 8); put(img, a, xx, y); out['tuft'].append((xx + 1, y + 1, xx + tw_ - 1, y + tw_ - 1))
    return out, y + tw_

def bale_hay():
    B, Q = BALE, HI; pf = B['px']; mg = 0.15
    img = np.zeros((TEX, TEX, 4)); img[..., :3] = (150, 120, 70); img[..., 3] = 255
    Lp = int(np.ceil((B['L'] + 2 * mg) * pf))
    tw_x = [-B['L'] / 4, B['L'] / 4]
    spec = dict(L=B['L'], W=B['W'], H=B['H'], r=B['r'], seed=11, centre=(0, B['H'] / 2 - B['sink'], 0), twines=tw_x,
                caps=('full', 'full'), strip=(0, 0, pf, mg, False), end_uv=[(Lp + 10, 0), (Lp + 10, int(B['H'] * pf) + 8)],
                twine_uv=(0, 1000, 16), rim_min=B['sink'] * 0.6)
    S = section(B['W'] / 2, B['H'] / 2, B['r'], Q['nb'], Q['nc'], Q['ns'], Q['nt'])
    Hs = int(np.ceil(S['P'] * pf)) + 2
    sw = TEX - Lp - 14
    spr, _ = sprites_into(img, Lp + 10, 2 * int(B['H'] * pf) + 20, sw, 70)
    spec['spr'] = spr
    hm = HMesh(TEX, TEX); geo = bale_geo(hm, spec, Q)
    # flake gaps in the texture exactly where the geometry creases are (the 'b' stations: local minima of the top row)
    ny_r, y_r = section_rows(S, pf, Hs)
    creases = geo['bnd']
    strip = strip_texture(Hs, Lp, pf, 21, ny_r, row_ao(B['H'] / 2, B['sink'], y_r),
                          bnd_px=[(x + B['L'] / 2 + mg) * pf for x in creases], twine_px=[(t + B['L'] / 2 + mg) * pf for t in tw_x])
    put(img, strip, 0, 0)
    eh, ew = int(np.ceil(B['H'] * pf)) + 2, int(np.ceil(B['W'] * pf)) + 2
    yy = B['H'] / 2 - (np.arange(eh) + 0.5) / pf
    for k, (ex, ey) in enumerate(spec['end_uv']): put(img, end_texture(eh, ew, pf, 40 + k, row_ao(B['H'] / 2, B['sink'], yy)), ex, ey)
    put(img, twine_texture(16, TEX - 8, 5), 0, 1000)
    return hm.to_mesh(), Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGBA'), creases

def hay_block():
    """one monolithic straw block (same build as bale_hay, bigger, open bottom), 2048 atlas."""
    B, Q = BLOCK, BQ; pf = B['px']; mg = 0.15; T = B['tex']
    img = np.zeros((T, T, 4)); img[..., :3] = (150, 120, 70); img[..., 3] = 255
    Lp = int(np.ceil((B['L'] + 2 * mg) * pf)); tw_x = list(B['twines'])
    eh, ew = int(np.ceil(B['H'] * pf)) + 2, int(np.ceil(B['W'] * pf)) + 2
    spec = dict(L=B['L'], W=B['W'], H=B['H'], r=B['r'], seed=17, centre=(0, B['H'] / 2 - B['sink'], 0), twines=tw_x, open=True,
                caps=('full', 'full'), strip=(0, 0, pf, mg, False), end_uv=[(Lp + 10, 0), (Lp + 16 + ew, 0)],
                twine_uv=(0, T - 20, 16), rim_min=B['sink'] * 0.6)
    S = section(B['W'] / 2, B['H'] / 2, B['r'], Q['nb'], Q['nc'], Q['ns'], Q['nt'], open_bottom=True)
    Hs = int(np.ceil(S['P'] * pf)) + 2
    spr, ye = sprites_into(img, Lp + 10, eh + 10, T - Lp - 18, 110, fh=96, ts=200)
    assert Hs < T - 24 and Lp + 16 + 2 * ew < T and S['P'] * pf < T - 8, (Hs, Lp, ew)
    spec['spr'] = spr
    hm = HMesh(T, T); geo = bale_geo(hm, spec, Q)
    ny_r, y_r = section_rows(S, pf, Hs)
    strip = strip_texture(Hs, Lp, pf, 23, ny_r, row_ao(B['H'] / 2, B['sink'], y_r),
                          bnd_px=[(x + B['L'] / 2 + mg) * pf for x in geo['bnd']], twine_px=[(t + B['L'] / 2 + mg) * pf for t in tw_x])
    put(img, strip, 0, 0)
    yy = B['H'] / 2 - (np.arange(eh) + 0.5) / pf
    for k, (ex, ey) in enumerate(spec['end_uv']): put(img, end_texture(eh, ew, pf, 80 + k, row_ao(B['H'] / 2, B['sink'], yy)), ex, ey)
    put(img, twine_texture(16, T - 8, 7), 0, T - 20)
    return hm.to_mesh(), Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGBA')

def block_shape():
    C = SHP; span = BLOCK['L'] - 2 * C['r']; n = int(round(span / 0.95)) + 1
    rows = [_row(x, y, 0, C) for y in (0.9, 2.6, 3.9) for x in np.linspace(-span / 2, span / 2, n)]
    return '\n'.join([str(len(rows))] + rows) + '\n'

def wall_layout(rg):
    """[(x0, x1, row)] bricks: 4 below, 3 + two short ones above, centred on the joints."""
    L = WALL['L']; gaps = rg.uniform(0.03, 0.07, 3); lens = np.full(4, (L - gaps.sum()) / 4) + rg.normal(0, 0.06, 4)
    lens *= (L - gaps.sum()) / lens.sum(); out = []; x = -L / 2; joints = []
    for k in range(4):
        out.append((x, x + lens[k], 0)); x += lens[k]
        if k < 3: joints.append(x + gaps[k] / 2); x += gaps[k]
    bricks = []
    for k in range(3):                                                   # row-2 bale k centred on joint k
        nb = [joints[k] - joints[k - 1]] if k else []
        nb += [joints[k + 1] - joints[k]] if k < 2 else []
        half = min(nb) / 2; g = rg.uniform(0.03, 0.06)
        bricks.append((joints[k] - half + g / 2, joints[k] + half - g / 2, 1))
    first, last = bricks[0][0], bricks[-1][1]
    g1, g2 = rg.uniform(0.03, 0.06, 2)
    out += [(-L / 2, first - g1, 1)] + bricks + [(last + g2, L / 2, 1)]
    return out

def hay_wall():
    Wd, Q = WALL, LO; pf = Wd['px']; mg = 0.15; rg = np.random.default_rng(5)
    img = np.zeros((TEX, TEX, 4)); img[..., :3] = (150, 120, 70); img[..., 3] = 255
    S = section(Wd['W'] / 2, Wd['bh'] / 2, Wd['r'], Q['nb'], Q['nc'], Q['ns'], Q['nt'], open_bottom=True)
    Hs = int(np.ceil(S['P'] * pf)) + 2; strip_ft = TEX / pf
    eh, ew = int(np.ceil(Wd['bh'] * pf)) + 2, int(np.ceil(Wd['W'] * pf)) + 2
    end_uv = [(k * (ew + 6), Hs + 6) for k in range(2)]
    spr, ye = sprites_into(img, 2 * (ew + 6) + 4, Hs + 6, TEX - 2 * (ew + 6) - 8, 90, fh=64, ts=120)
    assert ye < 1002 and Hs + 6 + eh < 1002, (ye, Hs, eh)
    hm = HMesh(TEX, TEX); bricks = wall_layout(rg); top_row = 2 * Wd['bh'] - Wd['sink'] - Wd['sit']
    for k, (x0, x1, row) in enumerate(bricks):
        L = x1 - x0; bh = Wd['bh'] + rg.normal(0, 0.015)
        cy = (bh / 2 - Wd['sink']) if row == 0 else (Wd['bh'] - Wd['sink'] - Wd['sit'] + bh / 2)
        if row == 1: cy = min(cy, top_row - bh / 2 + 0.015)
        nt = 2 if L < 3.0 else (3 if rg.random() < 0.4 else 2)
        tw = [(-L / 4, L / 4), (-L / 3, 0.0, L / 3)][nt - 2]
        tw = [t + rg.normal(0, 0.05) for t in tw]
        caps = ('full' if x0 <= -Wd['L'] / 2 + 1e-6 else 'fan', 'full' if x1 >= Wd['L'] / 2 - 1e-6 else 'fan')
        win = rg.uniform(0, strip_ft - (L + 2 * mg))
        cm = (lambda x, sz: True) if row == 1 else (lambda x, sz: rg.random() < 0.6)
        spec = dict(L=L, W=Wd['W'], H=bh, r=Wd['r'], seed=100 + k, centre=((x0 + x1) / 2, cy, rg.normal(0, 0.035)),
                    yaw=rg.normal(0, 0.012), roll=rg.normal(0, 0.008), twines=tw, open=True, caps=caps,
                    strip=(win * pf, 0, pf, mg, bool(rg.random() < 0.5)), end_uv=[end_uv[rg.integers(2)], end_uv[rg.integers(2)]],
                    twine_uv=(0, 1004, 16), spr=spr, cardmask=cm, rim_min=0.0 if row == 1 else Wd['sink'])
        bale_geo(hm, spec, Q)
    ny_r, y_r = section_rows(S, pf, Hs)
    strip = strip_texture(Hs, TEX, pf, 31, ny_r, row_ao(Wd['bh'] / 2, 0.0, y_r, strength=0.4, reach=0.35), crease=0.7)
    put(img, strip, 0, 0)
    yy = Wd['bh'] / 2 - (np.arange(eh) + 0.5) / pf
    for k, (ex, ey) in enumerate(end_uv): put(img, end_texture(eh, ew, pf, 60 + k, row_ao(Wd['bh'] / 2, 0.0, yy, 0.35, 0.3)), ex, ey)
    put(img, twine_texture(16, TEX - 8, 6), 0, 1004)
    return hm.to_mesh(), Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGBA'), bricks


# ------------------------------------------------------------------ collision
def _row(x, y, z, C): return f"{x:.4f} {y:.4f} {z:.4f} {C['r']} {C['friction']} {C['spring']} {C['damping']}"

def bale_shape(L, y_rows):
    C = SHP; span = L - 2 * C['r']; n = int(np.ceil(span / C['every'] - 1e-6)) + 1
    rows = [_row(x, y, 0, C) for y in y_rows for x in np.linspace(-span / 2, span / 2, n)]
    return '\n'.join([str(len(rows))] + rows) + '\n'


# ------------------------------------------------------------------ preview (software z-buffer, NOT a game render)
def preview(out_path, custom=None):
    """custom: list of (eye, target, fov, solo object indices) for extra views (debug)."""
    from preview_stt_scene import Cam, raster, load_jm
    def obj(name, pos, tex=None):
        V, I = load_jm(f'{OUTD}/{name}.jm'); t = np.asarray(Image.open(f'{OUTD}/{tex or name}.png').convert('RGBA'), np.float32) / 255
        V = V.copy(); V[:, :3] += np.array(pos, np.float32); return (V, I, t)
    objs = [obj('bale_hay', (0, 0, 0)), obj('hay_wall', (0, 0, -7.0)), obj('hay_block', (-9.0, 0, 3.0))]
    if os.path.exists(f'{OUTD}/bale_straw.jm') and os.path.exists(f'{OUTD}/bale_paille.png'): objs.append(obj('bale_straw', (6.5, 0, 0), 'bale_paille'))
    Lg = np.array([-0.45, 0.8, 0.4]); Lg /= np.linalg.norm(Lg)
    def shot(eye, tgt, W=900, H=640, fov=50, solo=None):
        cam = Cam(eye, tgt, W, H, fov); img = np.zeros((H, W, 3), np.float32)
        sky = np.linspace(0, 1, H)[:, None, None]; img[:] = np.array([0.55, 0.70, 0.90]) * (1 - sky) + np.array([0.82, 0.86, 0.90]) * sky
        zb = np.full((H, W), np.inf, np.float32)
        gs = np.arange(-40, 41, 2.0); GX, GZ = np.meshgrid(gs, gs); P = np.stack([GX, np.zeros_like(GX), GZ], -1).reshape(-1, 3)
        n = len(gs); ii, jj = np.meshgrid(np.arange(n - 1), np.arange(n - 1), indexing='ij'); a = (ii * n + jj).ravel()
        I = np.concatenate([np.stack([a, a + 1, a + n], 1), np.stack([a + 1, a + n + 1, a + n], 1)])
        rg = np.random.default_rng(0); C = np.array([0.55, 0.43, 0.31]) * (0.92 + 0.12 * rg.random((len(P), 1)))
        raster(img, zb, cam, P, I, lambda ti, B: (C[I[ti]] * B[:, :, None]).sum(1))
        for V, Ii, tex in (objs if solo is None else [objs[k] for k in solo]):
            th, tw = tex.shape[:2]
            def uvpx(ti, B, V=V, Ii=Ii, tw=tw, th=th):
                uv = (V[Ii[ti], 6:8][None] * B[:, :, None]).sum(1)
                return np.clip((1 - uv[:, 1]) * th, 0, th - 1).astype(int), np.clip(uv[:, 0] * tw, 0, tw - 1).astype(int)
            def col(ti, B, V=V, Ii=Ii, tex=tex):
                py, px = uvpx(ti, B); nn = (V[Ii[ti], 3:6][None] * B[:, :, None]).sum(1)
                return tex[py, px, :3] * (0.62 + 0.45 * np.clip(nn @ Lg, 0, 1))[:, None]
            # back-face culling like the game (cards are emitted two-sided)
            P3 = V[:, :3]; e = np.asarray(eye, np.float32)
            fn = np.cross(P3[Ii[:, 1]] - P3[Ii[:, 0]], P3[Ii[:, 2]] - P3[Ii[:, 0]])
            vis = np.einsum('ij,ij->i', fn, e[None] - P3[Ii[:, 0]]) > 0
            Iv = Ii[vis]
            def colv(ti, B, Iv=Iv, V=V, tex=tex):
                return col_any(ti, B, Iv, V, tex)
            def col_any(ti, B, Iv, V, tex):
                uv = (V[Iv[ti], 6:8][None] * B[:, :, None]).sum(1); nn = (V[Iv[ti], 3:6][None] * B[:, :, None]).sum(1)
                py = np.clip((1 - uv[:, 1]) * th, 0, th - 1).astype(int); px = np.clip(uv[:, 0] * tw, 0, tw - 1).astype(int)
                return tex[py, px, :3] * (0.62 + 0.45 * np.clip(nn @ Lg, 0, 1))[:, None]
            def alp(ti, B, Iv=Iv, V=V, tex=tex):
                uv = (V[Iv[ti], 6:8][None] * B[:, :, None]).sum(1)
                py = np.clip((1 - uv[:, 1]) * th, 0, th - 1).astype(int); px = np.clip(uv[:, 0] * tw, 0, tw - 1).astype(int)
                return tex[py, px, 3]
            raster(img, zb, cam, P3, Iv, colv, alp)
        return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    views = [shot(e, t, fov=f, solo=so) for e, t, f, so in custom] if custom else             [shot((3.4, 3.1, 4.4), (0.0, 0.75, 0.0), fov=42, solo=[0]),            # bale close-up, 3/4 from above
             shot((4.3, 1.3, 1.9), (0.6, 0.7, 0.0), fov=40, solo=[0]),              # bale end + twine, low
             shot((7.5, 4.2, -0.5), (-1.0, 1.6, -7.0), fov=50, solo=[1]),           # wall close 3/4
             shot((17.0, 6.0, 20.0), (-2.0, 1.4, -2.0), fov=50),                    # mid distance: block, wall, new bale, old bale (right)
             shot((-2.5, 6.0, 9.5), (-9.0, 2.2, 3.0), fov=50, solo=[2]),            # block close 3/4 from above
             shot((-20.0, 3.0, 9.0), (-9.0, 2.2, 3.0), fov=45, solo=[2])]            # block end + side, eye height
    W_, H_ = views[0].size; sheet = Image.new('RGB', (W_ * 2, H_ * ((len(views) + 1) // 2)), (255, 255, 255))
    for k, v in enumerate(views): sheet.paste(v, ((k % 2) * W_, (k // 2) * H_))
    os.makedirs(os.path.dirname(out_path), exist_ok=True); sheet.save(out_path); print('preview', out_path)


def build(outd=OUTD):
    os.makedirs(outd, exist_ok=True); info = {}
    m, img, _ = bale_hay(); nv, nt = m.write(f'{outd}/bale_hay.jm', MAT); img.save(f'{outd}/bale_hay.png', optimize=True)
    open(f'{outd}/bale_hay.shp', 'w', newline='\n').write(bale_shape(BALE['L'], [SHP['r'] - BALE['sink'] + 0.05]))
    V = np.array([v[:3] for v in m.V]); info['bale_hay'] = (nv, nt, V.min(0).round(2).tolist(), V.max(0).round(2).tolist())
    m, img, _ = hay_wall(); nv, nt = m.write(f'{outd}/hay_wall.jm', MAT); img.save(f'{outd}/hay_wall.png', optimize=True)
    y1 = SHP['r'] - WALL['sink'] + 0.05; y2 = 2 * WALL['bh'] - WALL['sink'] - WALL['sit'] - SHP['r'] + 0.05
    open(f'{outd}/hay_wall.shp', 'w', newline='\n').write(bale_shape(WALL['L'], [y1, y2]))
    V = np.array([v[:3] for v in m.V]); info['hay_wall'] = (nv, nt, V.min(0).round(2).tolist(), V.max(0).round(2).tolist())
    m, img = hay_block(); nv, nt = m.write(f'{outd}/hay_block.jm', MAT); img.save(f'{outd}/hay_block.png', optimize=True)
    open(f'{outd}/hay_block.shp', 'w', newline='\n').write(block_shape())
    V = np.array([v[:3] for v in m.V]); info['hay_block'] = (nv, nt, V.min(0).round(2).tolist(), V.max(0).round(2).tolist())
    for k, (nv, nt, lo, hi) in info.items(): print(f'{k}: {nv} vertices, {nt} triangles, bbox {lo} .. {hi} ft')
    return info

if __name__ == '__main__':
    build()
    if '--preview' in sys.argv: preview(os.path.join(os.path.dirname(ROOT), 'apercus_sgm', 'hay_3d.png'))
