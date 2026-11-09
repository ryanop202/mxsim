"""Plain WHITE inflatable arch over a walkway (Saint-Georges, replaces arch_white = the Red Bull arch the user disliked):
no logo, no round emblem, no spikes - "just a normal arch". One continuous round tube (diameter A['d']) bent in the local
x-y plane: straight legs near the ground, a half-ellipse above; puffy look = a slight bulge between soft sewn seams every
~3 ft (geometry + soft shading rings in the texture), white with very light grey shading, matte. Each foot stands on a flat
black base pad. props_usland.Mesh (1 ft units, y up), origin = ground, centre of the walkway; the walkway runs along z.
Guy cables (black thin tubes + a small dark ground anchor) are added by the track with arch_model(cables=...), their top
end taken from arch_attach(t, side).
Run: python scripts/arch_tube.py [--no-preview] -> assets/props/arch_tube.jm / .png (no cables)
     + ../apercus_sgm/arch_tube_3d.png (preview with 4 example cables, NOT a game render)"""
import os, sys
import numpy as np
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
from props_usland import Mesh, palette, OUTD

A = dict(width=34.0, top=19.5, d=3.8,   # v29 (user): thicker (was 2.6)
          leg=3.5, seam=3.0, sides=16, pad=(3.0, 3.0, 0.3), bulge=0.045,
         cable_r=0.035, cable_sides=5, anchor=(0.5, 0.25, 0.5))
# width = outer width (outside of the two legs), top = top of the tube, leg = height of the centreline where the straight
# legs end, seam = target seam spacing along the tube (ft), bulge = radius drop at a seam (fraction of the radius)
WHITE, BLACK, ANCHOR = (243, 243, 241), (26, 26, 28), (48, 46, 44)
TW = 1024
TH = 2048                                       # v41: room for the logo strip (the palette stays at the bottom)
ROWS = dict(seg=(8, 440), foot=(452, 884))
LOGO = dict(name='fosure', rows=(940, 1839), nseg=3, length=7.6, height=2.3)   # v41 (user): Fosure on top of the arch, both faces     # texture strips (f = 0 at the bottom row, f = 1 at the top row)
F_RINGS = (0.0, 0.12, 0.35, 0.65, 0.88, 1.0)  # rings inside one seam-to-seam segment
MATERIAL = (0, 0, 0, 0, 0)                     # matte

R = A['d'] / 2
AX = A['width'] / 2 - R                         # centreline half-width (leg axes at x = +-AX)
Y0 = A['pad'][2]                                # tube bottom on the pad

# ------------------------------------------------------------------ centreline (arc-length parameterised)
def _centreline():
    yt = A['top'] - R; b = yt - A['leg']
    leg = np.linspace(Y0, A['leg'], 40)
    th = np.linspace(np.pi, 0, 3000)
    P = np.concatenate([np.stack([np.full_like(leg, -AX), leg], 1),
                        np.stack([AX * np.cos(th), A['leg'] + b * np.sin(th)], 1)[1:],
                        np.stack([np.full_like(leg, AX), leg[::-1]], 1)[1:]])
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    return P, s
_P, _S = _centreline()
LENGTH = float(_S[-1])
NSEG = 2 * int(round((LENGTH / A['seam'] - 1) / 2)) + 1     # odd: a puffy bulge (not a seam) at the very top
SEG = LENGTH / NSEG

def centre(s):
    """centreline point (x, y, 0) and unit tangent at arc length s (0 = left foot)."""
    s = float(np.clip(s, 0, LENGTH)); x = np.interp(s, _S, _P[:, 0]); y = np.interp(s, _S, _P[:, 1])
    h = 0.05; a, b = max(s - h, 0), min(s + h, LENGTH)
    T = np.array([np.interp(b, _S, _P[:, 0]) - np.interp(a, _S, _P[:, 0]), np.interp(b, _S, _P[:, 1]) - np.interp(a, _S, _P[:, 1]), 0.0])
    return np.array([x, y, 0.0]), T / np.linalg.norm(T)

def radius(f):
    """tube radius inside a segment (f in [0, 1] between two seams): pinched at the seams, puffy in between."""
    return R * (1 - A['bulge'] + A['bulge'] * np.sin(np.pi * np.clip(f, 0, 1)) ** 0.6)

