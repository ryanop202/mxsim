"""Interlocking precast concrete blocks ("lego" blocks, 1.6 x 0.8 x 0.8 m) stacked as a retaining wall along the side of a big
dirt landing (Saint-Georges, user photo 221: light grey blocks, two round studs on top, dirt piled behind the wall).
Made from scratch with props_usland.Mesh (doc 12: 1 unit = 1 ft, y up, one texture, baked shades, chamfered edges, matte).

block_texture() -> PIL image (concrete_block.png, 1024 x 1024, shared by every wall)
wall_mesh(line_xz, ground_out, ground_in, origin, side=None) -> Mesh
  ONE ground-following mesh per wall (statue yaw 0, like rail_wood.rail_mesh): model x/z = world x/z - origin,
  y = height - ground_out(origin). line_xz = (n, 2) world points every ~1 ft = the OUTER face of the wall; the blocks go
  from the line towards the dirt (side = +1: to the left of the line direction (-dz, dx), -1: to the right, None: the side
  where ground_in is higher / ground_out lower, +1 on a tie). Columns of blocks every 5.25 ft, each stacked from the outer
  ground (lowest point under the column; the foundations step by whole block heights, like a real wall on a slope, so the
  bond runs on across the steps) up to just above the dirt behind it (ceil to
  whole blocks, 1..7). Running bond: odd layers shifted by half a block, half blocks at the wall ends and at the steps.
  Hidden faces are culled (bottoms, joints, tops under a block, backs buried in the dirt).
Run: python scripts/concrete_blocks.py -> assets/props/concrete_block.png + ../apercus_sgm/concrete_wall_3d.png (demo)"""
import os, sys
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
from props_usland import Mesh, OUTD

BL = dict(L=5.25, H=2.62, D=2.62, c=0.07,                  # block length (along the wall), height, depth, edge chamfer
          knob_r=(0.56, 0.49), knob_h=0.24, knob_seg=10,   # round studs: base / top radius, height
          sink=0.15, margin=0.10, nmax=7)                  # sunk in the outer ground, top above the dirt, max layers
TW = TH = 1024
PPF = 512 / BL['L']                                        # texture pixels per ft (97.5)
CONC = (204, 203, 197)
# texture rects (x0, y0, x1, y1), image pixels (y down)
R_FRONT = [(0, 0, 512, 256), (512, 0, 1024, 256), (0, 256, 512, 512), (512, 256, 1024, 512)]   # 2, 3 = bottom layer (dirt splash)
R_TOP = (0, 512, 512, 768)
R_END = [(512, 512, 768, 768), (768, 512, 1024, 768)]
R_KNOB_SIDE = (0, 784, 512, 832)
R_KNOB_TOP = (528, 784, 656, 912)

# ------------------------------------------------------------------ texture
def _noise(rg, shape, sig, amp):
    n = gaussian_filter(rg.normal(0, 1, shape), sig); return n / (n.std() + 1e-9) * amp

