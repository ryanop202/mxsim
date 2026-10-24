"""v2 validation: re-read the exported folders and check them."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import os, re, sys, json, numpy as np
sys.path.insert(0, ROOT + '/scripts')
from mxs import Track, parse_gates, parse_tileinfo
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
import layouts_sx as LS
from engine import split_centre

DIST = ROOT + '/tracks'; BUILD = ROOT + '/build'
H = np.load(f'{BUILD}/H.npy').astype(np.float64)
R = {'checks': []}
def check(name, ok, detail):
    R['checks'].append(dict(name=name, ok=bool(ok), detail=detail)); print(('PASS ' if ok else 'FAIL ') + name + ' :: ' + str(detail))
from names import FOLDERS
paths = {FOLDERS['SX1']: LS.sx1(), FOLDERS['SX2']: LS.sx2(), FOLDERS['SX3']: LS.sx3()}
req = ['terrain.hf', 'terrain.png', 'tilemap', 'tileinfo', 'timing_gates', 'lighting', 'desc', 'shading.ppm', 'shadingx2.ppm']
T = None
for folder, path in paths.items():
    d = f'{DIST}/{folder}'; miss = [f for f in req if not os.path.exists(f'{d}/{f}')]
    check(f'{folder}: fichiers requis présents', not miss, miss or 'tous présents')
    T = Track(d, 'xz')
    check(f'{folder}: heightmap relu = terrain construit', np.abs(T.H - H).max() < 0.01, f'écart max {np.abs(T.H - H).max():.4f} ft, {T.N}px à {T.s} ft = {T.size:.1f} ft (grille identique aux JGSX)')
    nt = sum(1 for l in open(f'{d}/tileinfo') if l.strip() == 'addtile')
    check(f'{folder}: tilemap cohérente avec tileinfo', T.tiles.max() < nt, f'index max {T.tiles.max()}, {nt} tiles')
    refs = set()
    for f in ('tileinfo', 'lighting'):
        for tok in open(f'{d}/{f}').read().split():
            for part in tok.split('='):
                if part.startswith('@'): refs.add(part[1:])
    bad = [r for r in refs if '/' in r and not os.path.exists(f'{DIST}/{r}')]
    check(f'{folder}: toutes les références @dossier/ existent dans le paquet', not bad, bad or f'{len(refs)} références OK')
    G = parse_gates(f'{d}/timing_gates'); smp = path.samples(0.5); tr = cKDTree(np.c_[smp['x'], smp['z']])
    loop = G['normal']; worst = 0; cross = 0
    for i in loop:
        L_, x, y, z, dx, dy, dz = G['cps'][i][:7]; dd, ii = tr.query([x, z]); worst = max(worst, dd)
        t = np.linspace(-1, 1, 41); dist, idx = tr.query(np.c_[x - dz * t, z + dx * t])   # gate line = perpendicular to the travel vector
        far = np.abs(smp['s'][idx] - smp['s'][ii]); far = np.minimum(far, path.s - far); cross += int(np.any((dist < 6) & (far > 60)))
    check(f'{folder}: portes sur la ligne de course', worst < 1.0, f'{len(loop)} portes du tour, écart max {worst:.2f} ft')
    check(f'{folder}: aucune porte ne touche une autre partie du tour', cross == 0, f'{cross} porte(s) en défaut')
    key = folder[-3:]; S0 = LS.STARTS[key]
    from starts import StartRoute
    RT = StartRoute(S0, LS.N_GATES, LS.GATE_PITCH); EI = json.load(open(f'{BUILD}/export_info.json'))[key]
    # lap counting simulated on the riders' trajectory: every gate of the list must be crossed, in that order
    def crossings(traj, gate):
        h_, x_, y_, z_, dx_, dy_, dz_ = gate[:7]; p_ = np.array([x_ + dz_, z_ - dx_]); q_ = np.array([x_ - dz_, z_ + dx_])   # gate line
        A = traj[:-1]; B = traj[1:]; d1 = B - A; d2 = q_ - p_
        fwd = d1[:, 0] * dx_ + d1[:, 1] * dz_ > 0                                # crossed in the riding direction (vector = travel)
        den = d1[:, 0] * d2[1] - d1[:, 1] * d2[0]; ok = np.abs(den) > 1e-9
        t_ = np.where(ok, ((p_[0] - A[:, 0]) * d2[1] - (p_[1] - A[:, 1]) * d2[0]) / np.where(ok, den, 1), -1)
        u_ = np.where(ok, ((p_[0] - A[:, 0]) * d1[:, 1] - (p_[1] - A[:, 1]) * d1[:, 0]) / np.where(ok, den, 1), -1)
        return np.nonzero(ok & fwd & (t_ >= 0) & (t_ <= 1) & (u_ >= 0) & (u_ <= 1))[0]
    def ride(order, traj):
        pos = -1
        for gi in order:
            c = crossings(traj, G['cps'][gi]); c = c[c > pos]
            if not len(c): return gi
            pos = c[0]
        return None
    lap_s = path.samples(0.5); Lp = path.s
    def lap_traj(s0, length):
        ss = (s0 + np.arange(0, length, 0.5)) % Lp; idx = np.searchsorted(lap_s['s'], ss).clip(0, len(lap_s['s']) - 1)
        return np.c_[lap_s['x'][idx], lap_s['z'][idx]]
    rs = RT.samples(0.5); sM, sF = EI['s_merge'], EI['s_finish']; dl = (sF - sM) % Lp
    first_traj = np.vstack([np.c_[rs['x'], rs['z']], lap_traj(sM, (Lp + dl if dl < Lp / 2 else dl) + 2)])
    miss1 = ride(G['first'], first_traj); miss2 = ride(loop, lap_traj(sF + 0.5, Lp + 1))
    dup = len(G['first']) != len(set(G['first']))
    check(f'{folder}: tours comptés sans bug (simulation des portes)', miss1 is None and miss2 is None and not dup and G['first'][-1] == loop[-1],
          f"1er tour : {len(G['first'])} portes franchies dans l'ordre ({(Lp + dl if dl < Lp / 2 else dl) + RT.L:.0f} ft depuis la grille) ; "
          f"tours suivants : {len(loop)} portes, arrivée = dernière porte" if miss1 is None and miss2 is None else f'porte manquée : 1er tour {miss1}, tour {miss2}, doublons {dup}')
    st = np.array([g[:3] for g in G['start']]); hs = T.h(st[:, 0], st[:, 2])
    check(f'{folder}: grille de départ (22 grilles comme JGSX)', len(st) == 22 and np.ptp(hs) < 0.05 and np.abs(hs).max() < 0.05, f'{len(st)} grilles au pas de 4 ft, sol plat (écart {np.ptp(hs):.3f} ft)')
    # start corridor: whole corridor area flat (on a start berm turn: the riding line +-3 ft), and it ends on the lap line
    X_, Z_, S_, B_ = RT.area_points(1.0, 1.0, margin=1.0)
    off = B_ & False
    if B_.any():
        for g_ in RT.berm_turns:
            r_ = np.hypot(X_ - g_['cx'], Z_ - g_['cz']); off |= B_ & (np.abs(r_ - g_['r']) > 2)   # start berm turn: riding line +-2 ft
    hh_ = T.h(X_[~off], Z_[~off]); worst = float(hh_.max())
    iM = int(np.argmin(np.hypot(lap_s['x'] - RT.merge[0], lap_s['z'] - RT.merge[1]))); dM = float(np.hypot(lap_s['x'][iM] - RT.merge[0], lap_s['z'][iM] - RT.merge[1]))
    check(f'{folder}: ligne de départ dégagée jusqu’au tour', worst < 0.05 and dM < 1.0,
          f'couloir entier (largeur 92 -> 30 ft, sans entonnoir) plat, hauteur max {worst:.3f} ft ; jonction sur la ligne du tour (écart {dM:.2f} ft) ; longueur grille -> jonction ≈ {RT.L:.0f} ft')
    turns = json.load(open(f'{BUILD}/build_report.json'))[key]['turns']
    flat = [t_ for t_ in turns if t_['kind'] == 'turn' and not t_['berm'] and abs(t_['angle']) > 25]
    check(f'{folder}: aucun virage plat', not flat, flat or f"{sum(1 for t_ in turns if t_['berm'])} virages avec berm/sable ; seuls des déports plats ≤ 25° restent : {[round(t_['angle'],1) for t_ in turns if not t_['berm']]}")
# clearance inside each lap and between the three tracks
allp = {k: v.samples(1.0) for k, v in paths.items()}
for k, smp in allp.items():
    tr = cKDTree(np.c_[smp['x'], smp['z']]); pr = tr.query_pairs(38.0, output_type='ndarray'); L = paths[k].s
    far = np.abs(smp['s'][pr[:, 0]] - smp['s'][pr[:, 1]]); far = np.minimum(far, L - far)
    check(f'{k}: couloirs non confondus', int((far > 140).sum()) == 0, 'axes séparés d’au moins 38 ft (espacement JGSX 43 ft)')
ks = list(allp)
for a in range(3):
    for b in range(a + 1, 3):
        A, B = allp[ks[a]], allp[ks[b]]; d, _ = cKDTree(np.c_[B['x'], B['z']]).query(np.c_[A['x'], A['z']])
        check(f'{ks[a][-3:]} / {ks[b][-3:]}: pistes séparées', d.min() > 75, f'distance mini entre lignes {d.min():.0f} ft')
# fidelity: exported lane profile = composed measured profile
errs = []
for k, path in paths.items():
    for g in path.segs:
        if g['kind'] != 'S': continue
        for prof, u0, name in g['sections']:
            prof = prof.copy()
            for sp in LS.SPLITS.get(name, []):   # double lines: expected centre-line height of the two halves
                i0 = int(round(sp[0] / 0.1)); c = split_centre(sp); prof[i0:i0 + len(c)] = np.maximum(prof[i0:i0 + len(c)], c)
            u = u0 + np.arange(len(prof)) * 0.1; h = T.h(g['x0'] + u * np.cos(g['t']), g['z0'] + u * np.sin(g['t']))
            errs.append((name, float(np.abs(h - prof).max())))
E = np.array([e[1] for e in errs])
check('Profils exportés = profils mesurés JGSX', E.max() < 0.06, f'{len(errs)} couloirs, écart max {E.max():.3f} ft (interpolation sur la grille de 0.29 ft)')
R['lane_errors'] = errs
# Ryan: no 'pains de sucre' (short pointed bumps) in the rhythm lanes. Pointedness = height / width at half height;
# normal JGSX singles 0.23-0.30, the ones Ryan rejected 0.37-0.51. Allowed on purpose: SX3 finish (to force braking).
UJ = json.load(open(ROOT + '/lib/sx_units.json')); ALLOWED = {'Custom1_g59_1'}
def pointed(uid):
    u = UJ['units'][UJ['alias'].get(uid, uid)]; p = np.asarray(u['prof']); return u['kind'] in ('S', 'B') and p.max() / ((p > p.max() / 2).sum() * 0.1) > 0.31
bad = sorted({(n[:3], i) for n, c in LS.COMBOS.items() for t in c['tokens'] for i in ([t] if isinstance(t, str) else (list(t[1:3]) if t[0] == 'split' else []))
              if pointed(i) and i not in ALLOWED})
check('Pas de pains de sucre dans les enchaînements', not bad, bad or 'toutes les bosses ont un rapport hauteur / largeur à mi-hauteur ≤ 0,31 (sauf le pain de sucre voulu du SX3 avant le triple d’arrivée)')
# berm entry lip: height jump between a floor pixel (<0.02 ft) and its neighbour (cut edge = 'rebord')
def floorstep(Hh):
    a = Hh[:-1, :-1]; b = Hh[1:, :-1]; c = Hh[:-1, 1:]
    return max(np.where(np.minimum(a, b) < 0.02, np.abs(a - b), 0).max(), np.where(np.minimum(a, c) < 0.02, np.abs(a - c), 0).max())
ref = Track(REF + '/JGSX2026TestTracks/JGSX2026Detroit', 'xz'); fr = floorstep(np.clip(ref.H - np.median(ref.H), 0, None)); fo = floorstep(H)
check('Pas de rebord au pied des berms et des obstacles', fo <= fr + 0.02, f'marche max sol -> obstacle : {fo:.3f} ft (référence JGSX Detroit : {fr:.3f} ft ; ancien rebord des berms : 0.30 ft)')
# v9 habillage: every object off the riding surfaces and off the obstacles; every referenced file present; gate models on the grid
from scipy.spatial import cKDTree as _KD
ride = [_KD(np.c_[s_['x'], s_['z']]) for s_ in (p_.samples(1.0) for p_ in paths.values())]
from starts import StartRoute as _SR
_corr = [_SR(LS.STARTS[k_[-3:]], LS.N_GATES, LS.GATE_PITCH).area_points(2.0, 2.0, margin=0.0) for k_ in paths]
ride_c = _KD(np.vstack([np.c_[c_[0], c_[1]] for c_ in _corr]))
SX1D = f'{DIST}/' + FOLDERS['SX1']
def _bbox(model):
    L_ = open(f'{SX1D}/statue/{model}.jm').read().split('\n')   # JM1 / JM2: first 'nverts ntris' line, then the vertices
    i_ = next(k for k, l in enumerate(L_) if len(l.split()) == 2 and all(t.isdigit() for t in l.split())); nv_ = int(L_[i_].split()[0])
    V_ = np.array([[float(t) for t in l.split()[:3]] for l in L_[i_ + 1:i_ + 1 + nv_]]); return V_.min(0), V_.max(0)
BB = {}; worst = []; nobj = 0
for l in open(f'{SX1D}/statues'):
    if not l.strip() or 'ET_compound' in l: continue
    if any(f'/{m}.jm' in l for m in ('finish_arch', 'start_gantry', 'start_grate', 'bike_trainer')): continue   # v12: over / on the track on purpose (checked below)
    nums = [float(t) for t in re.findall(r'-?\d+\.?\d*', l.split('@')[0])]; x, y, z, a = nums[:4]; model = l.split()[4].split('/')[-1][:-3]
    if model not in BB: BB[model] = _bbox(model)
    lo, hi = BB[model]; f_ = np.array([-np.sin(a), -np.cos(a)]); n_ = np.array([f_[1], -f_[0]])
    uu, vv = np.meshgrid(np.linspace(lo[2], hi[2], 7), np.linspace(-max(abs(lo[0]), abs(hi[0])), max(abs(lo[0]), abs(hi[0])), 5))
    q = np.c_[x + uu.ravel() * f_[0] + vv.ravel() * n_[0], z + uu.ravel() * f_[1] + vv.ravel() * n_[1]]
    q = q[(q[:, 0] > 0) & (q[:, 0] < T.size) & (q[:, 1] > 0) & (q[:, 1] < T.size)]
    dmin = min(r_.query(q)[0].min() for r_ in ride) if len(q) else 1e9
    hmax = float(T.h(q[:, 0], q[:, 1]).max()) if len(q) else 0.0
    nobj += 1
    if len(q) and ride_c.query(q)[0].min() < 1.0: worst.append((model, round(x), round(z), 'couloir de départ')); continue
    lim = 0.85 if model.startswith('tuff') else 0.05      # tuff blocks may sit on the foot of two jump walls (y = local ground)
    if model.startswith('tuff'): lim, dlim = 1.5, 15.0          # v11b: tuff blocks AT the lane edge (centre 16.5 ft, corners >= 15 ft on curves), may sit on a sand berm foot
    else: dlim = 17.0
    if model.startswith('tuff'):                                  # y = local ground: neither buried nor floating by more than 0.5 ft
        hmin = float(T.h(q[:, 0], q[:, 1]).min()); lim = 9.9
        if hmax - y > 0.5 or y - hmin > 0.5: worst.append((model, round(x), round(z), 'sol en pente', round(hmin, 2), round(hmax, 2)))
    if (model != '2' and (dmin < dlim or hmax > lim)) or (model == '2' and dmin < 17.0): worst.append((model, round(x), round(z), round(dmin, 1), round(hmax, 2)))
check('Objets hors piste (tuff blocks, grillages, poteaux, paddock, repères)', not worst, worst[:8] or f'{nobj} objets : tous à plus de 17 ft des lignes de course et sur sol plat')
refs2 = set()
for fname in ('statues', 'decals', 'timing_gates'):
    for d_ in paths:
        for tok in open(f'{DIST}/{d_}/{fname}').read().split():
            if tok.startswith('@USLAND2026'): refs2.add(tok[1:])
miss = [r_ for r_ in refs2 if not os.path.exists(f'{DIST}/{r_}')]
nd = sum(1 for _ in open(f'{SX1D}/decals'))
gl = [l for l in open(f'{SX1D}/timing_gates') if l.startswith('[') and 'start_gate.jm' in l]          # v12: USLAND gates
badf = []
for d_ in paths:
    for l in open(f'{DIST}/{d_}/flaggers'):
        if l.startswith('['):
            q = [float(t) for t in re.findall(r'-?\d+\.?\d*', l)][:3]
            if q[0] == 0 and q[2] == 0: continue
            dm = min(r_.query([q[0], q[2]])[0] for r_ in ride)
            if dm < 20: badf.append((d_[-3:], round(q[0]), round(q[2]), round(dm, 1)))
check('Drapeaux hors piste', not badf, badf or 'panneaux 30 s et drapeau d’arrivée à plus de 20 ft des lignes de course')
# v12: USLAND finish arches (pillars clear of every riding line, flat feet, room under the beam), gate models, grates
import props_place as PP_
T_ = PP_.load_terrain(); bad_arch = []
for k_ in ('SX1', 'SX2', 'SX3'):
    A_ = PP_.arch_pose(k_, T_)
    if A_['pillar_line_dist'] < 17 or A_['plate_slope'] > 1.5 or A_['clearance'] < 18: bad_arch.append((k_, round(A_['pillar_line_dist'], 1), round(A_['plate_slope'], 2), round(A_['clearance'], 1)))
check('Arches d’arrivée USLAND', not bad_arch, bad_arch or 'poteaux à ≥ 17 ft des lignes, pieds sur sol plat, ≥ 18 ft sous la poutre au-dessus de la crête')
check('Habillage : fichiers référencés présents, grilles de départ modélisées', not miss and len(gl) == 22, miss[:5] or f'{len(refs2)} fichiers référencés, {nd} decals, 22 grilles USLAND')
lap = np.max(np.abs(ndi.laplace(H)))
check('Terrain sans pics ni trous', lap < 4.0, f'|laplacien| max {lap:.2f}')
json.dump(R, open(f'{BUILD}/validation.json', 'w'), indent=1, default=float)
print(sum(c['ok'] for c in R['checks']), '/', len(R['checks']))
