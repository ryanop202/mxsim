"""Mobile mesh fence panel ("barriere Heras" / cloture de chantier), Saint-Georges v12, from the user's photo and sizes:
panel 3.50 m long x 1.90 m high, mesh 155 x 225 mm (vertical wires every ~155 mm, horizontal ones every ~215-225 mm),
40 mm galvanised steel frame tubes, wire 3.4 mm (drawn 6.7 mm so it still shows in game), a concrete foot block between
every two panels, a clamp joining the two tubes near the top. Made from scratch with props_usland.Mesh (doc 12 conventions:
1 unit = 1 ft, y up, baked shades, one texture, rounded edges, matte grain only on the concrete).
One model = one panel + the block under its left end (x = -L/2): placed every L ft along the fence line, the blocks hold two
tubes each (this panel's left one, the previous panel's right one). Origin = middle of the panel at ground level.
Run: python scripts/fence_heras.py -> assets/props/fence_heras.jm / .png"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
from props_usland import Mesh, palette, OUTD

FT = 1 / 0.3048
HF = dict(L=3.50 * FT, ytop=1.95 * FT, ybot=0.24 * FT, tube_r=0.020 * FT, bend=0.075 * FT, tube_dx=0.05 * FT,
          wire_r=0.00335 * FT, nv=22, nh=8,                                   # 22 / 8 intervals: wires every 155 / ~215 mm
          block=(0.70 * FT, 0.15 * FT, 0.22 * FT), block_r=0.02 * FT,          # length (along the fence), height, width
          clamp_y=1.62 * FT, clamp=(0.24 * FT, 0.09 * FT, 0.065 * FT))
STEEL, WIRE, CLAMP, CONC = (172, 176, 181), (186, 189, 193), (198, 172, 96), (178, 176, 168)

def concrete(w, h, shade, seed, holes=False, recess=False):
    """rough light concrete (speckle + soft blotches), baked shade; top: two tube holes; sides: the hand-hold recess."""
    r = np.random.default_rng(seed)
    a = np.zeros((h, w, 3)) + np.array(CONC, float)
    blot = np.asarray(Image.fromarray((r.random((h // 8 + 2, w // 8 + 2)) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), float) / 255
    a *= (0.93 + 0.10 * blot)[:, :, None]
    a *= (1 + 0.06 * r.normal(0, 1, (h, w)))[:, :, None]                      # fine grain (matte material)
    im = Image.fromarray(np.clip(a * shade, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    if holes:                                                                  # two holes
        for cx in (w / 2 - w * 0.114, w / 2 + w * 0.114):   # under the two tubes (+-0.08 m)
            rr = h * 0.17; d.ellipse([cx - rr, h / 2 - rr, cx + rr, h / 2 + rr], fill=(60, 60, 58))
            d.ellipse([cx - rr * 0.6, h / 2 - rr * 0.6, cx + rr * 0.6, h / 2 + rr * 0.6], fill=(35, 35, 34))
    if recess:                                                                 # recessed hand-hold, darker inside, lit lower lip
        x0, x1, y0, y1 = int(w * 0.40), int(w * 0.60), int(h * 0.35), int(h * 0.80)
        d.rectangle([x0, y0, x1, y1], fill=tuple(int(c * shade * 0.55) for c in CONC))
        d.line([x0, y1, x1, y1], fill=tuple(int(min(255, c * shade * 1.08)) for c in CONC), width=2)
    return im.filter(ImageFilter.GaussianBlur(0.6))

def heras_texture():
    img = Image.new('RGB', (512, 512), STEEL)
    rects = dict(top=(8, 8, 264, 88), side=(8, 104, 264, 160), end=(280, 104, 344, 160))
    img.paste(concrete(256, 80, 1.0, 1, holes=True), rects['top'][:2])
    img.paste(concrete(256, 56, 0.82, 2, recess=True), rects['side'][:2])
    img.paste(concrete(64, 56, 0.74, 3), rects['end'][:2])
    pal = palette(img, ['steel', 'wire', 'clamp', 'conc'], [STEEL, WIRE, CLAMP, (168, 166, 158)])
    pal.update(rects)
    return img, pal

def sweep(m, pts, r, src, seg=8):
    """round tube of radius r along a polyline (rings at every point, normal-averaged tangents), open ends."""
    pts = [np.asarray(p, float) for p in pts]; n = len(pts)
    tg = [pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)] for i in range(n)]; tg = [t / np.linalg.norm(t) for t in tg]
    rings = []
    for p, t in zip(pts, tg):
        a = np.array([0, 0, 1.0]) if abs(t[2]) < 0.9 else np.array([1.0, 0, 0])
        e1 = np.cross(t, a); e1 /= np.linalg.norm(e1); e2 = np.cross(t, e1)
        rings.append([p + r * (np.cos(k * 2 * np.pi / seg) * e1 + np.sin(k * 2 * np.pi / seg) * e2) for k in range(seg)])
    uv = m.uv_px(*src[1])
    for i in range(n - 1):
        A, B = rings[i], rings[i + 1]; c = (pts[i] + pts[i + 1]) / 2
        for k in range(seg):
            j = (k + 1) % seg; q = [A[k], A[j], B[j], B[k]]; N = np.mean(q, axis=0) - c; N /= np.linalg.norm(N)
            m.quad(q, N, lambda p_: uv)

def wire(m, p0, p1, r, src):
    """thin wire: triangular prism (3 faces, open ends)."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float); d = p1 - p0; d /= np.linalg.norm(d)
    a = np.array([0, 0, 1.0]); e1 = np.cross(d, a); e1 /= np.linalg.norm(e1); e2 = np.cross(d, e1)
    dirs = [np.cos(k * 2 * np.pi / 3 + np.pi / 2) * e2 + np.sin(k * 2 * np.pi / 3 + np.pi / 2) * e1 for k in range(3)]
    uv = m.uv_px(*src[1])
    for k in range(3):
        j = (k + 1) % 3; N = dirs[k] + dirs[j]; N /= np.linalg.norm(N)
        m.quad([p0 + r * dirs[k], p0 + r * dirs[j], p1 + r * dirs[j], p1 + r * dirs[k]], N, lambda p_: uv)