def _concrete(h, w, rg, shade=1.0, streaks=True, dirt=0.0, border=True):
    """light precast concrete: mottling, fine grain, pores / bug holes, rain streaks from the top, chipped darker edges,
    soft AO at the bottom; dirt = height (fraction of the face) of the brown splash rising from the ground."""
    a = np.ones((h, w, 3)) * np.array(CONC, float)
    a *= (1 + _noise(rg, (h, w), 38, 0.035) + _noise(rg, (h, w), 7, 0.020) + rg.normal(0, 0.025, (h, w)))[..., None]
    a *= np.array([1.0, 1.0, 0.985]) * (1 + _noise(rg, (h, w), 60, 0.012))[..., None]          # slight warm / cool drift
    if streaks:                                                                                 # rain / runoff streaks
        s = gaussian_filter(rg.normal(0, 1, (h, w)), (h * 0.35, 2.5)); s = np.clip(s / (s.std() + 1e-9) - 0.6, 0, None)
        fade = np.clip(1.15 - np.linspace(0, 1, h), 0, 1)[:, None]
        a *= (1 - 0.06 * s * fade)[..., None]
        a += (0.05 * s * fade)[..., None] * np.array([-4, -6, -12.0])                           # a bit brownish
    sp = rg.random((h, w))                                                                       # pores
    pore = gaussian_filter(((sp < 0.0035) * rg.uniform(0.3, 1, (h, w))).astype(float), 0.8) * 3.5
    a *= (1 - np.clip(pore, 0, 0.30))[..., None]
    for _ in range(int(h * w / 5000)):                                                           # bug holes: dark pit, light rim
        y, x = rg.integers(3, h - 3), rg.integers(3, w - 3); r = rg.uniform(1.2, 2.8)
        yy, xx = np.ogrid[-4:5, -4:5]; d = np.sqrt(yy ** 2 + xx ** 2)
        ys, xs = slice(y - 4, y + 5), slice(x - 4, x + 5)
        if a[ys, xs].shape[:2] != (9, 9): continue
        a[ys, xs] *= np.where(d < r, 0.68, np.where(d < r + 1.2, 1.05, 1.0))[..., None]
    if dirt > 0:                                                                                 # dirt splash from the ground
        yy = np.linspace(1, 0, h)[:, None] + _noise(rg, (h, w), (3, 5), 0.06) + _noise(rg, (h, w), 14, 0.05)
        m = np.clip((dirt - yy) / (dirt * 0.6), 0, 1) ** 1.4
        spk = gaussian_filter((rg.random((h, w)) < 0.02).astype(float), 1.0) * 3 * (yy < dirt * 1.8)
        m = np.clip(np.maximum(m, spk), 0, 0.9)
        a = a * (1 - m[..., None]) + np.array([148, 116, 84.0]) * (0.9 + 0.2 * rg.random((h, w, 1))) * m[..., None]
    if border:                                                                                   # chamfer band + chipped edges
        c = int(round(BL['c'] * PPF)) + 1
        yy, xx = np.mgrid[0:h, 0:w]; e = np.minimum(np.minimum(yy, h - 1 - yy), np.minimum(xx, w - 1 - xx)).astype(float)
        chip = np.clip(_noise(rg, (h, w), 3.0, 1.0) - 0.9, 0, None) * 5 * (e < c + 7)
        a *= (1 - 0.20 * (e < c))[..., None]                                                     # the bevel (joint) darker
        a *= (1 - 0.10 * np.clip(chip, 0, 1) * (e >= c))[..., None]
        a += (np.clip(chip, 0, 1) * (e < c + 4) * 18)[..., None]                                 # fresh broken concrete lighter
        a *= (0.80 + 0.20 * np.clip(e / (c * 1.6), 0, 1))[..., None]                             # dark joint line
    a *= (0.90 + 0.10 * np.clip(np.linspace(0, 1, h)[::-1] * 5, 0, 1))[:, None, None] if streaks else 1.0   # AO at the foot
    return np.clip(a * shade, 0, 255)

def block_texture():
    rg = np.random.default_rng(221)
    a = np.zeros((TH, TW, 3)) + np.array(CONC) * 0.8
    for k, (x0, y0, x1, y1) in enumerate(R_FRONT):
        a[y0:y1, x0:x1] = _concrete(y1 - y0, x1 - x0, rg, 0.86, dirt=0.22 if k >= 2 else 0.0)
    x0, y0, x1, y1 = R_TOP; a[y0:y1, x0:x1] = _concrete(y1 - y0, x1 - x0, rg, 1.0, streaks=False)
    for x0, y0, x1, y1 in R_END: a[y0:y1, x0:x1] = _concrete(y1 - y0, x1 - x0, rg, 0.80)
    x0, y0, x1, y1 = R_KNOB_SIDE; a[y0:y1, x0:x1] = _concrete(y1 - y0, x1 - x0, rg, 0.84, streaks=False, border=False)
    x0, y0, x1, y1 = R_KNOB_TOP; a[y0:y1, x0:x1] = _concrete(y1 - y0, x1 - x0, rg, 1.0, streaks=False, border=False)
    return Image.fromarray(a.astype(np.uint8))

# ------------------------------------------------------------------ geometry
def _rect_uv(m, rect, s, t):
    """(s, t) in 0..1 across the rect (s to the right, t up) -> uv."""
    x0, y0, x1, y1 = rect
    return m.uv_px(x0 + s * (x1 - x0), y1 - t * (y1 - y0))

