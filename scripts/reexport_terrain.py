"""Rewrite only the terrain files of the 3 track folders (terrain.hf / terrain.png / shading.ppm / shadingx2.ppm / tilemap)
from build/H.npy + build/tiles.npy (build_sx.py), with exactly the encoding and shading of export_sx.py, without the reference
archives. Keeps the concrete roads painted by dress_sx.py (tile 8) and every other file (statues, decals, timing_gates...).
Use after a change of the terrain only (e.g. one obstacle swapped in layouts_sx.py):
    python3 scripts/build_sx.py && python3 scripts/reexport_terrain.py"""
import os, sys
ROOT = os.environ.get('MXSIM_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
import numpy as np
from PIL import Image
from shading import lambert_shadow
from names import FOLDERS as F

H = np.load(f'{ROOT}/build/H.npy').astype(np.float64); tiles = np.load(f'{ROOT}/build/tiles.npy')
N = H.shape[0]; S = 0.28975; NE = 11
hmin, hmax = float(H.min()) - 0.5, float(H.max()) + 0.5
raw = np.round((H - hmin) / (hmax - hmin) * 65535).astype(np.uint16)
hf = f'{NE} {S:.6f} {hmin:.6f} {hmax:.6f}\n'
lam, _ = lambert_shadow(H, S, [-0.6528, 0.3590, 0.6671], shadow=False)
sh = np.clip(89.3 + 245.8 * lam, 0, 255).astype(np.uint8)          # calibrated on JGSX Detroit shading.ppm (r = 0.995)
for key, folder in F.items():
    d = f'{ROOT}/tracks/{folder}'
    old_tm = np.fromfile(f'{d}/tilemap', np.uint8).reshape(2048, 2048)
    tm = tiles.astype(np.uint8).copy(); tm[old_tm == 8] = 8                    # keep the concrete roads (dress_sx.roads)
    open(f'{d}/terrain.hf', 'w', newline='\n').write(hf); Image.fromarray(raw).save(f'{d}/terrain.png'); tm.tofile(f'{d}/tilemap')
    for nm, img in (('shading.ppm', sh), ('shadingx2.ppm', (sh // 2).astype(np.uint8))):
        with open(f'{d}/{nm}', 'wb') as fh: fh.write(f'P6\n{N} {N}\n255\n'.encode()); fh.write(np.repeat(img[:, :, None], 3, axis=2).tobytes())
    print(folder, 'terrain réécrit')
