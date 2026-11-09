"""Wooden post-and-rail fence section (Saint-Thibery v20, asked by the user: "des barrieres en bois dans l'herbe, au niveau du
bas, autour de la piste"). Made from scratch with props_usland.Mesh (doc 12 conventions: 1 unit = 1 ft, y up, baked shades,
one texture, rounded edges). One section = 8 ft: one post at x = -4 (the next section brings the next post), two rails on the
+z side of the posts (the track side when placed). Origin = middle of the section at ground level.
Run: python scripts/fence_wood.py -> assets/props/fence_wood.jm / .png"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
from props_usland import Mesh, palette, OUTD

FW = dict(L=8.0, post_r=0.24, post_h=3.6, rails=((1.15, 1.55), (2.55, 2.95)), rail_t=0.24, rail_r=0.07)
WOOD = (128, 94, 60)

def wood_strip(img, rect, along='x', seed=3):
    """weathered wood: base colour, long grain lines, a few darker knots and a light rounded mottle."""
    r = np.random.default_rng(seed); x0, y0, x1, y1 = rect; w, h = x1 - x0, y1 - y0
    a = np.zeros((h, w, 3)) + np.array(WOOD, float)
    L = w if along == 'x' else h; n = h if along == 'x' else w
    lines = np.cumsum(r.normal(0, 1, (n,))) * 0.0; grain = np.zeros((n, L))
    for k in range(40):                                        # grain lines across the strip
        c = r.uniform(0, n); amp = r.uniform(0.5, 2.0); ph = r.uniform(0, 6.3); fr = r.uniform(0.004, 0.02)
        pos = c + amp * np.sin(np.arange(L) * fr + ph)
        rows = np.arange(n)[:, None]; grain += np.exp(-((rows - pos[None, :]) ** 2) / 1.2) * r.uniform(0.05, 0.16)
    if along != 'x': grain = grain.T
    a *= (1 - grain[:, :, None])
    a *= (1 + 0.05 * r.normal(0, 1, (h, w)))[:, :, None]
    for _ in range(3):                                         # knots
        cx, cy = r.uniform(0, w), r.uniform(0, h); yy, xx = np.mgrid[0:h, 0:w]
        a *= (1 - 0.35 * np.exp(-(((xx - cx) / 5.0) ** 2 + ((yy - cy) / 3.0) ** 2)))[:, :, None]
    img.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), (x0, y0))

def fence_texture():
    img = Image.new('RGB', (512, 512), WOOD)
    rail, post = (8, 8, 504, 72), (8, 88, 72, 360)
    wood_strip(img, rail, 'x', 3); wood_strip(img, post, 'y', 5)
    pal = palette(img, ['wood', 'end'], [WOOD, (150, 118, 82)])
    pal.update(rail=rail, post=post)
    return img, pal

def fence_model(pal):
    m = Mesh(512, 512); L, R, Hp = FW['L'], FW['post_r'], FW['post_h']
    # post: 8-sided prism with a small rounded (chamfered) top
    seg = 8; ang = np.linspace(0, 2 * np.pi, seg + 1); cx, cz = -L / 2, 0.0
    x0, y0, x1, y1 = pal['post']; ytop = Hp - 0.12
    ring = lambda y, r: [np.array([cx + r * np.cos(t), y, cz + r * np.sin(t)]) for t in ang]
    A, B, C = ring(0.0, R), ring(ytop, R), ring(Hp, R * 0.55)
    for k in range(seg):
        n = np.array([np.cos((ang[k] + ang[k + 1]) / 2), 0, np.sin((ang[k] + ang[k + 1]) / 2)])
        u0, u1 = x0 + (x1 - x0) * k / seg, x0 + (x1 - x0) * (k + 1) / seg
        m.tri_fan([A[k], A[k + 1], B[k + 1], B[k]], n, [m.uv_px(u0, y1), m.uv_px(u1, y1), m.uv_px(u1, y0), m.uv_px(u0, y0)])
        nt = n * 0.55 + np.array([0, 0.83, 0]); nt /= np.linalg.norm(nt); e = m.uv_px(*pal['end'][1])
        m.tri_fan([B[k], B[k + 1], C[k + 1], C[k]], nt, [e] * 4)
    m.tri_fan(C[:-1][::-1], np.array([0, 1.0, 0]), [m.uv_px(*pal['end'][1])] * seg)
    # rails: rounded boxes along x, on the +z side of the post
    rx0, ry0, rx1, ry1 = pal['rail']; t = FW['rail_t']; z0 = R * 0.6; z1 = z0 + t
    for ya, yb in FW['rails']:
        m.rbox(-L / 2, L / 2, ya, yb, z0, z1, FW['rail_r'], 0, {'+y': ('r', pal['rail']), '-y': ('r', pal['rail']), '+z': ('r', pal['rail']),
               '-z': ('r', pal['rail'])}, pal['wood'])
    return m

if __name__ == '__main__':
    img, pal = fence_texture(); os.makedirs(OUTD, exist_ok=True)
    m = fence_model(pal); nv, nt = m.write(f'{OUTD}/fence_wood.jm', (0, 0, 0, 0, 0)); img.save(f'{OUTD}/fence_wood.png')
    V = np.array([v[:3] for v in m.V]); print('fence_wood', nv, 'vertices', nt, 'triangles; bbox', V.min(0).round(2), V.max(0).round(2))