def _block(m, O, tv, nv, L, vis, top_halves, rects, knobs, fill=()):
    """one chamfered block. O = outer-face bottom corner (model), tv = unit along the wall, nv = unit into the dirt.
    vis: set of visible faces among F (outer), B (back), T, S0 (u = 0 end), S1 (u = L end); the bottom is never drawn.
    top_halves: list of (u0, u1) parts of the top that are not covered (knob drawn in the middle of each).
    fill: faces drawn although covered (the floor / ceiling of the joint grooves at the running-bond T junctions, else
    one sees through the block there); they do not make the strips around them show."""
    H, D, c = BL['H'], BL['D'], BL['c']; up = np.array([0, 1.0, 0])
    lo, hi = np.array([0, 0, 0.0]), np.array([L, H, D])                       # local (u, v, w)
    P = lambda q: O + tv * q[0] + up * q[1] + nv * q[2]
    names = {(0, -1): 'S0', (0, 1): 'S1', (1, -1): 'Bo', (1, 1): 'T', (2, -1): 'F', (2, 1): 'B'}
    vecs = {0: tv, 1: up, 2: nv}
    def face_uv(fname, q):
        """planar projection of local point q on the rect of face fname."""
        u, v, w = q
        if fname in ('F', 'B'): return _rect_uv(m, rects['F'], u / L, v / H)
        if fname in ('T', 'Bo'): return _rect_uv(m, rects['T'], u / L, w / D)
        return _rect_uv(m, rects['S'], w / D, v / H)
    def inset(ax, sg):
        q0, q1 = lo.copy(), hi.copy()
        for k in range(3):
            if k != ax: q0[k] += c; q1[k] -= c
        return q0, q1
    pick = ['F', 'T', 'S0', 'S1', 'B']
    vis = set(vis) | ({'T'} if top_halves else set())
    # main faces
    for (ax, sg), fn in names.items():
        if fn not in vis and fn not in fill: continue
        q0, q1 = inset(ax, sg); val = hi[ax] if sg > 0 else lo[ax]
        o1, o2 = [k for k in range(3) if k != ax]
        spans = [(q0[0], q1[0])]
        if fn == 'T' and top_halves and 'T' not in fill: spans = [(max(a_, c), min(b_, L - c)) for a_, b_ in top_halves]
        for a_, b_ in spans:
            corners = []
            for s1, s2 in ((0, 0), (1, 0), (1, 1), (0, 1)):
                q = np.zeros(3); q[ax] = val
                q[o1] = (a_ if s1 == 0 else b_) if o1 == 0 else (q0[o1] if s1 == 0 else q1[o1])
                q[o2] = (a_ if s2 == 0 else b_) if o2 == 0 else (q0[o2] if s2 == 0 else q1[o2])
                corners.append(q)
            m.tri_fan([P(q) for q in corners], vecs[ax] * sg, [face_uv(fn, q) for q in corners])
    # edge strips (emitted if one of the two faces shows)
    for (a1, s1), f1 in names.items():
        for (a2, s2), f2 in names.items():
            if a2 <= a1: continue
            k = 3 - a1 - a2; ends = (names[(k, -1)], names[(k, 1)])
            if not ({f1, f2, *ends} & vis): continue                # a hidden joint strip still closes a visible corner pit
            mf = next((f for f in pick if f in (f1, f2) and f in vis), None) or next(f for f in pick if f in ends and f in vis)
            pa = np.zeros(3); pb = np.zeros(3)
            pa[a1] = hi[a1] if s1 > 0 else lo[a1]; pa[a2] = hi[a2] - c if s2 > 0 else lo[a2] + c
            pb[a2] = hi[a2] if s2 > 0 else lo[a2]; pb[a1] = hi[a1] - c if s1 > 0 else lo[a1] + c
            Q = []
            for p_ in (pa, pb):
                for kk in (lo[k] + c, hi[k] - c):
                    q = p_.copy(); q[k] = kk; Q.append(q)
            quad = [Q[0], Q[1], Q[3], Q[2]]
            N = vecs[a1] * s1 + vecs[a2] * s2; N /= np.linalg.norm(N)
            m.tri_fan([P(q) for q in quad], N, [face_uv(mf, q) for q in quad])
    # corner triangles
    for su in (-1, 1):
        for sv in (-1, 1):
            for sw in (-1, 1):
                fs = [names[(0, su)], names[(1, sv)], names[(2, sw)]]
                if not (set(fs) & vis): continue
                mf = next(f for f in pick if f in fs and f in vis)
                sgn = (su, sv, sw); Q = []
                for ax in range(3):
                    q = np.zeros(3)
                    for k in range(3):
                        e = hi[k] if sgn[k] > 0 else lo[k]
                        q[k] = e if k == ax else e - sgn[k] * c
                    Q.append(q)
                N = tv * su + up * sv + nv * sw; N /= np.linalg.norm(N)
                m.tri_fan([P(q) for q in Q], N, [face_uv(mf, q) for q in Q])
    # studs on the uncovered tops
    if knobs:
        r0, r1 = BL['knob_r']; kh = BL['knob_h']; n_ = BL['knob_seg']
        for a_, b_ in top_halves:
            ctr = O + tv * ((a_ + b_) / 2) + nv * (D / 2) + up * H
            ang = np.linspace(0, 2 * np.pi, n_ + 1)
            dirs = [tv * np.cos(t) + nv * np.sin(t) for t in ang]
            for k in range(n_):
                q = [ctr + dirs[k] * r0 - up * 0.02, ctr + dirs[k + 1] * r0 - up * 0.02,
                     ctr + dirs[k + 1] * r1 + up * kh, ctr + dirs[k] * r1 + up * kh]
                N = (dirs[k] + dirs[k + 1]) / 2 * kh + up * (r0 - r1); N /= np.linalg.norm(N)
                x0, y0, x1, y1 = R_KNOB_SIDE; ua, ub = x0 + (x1 - x0) * k / n_, x0 + (x1 - x0) * (k + 1) / n_
                m.tri_fan(q, N, [m.uv_px(ua, y1), m.uv_px(ub, y1), m.uv_px(ub, y0), m.uv_px(ua, y0)])
            m.tri_fan([ctr + d * r1 + up * kh for d in dirs[:-1]], up,
                      [_rect_uv(m, R_KNOB_TOP, 0.5 + 0.48 * np.cos(t), 0.5 + 0.48 * np.sin(t)) for t in ang[:-1]])

