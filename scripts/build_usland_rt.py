"""usland race track - build + export of tracks/USLANDRaceTrack (doc 13). Independent of the SX compound: own terrain, own
folder, every resource copied inside (references @USLANDRaceTrack/...). Needs only what is in the repo: lib/, refs/rf/*.saf,
assets/, tracks/USLAND2026SX1 (JGSX tile physics, JGSX Detroit decals and USLAND textures already versioned there).

  terrain    engine.render_lane_block / render_berm_stamp on Grid(10, 0.28975) = 2049 px, 593.4 ft
  tiles      JGSX physics blocks of the USLAND tracks (tileinfo of USLAND2026SX1, paths remapped): Main, Jumps Sx, WhoopsV2, Berm Exit Sx
  gates      timing.gates (22 gates at 4 ft, 1 gate per turn + 2-3 per lane, finish on the crest of the RF step-up take-off)
  objects    RF Anaheim stadium (stadium models + textures from refs/rf/sx2026r01anaheim1.medium.saf, its own positions),
             USLAND start (start_gate on every gate, start_grate, start_gantry), USLAND FINISH arch centred on lane F, one cone per turn
  decals     JGSX Detroit decals (track ground, obstacle and turn marks, tear-offs), USLAND chalk (start corridor + holeshot)
  billboards finish flames on the arch (v13b, RF 2026 Anaheim 1 files of assets/sx2026) + frills.js
  NOT done   RBT decor: refs/rbt holds the placement files only, the 24.RBT models / textures are missing (doc 13).
python3 scripts/build_usland_rt.py"""
import os, sys, json, shutil, re
ROOT = os.environ.get('MXSIM_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from scipy.signal import find_peaks
from scipy.spatial import cKDTree
from engine import Grid, render_lane_block, render_berm_stamp, turn_mid_angle, berm_ang_scale, LIB
from shading import lambert_shadow
import layout_usland_rt as LU
import layouts_sx as LS
import timing
import rf_units
import props_usland as PU
import pyro_chalk as PC
from props_place import statue_ang

OUT = f'{ROOT}/tracks/{LU.FOLDER}'; P = '@' + LU.FOLDER; BUILD = ROOT + '/build'
SX1 = f'{ROOT}/tracks/USLAND2026SX1'
rng = np.random.default_rng(2026)
os.makedirs(BUILD, exist_ok=True)

# ------------------------------------------------------------------------------------------------ terrain + tiles
G = Grid(LU.N_EXP, LU.S); N = G.N; S = G.s; SIZE = G.size
TW = LIB['sx_lateral']['top_width']
path = LU.track(); R = LU.start_route()
jumps = np.zeros((N, N)); whoops = np.zeros((N, N)); berms = np.zeros((N, N))
for g in path.segs:
    if g['kind'] == 'S':
        for prof, u0, name in g['sections']:
            render_lane_block(G, whoops if 'whoops' in name else jumps, g, prof, u0, TW)
    elif g.get('berm'):
        render_berm_stamp(G, berms, g['berm'], g['cx'], g['cz'], turn_mid_angle(g), ang_scale=berm_ang_scale(g['berm'], g['ang']))
H = np.maximum.reduce([jumps, whoops, berms])
TN = 2 ** LU.N_EXP
def t(a): return a[:-1:2, :-1:2][:TN, :TN]
T_MAIN, T_JUMP, T_WHOOP, T_BERM = 0, 1, 2, 3
tiles = np.full((TN, TN), T_MAIN, np.uint8)
tiles[t(jumps) > 0.05] = T_JUMP; tiles[t(whoops) > 0.05] = T_WHOOP; tiles[t(berms) > 0.05] = T_BERM

# ------------------------------------------------------------------------------------------------ folder
if os.path.exists(OUT): shutil.rmtree(OUT)                     # only this track's folder
os.makedirs(OUT)
def cp(src, dst):
    os.makedirs(os.path.dirname(f'{OUT}/{dst}'), exist_ok=True); shutil.copy(src, f'{OUT}/{dst}')
for d in ('tiles', 'roost', 'treads', 'sky'):
    for f in sorted(os.listdir(f'{SX1}/{d}')): cp(f'{SX1}/{d}/{f}', f'{d}/{f}')
for f in ('track', 'track_tnorm', 'single', 'table', 'tripleface', 'triplemiddle', 'whoops', '90', '180', 'Tearoff', 'Tearoff_tnorm', 'Tearoff_tspec'):
    cp(f'{SX1}/decal/{f}.png', f'decal/{f}.png')
for f in ('start_gate.jm', 'start_gate.png', 'start_gate_spec.png', 'start_grate.jm', 'start_grate.png', 'start_gantry.jm', 'start_gantry.png', 'finish_arch.png'):
    cp(f'{ROOT}/assets/props/{f}', f'statue/{f}')
for f in ('2.jm', '2.png', 'cone.shp'): cp(f'{SX1}/statue/{f}', f'statue/{f}')

hmin, hmax = float(H.min()) - 0.5, float(H.max()) + 0.5
raw = np.round((H - hmin) / (hmax - hmin) * 65535).astype(np.uint16)
open(f'{OUT}/terrain.hf', 'w', newline='\n').write(f'{LU.N_EXP} {S:.6f} {hmin:.6f} {hmax:.6f}\n')
Image.fromarray(raw).save(f'{OUT}/terrain.png'); tiles.tofile(f'{OUT}/tilemap')
open(f'{OUT}/tileinfo', 'w', newline='\n').write(open(f'{SX1}/tileinfo').read().replace('@USLAND2026SX1/', P + '/'))
open(f'{OUT}/lighting', 'w', newline='\n').write(open(f'{SX1}/lighting').read().replace('@USLAND2026SX1/', P + '/'))
open(f'{OUT}/desc', 'w', newline='\n').write(LU.DESC + '\n')
lam, _ = lambert_shadow(H, S, [-0.6528, 0.3590, 0.6671], shadow=False)
sh = np.clip(89.3 + 245.8 * lam, 0, 255).astype(np.uint8)        # calibrated on JGSX Detroit (shading.py, doc 01)
for nm, img in (('shading.ppm', sh), ('shadingx2.ppm', (sh // 2).astype(np.uint8))):
    with open(f'{OUT}/{nm}', 'wb') as fh: fh.write(f'P6\n{N} {N}\n255\n'.encode()); fh.write(np.repeat(img[:, :, None], 3, axis=2).tobytes())

# ------------------------------------------------------------------------------------------------ timing gates (timing.py)
LS.COMBOS.update(LU.COMBOS)                                    # finish_s looks the finish unit up in LS.COMBOS
LS.N_GATES, LS.GATE_PITCH = LU.N_GATES, LU.GATE_PITCH
tg, cps, first, normal, sM, sF = timing.gates(path, LU.START)
lines = []; sec = None
for l in tg.split('\n'):
    if l.endswith(':'): sec = l
    elif sec == 'startinggate:' and l.startswith('['):     # USLAND gate model on every gate (the game raises / drops it)
        l = ' '.join(l.split()[:4]) + f' {P}/statue/start_gate.jm {P}/statue/start_gate.png @startgate.shp'
    lines.append(l)
open(f'{OUT}/timing_gates', 'w', newline='\n').write('\n'.join(lines))
gates = [tuple(map(float, re.findall(r'-?\d+\.\d+', l)[:4])) for l in lines if l.startswith('[') and 'start_gate' in l]   # x y z a

# ------------------------------------------------------------------------------------------------ riding surfaces
lap = path.samples(1.0); LAP = cKDTree(np.c_[lap['x'], lap['z']])
cx_, cz_, cs_, cb_ = R.area_points(2.0, 2.0); CORR = cKDTree(np.c_[cx_, cz_])
def h_at(x, z): return H[np.clip((np.asarray(z) / S).astype(int), 0, N - 1), np.clip((np.asarray(x) / S).astype(int), 0, N - 1)]
def ride_dist(q): q = np.atleast_2d(q); return np.minimum(LAP.query(q)[0], CORR.query(q)[0])

# ------------------------------------------------------------------------------------------------ statues
def line(x, y, z, a, model, tex, shape='null'):
    a = float((a + np.pi) % (2 * np.pi) - np.pi)
    return f'[{x:.6f} {y:.6f} {z:.6f}] {a:.6f} {P}/statue/{model}.jm {P}/statue/{tex}.png {shape}'
stat = []; rep = dict(objects={})
# RF Anaheim stadium: files from the .saf, statue lines as in RF Anaheim 1 (same world positions: same 593.4 ft floor)
saf = f'{rf_units.RF_DIR}/sx2026r01anaheim1.medium.saf'; ix = rf_units.saf_index(saf); pre = 'sx2026r01anaheim1/stadiums/Anaheim/'
for rel in ix:
    if rel.startswith(pre):
        dst = f'{OUT}/stadiums/anaheim/{rel[len(pre):]}'; os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, 'wb').write(rf_units.saf_read(saf, rel, ix))
st_rf = rf_units.saf_read(saf, 'sx2026r01anaheim1/statues', ix).decode('utf-8', 'replace').replace('\r', '').split('\n')
stadium = [re.sub('@sx2026r01anaheim1/stadiums/anaheim/', f'{P}/stadiums/anaheim/', l, flags=re.I) for l in st_rf if 'stadiums/' in l.lower()]
stat += stadium; rep['objects']['stadium RF Anaheim'] = len(stadium)
# USLAND start: grate behind every gate (same yaw), gantry over the gate row
grate_len = PU.GRATE['gap'] + sum(L for _, L in PU.GRATE['parts'])
for x, y, z, a in gates:
    f = np.array([-np.sin(a), -np.cos(a)]); q = np.array([[x, z]]) - np.outer(np.linspace(PU.GRATE['gap'], grate_len, 9), f)
    stat.append(line(x, float(h_at(q[:, 0], q[:, 1]).max()), z, statue_ang(*f), 'start_grate', 'start_grate'))
gx, gz = np.mean([g[0] for g in gates]), np.mean([g[2] for g in gates]); ga = gates[0][3]
stat.append(line(gx, float(h_at(gx, gz)), gz, statue_ang(-np.sin(ga), -np.cos(ga)), 'start_gantry', 'start_gantry'))
# USLAND FINISH arch (props_place.centred_arch logic): origin in the middle of lane F on the finish line, model lowered by the
# crest height there (the game sets a statue on the ground under its origin), pillars on the flat ground beside the jump
fin = cps[normal[-1]]; fc = np.array([fin[1], fin[2]]); ff = np.array([fin[3], fin[4]]); ff /= np.linalg.norm(ff); fn = np.array([-ff[1], ff[0]])
plates = [h_at(*(fc + fn * sg * PU.ARCH_X + fn * u + ff * v)) for sg in (-1, 1) for u in np.linspace(-1.5, 1.5, 4) for v in np.linspace(-1.5, 1.5, 4)]
arch_y = float(min(plates)); drop = float(h_at(*fc)) - arch_y
Lm = open(f'{ROOT}/assets/props/finish_arch.jm').read().split('\n'); nv = int(Lm[2].split()[0]); am = Lm[:3]
for l in Lm[3:3 + nv]:
    v = l.split(); am.append(' '.join([f'{float(v[0]) - PU.ARCH_X:.6f}', f'{float(v[1]) - drop:.6f}'] + v[2:]))
open(f'{OUT}/statue/finish_arch_URT.jm', 'w', newline='\n').write('\n'.join(am + Lm[3 + nv:]))
stat.append(line(fc[0], 0.0, fc[1], statue_ang(*ff), 'finish_arch_URT', 'finish_arch'))
pillars = [fc + fn * sg * PU.ARCH_X for sg in (-1, 1)]
rep['arch'] = dict(centre=fc.round(2).tolist(), crest_ft=round(float(h_at(*fc)), 2), drop=round(drop, 2), plate_slope=round(float(np.ptp(plates)), 3),
                   pillar_ride_dist=round(float(min(ride_dist(p_)[0] for p_ in pillars)), 1), beam_clearance=round(arch_y + PU.ARCH_CLEAR - float(h_at(*fc)), 1))
# one cone per turn (dress_sx.turn_cones rule: 22 ft inside the riding line at mid-turn, turns >= 45 deg)
cones = []
for g in path.segs:
    if g['kind'] == 'T' and abs(g['ang']) >= 45:
        m = turn_mid_angle(g); c = np.array([g['cx'], g['cz']]) + np.array([np.cos(m), np.sin(m)]) * (g['r'] - 22.0)
        cones.append(c); stat.append(f'[{c[0]:.6f} 0.000000 {c[1]:.6f}] 0.000000 {P}/statue/2.jm {P}/statue/2.png {P}/statue/cone.shp')
rep['objects'].update(start_grate=len(gates), start_gantry=1, finish_arch=1, cones=len(cones))
open(f'{OUT}/statues', 'w', newline='\n').write('\n'.join(stat) + '\n')

# ------------------------------------------------------------------------------------------------ decals
def decal(x, z, a, size, tex): return f'[{x:.6f} {z:.6f}] {a:.6f} {size:.6f} 1.000000 {P}/decal/{tex}.png'
def ang_of(fx, fz): return float(np.arctan2(-fx, -fz))
dec = []
# riding surface: track.png every 3.9 ft x 5.2 ft (Detroit density); the bowl is wider (open first turn)
for x, z, th, sg in zip(*(path.samples(3.9)[k] for k in ('x', 'z', 'th', 'seg'))):
    nx, nz = -np.sin(th), np.cos(th); wide = path.segs[int(sg)]['kind'] == 'T' and path.segs[int(sg)]['berm'] is None
    for v in ((-20.8, -15.6, -10.4, -5.2, 0.0, 5.2, 10.4, 15.6, 20.8) if wide else (-10.4, -5.2, 0.0, 5.2, 10.4)):
        j = rng.normal(0, 0.8, 2); dec.append(decal(x + nx * v + j[0], z + nz * v + j[1], rng.uniform(-np.pi, np.pi), 26.0, 'track'))
for x, z in zip(*R.area_points(4.5, 5.5, margin=2.0)[:2]):
    dec.append(decal(x + rng.normal(0, 0.6), z + rng.normal(0, 0.6), rng.uniform(-np.pi, np.pi), 26.0, 'track'))
n_surface = len(dec)
# bare floor inside the stadium walls: same dirt, jittered 11 ft grid, off the riding surfaces
fx0, fx1, fz0, fz1 = LU.STADIUM_FLOOR
for z in np.arange(fz0 + 5.5, fz1, 11.0):
    for x in np.arange(fx0 + 5.5, fx1, 11.0):
        xj, zj = x + rng.uniform(-2.5, 2.5), z + rng.uniform(-2.5, 2.5)
        if ride_dist([xj, zj])[0] > 24.0: dec.append(decal(xj, zj, rng.uniform(-np.pi, np.pi), 26.0, 'track'))
n_floor = len(dec) - n_surface
# obstacle and turn marks (dress_sx.obstacle_decals / turn_decals rules)
for g in path.segs:
    if g['kind'] != 'S': continue
    c, s_ = np.cos(g['t']), np.sin(g['t']); a = ang_of(c, s_)
    for prof, u0, name in g['sections']:
        for (nm, st, en, hh), src in zip(LU.COMBOS[name]['items'], LU.COMBOS[name]['sources']):
            if nm.startswith('whoops'):
                pk, _ = find_peaks(prof[int(st / 0.1):int(en / 0.1)], prominence=0.8, distance=60)
                for k in pk:
                    uu = u0 + st + k * 0.1; dec.append(decal(g['x0'] + uu * c, g['z0'] + uu * s_, a, 110.0, 'whoops'))
                continue
            kind = LU.kind_of(('rf', nm) if src == 'RF' else nm); L = en - st
            uu = u0 + (st + en) / 2; x, z = g['x0'] + uu * c, g['z0'] + uu * s_
            if hh >= 6.6 or kind == 'X': tex, cl = 'tripleface', 79.1
            elif L >= 52 or kind in ('T', 'combo'): tex, cl = 'table', 63.4
            else: tex, cl = 'single', 47.5
            dec.append(decal(x, z, a, max(110.0, 110.0 * (L + 14) / cl), tex))
            if tex == 'tripleface' and L > 70: dec.append(decal(x, z, a, 110.0, 'triplemiddle'))
for g in path.segs:
    if g['kind'] == 'T' and g.get('berm'):
        m = turn_mid_angle(g); fx_, fz_ = np.cos(m), np.sin(m)
        if abs(g['ang']) > 120: dec.append(decal(g['cx'] + fx_ * 9, g['cz'] + fz_ * 9, ang_of(fx_, fz_), 110.0, '180'))
        else: dec.append(decal(g['cx'] + fx_ * 14, g['cz'] + fz_ * 14, ang_of(fx_, fz_), 110.0, '90'))
smp = path.samples(3.9)
for i in rng.choice(len(smp['x']), 50, replace=False):
    dec.append(decal(smp['x'][i] + rng.normal(0, 5), smp['z'][i] + rng.normal(0, 5), rng.uniform(-np.pi, np.pi), 4.84, 'Tearoff'))
# USLAND chalk (pyro_chalk v13b): both edges of the start corridor + holeshot line across the lap 15 ft after the merge (bowl exit)
rs = R.samples(1.0); nx, nz = -np.sin(rs['th']), np.cos(rs['th']); edges = []
for sg in (-1, 1):
    e = np.c_[rs['x'] + sg * nx * rs['w'] / 2, rs['z'] + sg * nz * rs['w'] / 2]
    stp = np.r_[np.linalg.norm(np.diff(e, axis=0), axis=1), 1.0]; tight = np.convolve(stp < 0.35, np.ones(4), 'same') >= 4
    if tight.any(): e = e[:int(np.argmax(tight))]
    edges.append(e)
i = int(np.argmin(np.abs(lap['s'] - (sM + 15.0) % path.s))); hc = np.array([lap['x'][i], lap['z'][i]]); hn = np.array([-np.sin(lap['th'][i]), np.cos(lap['th'][i])])
hole = np.array([hc - hn * 15.2, hc + hn * 15.2])
lines_ = edges + [hole]; pts = np.vstack(lines_); lo, hi = pts.min(0) - 10, pts.max(0) + 10; size = float(max(hi - lo)); ccx, ccz = (lo + hi) / 2
NC, k2 = 2048, 2; img = Image.new('L', (NC * k2, NC * k2), 0); dr = ImageDraw.Draw(img)
px = lambda e: [((x - (ccx - size / 2)) / size * NC * k2, (z - (ccz - size / 2)) / size * NC * k2) for x, z in e]
for e in lines_: dr.line(px(e), fill=255, width=max(2, int(round(PC.CHALK_W / size * NC * k2))), joint='curve')
al = np.array(img.resize((NC, NC), Image.LANCZOS)).astype(float) * np.clip(0.75 + 0.25 * np.random.default_rng(7).random((NC, NC)), 0, 1)
Image.fromarray(np.dstack([np.full((NC, NC), PC.CHALK_RGB, np.uint8)] * 3 + [al.clip(0, 255).astype(np.uint8)]), 'RGBA').save(f'{OUT}/decal/chalk_URT.png')
dec.append(f'[{ccx:.6f} {ccz:.6f}] 0.000000 {size:.6f} 1.000000 {P}/decal/chalk_URT.png')       # last = drawn on top
open(f'{OUT}/decals', 'w', newline='\n').write('\n'.join(dec) + '\n')
rep['decals'] = dict(total=len(dec), riding=n_surface, floor=n_floor, holeshot=hc.round(1).tolist())

# ------------------------------------------------------------------------------------------------ finish flames (v13b) + frills.js
for nm in PC.PYRO:
    os.makedirs(f'{OUT}/js/pyro/{nm}', exist_ok=True)
    for f in os.listdir(f'{PC.SRC}/pyro/{nm}'):
        if f.endswith('.png'): shutil.copy(f'{PC.SRC}/pyro/{nm}/{f}', f'{OUT}/js/pyro/{nm}/{f}')
    open(f'{OUT}/js/pyro/{nm}.seq', 'w', newline='\n').write(open(f'{PC.SRC}/pyro/{nm}.seq').read().replace('@sx2026/js/', f'{P}/js/'))
os.makedirs(f'{OUT}/js/sounds', exist_ok=True)
for nm in PC.SOUNDS: shutil.copy(f'{PC.SRC}/sounds/{nm}.raw', f'{OUT}/js/sounds/{nm}.raw')
top = PC.arch_top(); fy = arch_y + top
open(f'{OUT}/billboards', 'w', newline='\n').write('\n'.join(f'[{p_[0]:.6f} {fy:.6f} {p_[1]:.6f}] {PC.FLAME_SIZE:.6f} 1.000000 {P}/js/pyro/{seq}.seq'
                                                          for p_, seq in zip(pillars, ('finishflames2', 'finishflames'))) + '\n')
open(f'{OUT}/frills.js', 'w', encoding='ascii', newline='\n').write(PC.JS % dict(P=P, nf=min(PC.frames(s) for s in PC.PYRO), fx=fc[0], fy=fy, fz=fc[1]))

# ------------------------------------------------------------------------------------------------ flaggers (dress_sx.flaggers format)
f0 = np.array([np.cos(np.radians(LU.START['heading'])), np.sin(np.radians(LU.START['heading']))]); n0 = np.array([-f0[1], f0[0]])
g0 = np.array(LU.GATE); half = (LU.N_GATES - 1) / 2 * LU.GATE_PITCH
b1 = g0 - f0 * 25 + n0 * (half - 15); b2 = g0 - f0 * 25 - n0 * (half - 15)
best = None
for sg in (1, -1):
    for along in (6.0, -6.0, 8.0, -8.0, 0.0):
        for o in np.arange(18.0, 36.0, 0.25):
            q = fc + fn * sg * o + ff * along; d = float(ride_dist(q)[0]); dp = min(np.linalg.norm(q - p_) for p_ in pillars)
            if d >= 20 and dp >= 4 and (best is None or d > best[0] + 1e-6): best = (d, q)
fl = best[1]
open(f'{OUT}/flaggers', 'w', newline='\n').write('\n'.join([f'[{b1[0]:.6f} 0.000 {b1[1]:.6f}]', f'[{b2[0]:.6f} 0.000 {b2[1]:.6f}]', '8.4 1', '9',
    '@30sec_30.png', '@30sec_turn.seq', '@30sec_5.png', '@30sec_run.seq', '@30sec_done.png', '',
    f'[{fl[0]:.6f} 0.000 {fl[1]:.6f}]', '8 -1', '@finish_green.png', '@finish_crossed.png', '@finish_white.png', '@checkerwave.seq', '', '', '',
    '[0.00000000 0.000 0.00000000]', '9.6 1', '3 4 5 -1', '@flagger_resting.png', '@flagger_waving.seq', '']))
rep['flaggers'] = dict(board_30s=[b1.round(1).tolist(), b2.round(1).tolist()], finish=fl.round(1).tolist(), finish_ride_dist=round(best[0], 1))

# ------------------------------------------------------------------------------------------------ minimap (whole terrain, track only)
M = 1024; Hs = ndi.zoom(H, M / N, order=1)[:M, :M]
gzz, gxx = np.gradient(Hs, SIZE / M); light = np.clip(0.75 + 0.9 * (-gxx * 0.6 - gzz * 0.6), 0.35, 1.25)
base = np.array([0.78, 0.62, 0.45]); col = base[None, None] * light[..., None] * np.where((Hs > 0.15)[..., None], 0.85, 1.0)
jj, ii = np.meshgrid((np.arange(M) + 0.5) * SIZE / M, (np.arange(M) + 0.5) * SIZE / M)
mask = (ride_dist(np.c_[jj.ravel(), ii.ravel()]).reshape(M, M) < 22.0) | (Hs > 0.15)
a = ndi.gaussian_filter(ndi.binary_dilation(mask, iterations=2).astype(float), 1.5)
Image.fromarray((np.clip(np.dstack([col, a]), 0, 1) * 255).astype(np.uint8), 'RGBA').save(f'{OUT}/map.png')

# ------------------------------------------------------------------------------------------------ report
np.save(f'{BUILD}/usland_rt_H.npy', H.astype(np.float32)); np.save(f'{BUILD}/usland_rt_tiles.npy', tiles)
rep.update(folder=LU.FOLDER, desc=LU.DESC, lap_ft=path.s, start_ft=R.L, merge=list(LU.START['merge']), heights=[hmin, hmax], hmax=float(H.max()),
           gates=dict(n=len(cps), first=first, normal=normal, s_merge=sM, s_finish=sF),
           tiles={n_: int((tiles == i_).sum()) for i_, n_ in enumerate(['Main', 'Jumps Sx', 'WhoopsV2', 'Berm Exit Sx'])},
           sections={n_: dict(length=c['length'], items=[dict(id=it[0], start=round(it[1], 1), end=round(it[2], 1), H=round(it[3], 2), src=s_)
                                                          for it, s_ in zip(c['items'], c['sources'])]) for n_, c in LU.COMBOS.items()})
json.dump(rep, open(f'{BUILD}/usland_rt_build.json', 'w'), indent=1, default=float)
nfiles = sum(len(fs) for _, _, fs in os.walk(OUT)); mb = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(OUT) for f in fs) / 1e6
print(f'{LU.FOLDER}: {nfiles} files, {mb:.0f} MB | lap {path.s:.0f} ft | H max {H.max():.2f} ft | gates {len(cps)} | statues {len(stat)} | decals {len(dec)}')
print('arch', rep['arch'], '| flagger', rep['flaggers']['finish'])
