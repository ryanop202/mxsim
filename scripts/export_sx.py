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
copies = {'tiles/dirt.ppm': f'{REF}/JGMXDrDew/JGMXDrDew/tiles/dirt.ppm', 'tiles/hardpack.ppm': f'{REF}/JGMXDrDew/JGMXDrDew/tiles/hardpack.ppm',
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
TILES = [('Main', 'hardpack', dirt_fx), ('Jumps Sx', 'dirt', dirt_fx), ('WhoopsV2', 'dirt', dirt_fx), ('Berm Exit Sx', 'dirt', dirt_fx),
         ('Sand Straight', 'sand', sand_fx), ('Sand Bump Straight', 'sand', sand_fx), ('Sand Exit', 'sand', sand_fx), ('Sand Bump Solo', 'sand', sand_fx)]
ti = []
for name, tex, fx in TILES: ti += [f'name {name}'] + block(name) + [f'texture {P}/tiles/{tex}.ppm'] + fx + ['addtile', '']
tileinfo = '\n'.join(ti) + '\n'
hmin, hmax = float(H.min()) - 0.5, float(H.max()) + 0.5
raw = np.round((H - hmin) / (hmax - hmin) * 65535).astype(np.uint16)
hf = f'{NE} {S:.6f} {hmin:.6f} {hmax:.6f}\n'
lam, _ = lambert_shadow(H, S, [-0.6528, 0.3590, 0.6671], shadow=False)
sh = np.clip(89.3 + 245.8 * lam, 0, 255).astype(np.uint8)          # calibrated on JGSX Detroit shading.ppm (r = 0.995)
lighting = open(f'{DET}/lighting').read().replace('@JGSX2026Detroit/sky/', f'{P}/sky/')

def gates(path, start, cp_step=60.0, half=18.0):
    """JGSX-style timing: 22-gate row facing the start heading; 2 first-lap-only gates across the start straight;
    loop gates every cp_step ft starting just after the merge point M (lap counter = last gate, just before M)."""
    smp = path.samples(0.5); L = path.s
    gx, gz = start['gate']; h = np.radians(start['heading']); f = np.array([np.cos(h), np.sin(h)]); n = np.array([-f[1], f[0]])
    ang = float(np.arctan2(-f[0], -f[1]))                     # MXS gate angle: riders face (-sin a, -cos a)
    lines = ['startinggate:']
    for k in range(LS.N_GATES):
        o = (k - (LS.N_GATES - 1) / 2) * LS.GATE_PITCH; x, z = gx + o * n[0], gz + o * n[1]
        lines.append(f'[{x:.6f} 0.000000 {z:.6f}] {ang:.6f}')
    lines.append('checkpoints:'); cps = []
    sM = float(smp['s'][np.argmin(np.hypot(smp['x'] - start['merge'][0], smp['z'] - start['merge'][1]))])
    rel = list(np.arange(30.0, L - 30.0, cp_step)) + [L - 8.0]
    for r in rel:
        sv = (sM + r) % L; i = int(np.argmin(np.abs(smp['s'] - sv))); x, z, th = smp['x'][i], smp['z'][i], smp['th'][i]
        hl = half + (6.0 if path.segs[int(smp['seg'][i])]['kind'] == 'P' else 0.0)     # wider in the Glendale sand channel
        cps.append((hl, x, z, -np.sin(th) * hl, np.cos(th) * hl))
    loop_idx = list(range(len(cps)))
    for dist in (60.0, start['straight']):                    # first-lap-only gates across the start straight
        c = np.array([gx, gz]) + f * dist; hl = (LS.N_GATES - 1) / 2 * LS.GATE_PITCH + 8.0
        cps.append((hl, c[0], c[1], n[0] * hl, n[1] * hl))
    for c in cps: lines.append(f'{c[0]:.6f} [{c[1]:.6f} 0.000000 {c[2]:.6f}] [{c[3]:.6f} 0.000000 {c[4]:.6f}]')
    first = list(range(len(loop_idx), len(cps))) + loop_idx
    lines += ['firstlap:', ' '.join(map(str, first)) + ' ', 'normallap:', ' '.join(map(str, loop_idx)) + ' ', '']
    return '\n'.join(lines), cps, first, loop_idx, sM

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
json.dump({k: dict(n_cp=len(v[1]), first=v[2], normal=v[3], s_merge=v[4]) for k, v in GT.items()} | dict(hmin=hmin, hmax=hmax), open(f'{BUILD}/export_info.json', 'w'))
print('exported', {k: len(v[1]) for k, v in GT.items()}, 'heights', round(hmin, 2), round(hmax, 2))