def _polyline(line_xz):
    P = np.asarray(line_xz, float); S = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    def at(s):                                                     # point at arclength s (linear extrapolation past the ends)
        i = int(np.clip(np.searchsorted(S, s) - 1, 0, len(S) - 2)); f = (s - S[i]) / (S[i + 1] - S[i] + 1e-12)
        return P[i] + f * (P[i + 1] - P[i])
    return S, at

def wall_mesh(line_xz, ground_out, ground_in, origin, side=None):
    """see module doc. Returns the Mesh (texture concrete_block.png, 1024 x 1024)."""
    m = Mesh(TW, TH); L, H, D = BL['L'], BL['H'], BL['D']; Lh = L / 2
    S, at = _polyline(line_xz); ox, oz = origin; y0 = ground_out(ox, oz)
    def perp(s0, s1):
        d = at(s1) - at(s0); d /= np.linalg.norm(d) + 1e-12; return d, np.array([-d[1], d[0]])
    if side is None:                                               # dirt side: ground_in higher / ground_out lower there
        sc = 0.0
        for s in np.linspace(0, S[-1], 12):
            _, pp = perp(max(s - 1, 0), min(s + 1, S[-1])); p = at(s)
            a, b = p + 4 * pp, p - 4 * pp
            sc += (ground_in(*a) - ground_in(*b)) - (ground_out(*a) - ground_out(*b))
        side = 1 if sc >= 0 else -1
    nc = max(1, int(round(S[-1] / L)))
    # column bases (lowest outer ground under the column, sunk) and heights
    base = np.zeros(nc); top = np.zeros(nc)
    for c_ in range(nc):
        ss = np.linspace(c_ * L, (c_ + 1) * L, 7); _, pp = perp(c_ * L, (c_ + 1) * L)
        base[c_] = min(ground_out(*at(s)) for s in ss) - BL['sink']
        top[c_] = max(ground_in(*(at(s) + side * pp * (D + 0.3))) for s in ss)
    b0 = base.min(); K0 = np.floor((base - b0) / H + 1e-6).astype(int)   # foundations stepped by whole blocks (global layers)
    ncnt = np.clip(np.ceil((top - (b0 + K0 * H) + BL['margin']) / H), 1, BL['nmax']).astype(int)
    col = lambda cell: cell // 2
    occ = lambda k, cell: 0 <= cell < 2 * nc and K0[col(cell)] <= k < K0[col(cell)] + ncnt[col(cell)]
    blocks = []                                                     # (global layer, first cell, n cells)
    for k in range((K0 + ncnt).max()):
        cell = 0
        while cell < 2 * nc:                                        # running bond: odd layers shifted by half a block
            if not occ(k, cell): cell += 1; continue
            if cell % 2 == k % 2 and occ(k, cell + 1):
                blocks.append((k, cell, 2)); cell += 2
            else:
                blocks.append((k, cell, 1)); cell += 1
    owner = {}
    for b in blocks:
        for q in range(b[2]): owner[(b[0], b[1] + q)] = b
    rg = np.random.default_rng(5)
    for (k, cell, n) in blocks:
        s0, s1 = cell * Lh, (cell + n) * Lh; Lb = s1 - s0
        tv2, pp = perp(s0, s1); tv = np.array([tv2[0], 0, tv2[1]]); nv = side * np.array([pp[0], 0, pp[1]])
        p0 = at(s0); bse = b0 + k * H
        O = np.array([p0[0] - ox, bse - y0, p0[1] - oz])
        vis = {'F'}
        for fn, nb in (('S0', cell - 1), ('S1', cell + n)):
            if (k, nb) not in owner: vis.add(fn)
        dirt = min(ground_in(*(at(s) + side * pp * (D + 0.3))) for s in np.linspace(s0, s1, 4))
        if bse + H > dirt + 0.05: vis.add('B')
        halves = [((q - cell) * Lh, (q - cell + 1) * Lh) for q in range(cell, cell + n) if (k + 1, q) not in owner]
        if n == 2 and len(halves) == 2: halves = [(0, Lh), (Lh, L)]
        fv = (2 + rg.integers(2)) if k == K0[col(cell)] else rg.integers(2)
        x0, y0r, x1, y1 = R_FRONT[fv]
        if n == 1:
            off = rg.integers(2) * 256; frect = (x0 + off, y0r, x0 + off + 256, y1)
        else:
            frect = R_FRONT[fv]
        if n == 2: trect = R_TOP
        else: o_ = R_TOP[0] + 256 * rg.integers(2); trect = (o_, R_TOP[1], o_ + 256, R_TOP[3])
        fill = []
        if len(halves) < n: fill.append('T')                                 # partly / fully covered top: one full quad
        if k > K0[col(cell)] or (n == 2 and k > K0[col(cell + 1)]): fill.append('Bo')
        _block(m, O, tv, nv, Lb, vis, halves, dict(F=frect, T=trect, S=R_END[rg.integers(2)]), knobs=True, fill=fill)
    m.info = dict(columns=nc, heights=ncnt.tolist(), steps=K0.tolist(), blocks=len(blocks), side=side)
    return m

