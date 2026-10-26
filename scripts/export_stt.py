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

def grass_tile(path, n=256):
    """v21: more realistic tileable grass (256 x 256 PPM): mottled greens at several scales, thousands of short blades drawn with
    wrap-around (seamless), a few dry yellowish blades and darker clumps."""
    from PIL import ImageDraw
    r = np.random.default_rng(7); F = np.fft.fftfreq(n)[:, None] ** 2 + np.fft.fftfreq(n)[None, :] ** 2
    def noise(scale):
        w = np.fft.ifft2(np.fft.fft2(r.normal(size=(n, n))) * np.exp(-F * scale)).real; return (w - w.mean()) / w.std()
    big, mid = noise(4000.0), noise(600.0)
    base = np.array([58, 92, 38], float)
    img = base[None, None, :] * (1 + 0.10 * big[:, :, None] + 0.07 * mid[:, :, None])
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    greens = [(46, 78, 30), (64, 102, 40), (78, 118, 48), (90, 128, 56), (54, 88, 34)]
    dry = [(122, 124, 70), (138, 132, 82)]
    for k in range(9000):
        x, y = r.uniform(0, n), r.uniform(0, n); L = r.uniform(3, 9); a = r.normal(-np.pi / 2, 0.45)
        c = dry[r.integers(len(dry))] if r.random() < 0.06 else greens[r.integers(len(greens))]
        c = tuple(int(np.clip(v * r.uniform(0.85, 1.15), 0, 255)) for v in c)
        for ox_ in (-n, 0, n):
            for oy_ in (-n, 0, n):
                x0, y0 = x + ox_, y + oy_
                if -10 < x0 < n + 10 and -10 < y0 < n + 10:
                    d.line([(x0, y0), (x0 + L * np.cos(a), y0 + L * np.sin(a))], fill=c, width=1)
    a_ = np.asarray(im, float) * (1 - 0.12 * np.clip(noise(150.0), 0, None))[:, :, None]   # darker clumps
    ref = f"{ROOT}/assets/grass_jgsx/{LT.GRASS_TUFTS['tex']}.png" if getattr(LT, 'GRASS_TUFTS', None) else f'{ROOT}/assets/grass_dvdb/grass_dvdb.png'
    if (getattr(LT, 'GRASS_DECALS', None) or getattr(LT, 'GRASS_TUFTS', None)) and os.path.exists(ref):   # v25: ground tile matches the tufts    # v23: same mean colour as the grass decals (gaps don't show)
        q = np.asarray(Image.open(ref).convert('RGBA'), float); m_ = q[:, :, 3] > 200; tgt = q[:, :, :3][m_].mean(0)
        a_ = a_ * (tgt / a_.reshape(-1, 3).mean(0))[None, None, :]
    a_ = np.clip(a_, 0, 255).astype(np.uint8)
    with open(path, 'wb') as fh: fh.write(f'P6\n{n} {n}\n255\n'.encode()); fh.write(a_.tobytes())

