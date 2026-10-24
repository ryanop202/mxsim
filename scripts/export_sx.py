"""Export: the 3 track folders (names.FOLDERS) share one terrain; shared assets live in the SX1 folder."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import os, sys, json, shutil, numpy as np
sys.path.insert(0, ROOT + '/scripts')
from PIL import Image
from shading import lambert_shadow
import layouts_sx as LS

BUILD = ROOT + '/build'; OUT = ROOT + '/tracks'; REF = REF
from names import FOLDERS as F, DESC as _DESC
H = np.load(f'{BUILD}/H.npy').astype(np.float64); tiles = np.load(f'{BUILD}/tiles.npy')
N = H.shape[0]; S = 0.28975; NE = 11
if os.path.exists(OUT): shutil.rmtree(OUT)
for f in F.values(): os.makedirs(f'{OUT}/{f}')
A = f'{OUT}/{F["SX1"]}'; P = '@' + F['SX1']
DET = f'{REF}/JGSX2026TestTracks/JGSX2026Detroit'
copies = {'tiles/dirt.ppm': f'{REF}/JGMXDrDew/JGMXDrDew/tiles/dirt.ppm', 'tiles/hardpack.ppm': f'{REF}/JGMXDrDew/JGMXDrDew/tiles/hardpack.ppm', 'tiles/concrete.ppm': f'{REF}/JGMXDrDew/JGMXDrDew/tiles/concrete.ppm',
          'tiles/sand.ppm': f'{REF}/JGMXDesertSand/JGMXDesertSand/tiles/sand.ppm', 'roost/redroost.png': f'{REF}/JGMXDesertSand/JGMXDesertSand/tiles/redroost.png',
          'roost/dirt4.png': f'{REF}/JGMXDesertSand/JGMXDesertSand/tiles/dirt4.png', 'roost/hha.dust.png': f'{REF}/JGMXDesertSand/JGMXDesertSand/tiles/hha.dust.png'}
for k in ('dirt2x4', 'dirt2x8', 'sand1x4', 'sand1x8'): copies[f'treads/{k}.png'] = f'{DET}/decal/treads/{k}.png'
for k in ('sky-n', 'sky-e', 'sky-s', 'sky-w', 'sky-u', 'sky-env'): copies[f'sky/{k}.png'] = f'{DET}/sky/{k}.png'
for dst, src in copies.items():
    os.makedirs(os.path.dirname(f'{A}/{dst}'), exist_ok=True); shutil.copy(src, f'{A}/{dst}')
# tileinfo: physics blocks copied verbatim from JGSX (Custom test track tileinfo), textures remapped to the package
SXC = open(f'{REF}/JGSX2026TestTracks/JGSX2026Custom/tileinfo', errors='replace').read().split('addtile')
def block(name):
    for b in SXC:
        if f'name {name}' in b:
            return [l.strip() for l in b.splitlines() if l.strip() and not l.strip().startswith(('texture', 'roost', 'treadmark', 'name'))]
    raise KeyError(name)
dirt_fx = ['roost texture=@splash.png count=4 slip_threshold=2.0 slow_speed=0.0 fast_speed=64.0 slow_angle=1.07 fast_angle=0.196 size=0.80 grow=2.3 drag=1.90 vscale=1.0 randomize=5.0 r=123 g=73 b=52 a=255 fade_r=0 fade_g=0 fade_b=0 fade_a=1024',
           f'roost texture={P}/roost/redroost.png count=8 dig=0.0 slip_threshold=2.0 slow_speed=0.0 fast_speed=64.0 slow_angle=1.07 fast_angle=0.196 size=1.5 grow=4.0 drag=2.0 vscale=1.0 randomize=5.0 r=255 g=255 b=255 a=255 fade_r=0 fade_g=0 fade_b=0 fade_a=1024',
           f'treadmark texture={P}/treads/dirt2x4.png size=4 aspect=0.5 spacing=3 speed_threshold=-20', f'treadmark texture={P}/treads/dirt2x8.png size=8 aspect=0.25 spacing=6']
sand_fx = [f'roost texture={P}/roost/hha.dust.png count=4 dig=1.0 slip_threshold=2.0 slow_speed=0.0 fast_speed=50.0 slow_angle=1 fast_angle=0.1 size=2.0 grow=2.0 drag=1.5 vscale=1.0 randomize=1 r=255 g=255 b=255 a=255 fade_r=0 fade_g=0 fade_b=0 fade_a=-256',
           f'roost texture={P}/roost/dirt4.png count=4 dig=0.0 slip_threshold=2.0 slow_speed=0.0 fast_speed=50.0 slow_angle=1.57 fast_angle=0.296 size=1.0 grow=2.5 drag=1.0 vscale=1.0 randomize=1 r=255 g=255 b=255 a=255 fade_r=0 fade_g=0 fade_b=0 fade_a=256',
           f'treadmark texture={P}/treads/sand1x4.png size=4 aspect=0.25 spacing=3 speed_threshold=-20', f'treadmark texture={P}/treads/sand1x8.png size=8 aspect=0.125 spacing=6']
TILES = [('Main', 'dirt', dirt_fx), ('Jumps Sx', 'dirt', dirt_fx), ('WhoopsV2', 'dirt', dirt_fx), ('Berm Exit Sx', 'dirt', dirt_fx),
         ('Sand Straight', 'sand', sand_fx), ('Sand Bump Straight', 'sand', sand_fx), ('Sand Exit', 'sand', sand_fx), ('Sand Bump Solo', 'sand', sand_fx),
         ('Road', 'concrete', dirt_fx[2:])]   # v10: concrete service roads (physics of the Main block), painted by dress_sx.py
ti = []
for name, tex, fx in TILES: ti += [f'name {name}'] + block('Main' if name == 'Road' else name) + [f'texture {P}/tiles/{tex}.ppm'] + fx + ['addtile', '']
tileinfo = '\n'.join(ti) + '\n'
hmin, hmax = float(H.min()) - 0.5, float(H.max()) + 0.5
raw = np.round((H - hmin) / (hmax - hmin) * 65535).astype(np.uint16)
hf = f'{NE} {S:.6f} {hmin:.6f} {hmax:.6f}\n'
lam, _ = lambert_shadow(H, S, [-0.6528, 0.3590, 0.6671], shadow=False)
sh = np.clip(89.3 + 245.8 * lam, 0, 255).astype(np.uint8)          # calibrated on JGSX Detroit shading.ppm (r = 0.995)
lighting = open(f'{DET}/lighting').read().replace('@JGSX2026Detroit/sky/', f'{P}/sky/')

from timing import gate_marks, gates   # moved to timing.py (also used by regen_timing.py)

PATHS = {'SX1': LS.sx1(), 'SX2': LS.sx2(), 'SX3': LS.sx3()}
GT = {k: gates(PATHS[k], LS.STARTS[k]) for k in PATHS}
DESC = _DESC
for key, folder in F.items():
    d = f'{OUT}/{folder}'
    open(f'{d}/terrain.hf', 'w').write(hf); Image.fromarray(raw).save(f'{d}/terrain.png'); tiles.astype(np.uint8).tofile(f'{d}/tilemap')
    open(f'{d}/tileinfo', 'w').write(tileinfo); open(f'{d}/lighting', 'w').write(lighting); open(f'{d}/desc', 'w').write(DESC[key] + '\n')
    for e in ('flaggers', 'billboards', 'statues', 'decals'): open(f'{d}/{e}', 'w').close()
    for nm, img in (('shading.ppm', sh), ('shadingx2.ppm', (sh // 2).astype(np.uint8))):
        with open(f'{d}/{nm}', 'wb') as fh: fh.write(f'P6\n{N} {N}\n255\n'.encode()); fh.write(np.repeat(img[:, :, None], 3, axis=2).tobytes())
    open(f'{d}/timing_gates', 'w').write(GT[key][0])
json.dump({k: dict(n_cp=len(v[1]), first=v[2], normal=v[3], s_merge=v[4], s_finish=v[5]) for k, v in GT.items()} | dict(hmin=hmin, hmax=hmax), open(f'{BUILD}/export_info.json', 'w'))
print('exported', {k: len(v[1]) for k, v in GT.items()}, 'heights', round(hmin, 2), round(hmax, 2))
