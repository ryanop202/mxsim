"""Start gate floor plates (Saint-Georges, user photo 223): behind each gate the rear wheel stands on a SHORT steel plate of
expanded metal (diamond mesh, galvanised), framed by a red painted steel rectangle lying on the ground; a timber beam runs
across the whole row behind the plates. Made from scratch with props_usland.Mesh (doc 12: 1 unit = 1 ft, y up, one
texture, baked shades, matte grain).

floor_mesh(n_gates=22, pitch=4.0, length=5.0) -> (Mesh, PIL RGBA image)
  local frame: plates side by side along z (gate k centred at z = (k - (n-1)/2) * pitch), from x = 0 (the gate line) to
  x = +length (behind the gates); plate (diamond mesh, alpha cut-out holes: the dirt shows through) at y = 0.06, red frame
  (0.2 ft flat tube) around it, top at y = 0.10, sides sunk to y = -0.04 (no gap on uneven ground); timber beam
  0.5 x 0.5 ft (top edges chamfered) at x = length .. length + 0.5, y -0.05 .. 0.5, across the whole row.
Run: python scripts/start_grids.py -> assets/props/start_grids.jm / .png + ../apercus_sgm/start_grids_3d.png"""
import os, sys
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
from props_usland import Mesh, OUTD

G = dict(W=3.3, bar=0.2, y_plate=0.06, y_top=0.10, y_sink=-0.04, beam=0.5, beam_ch=0.06, beam_sink=-0.05, piece=8.0,
         lwd=0.18, swd=0.09, strand=0.028)          # diamond long / short diagonal (long one across the plate), strand width
PPF = 128                                            # texture px per ft
TW = TH = 1024
MUD = 1.0                                            # v31: dirt patches on the plates (0 = clean)
L_TEX = 5.0                                          # plate length drawn in the texture (other lengths stretch it)
R_PLATE = [(0, 0, int(G['W'] * PPF), int(L_TEX * PPF)), (432, 0, 432 + int(G['W'] * PPF), int(L_TEX * PPF))]   # image x = z, y = x
R_RED_SIDE = (0, 656, 1024, 688)                     # frame side faces (u along the bar)
R_WOOD = {'top': (0, 704, 1024, 768), 'front': (0, 776, 1024, 840), 'back': (0, 848, 1024, 912), 'ch': (0, 920, 1024, 952)}
R_WOOD_END = (880, 960, 944, 1024)
RED, STEEL, DIRT, WOOD = (176, 32, 30), (168, 172, 174), (132, 102, 74), (128, 100, 70)

def _noise(rg, shape, sig, amp):
    n = gaussian_filter(rg.normal(0, 1, shape), sig); return n / (n.std() + 1e-9) * amp

