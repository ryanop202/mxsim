"""Saint-Georges light pole: French raw concrete pole (EDF style, photo 204) carrying 4 floodlights + 2 PA horn speakers (photo 203).
Made from scratch with props_usland.Mesh (doc 12: 1 unit = 1 ft, y up, one texture per model, matte).

pole_concrete.jm / .png (1024 x 2048) / .shp
  Pole: rectangular, tapered 1.3 (z) x 1.0 (x) ft at the foot -> 0.65 x 0.5 ft at the top (y = HT). Raw concrete with
  aggregate speckle, mottling, rain streaks; on the two wide faces (+-x, the one facing the track and the back) the column of
  recessed panels of the photo (short near the ground, longer above); thin white steel straps; small ID plate; black cable + grey junction box on the back (-x) face.
  v3 (user): concrete darker (mid-light weathered grey), no white paint / collar: the foot is hidden in a protective stack
  of 10 car tyres (2.1 ft dia, 0.65 ft thick, 6.5 ft high) wrapped in a white tarp that follows the tyres (bulges, grooves,
  folds, skirt on the ground), gathered and tied round the pole at the top (photo 209).
  Two black PA horn speakers (1.6 x 1.1 x 0.9 ft) at 17 ft on short galvanised arms + strap, facing +x, turned +-0.35 rad.
  Head (v2, user photo 207: no wide crossbar): 2 floodlights side by side at the very top, slightly offset in height, on a
  compact galvanised frame clamped on the +x face (bars at y 43 / 45, z +-1.5), facing +x, tilted down TILT rad: dark grey
  housing 2.2 (z) x 1.8 x 0.55 ft, warm white glass face, finned back, small visor, stem + galvanised U yoke.
  Lamp-face centres = LAMPS (for export_stt_night.GLOW lamps (z, y), x 1.9).
Origin = ground, centre of the pole foot; lamps face local +x.
Run: python scripts/pole_concrete.py [--preview]  -> assets/props/ (+ ../apercus_sgm/pole_concrete_3d.png with --preview)"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
from props_usland import Mesh, OUTD

HT = 45.3                                   # pole top (ft)
BASE = (0.50, 0.65)                         # half sizes (x, z) at the foot: 1.0 x 1.3 ft
TOPH = (0.25, 0.325)                        # half sizes at the top: 0.5 x 0.65 ft
TILT = 0.30                                 # floodlights tilted down (rad)
LAMPS = [(1.9, 43.7, -1.3), (1.9, 44.3, 1.3)]   # lamp-face centres (x, y, z): 2 floodlights side by side, +z one 0.6 ft higher
HOUS = (0.275, 0.90, 1.10)                  # housing half depth / height / width: 0.55 x 1.8 x 2.2 ft
BANDS = (5.9, 7.4, 9.6, 12.3, 15.1, 19.6, 22.4, 25.8, 28.9, 32.6, 35.4, 38.3, 41.9)   # thin white steel straps (ft)
SPK = dict(y=17.0, z=1.1, x=1.45, yaw=0.35, pitch=0.10)
CONC = (165, 163, 158)                      # v3 (user): mid-light weathered concrete (was 210, 208, 202)
TARP = (236, 236, 231)
STACK = dict(n=10, t=0.65, r0=1.00, bulge=0.10, seg=24)   # tyre stack under the tarp: groove radius, bulge, segments
TW, TH = 1024, 2048
PPF = 1880 / HT                             # strip rows per ft
STRIP_W = 150
STRIPS = {k: (4 + k * 154, 0, 4 + k * 154 + STRIP_W, 1880) for k in range(4)}    # +x, -x, +z, -z faces
R_GLASS = (632, 8, 1016, 328)
R_FINS = (632, 344, 1016, 664)
R_GRILLE = (632, 680, 792, 840)
R_TARP = (632, 1200, 1016, 1880)
R_ROPE = (870, 868, 1010, 904)
MATS = dict(conc=CONC, galva=(172, 176, 174), black=(36, 36, 38), hous=(64, 66, 68), box=(190, 190, 184), inner=(22, 22, 23))
SHADES = (1.0, 0.86, 0.72, 0.55)            # baked: top, side, side near the ground, underside
PATCH0 = (632, 860)

def half(y):
    t = y / HT
    return BASE[0] + (TOPH[0] - BASE[0]) * t, BASE[1] + (TOPH[1] - BASE[1]) * t

# ------------------------------------------------------------------ texture
def noise(rg, shape, sig, amp):
    n = gaussian_filter(rg.normal(0, 1, shape), sig); return n / (n.std() + 1e-9) * amp

def concrete_field(H, W, rg, base, xscale=3):
    """raw concrete: mottling + aggregate speckle (generated at 1/xscale width then stretched so the specks are round on the
    pole, whose strips are ~3x denser across than along) + fine grain."""
    a = np.ones((H, W, 3)) * np.array(base, float)
    lo = noise(rg, (H, W), (40, 14), 5.0) + noise(rg, (H, W), (8, 6), 2.5)
    w3 = max(4, W // xscale)
    sp = rg.random((H, w3)); dark = (sp < 0.07) * rg.uniform(14, 40, (H, w3)); light = (sp > 0.965) * rg.uniform(6, 16, (H, w3))
    spk = np.asarray(Image.fromarray((dark - light + 64).astype(np.float32)).resize((W, H), Image.BILINEAR)) - 64
    tint = (sp < 0.02)[..., None] * np.array([6, 2, -6.0])                                    # a few warm (sand / flint) grains
    tint = np.asarray(Image.fromarray(np.clip(tint + 128, 0, 255).astype(np.uint8)).resize((W, H), Image.NEAREST)).astype(float) - 128
    fine = rg.normal(0, 2.2, (H, W))
    a += (lo - spk + fine)[..., None] + tint
    return a

def strip_tex(k, seed):
    """one pole face, full height (row 0 = top HT, row 1879 = ground), u across the face (viewer's left -> right)."""
    rg = np.random.default_rng(seed); x0, y0, x1, y1 = STRIPS[k]; W, H = x1 - x0, y1 - y0
    yv = HT - (np.arange(H)[:, None] + 0.5) / PPF                                               # model y of each row
    u = (np.arange(W)[None, :] + 0.5) / W
    a = concrete_field(H, W, rg, CONC)
    # weathering: rain streaks (darker vertical runs, longer under the straps and from the top), slightly greyer top
    st = gaussian_filter(rg.normal(0, 1, (H, W // 3)), (60, 1.2)); st = np.asarray(Image.fromarray(st.astype(np.float32)).resize((W, H), Image.BILINEAR))
    a *= (1 - 0.035 * np.clip(st, 0, 3))[..., None]
    for _ in range(9):
        cx = rg.uniform(0.08, 0.92) * W; ys = rg.choice((HT,) + BANDS); ln = rg.uniform(1.5, 6.0); wd = rg.uniform(1.5, 4.0)
        f = np.exp(-((np.arange(W)[None, :] - cx) / wd) ** 2) * np.clip((ys - yv) / 0.3, 0, 1) * np.clip(1 - (ys - yv) / ln, 0, 1)
        a *= (1 - 0.10 * f)[..., None] + np.array([0, 0, -0.012]) * f[..., None]
    a *= (1 - 0.06 * np.clip((yv - (HT - 3)) / 3, 0, 1))[..., None]
    # recessed panels (wide faces only): a column of rectangular recesses, short near the ground, longer above
    if k in (0, 1):
        f = np.ones((H, W)); ul, ur = 0.30, 0.70
        y = 0.75; hs = [0.45, 0.5, 0.55, 0.65, 0.8, 1.0, 1.2]; i = 0
        while True:
            h = hs[i] if i < len(hs) else 1.55; i += 1
            if y + h > HT - 1.6: break
            r0, r1 = int((HT - y - h) * PPF), int((HT - y) * PPF); c0, c1 = int(ul * W), int(ur * W)
            f[r0:r1, c0:c1] = 0.50                                                               # inside, in shadow
            f[r0:r0 + max(2, int(0.10 * PPF)), c0:c1] = 0.34                                     # top inner wall (underside)
            f[r0:r1, c0:c0 + 5] = 0.66                                                           # lit side wall
            f[r0:r1, c1 - 3:c1] = 0.42
            f[r1 - 2:r1, c0:c1] = 0.86                                                           # sill lip catching the sky
            f[r0 - 1:r0, c0 - 1:c1 + 1] *= 1.06; f[r1:r1 + 1, c0 - 1:c1 + 1] *= 0.93
            y += h + (0.16 if i < 4 else 0.22)
        a *= f[..., None]
    # thin white steel straps all round (+ the shadow line under them)
    for b in BANDS:
        r = int((HT - b) * PPF); a[r - 1:r + 2] = np.array((247, 247, 246.0)) + rg.normal(0, 1.5, (3, W, 1)); a[r + 2:r + 3] *= 0.82
        a[r:r + 1, int(W * 0.5):int(W * 0.5) + 6] = (150, 150, 152)                              # strap buckle
    # arrises: thin darker corner lines so the edges read
    a[:, :2] *= 0.86; a[:, -2:] *= 0.86
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    if k == 3:                                                                                   # ID plate on the -z face
        yp = 8.6; hppf = W / (2 * half(yp)[1])                                                    # px / ft across (u) vs PPF along y
        pw_, ph_ = int(0.46 * hppf), int(0.26 * PPF); cx, cy = W // 2, int((HT - yp) * PPF)
        pl = Image.new('RGB', (230, 130), (240, 240, 236)); d = ImageDraw.Draw(pl)
        try: fnt = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 80)
        except OSError: fnt = ImageFont.load_default()
        d.text((115, 68), 'SG 07', fill=(20, 20, 20), font=fnt, anchor='mm'); d.rectangle([0, 0, 229, 129], outline=(110, 110, 110), width=6)
        img.paste(pl.resize((pw_, ph_), Image.LANCZOS), (cx - pw_ // 2, cy - ph_ // 2))
    return img

def glass_tex():
    x0, y0, x1, y1 = R_GLASS; W, H = x1 - x0, y1 - y0; rg = np.random.default_rng(31)
    a = np.ones((H, W, 3)) * np.array(MATS['hous'], float) + rg.normal(0, 2, (H, W, 1))
    b = 14; yy, xx = np.mgrid[0:H, 0:W]
    inner = (xx >= b) & (xx < W - b) & (yy >= b) & (yy < H - b)
    g = np.ones((H, W, 3)) * np.array((246, 238, 214), float)
    g *= (1 - 0.06 * ((xx - W / 2) / W) ** 2 * 4 - 0.05 * (yy / H))[..., None]
    nx, ny = 6, 5; cw, ch = (W - 2 * b) / nx, (H - 2 * b) / ny
    lx = ((xx - b) % cw) / cw * 2 - 1; ly = ((yy - b) % ch) / ch * 2 - 1; r = np.hypot(lx, ly)      # LED reflector cells
    g *= np.where(r < 0.92, 1 - 0.06 * r, 0.93)[..., None]
    g += np.array([9, 9, 6.0]) * np.exp(-(r / 0.22) ** 2)[..., None]
    g += rg.normal(0, 1.5, (H, W, 1))
    a = np.where(inner[..., None], g, a)
    a[b - 2:b] *= 0.6; a[:, b - 2:b] *= 0.6; a[H - b:H - b + 2] *= 1.25; a[:, W - b:W - b + 2] *= 1.1
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def fins_tex():
    x0, y0, x1, y1 = R_FINS; W, H = x1 - x0, y1 - y0; rg = np.random.default_rng(32)
    a = np.ones((H, W, 3)) * np.array(MATS['hous'], float) + rg.normal(0, 2, (H, W, 1))
    for x in range(16, W - 16, 14):
        a[12:H - 12, x:x + 5] *= 1.28; a[12:H - 12, x + 5:x + 7] *= 0.7                            # heat-sink fins
    a[H // 2 - 30:H // 2 + 30, W // 2 - 50:W // 2 + 50] = np.array(MATS['galva'], float) * 0.8      # yoke plate
    a[:6] *= 0.8; a[-6:] *= 0.8; a[:, :6] *= 0.8; a[:, -6:] *= 0.8
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def grille_tex():
    x0, y0, x1, y1 = R_GRILLE; W, H = x1 - x0, y1 - y0; rg = np.random.default_rng(33)
    a = np.ones((H, W, 3)) * 30.0 + rg.normal(0, 2, (H, W, 1)); yy, xx = np.mgrid[0:H, 0:W]
    holes = ((xx % 8) < 4) & ((yy % 8) < 4); a[holes] = 12
    a[:10] *= 1.4; a[-10:] *= 0.8
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def tarp_tex():
    """white tarp: soft mottling, fine weave grain, faint fold streaks, dust towards the ground (v: row 0 = top of the tarp)."""
    x0, y0, x1, y1 = R_TARP; W, H = x1 - x0, y1 - y0; rg = np.random.default_rng(35)
    a = np.ones((H, W, 3)) * np.array(TARP, float) + noise(rg, (H, W), (30, 30), 4.0)[..., None] + rg.normal(0, 1.6, (H, W, 1))
    a[::3] *= 0.992; a[:, ::3] *= 0.992                                                          # weave
    fs = gaussian_filter(rg.normal(0, 1, (H, W)), (25, 2.5)); fs /= fs.std(); a *= (1 + 0.025 * np.clip(fs, -2.5, 2.5))[..., None]
    t = np.linspace(0, 1, H)[:, None]
    dust = np.clip((t - 0.70) / 0.30, 0, 1) ** 1.5 * (0.75 + 0.25 * noise(rg, (H, W), 6, 1).clip(-1, 1))
    a = a * (1 - 0.45 * dust[..., None]) + np.array([150, 128, 100.0]) * 0.45 * dust[..., None]
    sp = gaussian_filter((rg.random((H, W)) < 0.002).astype(float), 2.0) * (t > 0.5); a -= np.clip(sp * 300, 0, 50)[..., None] * np.array([0.8, 0.9, 1.0])
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def rope_tex():
    x0, y0, x1, y1 = R_ROPE; W, H = x1 - x0, y1 - y0; rg = np.random.default_rng(36)
    a = np.ones((H, W, 3)) * np.array((40, 52, 96), float); yy, xx = np.mgrid[0:H, 0:W]
    a *= (0.8 + 0.25 * (((xx + yy) % 8) < 4))[..., None]; a += rg.normal(0, 3, (H, W, 1))     # twisted nylon rope
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def patch_rect(mat, q):
    m = list(MATS).index(mat); x = PATCH0[0] + 56 * q; y = PATCH0[1] + 56 * m; return (x + 4, y + 4, x + 44, y + 44)

def build_texture():
    img = Image.new('RGB', (TW, TH), (128, 128, 128))
    for k in range(4): img.paste(strip_tex(k, 11 + k), STRIPS[k][:2])
    for fn, r in ((glass_tex, R_GLASS), (fins_tex, R_FINS), (grille_tex, R_GRILLE), (tarp_tex, R_TARP), (rope_tex, R_ROPE)): img.paste(fn(), r[:2])
    rg = np.random.default_rng(40)
    for m, col in enumerate(MATS.values()):
        for q, s in enumerate(SHADES):
            x, y = PATCH0[0] + 56 * q, PATCH0[1] + 56 * m
            amp = 5.0 if m == 0 else 3.0
            p = np.ones((48, 48, 3)) * np.array(col, float) * s + rg.normal(0, amp * 0.5, (48, 48, 1)) + noise(rg, (48, 48), 3, amp * 0.6)[..., None]
            img.paste(Image.fromarray(np.clip(p, 0, 255).astype(np.uint8)), (x, y))
    return img

# ------------------------------------------------------------------ geometry helpers
def shade_q(N, P):
    ny = N[1] / (np.linalg.norm(N) + 1e-12)
    return 0 if ny > 0.6 else (3 if ny < -0.3 else (2 if np.mean(np.asarray(P, float)[:, 1]) < 0.9 else 1))

def face(m, P, N, src):
    """P = [bl, br, tr, tl] seen from outside; src = rect (px0, py0, px1, py1) or a material name (grain patch, baked shade)."""
    N = np.asarray(N, float); N = N / np.linalg.norm(N)
    r = patch_rect(src, shade_q(N, P)) if isinstance(src, str) else src
    x0, y0, x1, y1 = r
    uv = [m.uv_px(x0, y1), m.uv_px(x1, y1), m.uv_px(x1, y0), m.uv_px(x0, y0)]
    m.tri_fan([np.asarray(p, float) for p in P], N, uv[:len(P)] if len(P) == 4 else uv[:len(P)])

def obox(m, c, ax, hs, src, skip=()):
    """oriented box: centre c, axes ax (3 orthonormal vectors), half sizes hs; src = material, or dict {(i, sign): src}."""
    c = np.asarray(c, float); ax = [np.asarray(a, float) / np.linalg.norm(a) for a in ax]
    for i in range(3):
        for s in (1, -1):
            if (i, s) in skip: continue
            n = s * ax[i]; o = [j for j in range(3) if j != i]
            j = max(o, key=lambda j: abs(ax[j][1])); kk = [x for x in o if x != j][0]
            up = ax[j] * (1 if ax[j][1] >= 0 else -1)
            if abs(ax[j][1]) < 1e-6 and abs(n[1]) > 0.5: up = ax[j]
            rt = np.cross(up, n); fc = c + n * hs[i]; hu, hr = hs[j], hs[kk]
            P = [fc - rt * hr - up * hu, fc + rt * hr - up * hu, fc + rt * hr + up * hu, fc - rt * hr + up * hu]
            sv = src.get((i, s), src.get('*')) if isinstance(src, dict) else src
            face(m, P, n, sv)

def bar(m, p0, p1, h, mat, w=None):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float); d = p1 - p0; L = np.linalg.norm(d); d /= L
    a = np.array([0, 1.0, 0]) if abs(d[1]) < 0.9 else np.array([1.0, 0, 0])
    e1 = np.cross(d, a); e1 /= np.linalg.norm(e1); e2 = np.cross(d, e1)
    obox(m, (p0 + p1) / 2, (d, e1, e2), (L / 2, h, w if w else h), mat)

def ring(m, y0, y1, mat='galva', t=0.035, gap=0.012):
    """steel strap / clamp round the (tapered) pole between y0 and y1."""
    hx, hz = half((y0 + y1) / 2); hx += gap; hz += gap; hy = (y1 - y0) / 2; yc = (y0 + y1) / 2
    for s in (1, -1):
        obox(m, (s * (hx + t / 2), yc, 0), np.eye(3), (t / 2, hy, hz + t), mat)
        obox(m, (0, yc, s * (hz + t / 2)), np.eye(3), (hx, hy, t / 2), mat)

# ------------------------------------------------------------------ model
def pole(m):
    ys = np.linspace(6.0, HT, 17)                                          # foot hidden in the tyre stack
    X, Y, Z = np.eye(3)
    fcs = [(X, -Z, 0), (-X, Z, 1), (Z, X, 2), (-Z, -X, 3)]
    for n, rt, k in fcs:
        ni = 0 if abs(n[0]) > 0.5 else 2; ri = 0 if abs(rt[0]) > 0.5 else 2
        def pt(y, side):
            h = half(y); hh = {0: h[0], 2: h[1]}
            return n * hh[ni] + rt * side * hh[ri] + np.array([0, y, 0])
        x0, _, x1, _ = STRIPS[k]
        for ya, yb in zip(ys[:-1], ys[1:]):
            P = [pt(ya, -1), pt(ya, 1), pt(yb, 1), pt(yb, -1)]
            N = n + np.array([0, (BASE[ni // 2] - TOPH[ni // 2]) / HT, 0])
            r = (x0, (HT - yb) * PPF, x1, (HT - ya) * PPF)
            face(m, P, N, r)
    hx, hz = half(HT)
    face(m, [(hx, HT, hz), (hx, HT, -hz), (-hx, HT, -hz), (-hx, HT, hz)], (0, 1, 0), 'conc')

def floodlights(m):
    """v2 (user photo 207): 2 floodlights side by side, slightly offset in height, on a compact galvanised frame clamped
    to the +x face at the very top (2 bars along z + 2 posts), each lamp on a stem + U yoke."""
    n = np.array([np.cos(TILT), -np.sin(TILT), 0.0]); up = np.array([np.sin(TILT), np.cos(TILT), 0.0]); Zv = np.array([0, 0, 1.0])
    hd, hh, hw = HOUS
    FY = (43.0, 45.0); hx = half(FY[0])[0]; fb = 0.12; cbx = hx + 0.03 + fb                 # frame bars (y), their centre x
    ZF = max(abs(l[2]) for l in LAMPS) + 0.2
    for fy in FY:
        bar(m, (cbx, fy, -ZF), (cbx, fy, ZF), fb, 'galva'); ring(m, fy - 0.2, fy + 0.2, t=0.04)
    centres = []
    for lx, ly, z in LAMPS:
        c = np.array([lx, ly, z]) - n * hd; centres.append(tuple(round(float(v), 4) for v in c + n * hd))   # c = pivot
        bar(m, (cbx, FY[0] - fb, z), (cbx, FY[1] + fb, z), 0.08, 'galva')                      # frame post
        obox(m, c, (n, up, Zv), HOUS, {(0, 1): R_GLASS, (0, -1): R_FINS, '*': 'hous'})
        obox(m, c + n * (hd + 0.08) + up * (hh + 0.012), (n, up, Zv), (0.18, 0.012, hw + 0.03), 'hous')   # visor
        yb = c[0] - hd * np.cos(TILT) - hh * np.sin(TILT) - 0.12                               # yoke back bar, behind the housing
        bar(m, (cbx + 0.08, c[1], z), (yb, c[1], z), 0.065, 'galva')                           # stem
        bar(m, (yb, c[1], z - hw - 0.1), (yb, c[1], z + hw + 0.1), 0.045, 'galva', 0.08)       # yoke back bar
        for s in (1, -1):
            bar(m, (yb - 0.04, c[1], z + s * (hw + 0.075)), (c[0] + 0.06, c[1], z + s * (hw + 0.075)), 0.03, 'galva', 0.08)   # yoke arms
    return centres

def horn(m, c, yaw, pitch):
    f = np.array([np.cos(yaw) * np.cos(pitch), -np.sin(pitch), np.sin(yaw) * np.cos(pitch)])
    u = np.array([0, 1.0, 0]) - f * f[1]; u /= np.linalg.norm(u); s = np.cross(f, u)
    c = np.asarray(c, float)
    obox(m, c - f * 0.59, (f, u, s), (0.21, 0.22, 0.22), 'black')                              # driver
    secs = [(-0.38, 0.17, 0.15), (-0.05, 0.30, 0.24), (0.35, 0.44, 0.35), (0.80, 0.55, 0.45)]
    th = 0.045
    def corners(fv, hw, hh, k=0.0):
        hw -= k; hh -= k; cc = c + f * fv
        return [cc - s * hw - u * hh, cc + s * hw - u * hh, cc + s * hw + u * hh, cc - s * hw + u * hh]
    O = [corners(*q) for q in secs]; I = [corners(q[0], q[1], q[2], th if q[0] > -0.3 else th * 0.6) for q in secs]
    for i in range(len(secs) - 1):
        for e in range(4):
            a, b = e, (e + 1) % 4
            P = [O[i][a], O[i][b], O[i + 1][b], O[i + 1][a]]
            mid = sum(P) / 4; ax = c + f * ((P[0] - c) @ f + (P[2] - c) @ f) / 2
            N = np.cross(P[1] - P[0], P[3] - P[0]); N *= np.sign(N @ (mid - ax)) or 1
            face(m, P, N, 'black')
            P = [I[i][a], I[i][b], I[i + 1][b], I[i + 1][a]]
            N = np.cross(P[1] - P[0], P[3] - P[0]); N *= -np.sign(N @ (mid - ax)) or 1
            face(m, P, N, 'inner')
    for e in range(4):                                                                           # mouth rim
        a, b = e, (e + 1) % 4
        face(m, [O[-1][a], O[-1][b], I[-1][b], I[-1][a]], f, 'black')
    face(m, I[0], f, R_GRILLE)                                                                   # throat grille
    return c - f * 0.80

def speakers(m):
    sy = SPK['y']; ring(m, sy - 0.22, sy + 0.22, t=0.04)
    hx = half(sy)[0]
    for s in (1, -1):
        rear = horn(m, (SPK['x'], sy, s * SPK['z']), s * SPK['yaw'], SPK['pitch'])
        bar(m, (hx + 0.05, sy, s * 0.30), rear, 0.06, 'galva')                                  # bracket arm
        bar(m, (hx + 0.05, sy - 0.18, s * 0.30), (hx + 0.05, sy + 0.18, s * 0.30), 0.16, 'galva', 0.03)   # base plate

def back_cable(m):
    def at(y, z=0.30): return np.array([-half(y)[0] - 0.045, y, z])
    bar(m, at(6.6), at(8.5), 0.04, 'black'); bar(m, at(9.5), at(cy_top := 42.8), 0.04, 'black')
    hx = half(9.0)[0]
    obox(m, (-hx - 0.13, 9.0, 0.12), np.eye(3), (0.13, 0.5, 0.34), 'box')                      # junction box
    return cy_top

def tyre_stack(m):
    """v3: stack of STACK['n'] tyres round the foot, wrapped in a white tarp: lathe (smooth normals) whose profile bulges at
    each tyre and dips at each joint, a skirt on the ground, the top sagging into the tyre hole then gathered round the pole
    (rounded-rectangle opening), tied with a rope, a short frill above. Folds = radial displacement of single vertices."""
    S = STACK; sg = S['seg']; rg = np.random.default_rng(7); top = S['n'] * S['t']
    th = np.linspace(0, 2 * np.pi, sg + 1)                                                       # last column = first (uv seam)
    def gather(y, off):                                                                          # superellipse round the pole
        hx, hz = half(y); a, b = hx * 1.18 + off, hz * 1.18 + off; c, s_ = np.abs(np.cos(th)), np.abs(np.sin(th))
        return 1 / ((c / a) ** 4 + (s_ / b) ** 4) ** 0.25
    full = lambda r: np.full(sg + 1, float(r))
    prof = [(0.0, full(S['r0'] + 0.14)), (0.07, full(S['r0'] + 0.07))]                         # skirt on the ground
    for j in range(S['n']):
        for tt in ((0.0, 1 / 3, 2 / 3) if j else (1 / 3, 2 / 3)):
            prof.append((j * S['t'] + tt * S['t'], full(S['r0'] + S['bulge'] * np.sin(np.pi * tt) ** 0.6)))
    prof += [(top - 0.02, full(S['r0'] + 0.01)), (top + 0.06, full(S['r0'] - 0.10)), (top + 0.10, np.maximum(0.86, gather(top, 0.10))),
             (top + 0.13, gather(top, 0.07)), (top + 0.24, gather(top, 0.03))]
    n_main = len(prof)
    Y = np.array([p[0] for p in prof]); R = np.array([p[1] for p in prof])
    # folds: vertical creases (a few columns pushed in / out over a height range), pleats where the tarp is gathered
    D = np.zeros_like(R)
    for _ in range(9):
        k = rg.integers(0, sg); ya, yb = sorted(rg.uniform(0, top, 2)); amp = rg.choice((-1, 1)) * rg.uniform(0.025, 0.045)
        w = np.clip(1 - np.abs(Y - (ya + yb) / 2) / ((yb - ya) / 2 + 0.6), 0, 1)
        D[:, k] += amp * w; D[:, (k + 1) % sg] -= 0.4 * amp * w
    D += rg.normal(0, 0.008, D.shape) * (Y < top)[:, None]
    pl = np.where(np.arange(sg + 1) % 2 == 0, 1.0, -1.0) * 0.035
    D[n_main - 3:] += pl[None, :] * np.array([0.5, 0.8, 1.0])[:, None]
    D[:, sg] = D[:, 0]; R = R + D
    def grid(Y, R, rect, vlen):
        P = np.stack([R * np.cos(th)[None], np.repeat(Y[:, None], sg + 1, 1), -R * np.sin(th)[None]], -1)
        dth = np.roll(P[:, :-1], -1, 1) - np.roll(P[:, :-1], 1, 1); dth = np.concatenate([dth, dth[:, :1]], 1)
        dv = np.gradient(P, axis=0)
        N = np.cross(dv, dth); rad = P.copy(); rad[..., 1] = 0
        if np.sum(N[len(Y) // 2] * rad[len(Y) // 2]) < 0: N = -N
        N /= np.linalg.norm(N, axis=-1, keepdims=True)
        x0, y0, x1, y1 = rect; base = len(m.V)
        for i in range(len(Y)):
            for j in range(sg + 1):
                m.V.append((*P[i, j], *N[i, j], *m.uv_px(x0 + (x1 - x0) * j / sg, y0 + (y1 - y0) * vlen[i])))
        for i in range(len(Y) - 1):
            for j in range(sg):
                a, b, c, d = [base + q for q in (i * (sg + 1) + j, i * (sg + 1) + j + 1, (i + 1) * (sg + 1) + j + 1, (i + 1) * (sg + 1) + j)]
                for tri in ((a, b, c), (a, c, d)):
                    p0, p1, p2 = [np.array(m.V[q][:3]) for q in tri]; nn = sum(np.array(m.V[q][3:6]) for q in tri)
                    m.I += list(tri) if np.cross(p1 - p0, p2 - p0) @ nn > 0 else [tri[0], tri[2], tri[1]]
    # v along the profile arc length, row 0 of the tarp texture = top of the tarp
    rm = R.mean(1); L = np.concatenate([[0], np.cumsum(np.hypot(np.diff(Y), np.diff(rm)))]); v = 1 - L / L[-1]
    grid(Y, R, R_TARP, v)
    yr = top + 0.24; rr = gather(yr, 0.03) + pl * 1.0
    grid(np.array([yr - 0.01, yr + 0.035, yr + 0.08, yr + 0.09]), np.stack([rr + 0.005, rr + 0.04, rr + 0.04, rr - 0.005]), R_ROPE,
         np.array([1.0, 0.65, 0.35, 0.0]))                                                       # rope
    yf = yr + 0.09; ff = gather(yf, 0.03) + pl * 1.3
    grid(np.array([yf, yf + 0.10, yf + 0.16]), np.stack([ff, ff + 0.04 + pl * 0.6, ff + 0.09 + pl * 1.2]),
         (R_TARP[0], R_TARP[1], R_TARP[2], R_TARP[1] + 40), np.array([1.0, 0.5, 0.0]))            # frill above the rope

def build_model():
    m = Mesh(TW, TH)
    pole(m); centres = floodlights(m); speakers(m); back_cable(m); tyre_stack(m)
    return m, centres

def shape():
    rows = [(0, y, 0, 1.3, 0.5, 150, 8) for y in (1.3, 2.6, 3.9, 5.2)]                         # wrapped tyre stack: padded
    rows += [(0, y, 0, 0.6, 0.5, 1000, 200) for y in (7.2, 8.4, 9.6)]                          # bare pole above it
    return '\n'.join([str(len(rows))] + [' '.join(f'{v:.4f}' if k < 4 else f'{v:g}' for k, v in enumerate(r)) for r in rows]) + '\n'

# ------------------------------------------------------------------ preview (software z-buffer, NOT a game render)
def preview(out_path):
    from preview_stt_scene import Cam, raster, load_jm
    from rider_gate import scale_person
    V, I = load_jm(f'{OUTD}/pole_concrete.jm'); t = np.asarray(Image.open(f'{OUTD}/pole_concrete.png').convert('RGBA'), np.float32) / 255
    objs = [(V, I, t), scale_person((3.0, 0, 2.2))]
    Lg = np.array([0.55, 0.75, 0.35]); Lg /= np.linalg.norm(Lg)
    def shot(eye, tgt, W=620, H=980, fov=50):
        cam = Cam(eye, tgt, W, H, fov); img = np.zeros((H, W, 3), np.float32)
        sky = np.linspace(0, 1, H)[:, None, None]; img[:] = np.array([0.55, 0.70, 0.90]) * (1 - sky) + np.array([0.82, 0.86, 0.90]) * sky
        zb = np.full((H, W), np.inf, np.float32)
        gs = np.arange(-120, 121, 3.0); GX, GZ = np.meshgrid(gs, gs); P = np.stack([GX, np.zeros_like(GX), GZ], -1).reshape(-1, 3)
        n = len(gs); ii, jj = np.meshgrid(np.arange(n - 1), np.arange(n - 1), indexing='ij'); a = (ii * n + jj).ravel()
        Ig = np.concatenate([np.stack([a, a + 1, a + n], 1), np.stack([a + 1, a + n + 1, a + n], 1)])
        rg = np.random.default_rng(0); C = np.array([0.55, 0.43, 0.31]) * (0.92 + 0.12 * rg.random((len(P), 1)))
        raster(img, zb, cam, P, Ig, lambda ti, B: (C[Ig[ti]] * B[:, :, None]).sum(1))
        for V_, Ii, tex in objs:
            th, tw = tex.shape[:2]
            def col(ti, B, V_=V_, Ii=Ii, tex=tex, th=th, tw=tw):
                uv = (V_[Ii[ti], 6:8][None] * B[:, :, None]).sum(1)
                py = np.clip((1 - uv[:, 1]) * th, 0, th - 1).astype(int); px = np.clip(uv[:, 0] * tw, 0, tw - 1).astype(int)
                nn = (V_[Ii[ti], 3:6][None] * B[:, :, None]).sum(1)
                return tex[py, px, :3] * (0.62 + 0.45 * np.clip(nn @ Lg, 0, 1))[:, None]
            raster(img, zb, cam, V_[:, :3], Ii, col)
        return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    views = [shot((44, 8, 22), (0, 23, 0), fov=60),                 # whole pole from the track, 3/4
             shot((11, 38.5, 6), (1.0, 44.0, 0), fov=45),           # head: 2 floodlights on their frame
             shot((-9, 41.5, -6), (0.5, 44.0, 0), fov=45),           # head from behind: yokes, fins, frame, clamps
             shot((7.0, 14.5, 4.0), (0.8, 16.8, 0), fov=45),         # speakers
             shot((9.0, 4.6, -3.0), (0.3, 3.8, 1.2), fov=50)]         # foot: wrapped tyre stack, person, ID plate
    W_, H_ = views[0].size; sheet = Image.new('RGB', (W_ * len(views), H_), (255, 255, 255))
    for k, v in enumerate(views): sheet.paste(v, (k * W_, 0))
    os.makedirs(os.path.dirname(out_path), exist_ok=True); sheet.save(out_path); print('preview', out_path)

def build(outd=OUTD):
    os.makedirs(outd, exist_ok=True)
    img = build_texture(); m, centres = build_model()
    nv, nt = m.write(f'{outd}/pole_concrete.jm', (0, 0, 0, 0, 0)); img.save(f'{outd}/pole_concrete.png', optimize=True)
    open(f'{outd}/pole_concrete.shp', 'w', newline='\n').write(shape())
    P = np.array([v[:3] for v in m.V])
    print(f'pole_concrete: {nv} vertices, {nt} triangles, bbox {P.min(0).round(3)} .. {P.max(0).round(3)} ft')
    print('lamp-face centres:', centres)
    return centres

if __name__ == '__main__':
    build()
    if '--preview' in sys.argv: preview(os.path.join(os.path.dirname(ROOT), 'apercus_sgm', 'pole_concrete_3d.png'))
