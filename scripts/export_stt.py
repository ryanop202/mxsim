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
    TG_ = getattr(LT, 'TURN_GATES', None)
    if TG_ and getattr(LT, 'PYLONS', None) and LT.PYLONS.get('points'): TG_ = dict(TG_, pylons=LT.PYLONS['points'])
    txt, cps, first, normal, sM, sF = gates(p, LS.STARTS['STT'], turn_gates=TG_)
    tl, sec = [], None
    for l in txt.split('\n'):
        if l.endswith(':'): sec = l
        elif sec == 'startinggate:' and l.startswith('['):
            v = l.split(']')[0][1:].split()     # v14: y = 0 - the game puts the gate on the ground (the platform) itself; y 2.5 floated
            # v30 (user): hollow red gate (USLAND gate without its plate), own model; same collision shape
            l = f'[{float(v[0]):.6f} 0.000000 {float(v[2]):.6f}] ' + l.split(']')[1].split()[0] + f' {P}/statue/start_gate_frame.jm {P}/statue/start_gate_frame.png @startgate.shp'
        tl.append(l)
    open(f'{OUT}/timing_gates', 'w', newline='\n').write('\n'.join(tl))
    # statues: grates behind the gates (v13: no start gantry, no finish arch - new ones to come)
    st = []; gl = [l for l in tl if l.startswith('[') and '@startgate.shp' in l]
    G = [[float(v) for v in l.split(']')[0][1:].split()] + [float(l.split(']')[1].split()[0])] for l in gl]
    gx = float(np.mean([g[0] for g in G])); gz = float(np.mean([g[2] for g in G])); fa = G[0][3]
    if getattr(LT, 'START_FLOOR', None):          # v28: ONE big floor (square mesh) behind the whole row, cut at each gate
        import stt_props; stt_props.build()
        for nm in ('start_floor', 'stake_yellow', 'start_gate_frame', 'pylon_black', 'bale_straw', 'boudin_black'):
            for e in ('jm', 'png'): shutil.copy(f'{ROOT}/assets/props/{nm}.{e}', f'{OUT}/statue/{nm}.{e}')
        for nm in ('pylon_black', 'bale_straw', 'boudin_black'): shutil.copy(f'{ROOT}/assets/props/{nm}.shp', f'{OUT}/statue/{nm}.shp')
        f = np.array([-np.sin(fa), -np.cos(fa)])
        st.append(f'[{gx:.6f} 0.000000 {gz:.6f}] {PP.statue_ang(*f):.6f} {P}/statue/start_floor.jm {P}/statue/start_floor.png null')
    else:
        for x, y, z, a in G:
            f = np.array([-np.sin(a), -np.cos(a)])
            st.append(statue(x, 0.0, z, PP.statue_ang(*f), 'start_grate', 'start_grate'))      # v14: y 0, the game puts it on the platform
    PY_ = getattr(LT, 'PYLONS', None)
    if PY_:                                       # v32: black pylon inside every turn, same spot each time (turn bisector)
        smp_p = p.samples(1.0); npy_ = 0
        for g in p.segs:
            if g['kind'] != 'T': continue
            sel = (smp_p['s'] >= g['s0']) & (smp_p['s'] <= g['s0'] + g['L']); X_, Z_ = smp_p['x'][sel], smp_p['z'][sel]
            c_ = np.array([g['cx'], g['cz']]); m_ = np.array([X_[len(X_) // 2], Z_[len(Z_) // 2]]); u_ = (m_ - c_) / np.linalg.norm(m_ - c_)
            k_ = 1.0 if abs(g['ang']) > 135 else np.sqrt(2)          # U turn: apex of the inner half circle; 90 deg: corner of the inner edges
            x_, z_ = c_ + u_ * (g['r'] - PY_['half'] - PY_['margin']) * k_
            if PY_.get('points'): x_, z_ = PY_['points'][npy_]      # v33: the user's spots
            npy_ += 1
            j_ = int(np.argmin(np.hypot(smp_p['x'] - x_, smp_p['z'] - z_)))   # v35: logo side (+z) faces the riding line
            a_ = PP.statue_ang(smp_p['x'][j_] - x_, smp_p['z'][j_] - z_)
            st.append(f'[{x_:.6f} 0.000000 {z_:.6f}] {a_:.6f} {P}/statue/pylon_black.jm {P}/statue/pylon_black.png {P}/statue/pylon_black.shp')
    # v35: straw bales (user's white rectangles), long axis = model x; statue +x -> (cos a, -sin a)
    for bx_, bz_, ba_ in getattr(LT, 'BALES', []):
        t_ = np.radians(ba_); a_ = float(np.arctan2(-np.sin(t_), np.cos(t_)))
        st.append(f'[{bx_:.6f} 0.000000 {bz_:.6f}] {a_:.6f} {P}/statue/bale_straw.jm {P}/statue/bale_straw.png {P}/statue/bale_straw.shp')
    BD_ = getattr(LT, 'BOUDINS', None); nbd = 0
    if BD_:
        import stt_props as SP_
        segL = SP_.BOUDIN['L']
        def tube_row(p0, p1, off):
            rows_ = []
            d0 = np.array(p1, float) - np.array(p0, float); Ld = np.linalg.norm(d0); d0 /= Ld; nn = np.array([-d0[1], d0[0]])
            k_ = max(1, int(round(Ld / segL))); a_ = float(np.arctan2(-d0[1], d0[0]))
            for sgn in (1, -1):
                for q in range(k_):
                    c = np.array(p0, float) + d0 * (Ld / 2 - (k_ * segL) / 2 + (q + 0.5) * segL) + nn * sgn * off
                    rows_.append(f'[{c[0]:.6f} 0.000000 {c[1]:.6f}] {a_:.6f} {P}/statue/boudin_black.jm {P}/statue/boudin_black.png {P}/statue/boudin_black.shp')
            return rows_
        W_ = BD_.get('whoops')
        if W_:
            for g in p.segs:
                if g['kind'] != 'S' or not g.get('tag', '').startswith(W_['tag']): continue
                c_, s_ = np.cos(g['t']), np.sin(g['t'])
                for prof, u0, name in g['sections']:
                    for n_, a0, b0, h_ in LS.COMBOS[name]['items']:
                        if W_['item'] not in n_: continue
                        u_a = u0 + a0 - W_['before']; u_b = u0 + a0 + (b0 - a0) * W_['frac']
                        rows = tube_row((g['x0'] + u_a * c_, g['z0'] + u_a * s_), (g['x0'] + u_b * c_, g['z0'] + u_b * s_), W_['off'])
                        st.extend(rows); nbd += len(rows)
        F_ = BD_.get('fmx'); R2_ = getattr(LT, 'FMX_RAMP', None)
        if F_ and R2_:
            lip = np.array(R2_['lip']) + np.array(LT.STT_ORIGIN); d_ = np.array(R2_['aim']) - np.array(R2_['lip']); d_ = d_ / np.linalg.norm(d_)
            # landing start: first point after the lip where the ground rises 1 ft above the gap floor
            land = None
            for t_ in np.arange(8.0, 120.0, 0.5):
                q_ = lip + d_ * t_; hq = float(H[int(round(q_[1] / S)), int(round(q_[0] / S))])
                h0 = float(H[int(round((lip + d_ * 6.0)[1] / S)), int(round((lip + d_ * 6.0)[0] / S))])
                if hq > h0 + 1.0: land = t_; break
            if land:
                rows = tube_row(lip + d_ * F_['start'], lip + d_ * (land - F_['end']), F_['off']); st.extend(rows); nbd += len(rows)
                print('fmx gap', round(land, 1), 'ft')
        print('boudins', nbd)
    FS_ = getattr(LT, 'FMX_STAKES', None); R3_ = getattr(LT, 'FMX_RAMP', None)
    if FS_ and R3_:                                # v35: yellow stakes on both ends of the steel ramp lip (on top of it)
        lip = np.array(R3_['lip']) + np.array(LT.STT_ORIGIN); d_ = np.array(R3_['aim']) - np.array(R3_['lip']); d_ = d_ / np.linalg.norm(d_)
        nn = np.array([-d_[1], d_[0]]); hw = 2.0 - FS_['inset']
        for sgn in (1, -1):
            q_ = lip - d_ * FS_['back'] + nn * sgn * hw
            st.append(f'[{q_[0]:.6f} {FS_["y"]:.6f} {q_[1]:.6f}] {PP.statue_ang(d_[0], d_[1]):.6f} {P}/statue/stake_yellow.jm {P}/statue/stake_yellow.png null')
    # v28: yellow marker stakes on the crest of every bump, both lane edges (drone photos)
    SK = getattr(LT, 'STAKES', None); nsk = 0
    if SK:
        from scipy.signal import find_peaks
        for g in p.segs:
            if g['kind'] != 'S': continue
            c_, s_ = np.cos(g['t']), np.sin(g['t'])
            for prof, u0, name in g['sections']:
                pk, _ = find_peaks(np.r_[0, prof, 0], prominence=SK['prom']); pk = pk - 1
                skip = [(a_, b_) for n_, a_, b_, h_ in LS.COMBOS[name]['items'] if n_.startswith(('Detroit_g31_1 (cut', 'trapeze'))]   # v29: none on the freestyle kicker / landing
                for k in pk:
                    if any(a_ <= k * 0.1 <= b_ for a_, b_ in skip): continue
                    top = prof >= prof[k] - 0.15; a_ = k; b_ = k
                    while a_ > 0 and top[a_ - 1]: a_ -= 1
                    while b_ < len(prof) - 1 and top[b_ + 1]: b_ += 1
                    us = [a_ * 0.1 + 0.5, b_ * 0.1 - 0.5] if (b_ - a_) * 0.1 > SK['table'] else [k * 0.1]
                    for uu in us:
                        for sg in (-1, 1):
                            x_ = g['x0'] + (u0 + uu) * c_ - sg * SK['v'] * s_; z_ = g['z0'] + (u0 + uu) * s_ + sg * SK['v'] * c_
                            st.append(f'[{x_:.6f} 0.000000 {z_:.6f}] {PP.statue_ang(c_, s_):.6f} {P}/statue/stake_yellow.jm {P}/statue/stake_yellow.png null'); nsk += 1   # v29: flat paddle facing the riders
        print('stakes', nsk)
    # v28: blue nets on the outside of the turns asked by the user, on the berm crest (flat part: r + half lane + flat_off)
    NT = getattr(LT, 'NETS', None); nnet = 0
    for f_ in os.listdir(f'{OUT}/statue'):          # v34: no stale net from an earlier export (a turn may lose its net)
        if f_.startswith('net_') and f_.endswith(('.jm', '.shp')): os.remove(f'{OUT}/statue/{f_}')
    if NT:
        smp_ = p.samples(1.0); TW_ = 30.4
        for g in p.segs:
            if g['kind'] != 'T' or (NT['turns'] != 'all' and g['tag'] not in NT['turns']) or g['tag'] in NT.get('skip', ()): continue
            sel = (smp_['s'] >= g['s0']) & (smp_['s'] <= g['s0'] + g['L'])
            cc = np.array([g['cx'], g['cz']]); U_, crs = [], []
            for x_, z_ in zip(smp_['x'][sel], smp_['z'][sel]):
                u = np.array([x_, z_]) - cc; u /= np.linalg.norm(u); U_.append(u)
                rr = np.arange(g['r'], g['r'] + 30, 0.5); hh = np.array([float(h_at(H, *(cc + u * r_))) for r_ in rr])
                k = int(np.argmax(hh))
                if hh[k] - hh[0] > 1.2 and 0 < k < len(hh) - 6 and hh[k] - hh[k + 6] > 0.2: crs.append(rr[k])   # a berm drops behind its crest
            if len(crs) >= 5:
                rc = float(np.median(crs)) + 1.0                 # one radius per turn: just behind the berm crest
                keep = [i for i, u in enumerate(U_) if float(h_at(H, *(cc + u * (rc - 1.0)))) > 1.5]   # the bermed part (half berms: 2nd half)
            else:                                                # v32 (user: a net in EVERY turn): no berm -> just outside the lane
                rc = g['r'] + TW_ / 2 + NT['flat_gap']; keep = []
            if len(keep) < 5: keep = list(range(len(U_)))
            pts = U_[keep[0]:keep[-1] + 1]
            line = np.array([cc + u * rc for u in pts])
            # v29: ONE continuous net per turn whose bottom follows the ground (user: no more square panels in steps)
            import stt_props
            def gnd(x, z):                                       # bilinear terrain height (world ft)
                fx, fz = x / S, z / S; j, i = int(fx), int(fz); a, b = fx - j, fz - i
                return float(H[i, j] * (1 - a) * (1 - b) + H[i, j + 1] * a * (1 - b) + H[i + 1, j] * (1 - a) * b + H[i + 1, j + 1] * a * b)
            Ls = np.r_[0, np.cumsum(np.linalg.norm(np.diff(line, axis=0), axis=1))]
            sv = np.linspace(0, Ls[-1], max(2, int(Ls[-1] / 1.0) + 1))
            line1 = np.c_[np.interp(sv, Ls, line[:, 0]), np.interp(sv, Ls, line[:, 1])]
            # origin on flat ground (the game puts the object on the ground under its origin and tilts it with the slope there)
            best = None
            for fr in np.linspace(0.0, 0.85, 18):
                for q in (0.5, 0.3, 0.7):
                    o = cc + (line1[int(q * (len(line1) - 1))] - cc) * fr
                    hs = [gnd(o[0] + dx, o[1] + dz) for dx in (-3, 0, 3) for dz in (-3, 0, 3)]
                    sc_ = max(hs) - min(hs)
                    if best is None or sc_ < best[0] - 1e-6: best = (sc_, o)
            org = best[1]
            nm_ = f"net_{''.join(ch for ch in g['tag'] if ch.isalnum())[:24]}"
            m_ = stt_props.net_ribbon(line1, gnd, org); m_.write(f'{OUT}/statue/{nm_}.jm', (0, 0, 0, 0, 0))
            open(f'{OUT}/statue/{nm_}.shp', 'w', newline='\n').write(stt_props.net_shape(line1, gnd, org))   # v31: soft collision
            st.append(f'[{org[0]:.6f} 0.000000 {org[1]:.6f}] 0.000000 {P}/statue/{nm_}.jm {P}/statue/net_ribbon.png {P}/statue/{nm_}.shp'); nnet += 1
            print('net', g['tag'], 'length %.0f ft, origin flatness %.3f ft' % (Ls[-1], best[0]))
        shutil.copy(f'{ROOT}/assets/props/net_ribbon.png', f'{OUT}/statue/net_ribbon.png')
        print('nets', nnet)
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
        from skimage.measure import find_contours                       # v27: one row of patches along the fence, at a constant
        ring = max(find_contours(DF, GD['clear']), key=len)                # distance, so the grass edge runs parallel to the fence
        Lr = np.r_[0, np.cumsum(np.hypot(*np.diff(ring, axis=0).T))]
        for sv in np.arange(0, Lr[-1], 13.0):
            k_ = min(int(np.searchsorted(Lr, sv)), len(ring) - 1); z_, x_ = ring[k_]
            dec.append(f'[{x_:.6f} {z_:.6f}] {rg.uniform(-np.pi, np.pi):.6f} {GD["size"]:.6f} 1.000000 {P}/decal/grass_dvdb.png'); ng += 1
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
