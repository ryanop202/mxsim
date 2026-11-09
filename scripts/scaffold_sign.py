"""SGM wooden sign structure (user's photo 222): two tall rough wooden poles (~20.5 ft, 10 ft apart) with sawn cross beams
nailed on their front, a big BLACK tarp panel (9 x 7 ft, upper part) and a smaller black panel (8 x 3 ft) below, both laced
to the beams, a twin floodlight on top of the right-hand pole, and at the foot of each pole a stack of 7 tyres wrapped in
a white tarp (~5 ft, bulging tyre shapes, the pole going through the middle).
- origin on the ground, centre between the poles; poles at x = +-5; FRONT (printed side) = local -z.
- the user will send the logo later: make(logo_path) prints an RGBA logo centred on the big panel (aspect kept, never
  mirrored); without a logo the panel stays plain black. make(..., small_logo_path) does the same for the small panel.
Run: python scripts/scaffold_sign.py [logo.png] [--preview]  -> assets/props/scaffold_sign.jm / .png
     (+ ../apercus_sgm/scaffold_sign_3d.png with --preview)"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
from props_usland import Mesh, palette, pipe, OUTD
import stt_ads as AD

S = dict(px=5.0, post_r=0.36, post_h=20.5, beam_t=0.30, beam_x=5.9,
         beams=((19.50, 19.95), (11.95, 12.40), (8.90, 9.35), (5.20, 5.65)),
         big=(-4.5, 4.5, 12.45, 19.45), small=(-4.0, 4.0, 5.80, 8.80), z_panel=-0.70, panel_t=0.02,
         tyres=7, tyre_h=0.72, tyre_R=1.30, seg=14)
TW = 2048
R_BIG = (0, 0, 1280, 996)            # 9 x 7 ft  (142 px / ft)
R_SMALL = (0, 1004, 1024, 1388)      # 8 x 3 ft  (128 px / ft)
R_BEAM = (0, 1396, 1280, 1452)       # 11.8 x 0.45 ft, grain along x
R_TARP = (0, 1460, 1280, 1908)       # tyre wrap: u around (8.2 ft), v up the stack (0 -> top dome)
R_POST = (1288, 0, 1544, 1908)       # pole: u around, v along the height (top row = top of the pole)
R_LENS = (1552, 0, 1712, 120)        # floodlight glass
BLACK = (15, 15, 17)

# ------------------------------------------------------------------ textures
def wood(w, h, along_x, seed, base=(132, 110, 86)):
    """weathered rough wood: long grain streaks, dark cracks, a few knots."""
    rg = np.random.default_rng(seed); sig = (1.2, 60) if along_x else (60, 1.2)
    a = np.ones((h, w, 3)) * np.array(base, float)
    g = gaussian_filter(rg.normal(0, 1, (h, w)), sig); g /= g.std() + 1e-9
    g2 = gaussian_filter(rg.normal(0, 1, (h, w)), (sig[0] / 6 + 0.6, sig[1] / 6 + 0.6)); g2 /= g2.std() + 1e-9
    lo = gaussian_filter(rg.normal(0, 1, (h, w)), 40); lo /= lo.std() + 1e-9
    a *= (1 + 0.10 * g + 0.05 * g2 + 0.06 * lo)[..., None]
    a = a * 0.85 + np.array([150, 148, 140.0]) * 0.15 * (0.6 + 0.4 * lo[..., None] ** 2)          # grey weathering
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    for _ in range(int(w * h / 9000)):                                                           # cracks
        if along_x:
            y = rg.uniform(0, h); x = rg.uniform(0, w); L = rg.uniform(30, 160)
            d.line([(x, y), (x + L, y + rg.uniform(-2, 2))], fill=(52, 42, 34), width=1)
        else:
            x = rg.uniform(0, w); y = rg.uniform(0, h); L = rg.uniform(40, 220)
            d.line([(x, y), (x + rg.uniform(-3, 3), y + L)], fill=(52, 42, 34), width=int(rg.integers(1, 3)))
    for _ in range(max(2, int(w * h / 60000))):                                                  # knots
        x, y = rg.uniform(0, w), rg.uniform(0, h); rx, ry = (rg.uniform(4, 9), rg.uniform(3, 6)) if along_x else (rg.uniform(4, 8), rg.uniform(6, 12))
        d.ellipse([x - rx * 1.6, y - ry * 1.6, x + rx * 1.6, y + ry * 1.6], fill=(108, 86, 66)); d.ellipse([x - rx, y - ry, x + rx, y + ry], fill=(66, 50, 38))
    return im

def tarp_panel(w, h, ppf, seed, logo=None):
    """black PVC tarp: faint wrinkles / stretch folds towards the corners, a hem and silver grommets; optional logo centred."""
    rg = np.random.default_rng(seed); yy, xx = np.mgrid[:h, :w].astype(float)
    a = np.ones((h, w, 3)) * np.array(BLACK, float)
    n = gaussian_filter(rg.normal(0, 1, (h, w)), 18); n /= n.std() + 1e-9
    u, v = xx / w - 0.5, yy / h - 0.5
    fold = np.sin((u * 1.0 + v * np.sign(u + 1e-9) * np.sign(v + 1e-9) * 1.0) * 60 + 3 * n) * np.clip(np.abs(u) * 2 * np.abs(v) * 2, 0, 1) ** 1.5
    a *= (1 + 0.10 * n + 0.18 * fold)[..., None]
    hem = int(0.12 * ppf); a[:hem] *= 1.6; a[-hem:] *= 1.6; a[:, :hem] *= 1.6; a[:, -hem:] *= 1.6
    if logo is not None:
        lg = Image.open(logo).convert('RGBA') if isinstance(logo, str) else logo
        al = np.asarray(lg)[..., 3]; ys, xs = np.nonzero(al > 10)
        if len(xs): lg = lg.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
        AD.paste(a, AD.fit(lg, w / 2, h / 2, w - 2 * hem - 0.5 * ppf, h - 2 * hem - 0.5 * ppf), lg)
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im); r = 0.055 * ppf
    for k in range(int(round((w / ppf) / 1.5)) + 1):
        x = hem / 2 + k * (w - hem) / int(round((w / ppf) / 1.5))
        for y in (hem / 2, h - hem / 2):
            d.ellipse([x - r, y - r, x + r, y + r], fill=(190, 190, 192)); d.ellipse([x - r / 2, y - r / 2, x + r / 2, y + r / 2], fill=(10, 10, 10))
    for k in range(1, int(round((h / ppf) / 1.5))):
        y = hem / 2 + k * (h - hem) / int(round((h / ppf) / 1.5))
        for x in (hem / 2, w - hem / 2):
            d.ellipse([x - r, y - r, x + r, y + r], fill=(190, 190, 192)); d.ellipse([x - r / 2, y - r / 2, x + r / 2, y + r / 2], fill=(10, 10, 10))
    return im

def tarp_wrap(w, h, seed=9):
    """white tarp wrapped round the tyre stack: vertical folds, darker in the tyre seams (row = model height), dirt at
    the bottom, gathered pleats on the top dome. Rows: 0 = top of the dome, h - 1 = ground."""
    rg = np.random.default_rng(seed); yy, xx = np.mgrid[:h, :w].astype(float)
    a = np.ones((h, w, 3)) * np.array((236, 236, 232), float)
    f = gaussian_filter(rg.normal(0, 1, (h, w)), (60, 9), mode="wrap"); f /= f.std() + 1e-9
    f2 = gaussian_filter(rg.normal(0, 1, (h, w)), (6, 1.5), mode='wrap'); f2 /= f2.std() + 1e-9
    a *= (1 + 0.05 * f + 0.008 * f2)[..., None]
    yft = (1 - yy / h) * TARP_V[1]                                       # model height (ft) of each row, top dome above the stack
    stack_h = S['tyres'] * S['tyre_h']
    ph = (yft % S['tyre_h']) / S['tyre_h']
    seam = np.exp(-((np.minimum(ph, 1 - ph)) / 0.10) ** 2) * (yft < stack_h)
    a *= (1 - 0.22 * seam)[..., None]
    pleat = (yft > stack_h) * (0.5 + 0.5 * np.sin(xx / w * 2 * np.pi * 26 + 2 * f))
    a *= (1 - 0.10 * pleat)[..., None]
    dirt = (np.clip((0.9 - yft) / 0.9, 0, 1) ** 1.3 * (0.7 + 0.3 * f))[..., None]
    a = a * (1 - 0.55 * dirt) + np.array([128, 104, 78.0]) * 0.55 * dirt
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

TARP_V = (0.0, S['tyres'] * S['tyre_h'] + 0.35)                         # tarp texture rows cover model y 0 .. 5.39

def lens(w, h):
    """floodlight front: white-yellow glass with the reflector facets behind, dark frame."""
    im = Image.new('RGB', (w, h), (40, 40, 42)); d = ImageDraw.Draw(im); b = int(h * 0.10)
    d.rectangle([b, b, w - b, h - b], fill=(236, 232, 210))
    for k in range(1, 8): x = b + k * (w - 2 * b) / 8; d.line([(x, b), (x, h - b)], fill=(205, 200, 178), width=2)
    for k in range(1, 5): y = b + k * (h - 2 * b) / 5; d.line([(b, y), (w - b, y)], fill=(210, 205, 182), width=1)
    return im

def texture(logo=None, small_logo=None):
    img = Image.new('RGB', (TW, TW), BLACK)
    def put(rect, im): img.paste(im.resize((rect[2] - rect[0], rect[3] - rect[1]), Image.LANCZOS) if im.size != (rect[2] - rect[0], rect[3] - rect[1]) else im, rect[:2])
    put(R_BIG, tarp_panel(R_BIG[2] - R_BIG[0], R_BIG[3] - R_BIG[1], (R_BIG[2] - R_BIG[0]) / 9.0, 1, logo))
    put(R_SMALL, tarp_panel(R_SMALL[2] - R_SMALL[0], R_SMALL[3] - R_SMALL[1], (R_SMALL[2] - R_SMALL[0]) / 8.0, 2, small_logo))
    put(R_BEAM, wood(R_BEAM[2] - R_BEAM[0], R_BEAM[3] - R_BEAM[1], True, 3, base=(140, 116, 88)))
    put(R_TARP, tarp_wrap(R_TARP[2] - R_TARP[0], R_TARP[3] - R_TARP[1]))
    put(R_POST, wood(R_POST[2] - R_POST[0], R_POST[3] - R_POST[1], False, 4))
    put(R_LENS, lens(R_LENS[2] - R_LENS[0], R_LENS[3] - R_LENS[1]))
    pal = palette(img, ['black', 'endgrain', 'rope', 'lamp', 'steel', 'beam'],
                  [BLACK, (176, 146, 108), (226, 222, 210), (52, 54, 58), (118, 120, 124), (128, 106, 82)])
    return img, pal

# ------------------------------------------------------------------ model helpers
def sfan(m, P, N, UV):
    """polygon with per-vertex (smooth) normals, wound counter-clockwise seen from outside."""
    a = len(m.V); P = [np.asarray(p, float) for p in P]; N = [np.asarray(n, float) / np.linalg.norm(n) for n in N]
    if np.dot(np.cross(P[1] - P[0], P[2] - P[0]), sum(N)) < 0: P, N, UV = P[::-1], N[::-1], UV[::-1]
    for p, n, t in zip(P, N, UV): m.V.append((*p, *n, *t))
    for k in range(1, len(P) - 1): m.I += [a, a + k, a + k + 1]

def lathe(m, prof, seg, cx, cz, rect, vrow, jit=None, ang0=0.0):
    """surface of revolution around the vertical axis at (cx, cz). prof = [(r, y)], bottom -> top; texture u around
    (rect x0 -> x1), v from vrow(i) (pixel row); jit(i, k) -> radius factor (k = seg wraps to 0)."""
    x0, _, x1, _ = rect; n = len(prof); ang = ang0 + np.linspace(0, 2 * np.pi, seg + 1)
    nrm = []
    for i in range(n):
        a, b = prof[max(i - 1, 0)], prof[min(i + 1, n - 1)]; tr, ty = b[0] - a[0], b[1] - a[1]; L = np.hypot(tr, ty)
        nrm.append((ty / L, -tr / L))
    def vert(i, k):
        r, y = prof[i]; f = jit(i, k % seg) if jit else 1.0; t = ang[k]
        return (np.array([cx + r * f * np.cos(t), y, cz + r * f * np.sin(t)]), np.array([nrm[i][0] * np.cos(t), nrm[i][1], nrm[i][0] * np.sin(t)]),
                m.uv_px(x0 + (x1 - x0) * k / seg, vrow(i)))
    for i in range(n - 1):
        for k in range(seg):
            q = [vert(i, k), vert(i, k + 1), vert(i + 1, k + 1), vert(i + 1, k)]
            if prof[i + 1][0] < 1e-6: q = q[:3]
            sfan(m, [v[0] for v in q], [v[1] for v in q], [v[2] for v in q])

def jitter(seed, amp):
    rg = np.random.default_rng(seed); tab = {}
    def f(i, k):
        if (i, k) not in tab: tab[(i, k)] = 1 + rg.uniform(-amp, amp)
        return tab[(i, k)]
    return f

def model(pal):
    m = Mesh(TW, TW); px, pr, ph = S['px'], S['post_r'], S['post_h']
    # ---- poles (rough, slightly irregular, gently tapered), top cut flat
    for sgn, seed in ((1, 21), (-1, 22)):
        ys = np.linspace(0, ph, 9); prof = [(pr * (1 - 0.10 * y / ph), y) for y in ys]
        y0r, y1r = R_POST[1], R_POST[3]
        j = jitter(seed, 0.07)
        lathe(m, prof, 10, sgn * px, 0.0, R_POST, lambda i: y1r - (y1r - y0r) * prof[i][1] / ph, j)
        top = [np.array([sgn * px + prof[-1][0] * j(len(prof) - 1, k) * np.cos(t), ph, prof[-1][0] * j(len(prof) - 1, k) * np.sin(t)])
                                       for k, t in enumerate(np.linspace(0, 2 * np.pi, 11)[:-1])]
        m.tri_fan(top, np.array([0, 1.0, 0]), [m.uv_px(*pal['endgrain'][1])] * 10)
    # ---- sawn beams nailed on the front of the poles
    z1 = -pr * 0.92; z0 = z1 - S['beam_t']; bx = S['beam_x']
    for y0, y1 in S['beams']:
        m.box(-bx, bx, y0, y1, z0, z1, {'-z': ('r', R_BEAM), '+z': ('r', R_BEAM), '+y': ('r', R_BEAM), '-y': ('r', R_BEAM),
                                         '+x': pal['endgrain'], '-x': pal['endgrain']})
    # ---- black panels (front -z textured, back plain black), laced to the beams with white rope
    zf = S['z_panel']; zb = zf + S['panel_t']
    for (xa, xb, ya, yb), rect in ((S['big'], R_BIG), (S['small'], R_SMALL)):
        m.box(xa, xb, ya, yb, zf, zb, {'-z': ('r', rect), '+z': pal['black'], '+y': pal['black'], '-y': pal['black'], '+x': pal['black'], '-x': pal['black']})
        nl = int(round((xb - xa) / 1.5))
        for k in range(nl + 1):                                    # lacing loops round the beam above / below
            x = xa + 0.06 + k * (xb - xa - 0.12) / nl
            bt = min(S['beams'], key=lambda b: abs(b[0] - yb)); bb = min(S['beams'], key=lambda b: abs(b[1] - ya))
            for yy0, yy1 in ((yb - 0.10, bt[1] + 0.03), (bb[0] - 0.03, ya + 0.10)):
                m.box(x - 0.03, x + 0.03, yy0, yy1, zf - 0.025, z1 + 0.02, {'*': pal['rope'], '-y': None, '+z': None})
        for y in (ya + 0.15, (ya + yb) / 2, yb - 0.15):            # side ties to the poles
            for s, xe in ((-1, xa), (1, xb)):
                pipe(m, [(xe, y, zf + 0.01), (s * (px - pr * 0.6), y + 0.1, -pr * 0.5)], 0.025, pal['rope'], seg=4)
    # ---- twin floodlight on top of the right-hand pole (viewer's right seen from -z = -x)
    xl = -px; yt = ph
    m.box(xl - 0.09, xl + 0.09, yt, yt + 0.55, -0.09, 0.09, {'*': pal['steel'], '-y': None})           # mast stub
    pipe(m, [(xl - 1.1, yt + 0.55, 0.0), (xl + 1.1, yt + 0.55, 0.0)], 0.06, pal['steel'], seg=6)      # cross arm
    for xc in (xl - 0.6, xl + 0.6):
        m.box(xc - 0.04, xc + 0.04, yt + 0.55, yt + 0.95, -0.05, 0.05, {'*': pal['steel']})            # yoke
        h0, h1 = yt + 0.85, yt + 1.55; d0, d1 = -0.30, 0.12
        m.box(xc - 0.42, xc + 0.42, h0, h1, d0, d1, {'*': pal['lamp'], '-z': ('r', R_LENS)})
        m.box(xc - 0.30, xc + 0.30, h0 + 0.12, h1 - 0.12, d1, d1 + 0.12, {'*': pal['lamp'], '-z': None})  # back fins
    # ---- tyre stacks wrapped in white tarp round the foot of each pole
    R, th, nt = S['tyre_R'], S['tyre_h'], S['tyres']; Hs = nt * th
    prof = [(R - 0.06, 0.0)]
    for i in range(nt):
        prof += [(R, (i + 0.5) * th), (R - 0.16, (i + 1) * th)]
    prof += [(R - 0.42, Hs + 0.16), (0.80, Hs + 0.27), (pr * 1.05, Hs + 0.33)]
    t0, t1 = R_TARP[1], R_TARP[3]
    vrow = lambda i: t1 - (t1 - t0) * (prof[i][1] - TARP_V[0]) / (TARP_V[1] - TARP_V[0])
    for sgn, seed in ((1, 31), (-1, 32)):
        jf = jitter(seed, 0.035)
        lathe(m, prof, S['seg'], sgn * px, 0.0, R_TARP, vrow, lambda i, k, jf=jf: 1.0 if i == len(prof) - 1 else jf(i, k), ang0=seed)
    return m

def tall(h=44.0, k=1.5, r=0.55):
    """v30 (user: "aussi haut qu'un poteau avec les lumieres"): poles as tall as the night light poles (h ft), the panels and
    beams k times bigger and kept at the top, thicker poles; the tyre stacks at the foot unchanged."""
    H0 = S['post_h']; Y = lambda y: h - (H0 - y) * k
    S.update(post_h=h, post_r=r, px=S['px'] * k, beam_x=S['beam_x'] * k, beam_t=S['beam_t'] * k,
             beams=tuple((Y(a), Y(a) + (b - a) * k) for a, b in S['beams']),
             big=(S['big'][0] * k, S['big'][1] * k, Y(S['big'][2]), Y(S['big'][3])),
             small=(S['small'][0] * k, S['small'][1] * k, Y(S['small'][2]), Y(S['small'][3])), z_panel=-r * 0.92 - S['beam_t'] * k - 0.25, panel_t=0.2)   # thick: no z-fight front / back

# ------------------------------------------------------------------ build
def make(logo_path=None, small_logo_path=None, outd=OUTD, name='scaffold_sign'):
    """write <outd>/<name>.jm / .png; logo_path (RGBA image) printed centred on the big black panel, small_logo_path on the
    small one; None = plain black."""
    os.makedirs(outd, exist_ok=True)
    img, pal = texture(logo_path, small_logo_path); m = model(pal)
    nv, nt = m.write(f'{outd}/{name}.jm', (0, 0, 0, 0, 0)); img.save(f'{outd}/{name}.png', optimize=True)
    P = np.array([v[:3] for v in m.V]); print(f'{name}: {nv} vertices, {nt} triangles, bbox {P.min(0).round(2)} .. {P.max(0).round(2)} ft')
    return nv, nt

# ------------------------------------------------------------------ preview (software z-buffer, NOT a game render)
def preview(out_path, outd=OUTD, name='scaffold_sign'):
    from preview_stt_scene import Cam, raster, load_jm
    from rider_gate import scale_person
    V, I = load_jm(f'{outd}/{name}.jm'); tex = np.asarray(Image.open(f'{outd}/{name}.png').convert('RGBA'), np.float32) / 255
    objs = [(V, I, tex), scale_person((-2.0, 0, -4.0))]
    Lg = np.array([0.3, 0.8, -0.5]); Lg /= np.linalg.norm(Lg)
    def shot(eye, tgt, W=760, H=900, fov=50):
        cam = Cam(eye, tgt, W, H, fov); img = np.zeros((H, W, 3), np.float32)
        sky = np.linspace(0, 1, H)[:, None, None]; img[:] = np.array([0.55, 0.70, 0.90]) * (1 - sky) + np.array([0.82, 0.86, 0.90]) * sky
        zb = np.full((H, W), np.inf, np.float32)
        gs = np.arange(-60, 61, 5.0); GX, GZ = np.meshgrid(gs, gs); P = np.stack([GX, np.zeros_like(GX), GZ], -1).reshape(-1, 3)
        n = len(gs); ii, jj = np.meshgrid(np.arange(n - 1), np.arange(n - 1), indexing='ij'); a = (ii * n + jj).ravel()
        Ig = np.concatenate([np.stack([a, a + 1, a + n], 1), np.stack([a + 1, a + n + 1, a + n], 1)])
        rg = np.random.default_rng(0); C = np.array([0.55, 0.43, 0.31]) * (0.92 + 0.12 * rg.random((len(P), 1)))
        raster(img, zb, cam, P, Ig, lambda ti, B: (C[Ig[ti]] * B[:, :, None]).sum(1))
        for V_, I_, tx in objs:
            th, tw = tx.shape[:2]
            def uvpx(ti, B, V_=V_, I_=I_, tw=tw, th=th):
                uv = (V_[I_[ti], 6:8][None] * B[:, :, None]).sum(1)
                return np.clip((1 - uv[:, 1]) * th, 0, th - 1).astype(int), np.clip(uv[:, 0] * tw, 0, tw - 1).astype(int)
            def col(ti, B, V_=V_, I_=I_, tx=tx):
                py, px = uvpx(ti, B); nn = (V_[I_[ti], 3:6][None] * B[:, :, None]).sum(1)
                nn /= np.linalg.norm(nn, axis=1, keepdims=True) + 1e-9
                return tx[py, px, :3] * (0.62 + 0.45 * np.clip(nn @ Lg, 0, 1))[:, None]
            raster(img, zb, cam, V_[:, :3], I_, col, lambda ti, B, tx=tx: tx[uvpx(ti, B)][:, 3])
        return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    views = [shot((0.0, 9.0, -34.0), (0.0, 10.5, 0.0), fov=48),           # front (riders' side)
             shot((-16.0, 5.0, -20.0), (0.0, 10.0, 0.0), fov=55),         # 3/4 front, person for scale
             shot((10.0, 12.0, 26.0), (0.0, 10.0, 0.0), fov=50),          # back
             shot((-13.0, 8.0, -7.0), (-5.0, 4.5, 0.0), fov=50)]           # close-up: tyre stack
    W_, H_ = views[0].size; sheet = Image.new('RGB', (W_ * 4, H_), (255, 255, 255))
    for k, v in enumerate(views): sheet.paste(v, (k * W_, 0))
    os.makedirs(os.path.dirname(out_path), exist_ok=True); sheet.save(out_path); print('preview', out_path)

if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if '--tall' in sys.argv: tall()
    make(args[0] if args else None)
    if '--preview' in sys.argv: preview(os.path.join(os.path.dirname(ROOT), 'apercus_sgm', 'scaffold_sign_3d.png'))
