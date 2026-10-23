"""Export the built compound to three MX Simulator track folders sharing one terrain.

Folder layout (install into MX Simulator's personal tracks folder):
  RyanCompoundMX/   full track (MX lap) + shared assets (tiles/, sky/, roost/, treads/)
  RyanCompoundSX1/  same terrain, SX1 timing gates
  RyanCompoundSX2/  same terrain, SX2 timing gates
"""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import os, sys, re, json, shutil, numpy as np
sys.path.insert(0, ROOT + '/scripts')
from PIL import Image
from shading import lambert_shadow
from engine import LIB
import layouts

BUILD = ROOT + '/legacy_mx/build'; OUT = ROOT + '/legacy_mx/tracks'; REF = REF
MXF, SX1F, SX2F = 'RyanCompoundMX', 'RyanCompoundSX1', 'RyanCompoundSX2'
H = np.load(f'{BUILD}/H.npy').astype(np.float64); tiles = np.load(f'{BUILD}/tiles.npy')
N = H.shape[0]; S = 0.4; N_EXP = 11
assert N == 2 ** (N_EXP + 1) + 1 and tiles.shape == (2 ** N_EXP, 2 ** N_EXP)
if os.path.exists(OUT): shutil.rmtree(OUT)
for f in (MXF, SX1F, SX2F): os.makedirs(f'{OUT}/{f}')

# ---------------- shared assets (copied from the reference archives) into the MX folder
A = f'{OUT}/{MXF}'
copies = {
    'tiles/dirt.ppm': f'{REF}/JGMXDrDew/JGMXDrDew/tiles/dirt.ppm',
    'tiles/hardpack.ppm': f'{REF}/JGMXDrDew/JGMXDrDew/tiles/hardpack.ppm',
    'tiles/grass.ppm': f'{REF}/JGMXDrDew/JGMXDrDew/tiles/grass.ppm',
    'tiles/sand.ppm': f'{REF}/JGMXDesertSand/JGMXDesertSand/tiles/sand.ppm',
    'roost/redroost.png': f'{REF}/JGMXDesertSand/JGMXDesertSand/tiles/redroost.png',
    'roost/dirt4.png': f'{REF}/JGMXDesertSand/JGMXDesertSand/tiles/dirt4.png',
    'roost/hha.dust.png': f'{REF}/JGMXDesertSand/JGMXDesertSand/tiles/hha.dust.png',
    'treads/dirt2x4.png': f'{REF}/JGSX2026TestTracks/JGSX2026Detroit/decal/treads/dirt2x4.png',
    'treads/dirt2x8.png': f'{REF}/JGSX2026TestTracks/JGSX2026Detroit/decal/treads/dirt2x8.png',
    'treads/sand1x4.png': f'{REF}/JGSX2026TestTracks/JGSX2026Detroit/decal/treads/sand1x4.png',
    'treads/sand1x8.png': f'{REF}/JGSX2026TestTracks/JGSX2026Detroit/decal/treads/sand1x8.png',
}
for k in ('skybox-0', 'skybox-1', 'skybox-2', 'skybox-3', 'skybox-4', 'skybox-6'):
    copies[f'sky/{k}.png'] = f'{REF}/JGMXDesertSand/JGMXDesertSand/sky/{k}.png'
for dst, src in copies.items():
    os.makedirs(os.path.dirname(f'{A}/{dst}'), exist_ok=True); shutil.copy(src, f'{A}/{dst}')

# ---------------- tileinfo (physics blocks copied verbatim from the references; textures remapped)
def block(ref_file, idx):
    txt = open(ref_file, errors='replace').read().split('addtile')[idx]
    return [l.strip() for l in txt.splitlines() if l.strip() and not l.strip().startswith(('texture', 'roost', 'treadmark', 'name'))]
