"""Saint-Thibéry -> game folder tracks/USLAND2026StThibery (first playable version of the v4 track map).
Own terrain / tilemap / shading / timing gates / statues / decals / flaggers / minimap; textures and models are the shared
USLAND ones (@USLAND2026SX1/..., installed with the USLAND pack), like SX2 and SX3. No fence, no paddock, no flames, no start gantry / finish arch (v13: removed, new ones to come).
Works without the reference archives. Run: python3 scripts/export_stt.py"""
import os, sys, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
import numpy as np
from PIL import Image
from matplotlib.colors import LightSource
import matplotlib.cm as cm
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from shading import lambert_shadow
import layouts_sx as LS, layouts_stt as LT, build_stt as B, props_usland as PU, props_place as PP
from timing import gates
from starts import StartRoute
from engine import turn_mid_angle

FOLDER, DESC = 'USLAND2026StThibery', 'USLAND: Saint-Thibery'
SH = '@USLAND2026SX1'; P = '@' + FOLDER
OUT = f'{ROOT}/tracks/{FOLDER}'; S = 0.28975
rng = np.random.default_rng(31)

def ang_of(fx, fz): return float(np.arctan2(-fx, -fz))                 # decal / gate convention
def statue(x, y, z, a, model, tex, shared=True):
    pre = SH if shared else P
    return f'[{x:.6f} {y:.6f} {z:.6f}] {a:.6f} {pre}/statue/{model}.jm {SH}/statue/{tex}.png null'
def decal(x, z, a, size, tex): return f'[{x:.6f} {z:.6f}] {a:.6f} {size:.6f} 1.000000 {SH}/decal/{tex}.png'
def h_at(H, x, z): return H[np.clip((np.asarray(z) / S).astype(int), 0, H.shape[0] - 1), np.clip((np.asarray(x) / S).astype(int), 0, H.shape[1] - 1)]

