"""Wooden barrier that follows the ground (Saint-Georges v19, user: the climbing barriers along the finish landing did not
touch the ground and the last post was missing). Same look as fence_wood (posts + 2 rails) but ONE mesh per barrier whose
posts stand on the ground and whose rails follow it, like the turn nets (statue yaw 0, origin on flat ground).
rail_mesh(line_xz, ground, origin) -> Mesh; rail_texture() -> image (assets/props/rail_wood.png)."""
import os, sys
import numpy as np
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
from props_usland import Mesh, palette, OUTD

RW = dict(post_every=8.0, post_w=0.48, post_h=3.6, sink=0.3, rails=((1.15, 1.55), (2.55, 2.95)), rail_t=0.24)
WOOD, WOOD_D = (150, 112, 70), (118, 86, 52)

def _grain(h, w, along_x, seed, base):
    from scipy.ndimage import gaussian_filter
    rg = np.random.default_rng(seed); sig = (1.0, 16.0) if along_x else (16.0, 1.0)
    g = gaussian_filter(rg.normal(0, 1, (h, w)), sig); g /= g.std() + 1e-9
    k = gaussian_filter(rg.normal(0, 1, (h, w)), 18); k /= k.std() + 1e-9
    a = np.array(base, float)[None, None] * (1 + 0.11 * g[..., None] + 0.07 * k[..., None]); a[np.abs(g) > 2.0] *= 0.74
    return a

def rail_texture():
    """v83 (Saint-Georges v28, user: wood texture on all the wood): rows 0..127 rail planks (grain along u), rows 128..255
    posts (grain along v). The palette is kept for old callers."""
    a = np.zeros((256, 256, 3)); a[:128] = _grain(128, 256, True, 1, WOOD); a[128:] = _grain(128, 256, False, 2, WOOD_D)
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); pal = palette(img, ['post', 'rail'], [WOOD_D, WOOD]); return img, pal

def rail_mesh(line_xz, ground, origin, pal):
    from scipy.ndimage import gaussian_filter1d
    m = Mesh(256, 256); ox, oz = origin; g0 = ground(ox, oz)
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(line_xz, axis=0), axis=1))]
    gy = gaussian_filter1d(np.array([ground(x, z) for x, z in line_xz]) - g0, 1.0, mode='nearest')
    P = np.c_[line_xz[:, 0] - ox, line_xz[:, 1] - oz]
    up = np.array([0, 1.0, 0]); t_ = RW['rail_t'] / 2
    # rails: a square bar per 1 ft piece, following the ground
    for y0, y1 in RW['rails']:
        for i in range(len(P) - 1):
            a = np.array([P[i, 0], gy[i], P[i, 1]]); b = np.array([P[i + 1, 0], gy[i + 1], P[i + 1, 1]])
            d = b - a; d[1] = 0; d /= np.linalg.norm(d) + 1e-12; n = np.cross(d, up)
            ua_, ub_ = (i % 8) * 32 + 1, (i % 8 + 1) * 32 - 1          # v83: wood grain, 8 ft repeat
            A = [a + n * t_ + up * y0, a - n * t_ + up * y0, a - n * t_ + up * y1, a + n * t_ + up * y1]
            B = [b + n * t_ + up * y0, b - n * t_ + up * y0, b - n * t_ + up * y1, b + n * t_ + up * y1]
            for k, nn in ((0, -n), (1, -up), (2, n), (3, up)):          # side, bottom, side, top (normal = outward)
                j = (k + 1) % 4; q = [A[k], A[j], B[j], B[k]]; c = np.mean(q, axis=0); mid = (a + b) / 2 + up * (y0 + y1) / 2
                nrm = c - mid; nrm[1] = nrm[1] if k in (1, 3) else 0.0; nrm /= np.linalg.norm(nrm) + 1e-12
                v0_, v1_ = 4 + k * 30, 28 + k * 30
                m.tri_fan(q, nrm, [m.uv_px(ua_, v0_), m.uv_px(ua_, v1_), m.uv_px(ub_, v1_), m.uv_px(ub_, v0_)])
    # posts: one every ~post_every ft INCLUDING both ends, standing on the ground (sunk a bit)
    n_ = max(1, int(round(L[-1] / RW['post_every'])))
    for s in np.linspace(0, L[-1], n_ + 1):
        x = np.interp(s, L, P[:, 0]); z = np.interp(s, L, P[:, 1]); y = np.interp(s, L, gy); w = RW['post_w'] / 2
        ya, yb = y - RW['sink'], y + RW['post_h']                       # v83: 4 grained sides + a top
        C = [(x - w, z - w), (x + w, z - w), (x + w, z + w), (x - w, z + w)]
        for k in range(4):
            (xa, za), (xb, zb) = C[k], C[(k + 1) % 4]; nrm = np.array([zb - za, 0, -(xb - xa)]); nrm /= np.linalg.norm(nrm)
            c_ = np.array([(xa + xb) / 2 - x, 0, (za + zb) / 2 - z])
            if nrm @ c_ < 0: nrm = -nrm
            m.tri_fan([np.array([xa, ya, za]), np.array([xb, ya, zb]), np.array([xb, yb, zb]), np.array([xa, yb, za])], nrm,
                      [m.uv_px(k * 64 + 2, 252), m.uv_px(k * 64 + 60, 252), m.uv_px(k * 64 + 60, 132), m.uv_px(k * 64 + 2, 132)])
        m.tri_fan([np.array([px_, yb, pz_]) for px_, pz_ in C][::-1], np.array([0, 1.0, 0]), [m.uv_px(30, 140)] * 4)
    return m