# ------------------------------------------------------------------ texture
def _plate(rg, h, w):
    """one framed plate seen from above (h rows = length along x, w cols = width along z): red frame ring, galvanised
    border, expanded metal (diamond holes = alpha 0) with dirt in places. Supersampled x3 for clean strands."""
    ss = 3; H, W = h * ss, w * ss
    yy, xx = np.mgrid[0:H, 0:W] / (PPF * ss)                     # ft: yy along x (length), xx along z (width)
    a_, b_ = xx, yy
    p = a_ / (G['lwd'] / 2); q = b_ / (G['swd'] / 2)
    u = (p + q) / 2; v = (q - p) / 2                               # diamonds = unit squares in (u, v)
    gu = np.sqrt(1 / G['lwd'] ** 2 + 1 / G['swd'] ** 2); wu = G['strand'] * gu
    du = np.abs(u - np.floor(u) - 0.5); dv = np.abs(v - np.floor(v) - 0.5)   # 0 on a strand centre line
    on_u, on_v = du < wu / 2, dv < wu / 2
    metal = on_u | on_v
    # strand shading: expanded metal strands are tilted -> one side bright, the other dark; bonds (crossings) brighter
    side = np.where(on_u, np.sign(u - np.floor(u) - 0.5), np.sign(v - np.floor(v) - 0.5))
    shade = 1 + 0.16 * side + 0.10 * (on_u & on_v)
    bar, edge = G['bar'], G['bar'] + (0.04 if MUD < 1 else 0.10)
    dist = np.minimum(np.minimum(xx, w / PPF - xx), np.minimum(yy, h / PPF - yy))   # ft from the outer edge
    ring, border = dist < bar, (dist >= bar) & (dist < edge)
    alpha = (metal | ring | border).astype(float)
    def down(x):
        return x.reshape(h, ss, w, ss, *x.shape[2:]).mean(axis=(1, 3))
    alpha = down(alpha); shade = down(np.where(metal, shade, 1.0)); ring = down(ring.astype(float)); border = down(border.astype(float))
    st = np.ones((h, w, 3)) * np.array(STEEL, float)
    st *= (1 + _noise(rg, (h, w), 30, 0.05) + rg.normal(0, 0.03, (h, w)))[..., None] * shade[..., None]
    st[..., :] *= (1 - 0.18 * np.clip(_noise(rg, (h, w), 18, 1.0) - 0.8, 0, 1))[..., None]          # dull / oily patches
    bd = np.ones((h, w, 3)) * np.array(STEEL, float) * 1.05 * (1 + rg.normal(0, 0.025, (h, w)))[..., None]
    rd = np.ones((h, w, 3)) * np.array(RED, float) * (1 + _noise(rg, (h, w), 20, 0.06) + rg.normal(0, 0.03, (h, w)))[..., None]
    wear = np.clip(_noise(rg, (h, w), (1.0, 4.0), 1.0) + _noise(rg, (h, w), (4.0, 1.0), 1.0) - 2.2, 0, 1)   # scratches
    if MUD < 1: wear = wear * 0.35                                                               # v31 (user): no rust, light grey scratches
    rd = rd * (1 - wear[..., None]) + (np.array([92, 64, 50.0]) if MUD >= 1 else np.array(STEEL, float) * 0.85) * wear[..., None]
    col = st * (1 - ring - border)[..., None] + bd * border[..., None] + rd * ring[..., None]
    # dirt: patches on the steel (clogged holes become opaque dirt), heavier near the rear (wheel spin) and the sides
    dr = _noise(rg, (h, w), 14, 1.0) + _noise(rg, (h, w), 4, 0.4) + 1.2 * np.linspace(-0.4, 1.0, h)[:, None] ** 3
    dm = np.clip((dr - 1.3) * 1.8, 0, 1) * (1 - 0.6 * ring) * MUD                                  # less on the painted frame
    dirt_c = np.array(DIRT, float) * (0.88 + 0.22 * rg.random((h, w, 1)))
    col = col * (1 - dm[..., None] * 0.85) + dirt_c * (dm[..., None] * 0.85)
    alpha = np.maximum(alpha, (dm > 0.55) * (1 - ring))
    yy1 = np.arange(h)[:, None]; xx1 = np.arange(w)[None]
    e = np.minimum(np.minimum(yy1, h - 1 - yy1), np.minimum(xx1, w - 1 - xx1))
    col *= (0.82 + 0.18 * np.clip(e / 4.0, 0, 1))[..., None]                                          # dark outer edge
    return np.dstack([np.clip(col, 0, 255), np.clip(alpha, 0, 1) * 255])

