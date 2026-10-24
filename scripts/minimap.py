"""Minimaps (map.png, 1024 x 1024 RGBA like JGMX Dr. Dew): the top-view look (hillshade + height colours) without any line
or label. v11 (Ryan): each folder's map is framed on ITS track only (square box around the track + 12 ft), same orientation as
the top views (x to the right, z down), transparent outside the track.
Writes tracks/<folder>/map.png and viewer/figures/06_minimap_SX*.png. Run after dress_sx.py."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
import sys, numpy as np
sys.path.insert(0, ROOT + '/scripts')
from PIL import Image
from matplotlib.colors import LightSource
import matplotlib.cm as cm
from scipy import ndimage as ndi
import dress_sx as D
from names import FOLDERS

M = 1024
masks, xx, yy = D.riding_mask()
for key, folder in FOLDERS.items():
    fm = masks[key]['foot']; zs, xs = np.nonzero(fm); c4 = 4 * D.S
    x0, x1, z0, z1 = xs.min() * c4 - 12, (xs.max() + 1) * c4 + 12, zs.min() * c4 - 12, (zs.max() + 1) * c4 + 12
    side = max(x1 - x0, z1 - z0); cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    gx = cx - side / 2 + (np.arange(M) + 0.5) * side / M; gz = cz - side / 2 + (np.arange(M) + 0.5) * side / M
    ix = np.clip((gx / D.S).astype(int), 0, D.N - 1); iz = np.clip((gz / D.S).astype(int), 0, D.N - 1)
    inside = ((gx >= 0) & (gx < D.SIZE))[None, :] & ((gz >= 0) & (gz < D.SIZE))[:, None]
    Hc = D.H[np.ix_(iz, ix)]; s = side / M
    shade = LightSource(300, 40).hillshade(Hc, vert_exag=3 / s)
    col = cm.terrain(np.clip(Hc / 12.0, 0, 1))[:, :, :3]
    base = np.dstack([shade] * 3) * 0.75 + 0.25
    rgb = np.where((Hc > 0.15)[:, :, None], base * (0.65 + 0.35 * col), base * np.array([0.78, 0.62, 0.45]))   # dirt tone on the floor
    m = fm[np.clip((gz / c4).astype(int), 0, fm.shape[0] - 1)][:, np.clip((gx / c4).astype(int), 0, fm.shape[1] - 1)] & inside
    m = ndi.binary_dilation(m, iterations=3)
    a = ndi.gaussian_filter(m.astype(float), 1.5)
    img = np.dstack([rgb, a]); img = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    Image.fromarray(img, 'RGBA').save(f'{D.OUT}/{folder}/map.png')
    prev = Image.new('RGBA', (M, M), (235, 235, 235, 255)); prev.alpha_composite(Image.fromarray(img, 'RGBA'))   # preview: transparency shown light grey
    prev.convert('RGB').save(f'{ROOT}/viewer/figures/06_minimap_{key}.png')
    print('map', folder, 'box', [round(v) for v in (cx - side / 2, cx + side / 2, cz - side / 2, cz + side / 2)])