def _f_of_s(s):
    k = min(int(s // SEG), NSEG - 1); return (s - k * SEG) / SEG

def arch_attach(t, side=+1):
    """point (x, y, z) on the tube surface at arch parameter t in [0, 1] (arc length; 0 = left foot (-x), 1 = right foot),
    on the +z face (side=+1) or the -z face (side=-1)."""
    s = float(np.clip(t, 0, 1)) * LENGTH; C, _ = centre(s)
    return tuple(C + np.array([0, 0, (1 if side >= 0 else -1) * radius(_f_of_s(s))]))

# ------------------------------------------------------------------ texture
def texture():
    """u = angle round the tube (0 = outer side, 0.25 = +z face, 0.5 = inner side / underside, 0.75 = -z face),
    v = along one seam-to-seam segment. Soft seam rings, a very light grey on the inner side, AO on the foot strip."""
    img = np.zeros((TH, TW, 3)) + np.array(WHITE, float)
    ph = (np.arange(TW) + 0.5) / TW * 2 * np.pi
    inner = 1 - 0.07 * np.clip(-np.cos(ph), 0, 1) ** 1.5                     # underside a touch greyer
    rg = np.random.default_rng(3)
    for name, (r0, r1) in ROWS.items():
        n = r1 - r0 + 1; f = 1 - (np.arange(n) + 0.5) / n                     # f = 1 at the top row of the strip
        e = np.minimum(f, 1 - f) * SEG                                        # ft to the nearest seam
        k = 1 - 0.14 * np.exp(-(e / 0.035) ** 2) - 0.05 * np.exp(-(e / 0.22) ** 2) + 0.012 * np.sin(np.pi * f)
        k = k[:, None] * inner[None, :]
        if name == 'foot':                                                    # f = 0 is the ground end: soft AO
            h = f * SEG
            k = k * (1 - 0.16 * np.clip(1 - h / 1.4, 0, 1) ** 1.6)[:, None]
        k = k + rg.normal(0, 0.004, k.shape)                                  # matte vinyl, very fine grain
        img[r0:r1 + 1] *= k[..., None]
    if LOGO:                                                                  # v41: the top segments' strip = seg strip x nseg + logo
        r0, r1 = LOGO['rows']; n = LOGO['nseg']; hseg = (r1 - r0 + 1) // n; s0, s1 = ROWS['seg']
        segim = Image.fromarray(np.clip(img[s0:s1 + 1], 0, 255).astype(np.uint8)).resize((TW, hseg), Image.LANCZOS)
        for q in range(n): img[r0 + q * hseg:r0 + (q + 1) * hseg] = np.asarray(segim, float)
        import stt_ads as AD_
        lg = AD_.logo(LOGO['name'])
        ppa = hseg / SEG; ppr = TW / (2 * np.pi * R)                           # px per ft along the arch / round the tube
        k = min(LOGO['length'] / lg.width, LOGO['height'] / lg.height)
        wl, hl = lg.width * k, lg.height * k                                   # ft
        cy = r0 + n * hseg / 2
        for u0, rot in ((0.25, 90), (0.75, -90)):                              # +z face: reads left to right from +z; -z face from -z
            q_ = lg.resize((max(2, int(wl * ppa)), max(2, int(hl * ppr))), Image.LANCZOS).rotate(rot, expand=True)
            a_ = np.asarray(q_, float) / 255.0; h_, w_ = a_.shape[:2]
            y0, x0 = int(cy - h_ / 2), int(u0 * TW - w_ / 2)
            sub = img[y0:y0 + h_, x0:x0 + w_]; al = a_[..., 3:4]
            img[y0:y0 + h_, x0:x0 + w_] = sub * (1 - al) + a_[..., :3] * 255 * al
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    pal = palette(im, ['blk', 'anchor'], [BLACK, ANCHOR])
    return im, pal

# ------------------------------------------------------------------ mesh helpers
def _smooth(m, P, N, UV):
    a = len(m.V); P = [np.asarray(p, float) for p in P]; N = [np.asarray(n, float) / np.linalg.norm(n) for n in N]
    if np.dot(np.cross(P[1] - P[0], P[2] - P[0]), sum(N)) < 0: P, N, UV = P[::-1], N[::-1], UV[::-1]
    for p, n, t in zip(P, N, UV): m.V.append((*p, *n, *t))
    for k in range(1, len(P) - 1): m.I += [a, a + k, a + k + 1]

def _flat_uv(m, src):
    """plain colour (the 'top' shade sub-square of a palette entry, no baked shade)."""
    px, py = src[1]; return m.uv_px(px - 16, py - 16)

def _tube_body(m):
    ns = A['sides']; ph = np.linspace(0, 2 * np.pi, ns + 1); Z = np.array([0, 0, 1.0])
    for k in range(NSEG):
        foot = k == 0 or k == NSEG - 1; r0, r1 = ROWS['foot' if foot else 'seg']
        km = NSEG // 2; nl = LOGO['nseg'] if LOGO else 0
        if LOGO and abs(k - km) <= nl // 2:                                   # v41: the logo strip (k increasing = higher up the strip)
            hseg = (LOGO['rows'][1] - LOGO['rows'][0] + 1) // nl; q = (nl - 1) - (k - (km - nl // 2))
            r0 = LOGO['rows'][0] + q * hseg; r1 = r0 + hseg - 1
        flip = k == NSEG - 1                                                   # right foot: ground end at the bottom row too
        rings = []
        for f in F_RINGS:
            s = (k + f) * SEG; C, T = centre(s); No = np.array([-T[1], T[0], 0.0])
            r = radius(f); df = 1e-3
            dr = 0.0 if f in (0.0, 1.0) else (radius(f + df) - radius(f - df)) / (2 * df * SEG)
            fv = 1 - f if flip else f; vy = r1 - fv * (r1 - r0)
            ring = []
            for j, p in enumerate(ph):
                D = np.cos(p) * No + np.sin(p) * Z
                ring.append((C + r * D, D - dr * T, m.uv_px(j / ns * TW, vy)))
            rings.append(ring)
        for i in range(len(rings) - 1):
            for j in range(ns):
                q = [rings[i][j], rings[i][j + 1], rings[i + 1][j + 1], rings[i + 1][j]]
                _smooth(m, [a[0] for a in q], [a[1] for a in q], [a[2] for a in q])
    # flat caps under the feet (sitting on the pads)
    for s in (0.0, LENGTH):
        C, T = centre(s); No = np.array([-T[1], T[0], 0.0]); r = radius(0.0)
        P = [C + r * (np.cos(p) * No + np.sin(p) * Z) for p in ph[:-1]]
        uv = m.uv_px(TW / 2, ROWS['foot'][1] - 2)
        _smooth(m, P, [np.array([0, -1.0, 0])] * len(P), [uv] * len(P))

def _cable(m, p0, p1, pal):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float); d = p1 - p0; L = np.linalg.norm(d); d /= L
    a = np.array([0, 1.0, 0]) if abs(d[1]) < 0.9 else np.array([1.0, 0, 0])
    e1 = np.cross(d, a); e1 /= np.linalg.norm(e1); e2 = np.cross(d, e1)
    n = A['cable_sides']; ang = np.linspace(0, 2 * np.pi, n + 1); uv = _flat_uv(m, pal['blk'])
    p0 = p0 - d * 0.08                                                        # starts just inside the tube skin
    for k in range(n):
        D0 = np.cos(ang[k]) * e1 + np.sin(ang[k]) * e2; D1 = np.cos(ang[k + 1]) * e1 + np.sin(ang[k + 1]) * e2
        rr = A['cable_r']
        _smooth(m, [p0 + rr * D0, p0 + rr * D1, p1 + rr * D1, p1 + rr * D0], [D0, D1, D1, D0], [uv] * 4)
    ax, ay, az = A['anchor']; x, y, z = p1                                     # small dark ground anchor (stake plate)
    m.box(x - ax / 2, x + ax / 2, y - 0.12, y - 0.12 + ay, z - az / 2, z + az / 2, {'*': pal['anchor']})

def arch_model(cables=()):
    """-> (Mesh, PIL.Image). cables = [((x, y, z) start, (x, y, z) end), ...] in model coordinates (start normally from
    arch_attach), each a thin black tube with a small dark anchor at its end."""
    img, pal = texture(); m = Mesh(TW, TH)
    _tube_body(m)
    px, pz, ph = A['pad']
    for x in (-AX, AX): m.box(x - px / 2, x + px / 2, 0.0, ph, -pz / 2, pz / 2, {'*': pal['blk']})
    for c0, c1 in cables: _cable(m, c0, c1, pal)
    return m, img

# ------------------------------------------------------------------ preview (software z-buffer, NOT a game render)
MOUNDS = [(sx * 16.0, sz * 32.0) for sx in (-1, 1) for sz in (-1, 1)]       # preview only: 4 humps (mound slopes)
def mound_h(x, z):
    return sum(15.0 * np.exp(-((x - mx) ** 2 + (z - mz) ** 2) / (2 * 6.5 ** 2)) for mx, mz in MOUNDS)

def example_cables():
    """4 cables from t = 0.25 / 0.75 on both faces, outward and down to points ~10 ft up the preview humps."""
    out = []
    for t in (0.25, 0.75):
        for side in (1, -1):
            p0 = np.array(arch_attach(t, side)); x = 1.15 * p0[0]
            z = side * 32.0; mx = np.sign(x) * 16.0
            # walk from the hump top towards the arch until the hump is 10 ft high
            for zz in np.linspace(z, 0, 400):
                if mound_h(x, zz) <= 10.0: break
            out.append((tuple(p0), (x, float(mound_h(x, zz)), float(zz))))
    return out

def preview(out_path):
    from preview_stt_scene import Cam, raster
    from rider_gate import scale_person
    cab = example_cables(); m, img = arch_model(cab)
    V = np.array(m.V, np.float32); I = np.array(m.I, np.int64).reshape(-1, 3); tex = np.asarray(img.convert('RGBA'), np.float32) / 255
    objs = [(V, I, tex), scale_person((-10.0, 0, -3.0)), scale_person((3.0, 0, 2.0))]
    Lg = np.array([-0.45, 0.8, 0.4]); Lg /= np.linalg.norm(Lg)
    for c0, c1 in cab: print('cable', np.round(c0, 2), '->', np.round(c1, 2), 'length %.1f ft' % np.linalg.norm(np.subtract(c1, c0)))
    def shot(eye, tgt, W=900, H=700, fov=55):
        cam = Cam(eye, tgt, W, H, fov); im = np.zeros((H, W, 3), np.float32)
        sky = np.linspace(0, 1, H)[:, None, None]; im[:] = np.array([0.55, 0.70, 0.90]) * (1 - sky) + np.array([0.82, 0.86, 0.90]) * sky
        zb = np.full((H, W), np.inf, np.float32)
        gs = np.arange(-60, 61, 2.0); GX, GZ = np.meshgrid(gs, gs); GY = mound_h(GX, GZ)
        P = np.stack([GX, GY, GZ], -1).reshape(-1, 3)
        n = len(gs); ii, jj = np.meshgrid(np.arange(n - 1), np.arange(n - 1), indexing='ij'); a = (ii * n + jj).ravel()
        Ig = np.concatenate([np.stack([a, a + 1, a + n], 1), np.stack([a + 1, a + n + 1, a + n], 1)])
        gy_, gx_ = np.gradient(GY, 2.0); Ng = np.stack([-gx_, np.ones_like(GY), -gy_], -1).reshape(-1, 3); Ng /= np.linalg.norm(Ng, axis=1)[:, None]
        rg = np.random.default_rng(0); C = np.array([0.55, 0.43, 0.31]) * (0.92 + 0.12 * rg.random((len(P), 1))) * (0.6 + 0.45 * np.clip(Ng @ Lg, 0, 1))[:, None]
        raster(im, zb, cam, P, Ig, lambda ti, B: (C[Ig[ti]] * B[:, :, None]).sum(1))
        for V_, I_, t_ in objs:
            th, tw = t_.shape[:2]
            def uvpx(ti, B, V_=V_, I_=I_, tw=tw, th=th):
                uv = (V_[I_[ti], 6:8][None] * B[:, :, None]).sum(1)
                return np.clip((1 - uv[:, 1]) * th, 0, th - 1).astype(int), np.clip(uv[:, 0] * tw, 0, tw - 1).astype(int)
            def col(ti, B, V_=V_, I_=I_, t_=t_):
                py, px = uvpx(ti, B); nn = (V_[I_[ti], 3:6][None] * B[:, :, None]).sum(1)
                nn /= np.linalg.norm(nn, axis=1)[:, None] + 1e-9
                return t_[py, px, :3] * (0.55 + 0.45 * np.clip(nn @ Lg, 0, 1))[:, None]
            raster(im, zb, cam, V_[:, :3], I_, col)
        return Image.fromarray((np.clip(im, 0, 1) * 255).astype(np.uint8))
    views = [shot((0.0, 4.5, 21.0), (0.0, 10.0, 0.0), fov=80),               # down the walkway, between the humps
             shot((38.0, 20.0, 40.0), (0.0, 8.0, 0.0), fov=55),               # 3/4 from above, cables to the humps
             shot((62.0, 9.0, 4.0), (0.0, 9.0, 0.0), fov=55),                 # side on (along x)
             shot((-5.0, 4.5, 11.0), (-15.0, 3.5, 0.0), fov=55)]              # left foot close-up, base pad, person
    W_, H_ = views[0].size; sheet = Image.new('RGB', (W_ * 2, H_ * 2), (255, 255, 255))
    for k, v in enumerate(views): sheet.paste(v, ((k % 2) * W_, (k // 2) * H_))
    os.makedirs(os.path.dirname(out_path), exist_ok=True); sheet.save(out_path); print('preview', out_path)

def build(outd=OUTD):
    os.makedirs(outd, exist_ok=True); m, img = arch_model()
    nv, nt = m.write(f'{outd}/arch_tube.jm', MATERIAL); img.save(f'{outd}/arch_tube.png', optimize=True)
    P = np.array([v[:3] for v in m.V]); print(f'arch_tube: {nv} vertices, {nt} triangles, {NSEG} segments of {SEG:.2f} ft '
                                              f'(tube {LENGTH:.1f} ft), bbox {P.min(0).round(2)} .. {P.max(0).round(2)} ft')
    return nv, nt

if __name__ == '__main__':
    build()
    if '--no-preview' not in sys.argv: preview(os.path.join(os.path.dirname(ROOT), 'apercus_sgm', 'arch_tube_3d.png'))