DD = f'{REF}/JGMXDrDew/JGMXDrDew/tileinfo'; DS = f'{REF}/JGMXDesertSand/JGMXDesertSand/tileinfo'; SXC = f'{REF}/JGSX2026TestTracks/JGSX2026Custom/tileinfo'
P = '@' + MXF
dirt_fx = [f'roost texture=@splash.png count=4 slip_threshold=2.0 slow_speed=0.0 fast_speed=64.0 slow_angle=1.07 fast_angle=0.196 size=0.80 grow=2.3 drag=1.90 vscale=1.0 randomize=5.0 r=123 g=73 b=52 a=255 fade_r=0 fade_g=0 fade_b=0 fade_a=1024',
           f'roost texture={P}/roost/redroost.png count=8 dig=0.0 slip_threshold=2.0 slow_speed=0.0 fast_speed=64.0 slow_angle=1.07 fast_angle=0.196 size=1.5 grow=4.0 drag=2.0 vscale=1.0 randomize=5.0 r=255 g=255 b=255 a=255 fade_r=0 fade_g=0 fade_b=0 fade_a=1024',
           f'treadmark texture={P}/treads/dirt2x4.png size=4 aspect=0.5 spacing=3 speed_threshold=-20',
           f'treadmark texture={P}/treads/dirt2x8.png size=8 aspect=0.25 spacing=6']
sand_fx = [f'roost texture={P}/roost/hha.dust.png count=4 dig=1.0 slip_threshold=2.0 slow_speed=0.0 fast_speed=50.0 slow_angle=1 fast_angle=0.1 size=2.0 grow=2.0 drag=1.5 vscale=1.0 randomize=1 r=255 g=255 b=255 a=255 fade_r=0 fade_g=0 fade_b=0 fade_a=-256',
           f'roost texture={P}/roost/dirt4.png count=4 dig=0.0 slip_threshold=2.0 slow_speed=0.0 fast_speed=50.0 slow_angle=1.57 fast_angle=0.296 size=1.0 grow=2.5 drag=1.0 vscale=1.0 randomize=1 r=255 g=255 b=255 a=255 fade_r=0 fade_g=0 fade_b=0 fade_a=256',
           f'treadmark texture={P}/treads/sand1x4.png size=4 aspect=0.25 spacing=3 speed_threshold=-20',
           f'treadmark texture={P}/treads/sand1x8.png size=8 aspect=0.125 spacing=6']
TILES = [  # order = tilemap index used by build_compound.py
    ('Grass (Dr.Dew grass physics)', block(DD, 3), f'{P}/tiles/grass.ppm', ['roost texture=@roost.png count=6 size=1.0']),
    ('MX dirt (Dr.Dew dirt physics)', block(DD, 1), f'{P}/tiles/dirt.ppm', dirt_fx),
    ('MX jumps (Dr.Dew JUMPS physics)', block(DD, 4), f'{P}/tiles/dirt.ppm', dirt_fx),
    ('MX sand (Desert Sand physics)', block(DS, 0), f'{P}/tiles/sand.ppm', sand_fx),
    ('SX floor (JGSX Main)', block(SXC, 0), f'{P}/tiles/hardpack.ppm', dirt_fx),
    ('SX jumps (JGSX Jumps Sx)', block(SXC, 3), f'{P}/tiles/dirt.ppm', dirt_fx),
    ('SX whoops (JGSX WhoopsV2)', block(SXC, 7), f'{P}/tiles/dirt.ppm', dirt_fx),
    ('SX berms (JGSX Berm Exit Sx)', block(SXC, 1), f'{P}/tiles/dirt.ppm', dirt_fx),
]
ti = []
for name, phys, tex, fx in TILES:
    ti += [f'name {name}'] + phys + [f'texture {tex}'] + fx + ['addtile', '']
tileinfo = '\n'.join(ti) + '\n'

# ---------------- terrain files
hmin, hmax = float(H.min()) - 0.5, float(H.max()) + 0.5
raw = np.round((H - hmin) / (hmax - hmin) * 65535).astype(np.uint16)
hf = f'{N_EXP} {S:.6f} {hmin:.6f} {hmax:.6f}\n'
# quantisation check
q = hmin + raw.astype(np.float64) / 65535 * (hmax - hmin)
qerr = float(np.abs(q - H).max())
# lightmap: calibrated on JGMX Desert Sand (shade = 92.0 + 216.6 * lambert, r = 0.982)
SUN = [0.5128, 0.50, 0.3164]
lam, _ = lambert_shadow(H, S, SUN, shadow=False)
sh = np.clip(92.0 + 216.6 * lam, 0, 255).astype(np.uint8)
lighting = open(f'{REF}/JGMXDesertSand/JGMXDesertSand/lighting').read().replace('@JGMXDesertSand/sky/', f'{P}/sky/')

