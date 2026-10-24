"""Minimaps (map.png, 1024 x 1024 RGBA, whole terrain like JGMX Dr. Dew): the top-view look (hillshade + height colours)
without any line or label; each folder shows its own track (riding surface + obstacles), transparent elsewhere.
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
H = D.H; st = (H.shape[0] - 1) // M
Hc = H[:M * st:st, :M * st:st]; s = D.S * st
shade = LightSource(300, 40).hillshade(Hc, vert_exag=3 / s)
col = cm.terrain(np.clip(Hc / 12.0, 0, 1))[:, :, :3]
base = np.dstack([shade] * 3) * 0.75 + 0.25
rgb = np.where((Hc > 0.15)[:, :, None], base * (0.65 + 0.35 * col), base * np.array([0.78, 0.62, 0.45]))   # dirt tone on the floor
masks, xx, yy = D.riding_mask()
for key, folder in FOLDERS.items():
    m = masks[key]['foot'].astype(np.uint8)
    m = np.array(Image.fromarray(m * 255).resize((M, M), Image.NEAREST)) > 0
    m = ndi.binary_dilation(m, iterations=2)
    a = ndi.gaussian_filter(m.astype(float), 1.0)
    img = np.dstack([rgb, a]); img = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    Image.fromarray(img, 'RGBA').save(f'{D.OUT}/{folder}/map.png')
    Image.fromarray(img, 'RGBA').save(f'{ROOT}/viewer/figures/06_minimap_{key}.png')
    print('map', folder)
