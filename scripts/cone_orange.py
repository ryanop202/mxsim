"""Traffic cone (Saint-Georges v17, user's on-board photo: a cone at the left of the finish take-off).
75 cm orange cone, two white reflective bands, black square base. props_usland.Mesh (1 unit = 1 ft, y up, baked shades).
Run: python scripts/cone_orange.py -> assets/props/cone_orange.jm / .png"""
import os, sys
import numpy as np
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
from props_usland import Mesh, palette, OUTD

FT = 1 / 0.3048
C = dict(H=0.75 * FT, base=0.38 * FT, base_h=0.035 * FT, r0=0.15 * FT, r1=0.028 * FT, seg=20,
         bands=((0.30, 0.42), (0.52, 0.60)))            # white bands (m from the ground)
ORANGE, WHITE, BLACK = (236, 96, 24), (232, 232, 228), (26, 26, 28)

def cone():
    img = Image.new('RGB', (256, 256), ORANGE); pal = palette(img, ['o', 'w', 'k'], [ORANGE, WHITE, BLACK])
    m = Mesh(256, 256); b, bh = C['base'] / 2, C['base_h']
    m.box(-b, b, 0.0, bh, -b, b, {'*': pal['o']})   # v28b (user): orange base too
    # body: truncated cone, rings at the band limits, each ring band one colour
    ys = [bh] + [y * FT for ab in C['bands'] for y in ab] + [C['H']]
    cols = ['o', 'w', 'o', 'w', 'o']
    rad = lambda y: C['r0'] + (C['r1'] - C['r0']) * (y - bh) / (C['H'] - bh)
    ang = np.linspace(0, 2 * np.pi, C['seg'] + 1)[:-1]; slope = (C['r0'] - C['r1']) / (C['H'] - bh)
    for k in range(len(ys) - 1):
        y0, y1 = ys[k], ys[k + 1]; r0, r1 = rad(y0), rad(y1); uv = m.uv_px(*pal[cols[k]][1])
        for i in range(C['seg']):
            a, c = ang[i], ang[(i + 1) % C['seg']]; am = a + np.pi / C['seg']   # v28b fix (user: open on one side): the wrap quad's normal pointed inwards
            P = [(r0 * np.cos(a), y0, r0 * np.sin(a)), (r0 * np.cos(c), y0, r0 * np.sin(c)),
                 (r1 * np.cos(c), y1, r1 * np.sin(c)), (r1 * np.cos(a), y1, r1 * np.sin(a))]
            n = np.array([np.cos(am), slope, np.sin(am)]); m.quad(P, n / np.linalg.norm(n), lambda p: uv)
    top = [(C['r1'] * np.cos(a), C['H'], C['r1'] * np.sin(a)) for a in ang]
    m.tri_fan(top, np.array([0, 1.0, 0]), [m.uv_px(*pal['o'][1])] * len(top))
    return img, m

if __name__ == '__main__':
    img, m = cone(); os.makedirs(OUTD, exist_ok=True)
    nv, nt = m.write(f'{OUTD}/cone_orange.jm', (0, 0, 0, 0, 0)); img.save(f'{OUTD}/cone_orange.png')
    V = np.array([v[:3] for v in m.V]); print('cone_orange', nv, 'vertices', nt, 'triangles; bbox', V.min(0).round(2), V.max(0).round(2))