def terrain(H, tiles):
    N = H.shape[0]; hmin, hmax = float(H.min()) - 0.5, float(H.max()) + 0.5
    open(f'{OUT}/terrain.hf', 'w', newline='\n').write(f'11 {S:.6f} {hmin:.6f} {hmax:.6f}\n')
    Image.fromarray(np.round((H - hmin) / (hmax - hmin) * 65535).astype(np.uint16)).save(f'{OUT}/terrain.png')
    tiles.astype(np.uint8).tofile(f'{OUT}/tilemap')
    lam, _ = lambert_shadow(H, S, [-0.6528, 0.3590, 0.6671], shadow=False); sh = np.clip(89.3 + 245.8 * lam, 0, 255).astype(np.uint8)
    for nm, img in (('shading.ppm', sh), ('shadingx2.ppm', (sh // 2).astype(np.uint8))):
        with open(f'{OUT}/{nm}', 'wb') as fh: fh.write(f'P6\n{N} {N}\n255\n'.encode()); fh.write(np.repeat(img[:, :, None], 3, axis=2).tobytes())

def obstacle_and_turn_decals(p):
    out = []
    for g in p.segs:
        if g['kind'] == 'S':
            c, s_ = np.cos(g['t']), np.sin(g['t']); a = ang_of(c, s_)
            for prof, u0, name in g['sections']:
                for nm, st, en, hh in LS.COMBOS[name]['items']:
                    L = en - st
                    if nm.startswith('whoops'):
                        for k in range(12):
                            uu = u0 + st + (k + 0.5) * L / 12; out.append(decal(g['x0'] + uu * c, g['z0'] + uu * s_, a, 110.0, 'whoops'))
                        continue
                    uu = u0 + (st + en) / 2; tex, cl = ('tripleface', 79.1) if hh >= 6.6 else (('table', 63.4) if L >= 52 else ('single', 47.5))
                    out.append(decal(g['x0'] + uu * c, g['z0'] + uu * s_, a, max(110.0, 110.0 * (L + 14) / cl), tex))
        elif g['kind'] == 'T' and g.get('berm'):
            m = turn_mid_angle(g); fx, fz = np.cos(m), np.sin(m)
            if abs(g['ang']) > 120: out.append(decal(g['cx'] + fx * 9, g['cz'] + fz * 9, ang_of(fx, fz), 110.0, '180'))
            else: out.append(decal(g['cx'] + fx * 14, g['cz'] + fz * 14, ang_of(fx, fz), 110.0, '90'))
    return out

def surface_decals(p, R):
    out = []; smp = p.samples(3.9)
    for x, z, th in zip(smp['x'], smp['z'], smp['th']):
        nx, nz = -np.sin(th), np.cos(th)
        for v in (-10.4, -5.2, 0.0, 5.2, 10.4):
            j = rng.normal(0, 0.8, 2); out.append(decal(x + nx * v + j[0], z + nz * v + j[1], rng.uniform(-np.pi, np.pi), 26.0, 'track'))
    X_, Z_, _, _ = R.area_points(4.5, 5.5, margin=2.0)
    for x, z in zip(X_, Z_): out.append(decal(x + rng.normal(0, 0.6), z + rng.normal(0, 0.6), rng.uniform(-np.pi, np.pi), 26.0, 'track'))
    for i in rng.choice(len(smp['x']), 40, replace=False):
        out.append(decal(smp['x'][i] + rng.normal(0, 5), smp['z'][i] + rng.normal(0, 5), rng.uniform(-np.pi, np.pi), 4.84, 'Tearoff'))
    return out

def main():
    H, p, rep = B.build(); H = H.astype(np.float64); tiles = np.load(f'{ROOT}/build/stt_tiles.npy')
    os.makedirs(f'{OUT}/statue', exist_ok=True)
    terrain(H, tiles)
    A = f'{ROOT}/tracks/USLAND2026SX1'
    for f in ('tileinfo', 'lighting'): shutil.copy(f'{A}/{f}', f'{OUT}/{f}')
    open(f'{OUT}/desc', 'w', newline='\n').write(DESC + '\n'); open(f'{OUT}/billboards', 'w').close()
    # timing gates (JGSX method, timing.py) + our gate model on the starting gates
    txt, cps, first, normal, sM, sF = gates(p, LS.STARTS['STT'])
    tl, sec = [], None
    for l in txt.split('\n'):
        if l.endswith(':'): sec = l
        elif sec == 'startinggate:' and l.startswith('['):
            v = l.split(']')[0][1:].split()     # v14: y = 0 - the game puts the gate on the ground (the platform) itself; y 2.5 floated
            l = f'[{float(v[0]):.6f} 0.000000 {float(v[2]):.6f}] ' + l.split(']')[1].split()[0] + f' {SH}/statue/start_gate.jm {SH}/statue/start_gate.png @startgate.shp'
        tl.append(l)
    open(f'{OUT}/timing_gates', 'w', newline='\n').write('\n'.join(tl))
    # statues: grates behind the gates (v13: no start gantry, no finish arch - new ones to come)
    st = []; gl = [l for l in tl if l.startswith('[') and '@startgate.shp' in l]
    G = [[float(v) for v in l.split(']')[0][1:].split()] + [float(l.split(']')[1].split()[0])] for l in gl]
    for x, y, z, a in G:
        f = np.array([-np.sin(a), -np.cos(a)]); q = np.array([[x, z]]) - np.outer(np.linspace(PU.GRATE['gap'], PU.GRATE['gap'] + 7, 8), f)
        st.append(statue(x, 0.0, z, PP.statue_ang(*f), 'start_grate', 'start_grate'))      # v14: y 0, the game puts it on the platform
    gx = float(np.mean([g[0] for g in G])); gz = float(np.mean([g[2] for g in G])); fa = G[0][3]
    fin = cps[normal[-1]]; c = np.array([fin[1], fin[2]]); f = np.array([fin[3], fin[4]]); f /= np.linalg.norm(f); n = np.array([-f[1], f[0]])
    if os.path.exists(f'{OUT}/statue/finish_arch_STT.jm'): os.remove(f'{OUT}/statue/finish_arch_STT.jm')
    # v14: steel skin + frame of the freestyle ramp (props_usland fmx_ramp, origin = foot centre, +z = riding direction);
    # the ramp itself is terrain (build_stt.extras), the model sits on it
    R_ = getattr(LT, 'FMX_RAMP', None)
    if R_ and os.path.exists(f'{ROOT}/assets/props/fmx_ramp.jm'):
        for e in ('jm', 'png'): shutil.copy(f'{ROOT}/assets/props/fmx_ramp.{e}', f'{OUT}/statue/fmx_ramp.{e}')
        import compose
        k = compose.lane([('cut', 'Detroit_g31_1', R_['H'], 0.9)])[0]; il = int(np.argmax(k)) * 0.1
        d_ = np.array([R_['aim'][0] - R_['lip'][0], R_['aim'][1] - R_['lip'][1]]); d_ /= np.linalg.norm(d_)
        fx_, fz_ = R_['lip'][0] + LT.STT_ORIGIN[0] - d_[0] * il, R_['lip'][1] + LT.STT_ORIGIN[1] - d_[1] * il
        st.append(f'[{fx_:.6f} 0.000000 {fz_:.6f}] {PP.statue_ang(*d_):.6f} {P}/statue/fmx_ramp.jm {P}/statue/fmx_ramp.png null')
    open(f'{OUT}/statues', 'w', newline='\n').write('\n'.join(st) + '\n')
    # decals (ground texture over the riding surface, obstacle and turn decals)
    R = StartRoute(LS.STARTS['STT'], LS.N_GATES, LS.GATE_PITCH)
    dec = surface_decals(p, R) + obstacle_and_turn_decals(p)
    open(f'{OUT}/decals', 'w', newline='\n').write('\n'.join(dec) + '\n')
    # flaggers: 30 s board behind the gate row, finish flagger beside the finish line on flat ground away from the lanes
    smp = p.samples(1.0); tr = cKDTree(np.c_[smp['x'], smp['z']])
    fr = np.array([-np.sin(fa), -np.cos(fa)]); nr = np.array([-fr[1], fr[0]]); half = (LS.N_GATES - 1) / 2 * LS.GATE_PITCH
    b1 = np.array([gx, gz]) - fr * 25 + nr * (half - 15); b2 = np.array([gx, gz]) - fr * 25 - nr * (half - 15)
    cands = [c + n * sg * o_ + f * a_ for sg in (1, -1) for o_ in (24.0, 28.0, 32.0) for a_ in (6.0, -6.0)]
    fl = max(cands, key=lambda q: tr.query(q)[0] - 50 * float(h_at(H, *q) > 0.1))
    open(f'{OUT}/flaggers', 'w', newline='\n').write('\n'.join([f'[{b1[0]:.6f} 0.000 {b1[1]:.6f}]', f'[{b2[0]:.6f} 0.000 {b2[1]:.6f}]', '8.4 1', '9',
        '@30sec_30.png', '@30sec_turn.seq', '@30sec_5.png', '@30sec_run.seq', '@30sec_done.png', '',
        f'[{fl[0]:.6f} 0.000 {fl[1]:.6f}]', '8 -1', '@finish_green.png', '@finish_crossed.png', '@finish_white.png',
        '@checkerwave.seq', '', '', '', '[0.00000000 0.000 0.00000000]', '9.6 1', '3 4 5 -1', '@flagger_resting.png', '@flagger_waving.seq', '']))
    # minimap over the whole terrain (the game stretches map.png over it), this track only
    M = 1024; N = H.shape[0]; side = (N - 1) * S; g1 = (np.arange(M) + 0.5) * side / M
    Hc = H[np.ix_((g1 / S).astype(int), (g1 / S).astype(int))]
    shade = LightSource(300, 40).hillshade(Hc, vert_exag=3 / (side / M)); col = cm.terrain(np.clip(Hc / 12.0, 0, 1))[:, :, :3]
    base = np.dstack([shade] * 3) * 0.75 + 0.25
    rgb = np.where((Hc > 0.15)[:, :, None], base * (0.65 + 0.35 * col), base * np.array([0.78, 0.62, 0.45]))
    gxx, gzz = np.meshgrid(g1, g1); d, _ = tr.query(np.c_[gxx.ravel(), gzz.ravel()]); m = (d.reshape(M, M) < 24)
    a = ndi.gaussian_filter(m.astype(float), 1.5)
    Image.fromarray((np.clip(np.dstack([rgb, a]), 0, 1) * 255).astype(np.uint8), 'RGBA').save(f'{OUT}/map.png')
    return dict(lap=p.s, gates=len(G), checkpoints=len(cps), first=len(first), normal=len(normal), statues=len(st), decals=len(dec),
                gate_y=round(float(np.mean([g[1] for g in G])), 2), grate_y=round(float(np.mean([float(l.split()[1]) for l in st])), 2),
                flagger=[round(v, 1) for v in fl], flagger_dist=round(float(tr.query(fl)[0]), 1))

if __name__ == '__main__':
    print(main())