RR = dict(post_every=8.0, post_h=3.4, post_r=0.17, rail_r=0.15, rail_y=3.15, sink=0.4, sides=8)   # v83 (Saint-Georges v28)

def rail_round(line_xz, ground, origin):
    """v83 (Saint-Georges v28, user's on-board photo): the simple wooden barrier along the metal fence: round posts every
    post_every ft and ONE round top rail following the ground (statue yaw 0, origin on the ground). Texture: rail_texture()."""
    from scipy.ndimage import gaussian_filter1d
    m = Mesh(256, 256); ox, oz = origin; g0 = ground(ox, oz); C = RR; n_ = C['sides']
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(line_xz, axis=0), axis=1))]
    gy = gaussian_filter1d(np.array([ground(x, z) for x, z in line_xz]) - g0, 1.5, mode='nearest')
    P = np.c_[line_xz[:, 0] - ox, line_xz[:, 1] - oz]; up = np.array([0, 1.0, 0])
    for i in range(len(P) - 1):                                   # top rail: a round bar per piece, wood grain along it
        a = np.array([P[i, 0], gy[i] + C['rail_y'], P[i, 1]]); b = np.array([P[i + 1, 0], gy[i + 1] + C['rail_y'], P[i + 1, 1]])
        d = b - a; d /= np.linalg.norm(d) + 1e-12; e1 = np.cross(d, up); e1 /= np.linalg.norm(e1) + 1e-12; e2 = np.cross(e1, d)
        ua_, ub_ = (i % 8) * 32 + 1, (i % 8 + 1) * 32 - 1
        for k in range(n_):
            t0, t1 = 2 * np.pi * k / n_, 2 * np.pi * (k + 1) / n_
            r0 = e1 * np.cos(t0) + e2 * np.sin(t0); r1 = e1 * np.cos(t1) + e2 * np.sin(t1); r_ = C['rail_r']
            v0_, v1_ = 4 + k * 120 / n_, 4 + (k + 1) * 120 / n_
            m.tri_fan([a + r0 * r_, b + r0 * r_, b + r1 * r_, a + r1 * r_], (r0 + r1) / 2,
                      [m.uv_px(ua_, v0_), m.uv_px(ub_, v0_), m.uv_px(ub_, v1_), m.uv_px(ua_, v1_)])
    np_ = max(1, int(round(L[-1] / C['post_every'])))
    for sv in np.linspace(0, L[-1], np_ + 1):                    # round posts, grain along them, a rounded top
        x = np.interp(sv, L, P[:, 0]); z = np.interp(sv, L, P[:, 1]); y = np.interp(sv, L, gy); r_ = C['post_r']
        ya, yb = y - C['sink'], y + C['post_h']
        for k in range(n_):
            t0, t1 = 2 * np.pi * k / n_, 2 * np.pi * (k + 1) / n_
            c0 = np.array([np.cos(t0), 0, np.sin(t0)]); c1 = np.array([np.cos(t1), 0, np.sin(t1)]); c = np.array([x, 0, z])
            u0, u1 = k * 256 / n_ + 1, (k + 1) * 256 / n_ - 1
            m.tri_fan([c + c0 * r_ + up * ya, c + c1 * r_ + up * ya, c + c1 * r_ + up * yb, c + c0 * r_ + up * yb], (c0 + c1) / 2,
                      [m.uv_px(u0, 252), m.uv_px(u1, 252), m.uv_px(u1, 132), m.uv_px(u0, 132)])
        m.tri_fan([np.array([x + np.cos(t) * r_, yb + 0.05, z + np.sin(t) * r_]) for t in np.linspace(0, 2 * np.pi, n_, endpoint=False)][::-1],
                  up, [m.uv_px(128, 200)] * n_)
    return m

if __name__ == '__main__':
    img, pal = rail_texture(); os.makedirs(OUTD, exist_ok=True); img.save(f'{OUTD}/rail_wood.png'); print('rail_wood.png')
