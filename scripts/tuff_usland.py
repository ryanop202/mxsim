"""v11 white tuff block with the USLAND logo on both long sides.
- model tuff_usland.jm: plain box with the JGSX tuff-medium.jm size (1.8 x 1.8 x 5.4 ft, long axis = local z), flat faces;
  the two long sides (+x / -x) each map to one half of the texture, the other faces to a white corner.
  UV orientation copied from the JGSX transit van (readable text on both sides): +x face u = (2.7 - z)/5.4, -x face
  u = (z + 2.7)/5.4, v grows upward (v = 0 = bottom row of the image). Winding: cross(b-a, c-a) along the normal (as tuff-medium.jm).
- texture tuff_usland.png 1024 x 1024: rows 0-511 = +x side, rows 512-1023 = -x side; white with a thin grey edge and the logo
  (logo pre-squeezed so it is not stretched on the 3:1 face).
Input: the logo image given by Ryan (assets/usland_logo.png). Writes into tracks/<SX1>/statue/."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
import numpy as np
from PIL import Image
from names import FOLDERS

W, Hh, Lb = 1.8, 1.8, 5.4
OUTD = f'{ROOT}/tracks/{FOLDERS["SX1"]}/statue'

def model():
    x0, x1, y0, y1, z0, z1 = -W / 2, W / 2, 0.0, Hh, -Lb / 2, Lb / 2
    white = (0.02, 0.52)
    faces = []   # (4 corners counter-clockwise seen from outside, normal, uv function)
    def q(n, pts, uv): faces.append((pts, n, uv))
    q((1, 0, 0), [(x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1)], lambda p: ((Lb / 2 - p[2]) / Lb, 0.5 + 0.5 * p[1] / Hh))
    q((-1, 0, 0), [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)], lambda p: ((p[2] + Lb / 2) / Lb, 0.5 * p[1] / Hh))
    q((0, 1, 0), [(x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)], lambda p: white)
    q((0, -1, 0), [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], lambda p: white)
    q((0, 0, 1), [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], lambda p: white)
    q((0, 0, -1), [(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)], lambda p: white)
    V, I = [], []
    for pts, n, uv in faces:
        P = np.array(pts, float); a = len(V)
        if np.dot(np.cross(P[1] - P[0], P[2] - P[0]), n) < 0: P = P[::-1]          # winding: cross(b-a, c-a) along the normal
        for p in P: V.append((*p, *n, *uv(p)))
        I += [a, a + 1, a + 2, a, a + 2, a + 3]
    lines = ['JM1', '0.000000 0.000000 0.000000 0.000000 0.000000', f'{len(V)} {len(I) // 3}']
    lines += [' '.join(f'{v:.6f}' for v in row) for row in V] + [str(i) for i in I] + ['']
    open(f'{OUTD}/tuff_usland.jm', 'w').write('\n'.join(lines))

def texture(logo_path):
    lg = np.array(Image.open(logo_path).convert('RGB')).astype(float)
    ink = lg.min(2) < 150                                     # navy text + red marks (the faint ghost text stays out)
    ys, xs = np.nonzero(ink); crop = Image.open(logo_path).convert('RGB').crop((xs.min() - 6, ys.min() - 6, xs.max() + 7, ys.max() + 7))
    a = crop.size[0] / crop.size[1]
    w_ft = 4.5; h_ft = w_ft / a                              # logo size on the block
    pw, ph = int(w_ft * 1024 / Lb), int(h_ft * 512 / Hh)      # pre-squeezed so it is not stretched on the face
    crop = crop.resize((pw, ph), Image.LANCZOS)
    c = np.array(crop).astype(float); bg = np.median(np.r_[c[0], c[-1], c[:, 0], c[:, -1]], axis=0)
    c = np.clip(c + (255 - bg), 0, 255).astype(np.uint8)    # logo background -> pure white
    tex = Image.new('RGB', (1024, 1024), (255, 255, 255))
    for r0 in (0, 512):
        tex.paste(Image.fromarray(c), ((1024 - pw) // 2, r0 + (512 - ph) // 2))
    t = np.array(tex)
    for r0 in (0, 512):                                       # thin grey edge (moulded block look)
        t[r0:r0 + 10] = t[r0 + 502:r0 + 512] = 205; t[r0:r0 + 512, :10] = t[r0:r0 + 512, -10:] = 205
    Image.fromarray(t).save(f'{OUTD}/tuff_usland.png')

if __name__ == '__main__':
    os.makedirs(OUTD, exist_ok=True); model(); texture(f'{ROOT}/assets/usland_logo.png'); print('tuff_usland.jm + tuff_usland.png')