def heras_model(pal):
    m = Mesh(512, 512); L, yt, yb, R, rb = HF['L'], HF['ytop'], HF['ybot'], HF['tube_r'], HF['bend']
    bl, bh, bw = HF['block']; xl, xr = -L / 2 + HF['tube_dx'] * 1.6, L / 2 - HF['tube_dx'] * 1.6
    foot = bh * 0.35                                                            # tubes go down into the block holes
    # frame: one bent tube (left leg, rounded top corners, top rail, right leg) + the welded bottom rail
    arc = lambda cx, a0, a1: [(cx + rb * np.cos(t), yt - rb + rb * np.sin(t), 0.0) for t in np.linspace(a0, a1, 5)]
    frame = [(xl, foot, 0.0)] + arc(xl + rb, np.pi, np.pi / 2) + arc(xr - rb, np.pi / 2, 0.0) + [(xr, foot, 0.0)]
    sweep(m, frame, R, pal['steel'])
    sweep(m, [(xl, yb, 0.0), (xr, yb, 0.0)], R * 0.85, pal['steel'])
    # mesh: vertical wires (stop under the rounded corners), horizontal wires tube to tube, welded on the track side (+z)
    zw = R * 0.35; r = HF['wire_r']
    for k in range(1, HF['nv']):
        x = xl + (xr - xl) * k / HF['nv']; dx = max(0.0, rb - min(x - xl, xr - x))
        top = yt - rb + np.sqrt(max(rb * rb - dx * dx, 0.0)) if dx > 0 else yt
        wire(m, (x, yb, zw), (x, top - R * 0.5, zw), r, pal['wire'])
    for k in range(1, HF['nh']):
        y = yb + (yt - yb) * k / HF['nh']; wire(m, (xl, y, zw + r), (xr, y, zw + r), r, pal['wire'])
    # concrete block under the joint (x = -L/2): rounded edges along its length, holes on top, hand-holds on the sides
    faces = {'+y': ('r', pal['top']), '+z': ('r', pal['side']), '-z': ('r', pal['side']), '+x': ('r', pal['end']), '-x': ('r', pal['end'])}
    m.rbox(-L / 2 - bl / 2, -L / 2 + bl / 2, 0.0, bh, -bw / 2, bw / 2, HF['block_r'], 0, faces, pal['conc'], seg=3)
    # clamp joining the two tubes at the joint, near the top (rounded vertical edges)
    cl, ch, cw = HF['clamp']; cy = HF['clamp_y']
    m.rbox(-L / 2 - cl / 2, -L / 2 + cl / 2, cy - ch / 2, cy + ch / 2, -cw, cw, cw * 0.45, 1, {'*': pal['clamp']}, pal['clamp'], seg=3)
    return m

if __name__ == '__main__':
    img, pal = heras_texture(); os.makedirs(OUTD, exist_ok=True)
    m = heras_model(pal); nv, nt = m.write(f'{OUTD}/fence_heras.jm', (12, 0.5, 0.3, 0.3, 0.3)); img.save(f'{OUTD}/fence_heras.png')
    V = np.array([v[:3] for v in m.V]); print('fence_heras', nv, 'vertices', nt, 'triangles; bbox', V.min(0).round(2), V.max(0).round(2))