def grid_texture():
    rg = np.random.default_rng(223)
    a = np.zeros((TH, TW, 4)); a[..., :3] = np.array(DIRT) * 0.8; a[..., 3] = 255
    for x0, y0, x1, y1 in R_PLATE: a[y0:y1, x0:x1] = _plate(rg, y1 - y0, x1 - x0)
    x0, y0, x1, y1 = R_RED_SIDE; h, w = y1 - y0, x1 - x0                     # frame sides: red, worn, dirty at the foot
    s = np.ones((h, w, 3)) * np.array(RED, float) * 0.80 * (1 + rg.normal(0, 0.03, (h, w)))[..., None]
    wear = np.clip(_noise(rg, (h, w), (0.8, 5), 1.0) - 1.6, 0, 1) * (1.0 if MUD >= 1 else 0.3)
    s = s * (1 - wear[..., None]) + (np.array([80, 56, 44.0]) if MUD >= 1 else np.array(STEEL, float) * 0.8) * wear[..., None]
    dm = np.clip(np.linspace(-0.6, 1.0, h)[:, None] + _noise(rg, (h, w), (2, 8), 0.3), 0, 1) ** 1.5
    dm = dm * (1.0 if MUD >= 1 else 0.35)
    s = s * (1 - dm[..., None] * 0.7) + np.array(DIRT, float) * 0.85 * dm[..., None] * 0.7
    a[y0:y1, x0:x1, :3] = s
    for k, (nm, (x0, y0, x1, y1)) in enumerate(R_WOOD.items()):              # weathered timber, grain along u, 8 ft per strip
        h, w = y1 - y0, x1 - x0
        g = _noise(rg, (h, w), (0.8, 25), 1.0); kn = _noise(rg, (h, w), 10, 1.0)
        c = np.array(WOOD, float)[None, None] * (1 + 0.10 * g[..., None] + 0.06 * kn[..., None])
        c[np.abs(g) > 2.0] *= 0.72
        c = c * 0.75 + np.array([128, 126, 120.0]) * 0.25                                             # grey weathering
        c *= (1 + rg.normal(0, 0.03, (h, w)))[..., None]
        c[:, :5] *= 0.55; c[:, -5:] *= 0.55                                                            # butt joint between pieces
        if nm != 'top':
            dm = np.clip(np.linspace(-0.5, 1.0, h)[:, None] + _noise(rg, (h, w), (3, 12), 0.25), 0, 1)
            c = c * (1 - 0.6 * dm[..., None]) + np.array(DIRT, float) * 0.8 * 0.6 * dm[..., None]
        c *= {'top': 1.0, 'front': 0.84, 'back': 0.80, 'ch': 0.92}[nm]
        a[y0:y1, x0:x1, :3] = c
    x0, y0, x1, y1 = R_WOOD_END; h, w = y1 - y0, x1 - x0                     # end grain: rings
    yy, xx = np.mgrid[0:h, 0:w]; r = np.hypot(yy - h * 0.9, xx - w * 0.4)
    a[y0:y1, x0:x1, :3] = np.array(WOOD, float) * 0.78 * (1 + 0.08 * np.sin(r * 1.3))[..., None] * (1 + rg.normal(0, 0.03, (h, w)))[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')

# ------------------------------------------------------------------ mesh
def floor_mesh(n_gates=22, pitch=4.0, length=5.0, frame_rgb=None, beam_gap=0.0, clean=None):
    """v30 (user): frame_rgb = colour of the plate frame (None = the v29 red; the user wants the usual galvanised steel),
    beam_gap = air between the plates and the timber beam (ft); plates longer than L_TEX are drawn in pieces (no stretch)."""
    global RED
    if frame_rgb: RED = tuple(frame_rgb)
    if clean:                                      # v31 (Saint-Georges user): thin frame, big clear diamonds, no mud, off the ground
        G.update(bar=clean.get('bar', 0.10), lwd=clean.get('lwd', 0.36), swd=clean.get('swd', 0.18), strand=clean.get('strand', 0.035),
                 y_plate=clean.get('y_plate', 0.22), y_top=clean.get('y_top', 0.28), y_sink=-0.04)
        global MUD; MUD = clean.get('mud', 0.0)
    m = Mesh(TW, TH); W, b = G['W'], G['bar']; yt, yp, ys = G['y_top'], G['y_plate'], G['y_sink']
    up = np.array([0, 1.0, 0])
    for k in range(n_gates):
        zc = (k - (n_gates - 1) / 2) * pitch; z0, z1 = zc - W / 2, zc + W / 2
        rx0, ry0, rx1, ry1 = R_PLATE[k % 2]
        uv = lambda x, z: m.uv_px(rx0 + (z - z0) / W * (rx1 - rx0), ry0 + x / length * (ry1 - ry0))
        # mesh plate (alpha holes), inside the frame
        eg_ = G['bar'] + (0.04 if MUD < 1 else 0.10) + 0.02                               # v37: pieces use only the mesh inside the drawn frame
        npc_ = int(np.ceil((length - 2 * b) / (L_TEX - 2 * eg_ - 0.02)))                 # v30: pieces, each mapped 1:1
        xs_ = np.linspace(b, length - b, npc_ + 1)
        for q_ in range(npc_):
            xa_, xb_ = xs_[q_], xs_[q_ + 1]
            off_ = b if q_ == 0 else ((L_TEX - b - (xb_ - xa_)) if q_ == npc_ - 1 else eg_)   # (no frame line at the seams)
            if q_ == 0 and npc_ > 1: off_ = b
            if q_ > 0: off_ = max(off_, eg_)
            uvq = lambda x, z, xa_=xa_, off_=off_: m.uv_px(rx0 + (z - z0) / W * (rx1 - rx0), ry0 + (x - xa_ + off_) * PPF)
            Q = [(xa_, z0 + b), (xb_, z0 + b), (xb_, z1 - b), (xa_, z1 - b)]
            m.tri_fan([np.array([x, yp, z]) for x, z in Q], up, [uvq(x, z) for x, z in Q])
        # frame: top ring (4 trapezoids), outer sides, inner sides above the plate
        O = [(0, z0), (length, z0), (length, z1), (0, z1)]; I = [(b, z0 + b), (length - b, z0 + b), (length - b, z1 - b), (b, z1 - b)]
        for i in range(4):
            j = (i + 1) % 4
            T = [O[i], O[j], I[j], I[i]]
            m.tri_fan([np.array([x, yt, z]) for x, z in T], up, [uv(x, z) for x, z in T])
            (xa, za), (xb, zb) = O[i], O[j]; ln = np.hypot(xb - xa, zb - za)
            N = np.array([zb - za, 0, -(xb - xa)]) / ln
            if N @ np.array([(xa + xb) / 2 - length / 2, 0, (za + zb) / 2 - zc]) < 0: N = -N
            sx0, sy0, sx1, sy1 = R_RED_SIDE; ue = sx0 + (sx1 - sx0) * ln / 6.0
            m.tri_fan([np.array([xa, ys, za]), np.array([xb, ys, zb]), np.array([xb, yt, zb]), np.array([xa, yt, za])], N,
                      [m.uv_px(sx0, sy1), m.uv_px(ue, sy1), m.uv_px(ue, sy0), m.uv_px(sx0, sy0)])
            (xa, za), (xb, zb) = I[i], I[j]
            m.tri_fan([np.array([xa, yp - 0.01, za]), np.array([xb, yp - 0.01, zb]), np.array([xb, yt, zb]), np.array([xa, yt, za])], -N,
                      [m.uv_px(sx0, sy1), m.uv_px(ue, sy1), m.uv_px(ue, sy0 + 12), m.uv_px(sx0, sy0 + 12)])
    # timber beam across the row, top edges chamfered, in pieces of G['piece'] ft (texture strip = one piece)
    bw, ch, x0 = G['beam'], G['beam_ch'], length + beam_gap
    prof = [(x0, G['beam_sink'], 'front', -1), (x0, bw - ch, 'ch', -1), (x0 + ch, bw, 'top', 0), (x0 + bw - ch, bw, 'ch', 1),
            (x0 + bw, bw - ch, 'back', 1), (x0 + bw, G['beam_sink'], None, 0)]
    za_, zb_ = -n_gates * pitch / 2, n_gates * pitch / 2; npc = max(1, int(round((zb_ - za_) / G['piece'])))
    zs = np.linspace(za_, zb_, npc + 1)
    for p in range(npc):
        for i in range(len(prof) - 1):
            (xa, ya, nm, _), (xb, yb, _, _) = prof[i], prof[i + 1]
            N = np.array([yb - ya, -(xb - xa), 0.0]); N /= np.linalg.norm(N)
            if N @ np.array([(xa + xb) / 2 - (x0 + bw / 2), (ya + yb) / 2 - bw / 3, 0]) < 0: N = -N
            rx0, ry0, rx1, ry1 = R_WOOD[nm]; ue = rx0 + (rx1 - rx0) * (zs[p + 1] - zs[p]) / G['piece']
            m.tri_fan([np.array([xa, ya, zs[p]]), np.array([xb, yb, zs[p]]), np.array([xb, yb, zs[p + 1]]), np.array([xa, ya, zs[p + 1]])], N,
                      [m.uv_px(rx0, ry1), m.uv_px(rx0, ry0), m.uv_px(ue, ry0), m.uv_px(ue, ry1)])
    for zz, sg in ((za_, -1), (zb_, 1)):                                   # end grain caps
        ex0, ey0, ex1, ey1 = R_WOOD_END
        pts = [np.array([x, y, zz]) for x, y, _, _ in prof]
        m.tri_fan(pts, np.array([0, 0, sg * 1.0]), [m.uv_px(ex0 + (x - x0) / bw * (ex1 - ex0), ey1 - (y - G['beam_sink']) / (bw - G['beam_sink']) * (ey1 - ey0))
                                                    for x, y, _, _ in prof])
    return m, grid_texture()

def beam_shape(n_gates=22, pitch=4.0, length=5.0, beam_gap=0.0, r=0.3, every=0.5):
    """v31 (user: 'mets de la physique dans la poutre'): collision spheres along the timber beam (statue frame)."""
    x = length + beam_gap + G['beam'] / 2; rows = []
    for z in np.arange(-n_gates * pitch / 2 + r, n_gates * pitch / 2 - r + 1e-6, every):
        rows.append(f'{x:.4f} {r - 0.05:.4f} {z:.4f} {r:.3f} 1.0 400 40')
    return '\n'.join([str(len(rows))] + rows) + '\n'

# ------------------------------------------------------------------ preview
def preview(out_path, m, tex):
    from preview_stt_scene import Cam, raster
    from rider_gate import scale_person
    V = np.array(m.V, np.float32); I = np.array(m.I, np.int64).reshape(-1, 3); t = np.asarray(tex, np.float32) / 255
    objs = [(V, I, t), scale_person((7.2, 0, -2.0))]
    Lg = np.array([-0.45, 0.8, 0.4]); Lg /= np.linalg.norm(Lg)
    gs = np.arange(-60, 61, 2.0); GX, GZ = np.meshgrid(gs, gs); Pg = np.stack([GX, np.zeros_like(GX), GZ], -1).reshape(-1, 3)
    n = len(gs); ii, jj = np.meshgrid(np.arange(n - 1), np.arange(n - 1), indexing='ij'); a = (ii * n + jj).ravel()
    Ig = np.concatenate([np.stack([a, a + 1, a + n], 1), np.stack([a + 1, a + n + 1, a + n], 1)])
    rg = np.random.default_rng(0); Cg = np.array([0.66, 0.52, 0.38]) * (0.88 + 0.16 * rg.random((len(Pg), 1)))
    def shot(eye, tgt, W=900, H=640, fov=50):
        cam = Cam(eye, tgt, W, H, fov); img = np.zeros((H, W, 3), np.float32)
        sky = np.linspace(0, 1, H)[:, None, None]; img[:] = np.array([0.55, 0.70, 0.90]) * (1 - sky) + np.array([0.85, 0.88, 0.92]) * sky
        zb = np.full((H, W), np.inf, np.float32)
        raster(img, zb, cam, Pg, Ig, lambda ti, B: (Cg[Ig[ti]] * B[:, :, None]).sum(1))
        for V_, I_, tex_ in objs:
            th, tw = tex_.shape[:2]
            def uvpx(ti, B, V_=V_, I_=I_, tw=tw, th=th):
                uv = (V_[I_[ti], 6:8][None] * B[:, :, None]).sum(1)
                return np.clip((1 - uv[:, 1]) * th, 0, th - 1).astype(int), np.clip(uv[:, 0] * tw, 0, tw - 1).astype(int)
            def col(ti, B, V_=V_, I_=I_, tex_=tex_):
                py, px = uvpx(ti, B); nn = (V_[I_[ti], 3:6][None] * B[:, :, None]).sum(1)
                return tex_[py, px, :3] * (0.62 + 0.45 * np.clip(nn @ Lg, 0, 1))[:, None]
            raster(img, zb, cam, V_[:, :3], I_, col, lambda ti, B, tex_=tex_: tex_[uvpx(ti, B)][:, 3])
        return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    views = [shot((14, 5.5, -50), (2, 0, -30), fov=45),         # like the photo: low, from the end of the row
             shot((2.5, 4.0, -36), (3.5, 0, -40), fov=60),      # close-up on two plates (diamond mesh, dirt through)
             shot((30, 22, 10), (2, 0, 0), fov=60),             # high 3/4 over the whole row, beam behind
             shot((-60, 6, -20), (3, 0, 0), fov=40)]            # far away from the track side (mesh at a distance)
    W_, H_ = views[0].size; sheet = Image.new('RGB', (W_ * 2, H_ * 2))
    for k, v in enumerate(views): sheet.paste(v, ((k % 2) * W_, (k // 2) * H_))
    os.makedirs(os.path.dirname(out_path), exist_ok=True); sheet.save(out_path); print('preview', out_path)

if __name__ == '__main__':
    m, tex = floor_mesh(); os.makedirs(OUTD, exist_ok=True)
    nv, nt = m.write(f'{OUTD}/start_grids.jm', (16, 0.6, 0.35, 0.35, 0.35)); tex.save(f'{OUTD}/start_grids.png', optimize=True)
    P = np.array([v[:3] for v in m.V]); print(f'start_grids: {nv} vertices, {nt} triangles, bbox {P.min(0).round(2)} .. {P.max(0).round(2)} ft')
    preview(os.path.join(os.path.dirname(ROOT), 'apercus_sgm', 'start_grids_3d.png'), m, tex)
