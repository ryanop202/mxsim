"""Saint-Georges v28 (user's photo: the long logo boudins are really 3 boudins in one, the 50 Factory logo much longer): a
logo boudin 3 segments long (same section as stt_ads.boudin_logo, 18 ft), one big logo per side, grey ends.

Writes assets/props/boudin_logo3.jm / .shp and the textures <name>3.png (2048 x 1024) for the logo boudins of this track.
Run from mxsim:  ../venv_mx/Scripts/python.exe scripts/boudin3.py
"""
import os, sys
import numpy as np
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import stt_props as SP
import stt_ads as AD
from props_usland import Mesh, OUTD

N = 3; TW, TH = 2048, 1024
LOGO = dict(h=1.40, s=1.50, w=0.86)            # logo height (ft of arc), centre height over the foot (ft of arc), max width (x length)
SKINS = {'startb_50factory': ('50factory', (249, 229, 42), 1.0), 'boudin_fly': ('fly', None, 1.0),
         'boudin_sxtour': ('sxtour', None, 1.0), 'boudin_bobcat': ('bobcat', (196, 22, 18), 1.3)}   # v28b (user): Bobcat logo bigger
GREY = (118, 120, 124)

def model():
    B = SP.BOUDIN; m = Mesh(TW, TH); sec = AD._boudin_arc(); half = sec[-1][3] / 2; RW = AD.BL['rows']
    L = N * B['L']; hx = L / 2; pxu, pxv = TW / L, RW / half; xs = np.linspace(-hx, hx, 9 * N)
    def uv(x, s_):
        if s_ <= half + 1e-9: return m.uv_px((x + hx) * pxu, RW - s_ * pxv)
        return m.uv_px((hx - x) * pxu, RW + RW - (sec[-1][3] - s_) * pxv)
    for k in range(len(sec) - 1):
        (za, ya, na, sa), (zb, yb, nb, sb) = sec[k], sec[k + 1]
        for i in range(len(xs) - 1):
            xa, xb = xs[i], xs[i + 1]
            U = [uv(xa, sa if sb <= half + 1e-9 else sa + 1e-6), uv(xb, sa if sb <= half + 1e-9 else sa + 1e-6), uv(xb, sb), uv(xa, sb)]
            SP._smooth(m, [(xa, ya, za), (xb, ya, za), (xb, yb, zb), (xa, yb, zb)], [na, na, nb, nb], U)
    cu = m.uv_px(TW / 2, 990)
    for sx in (1, -1):
        m.tri_fan([np.array((sx * hx, y, z)) for z, y, _, _ in sec], np.array([sx * 1.0, 0, 0]), [cu] * len(sec))
    return m

def texture(logo, base, k):
    B = SP.BOUDIN; sec = AD._boudin_arc(); half = sec[-1][3] / 2; RW = AD.BL['rows']; L = N * B['L']; pxu, pxv = TW / L, RW / half
    img = np.zeros((TH, TW, 3)); img[:] = SP._vinyl(TH, TW, 60, 30, 44, amp=4, base=base or (17, 17, 19.0))
    lg = AD.logo(logo, dark=base is None)
    for r0 in (0, RW):
        cy = r0 + RW - LOGO['s'] * pxv
        AD.paste(img, AD.fit(lg, TW / 2, cy, LOGO['w'] * L * pxu * k, LOGO['h'] * pxv * k), lg)
    img[960:] = SP._vinyl(TH - 960, TW, 60, 30, 45, amp=4, base=GREY)          # grey ends (user: "gris a l'interieur")
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))

def shape():
    B = SP.BOUDIN; C = SP.BOUDIN_SHP; hx = (N * B['L'] - B['gap']) / 2; rows = []
    for x in np.arange(-hx + C['r'] * 0.6, hx - C['r'] * 0.6 + 1e-6, C['every']):
        rows.append(f"{x:.4f} {C['r'] - B['sink'] + 0.05:.4f} 0 {C['r']} {C['friction']} {C['spring']} {C['damping']}")
    return '\n'.join([str(len(rows))] + rows) + '\n'

if __name__ == '__main__':
    m = model(); print('boudin_logo3', m.write(f'{OUTD}/boudin_logo3.jm', (24, 0.5, 0.4, 0.4, 0.4)))
    open(f'{OUTD}/boudin_logo3.shp', 'w', newline='\n').write(shape())
    for nm, (lg, base, k) in SKINS.items(): texture(lg, base, k).save(f'{OUTD}/{nm}3.png'); print(nm + '3.png')