def write_common(folder, desc):
    d = f'{OUT}/{folder}'
    open(f'{d}/terrain.hf', 'w').write(hf)
    Image.fromarray(raw).save(f'{d}/terrain.png')
    tiles.astype(np.uint8).tofile(f'{d}/tilemap')
    open(f'{d}/tileinfo', 'w').write(tileinfo)
    open(f'{d}/lighting', 'w').write(lighting)
    open(f'{d}/desc', 'w').write(desc + '\n')
    for empty in ('flaggers', 'billboards', 'statues', 'decals'): open(f'{d}/{empty}', 'w').close()
    for nm, img in (('shading.ppm', sh), ('shadingx2.ppm', (sh // 2).astype(np.uint8))):
        with open(f'{d}/{nm}', 'wb') as fh:
            fh.write(f'P6\n{N} {N}\n255\n'.encode()); fh.write(np.repeat(img[:, :, None], 3, axis=2).tobytes())

# ---------------- timing gates
def gates_for(path, start_xz, n_gates, cp_step, half_len, start_pad_dx=0.0):
    smp = path.samples(0.5); L = path.s
    lines = ['startinggate:']
    gx, gz = start_xz
    for k in range(n_gates):   # row along +z, riders facing +x  (angle -pi/2, same convention as JGSX references)
        lines.append(f'[{gx:.6f} 0.000000 {gz - (n_gates - 1) * 2.0 + 4.0 * k:.6f}] -1.570796')
    lines.append('checkpoints:')
    cps = []
    svals = list(np.arange(cp_step * 0.5, L - cp_step * 0.4, cp_step)) + [L - 1.0]
    for s in svals:
        i = int(np.argmin(np.abs(smp['s'] - s))); x, z, th = smp['x'][i], smp['z'][i], smp['th'][i]
        nx, nz = -np.sin(th) * half_len, np.cos(th) * half_len
        cps.append((x, z, nx, nz))
        lines.append(f'{half_len:.6f} [{x:.6f} 0.000000 {z:.6f}] [{nx:.6f} 0.000000 {nz:.6f}]')
    idx = ' '.join(str(i) for i in range(len(cps)))
    lines += ['firstlap:', idx + ' ', 'normallap:', idx + ' ', '']
    return '\n'.join(lines), cps

mx = layouts.mx(); sx1 = layouts.sx1(); sx2 = layouts.sx2()
G_MX, cps_mx = gates_for(mx, (50.0, 1060.0), 20, 120.0, 26.0)
G_SX1, cps_sx1 = gates_for(sx1, (layouts.SX1_ORIGIN[0] + 25.0, layouts.SX1_ORIGIN[1] + 395.0), 20, 60.0, 18.0)
G_SX2, cps_sx2 = gates_for(sx2, (layouts.SX2_ORIGIN[0] + 25.0, layouts.SX2_ORIGIN[1] + 25.0), 20, 60.0, 18.0)
write_common(MXF, 'Ryan Compound: MX')
write_common(SX1F, 'Ryan Compound: SX 1')
write_common(SX2F, 'Ryan Compound: SX 2')
open(f'{OUT}/{MXF}/timing_gates', 'w').write(G_MX)
open(f'{OUT}/{SX1F}/timing_gates', 'w').write(G_SX1)
open(f'{OUT}/{SX2F}/timing_gates', 'w').write(G_SX2)
json.dump(dict(hmin=hmin, hmax=hmax, quant_err_ft=qerr, n_cp=dict(MX=len(cps_mx), SX1=len(cps_sx1), SX2=len(cps_sx2)),
               cps=dict(MX=cps_mx, SX1=cps_sx1, SX2=cps_sx2)), open(f'{BUILD}/export_info.json', 'w'), default=float)
print('exported; height range', hmin, hmax, 'quantisation error', qerr, 'checkpoints', len(cps_mx), len(cps_sx1), len(cps_sx2))