def main():
    H, p, rep = B.build(); H = H.astype(np.float64); tiles = np.load(f'{ROOT}/build/stt_tiles.npy')
    GR = getattr(LT, 'GRASS_OUTSIDE', None)
    if GR:                                       # v18/v24: grass tile outside, dirt inside and (v24) up to the fence
        from scipy.ndimage import distance_transform_edt
        TN = tiles.shape[0]; g = (np.arange(TN) * 2 + 0.5) * S; GX, GZ = np.meshgrid(g - LT.STT_ORIGIN[0], g - LT.STT_ORIGIN[1])
        DF = np.load(f'{ROOT}/build/stt_dist.npy')                      # v25: same rounded distance field as the bank
        ii = np.clip(((GZ + LT.STT_ORIGIN[1])).astype(int), 0, DF.shape[0] - 1); jj = np.clip(((GX + LT.STT_ORIGIN[0])).astype(int), 0, DF.shape[1] - 1)
        dirt = DF[ii, jj] <= (LT.FENCE['off'] if GR.get('dirt_to_fence') and getattr(LT, 'FENCE', None) else 0.0)
        gi = sum(1 for l in open(f'{ROOT}/tracks/USLAND2026SX1/tileinfo') if l.strip() == 'addtile')   # grass = next block index
        tiles = np.where(dirt, tiles, gi).astype(np.uint8)
    os.makedirs(f'{OUT}/statue', exist_ok=True)
    terrain(H, tiles)
    A = f'{ROOT}/tracks/USLAND2026SX1'
    for f in ('tileinfo', 'lighting'): shutil.copy(f'{A}/{f}', f'{OUT}/{f}')
    if GR:                                       # v18: grass tile appended to the SX1 tileinfo (5th block), own texture
        os.makedirs(f'{OUT}/tiles', exist_ok=True); grass_tile(f'{OUT}/tiles/grass.ppm')
        ti = open(f'{OUT}/tileinfo').read(); blk = ti.split('addtile')[0]
        blk = blk.replace('name Main', 'name Grass').replace('@USLAND2026SX1/tiles/dirt.ppm', f'{P}/tiles/grass.ppm')
        blk = blk.replace('r=123 g=73 b=52', 'r=72 g=104 b=46')
        open(f'{OUT}/tileinfo', 'w', newline='\n').write(ti.rstrip('\n') + '\n\n' + blk.strip('\n') + '\naddtile\n\n')
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
    # v18: the user's steel FMX ramp (fmxRamp.rar: ramp_50.jm / .png / _norm.png / .shp collision). Model: foot at the origin,
    # rides towards local -z, lip (9 ft) at z = -model_len. Lip put where the dirt ramp lip was, facing the same way.
    R_ = getattr(LT, 'FMX_RAMP', None)
    if R_ and R_.get('model'):
        src = f"{ROOT}/assets/fmx_ramp_user"
        for e in ('.jm', '.png', '_norm.png', '.shp'): shutil.copy(f"{src}/{R_['model']}{e}", f"{OUT}/statue/{R_['model']}{e}")
        d_ = np.array([R_['aim'][0] - R_['lip'][0], R_['aim'][1] - R_['lip'][1]]); d_ /= np.linalg.norm(d_)
        fx_, fz_ = R_['lip'][0] + LT.STT_ORIGIN[0] - d_[0] * R_['model_len'], R_['lip'][1] + LT.STT_ORIGIN[1] - d_[1] * R_['model_len']
        m_ = R_['model']
        st.append(f'[{fx_:.6f} 0.000000 {fz_:.6f}] {PP.statue_ang(-d_[0], -d_[1]):.6f} {P}/statue/{m_}.jm {P}/statue/{m_}.png {P}/statue/{m_}.shp')
    # v20: wooden fence around the dirt area (arena box + start area), in the grass at the foot of the bank
    FE = getattr(LT, 'FENCE', None)
    if FE:
        for e in ('jm', 'png'): shutil.copy(f"{ROOT}/assets/props/{FE['model']}.{e}", f"{OUT}/statue/{FE['model']}.{e}")
        # v25: the fence follows the line d = off of the bank's distance field (flat terrace), closed, rounded everywhere
        from skimage.measure import find_contours
        DF = np.load(f'{ROOT}/build/stt_dist.npy'); o = FE['off']
        cs = max(find_contours(DF, o), key=len)                          # (row = world z, col = world x), 1 ft grid
        path = [np.array([c_[1] - LT.STT_ORIGIN[0], c_[0] - LT.STT_ORIGIN[1]]) for c_ in cs[::3]] + [np.array([cs[0][1] - LT.STT_ORIGIN[0], cs[0][0] - LT.STT_ORIGIN[1]])]
        seg = [(path[i], path[i + 1]) for i in range(len(path) - 1) if np.linalg.norm(path[i + 1] - path[i]) > 1e-6]
        L_ = np.cumsum([0] + [np.linalg.norm(b - a) for a, b in seg]); m_ = max(1, int(round(L_[-1] / FE['step']))); stp = L_[-1] / m_
        def at(sv):
            i = min(int(np.searchsorted(L_, sv, 'right')) - 1, len(seg) - 1); a, b = seg[i]
            return a + (b - a) * (sv - L_[i]) / max(np.linalg.norm(b - a), 1e-9)
        dfl = lambda q: float(DF[int(q[1] + LT.STT_ORIGIN[1]), int(q[0] + LT.STT_ORIGIN[0])])
        nf = 0
        for q in range(m_):
            pa, pb = at(q * stp), at((q + 1) * stp); c_ = (pa + pb) / 2 + np.array(LT.STT_ORIGIN); t_ = (pb - pa) / np.linalg.norm(pb - pa)
            inw = np.array([-t_[1], t_[0]])
            if dfl((pa + pb) / 2 + inw * 3) > dfl((pa + pb) / 2 - inw * 3): inw = -inw   # v25: inward = towards the track
            st.append(f"[{c_[0]:.6f} 0.000000 {c_[1]:.6f}] {PP.statue_ang(inw[0], inw[1]):.6f} {P}/statue/{FE['model']}.jm {P}/statue/{FE['model']}.png null"); nf += 1
        print('fence sections', nf)
    # v25: 3D grass tufts on the grass (outside the fence), random size mix and rotation
    GT = getattr(LT, 'GRASS_TUFTS', None)
    if GT and getattr(LT, 'FENCE', None):
        for gf_ in os.listdir(f'{ROOT}/assets/grass_jgsx'): shutil.copy(f'{ROOT}/assets/grass_jgsx/{gf_}', f'{OUT}/statue/{gf_}')
        DF = np.load(f'{ROOT}/build/stt_dist.npy'); side = DF.shape[0] - 1.0; rt = np.random.default_rng(25); o = LT.FENCE['off']; nt_ = 0
        names = [m for m, _ in GT['models']]; prob = np.array([w for _, w in GT['models']]); prob /= prob.sum()
        for zz in np.arange(GT['step'] / 2, side, GT['step']):
            for xx in np.arange(GT['step'] / 2, side, GT['step']):
                x_, z_ = xx + rt.uniform(-0.45, 0.45) * GT['step'], zz + rt.uniform(-0.45, 0.45) * GT['step']
                if not (8 < x_ < side - 8 and 8 < z_ < side - 8): continue
                dv = DF[int(z_), int(x_)]
                if not (o + GT['dmin'] <= dv <= o + GT['dmax']) or rt.random() > GT['p']: continue
                m_ = names[rt.choice(len(names), p=prob)]
                st.append(f"[{x_:.6f} 0.000000 {z_:.6f}] {rt.uniform(-np.pi, np.pi):.6f} {P}/statue/{m_}.jm {P}/statue/{GT['tex']}.png null"); nt_ += 1
        print('grass tufts', nt_)
    open(f'{OUT}/statues', 'w', newline='\n').write('\n'.join(st) + '\n')
    # decals (ground texture over the riding surface, obstacle and turn decals)
    R = StartRoute(LS.STARTS['STT'], LS.N_GATES, LS.GATE_PITCH)
    dec = surface_decals(p, R) + obstacle_and_turn_decals(p)
    # v25: track-coloured decals over the dirt up to the fence, put FIRST in the file so the track and obstacle decals are drawn
    # over them (v24 put them last and hid the bump textures); 26 / 13 / 6 ft patches so the edge follows the fence line
    DD = getattr(LT, 'DIRT_DECALS', None)
    if DD and getattr(LT, 'FENCE', None):
        DF = np.load(f'{ROOT}/build/stt_dist.npy'); side = DF.shape[0] - 1.0; rg2 = np.random.default_rng(24); dfirst = []; o = LT.FENCE['off']
        for size, step_, lo, hi in ((26.0, 10.0, -1e9, o - 14.0), (13.0, 5.0, o - 14.0, o - 7.0), (6.0, 2.5, o - 7.0, o - 3.2)):
            for zz in np.arange(step_ / 2, side, step_):
                for xx in np.arange(step_ / 2, side, step_):
                    x_, z_ = xx + rg2.uniform(-0.3, 0.3) * step_, zz + rg2.uniform(-0.3, 0.3) * step_
                    dv = DF[min(int(z_), DF.shape[0] - 1), min(int(x_), DF.shape[1] - 1)]
                    if lo < dv <= hi: dfirst.append(decal(x_, z_, rg2.uniform(-np.pi, np.pi), size, 'track'))
        dec = dfirst + dec; print('dirt decals', len(dfirst))
    # v23: grass decals (DVDBVisualsCompound grass.png, chosen by the user; 3rd-party file, local use only) laid like DVDB does:
    # 45 ft patches, random rotation, jittered grid every 26 ft (each spot covered ~3 times), on the grass only (>= 6 ft from dirt)
    GD = getattr(LT, 'GRASS_DECALS', None)
    if GD and getattr(LT, 'GRASS_OUTSIDE', None):
        os.makedirs(f'{OUT}/decal', exist_ok=True)
        for e in ('', '_tnorm'): shutil.copy(f"{ROOT}/assets/grass_dvdb/grass_dvdb{e}.png", f"{OUT}/decal/grass_dvdb{e}.png")
        from scipy.ndimage import distance_transform_edt
        DF = np.load(f'{ROOT}/build/stt_dist.npy'); side = DF.shape[0] - 1.0; rg = np.random.default_rng(23); ng = 0
        dd = DF[::2, ::2]                                                 # 2 ft grid as before
        for zz in np.arange(GD['step'] / 2, side, GD['step']):
            for xx in np.arange(GD['step'] / 2, side, GD['step']):
                x_, z_ = xx + rg.uniform(-0.4, 0.4) * GD['step'], zz + rg.uniform(-0.4, 0.4) * GD['step']
                i_, j_ = min(int(z_ / 2.0), dd.shape[0] - 1), min(int(x_ / 2.0), dd.shape[1] - 1)
                if dd[i_, j_] < GD['clear'] or not (0 < x_ < side and 0 < z_ < side): continue
                dec.append(f'[{x_:.6f} {z_:.6f}] {rg.uniform(-np.pi, np.pi):.6f} {GD["size"]:.6f} 1.000000 {P}/decal/grass_dvdb.png'); ng += 1
        print('grass decals', ng)
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
    gxx, gzz = np.meshgrid(g1, g1); d, _ = tr.query(np.c_[gxx.ravel(), gzz.ravel()]); m = (d.reshape(M, M) < 40)   # v24: thicker ribbon (bigger on the in-game map)
    a = ndi.gaussian_filter(m.astype(float), 1.5)
    Image.fromarray((np.clip(np.dstack([rgb, a]), 0, 1) * 255).astype(np.uint8), 'RGBA').save(f'{OUT}/map.png')
    return dict(lap=p.s, gates=len(G), checkpoints=len(cps), first=len(first), normal=len(normal), statues=len(st), decals=len(dec),
                gate_y=round(float(np.mean([g[1] for g in G])), 2), grate_y=round(float(np.mean([float(l.split()[1]) for l in st])), 2),
                flagger=[round(v, 1) for v in fl], flagger_dist=round(float(tr.query(fl)[0]), 1))

if __name__ == '__main__':
    print(main())