# ------------------------------------------------------------------ demo + preview
_demo_curve = lambda x: -0.0008 * (np.asarray(x, float) - 40) ** 2 + 1.28   # a gentle bend, to test a curved wall

def _demo_grounds():
    """fake landing along the wall (line z = 0, x 0 -> 80 ft): dirt rises 0 -> 16 ft over 60 ft then drops; outer ground
    rising 5 % (4 ft over the wall: shows the stepped foundation); the dirt is on +z."""
    def gin(x, z):
        x = float(x)
        h = 16 * np.clip(x / 60, 0, 1) ** 1.15 if x <= 60 else 16 * np.clip(1 - (x - 60) / 22, 0, 1) ** 0.8
        zl = z - _demo_curve(x)
        return h * float(np.clip(zl / 3.0, 0, 1)) + 0.05 * x if zl > 0 else 0.05 * x
    gout = lambda x, z: 0.05 * float(x)
    return gin, gout

def preview(out_path, m, tex, gin, gout, origin):
    from preview_stt_scene import Cam, raster
    V = np.array(m.V, np.float32); I = np.array(m.I, np.int64).reshape(-1, 3)
    V[:, 0] += origin[0]; V[:, 2] += origin[1]; V[:, 1] += gout(*origin)
    t = np.asarray(tex.convert('RGBA'), np.float32) / 255; th, tw = t.shape[:2]
    # terrain: outer ground (z < 0) and the dirt landing behind the wall
    xs = np.arange(-30, 111, 1.0); zs = np.arange(-60, 61, 1.0); GX, GZ = np.meshgrid(xs, zs)
    hy = np.vectorize(gin)(GX, GZ)
    hy = np.where(GZ > _demo_curve(GX), np.maximum(hy - np.clip((GZ - 40) * 0.5, 0, None), np.vectorize(gout)(GX, GZ)), hy)   # dirt slope far side
    P = np.stack([GX, hy, GZ], -1).reshape(-1, 3).astype(np.float32); n = len(xs)
    gy, gx = np.gradient(hy, 1.0); Nn = np.stack([-gx, np.ones_like(gx), -gy], -1); Nn /= np.linalg.norm(Nn, axis=-1, keepdims=True)
    Lg = np.array([-0.45, 0.8, -0.4]); Lg /= np.linalg.norm(Lg)
    rg = np.random.default_rng(0)
    C = (np.array([0.62, 0.47, 0.33]) * (0.45 + 0.6 * np.clip(Nn @ Lg, 0, 1))[..., None]).reshape(-1, 3) * (0.94 + 0.08 * rg.random((P.shape[0], 1)))
    ii, jj = np.meshgrid(np.arange(len(zs) - 1), np.arange(n - 1), indexing='ij'); a = (ii * n + jj).ravel()
    It = np.concatenate([np.stack([a, a + 1, a + n], 1), np.stack([a + 1, a + n + 1, a + n], 1)])
    def shot(eye, tgt, W=900, H=640, fov=50):
        cam = Cam(eye, tgt, W, H, fov); img = np.zeros((H, W, 3), np.float32)
        sky = np.linspace(0, 1, H)[:, None, None]; img[:] = np.array([0.55, 0.70, 0.90]) * (1 - sky) + np.array([0.85, 0.88, 0.92]) * sky
        zb = np.full((H, W), np.inf, np.float32)
        raster(img, zb, cam, P, It, lambda ti, B: (C[It[ti]] * B[:, :, None]).sum(1))
        def uvpx(ti, B):
            uv = (V[I[ti], 6:8][None] * B[:, :, None]).sum(1)
            return np.clip((1 - uv[:, 1]) * th, 0, th - 1).astype(int), np.clip(uv[:, 0] * tw, 0, tw - 1).astype(int)
        def col(ti, B):
            py, px = uvpx(ti, B); nn = (V[I[ti], 3:6][None] * B[:, :, None]).sum(1)
            return t[py, px, :3] * (0.66 + 0.40 * np.clip(nn @ Lg, 0, 1))[:, None]
        raster(img, zb, cam, V[:, :3], I, col)
        return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    views = [shot((90, 9, -45), (40, 7, 2)),                 # like the photo: low, from the track side, 3/4
             shot((-25, 14, -30), (35, 6, 2)),               # from the start of the wall
             shot((52, 26, 30), (40, 10, 0), fov=55),        # from the landing (tops, studs, backs above the dirt)
             shot((63, 8, -14), (58, 10, 1), fov=50)]        # close-up of the tallest part
    W_, H_ = views[0].size; sheet = Image.new('RGB', (W_ * 2, H_ * 2))
    for k, v in enumerate(views): sheet.paste(v, ((k % 2) * W_, (k // 2) * H_))
    os.makedirs(os.path.dirname(out_path), exist_ok=True); sheet.save(out_path); print('preview', out_path)

if __name__ == '__main__':
    tex = block_texture(); os.makedirs(OUTD, exist_ok=True); tex.save(f'{OUTD}/concrete_block.png', optimize=True)
    print('concrete_block.png')
    gin, gout = _demo_grounds()
    line = np.stack([np.arange(0, 81, 1.0), np.zeros(81)], 1)
    line[:, 1] = _demo_curve(line[:, 0])
    m = wall_mesh(line, gout, gin, (0.0, 0.0))
    print('demo wall:', len(m.V), 'vertices,', len(m.I) // 3, 'triangles', m.info)
    preview(os.path.join(os.path.dirname(ROOT), 'apercus_sgm', 'concrete_wall_3d.png'), m, tex, gin, gout, (0.0, 0.0))
