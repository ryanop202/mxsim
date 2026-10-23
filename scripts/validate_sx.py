"""v2 validation: re-read the exported folders and check them."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import os, sys, json, numpy as np
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
paths = {'RyanCompoundSX1': LS.sx1(), 'RyanCompoundSX2': LS.sx2(), 'RyanCompoundSX3': LS.sx3()}
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
        t = np.linspace(-1, 1, 41); dist, idx = tr.query(np.c_[x + dx * t, z + dz * t])
        far = np.abs(smp['s'][idx] - smp['s'][ii]); far = np.minimum(far, path.s - far); cross += int(np.any((dist < 6) & (far > 60)))
    check(f'{folder}: portes sur la ligne de course', worst < 1.0, f'{len(loop)} portes du tour, écart max {worst:.2f} ft')
    check(f'{folder}: aucune porte ne touche une autre partie du tour', cross == 0, f'{cross} porte(s) en défaut')
    extra = [i for i in G['first'] if i not in loop]
    check(f'{folder}: ordre des tours', set(loop) <= set(G['first']) and G['first'][len(extra):] == loop, f'1er tour {len(G["first"])} portes (dont {len(extra)} sur la ligne de départ), tours suivants {len(loop)}')
    key = folder[-3:]; S0 = LS.STARTS[key]; hd = np.radians(S0['heading']); f = np.array([np.cos(hd), np.sin(hd)]); nv = np.array([-f[1], f[0]])
    st = np.array([g[:3] for g in G['start']]); hs = T.h(st[:, 0], st[:, 2])
    check(f'{folder}: grille de départ (22 grilles comme JGSX)', len(st) == 22 and np.ptp(hs) < 0.05 and np.abs(hs).max() < 0.05, f'{len(st)} grilles au pas de 4 ft, sol plat (écart {np.ptp(hs):.3f} ft)')
    # start corridor: from every gate, straight ahead then funnel into the lap lane at the merge point: all flat floor, 3 ft each side
    M = np.array(S0['merge']); worst = 0.0
    tM = path.samples(0.5); iM = np.argmin(np.hypot(tM['x'] - M[0], tM['z'] - M[1])); thM = tM['th'][iM]; nM = np.array([-np.sin(thM), np.cos(thM)])
    for g in st:
        a = np.array([g[0], g[2]]); b = a + f * S0['straight']; o = (a - np.array(S0['gate'])) @ nv
        c = M + np.clip(o, -10, 10) * nM * np.sign(nv @ nM if abs(nv @ nM) > 0.1 else 1)
        for p0, p1 in ((a, b), (b, c)):
            u = np.linspace(0, 1, int(np.hypot(*(p1 - p0)) / 0.5) + 2)[:, None]; q = p0 + (p1 - p0) * u
            dirv = (p1 - p0) / max(np.hypot(*(p1 - p0)), 1e-6); lat = np.array([-dirv[1], dirv[0]])
            for off in (-3, 0, 3):
                worst = max(worst, float(T.h(q[:, 0] + off * lat[0], q[:, 1] + off * lat[1]).max()))
    L_start = S0['straight'] + float(np.hypot(*(M - (np.array(S0['gate']) + f * S0['straight']))))
    check(f'{folder}: ligne de départ dégagée jusqu’au tour', worst < 0.05, f'22 trajectoires grille -> entonnoir -> point de jonction, hauteur max {worst:.3f} ft ; longueur jusqu’à la jonction ≈ {L_start:.0f} ft')
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
# berm entry lip: height jump between a floor pixel (<0.02 ft) and its neighbour (cut edge = 'rebord')
def floorstep(Hh):
    a = Hh[:-1, :-1]; b = Hh[1:, :-1]; c = Hh[:-1, 1:]
    return max(np.where(np.minimum(a, b) < 0.02, np.abs(a - b), 0).max(), np.where(np.minimum(a, c) < 0.02, np.abs(a - c), 0).max())
ref = Track(REF + '/JGSX2026TestTracks/JGSX2026Detroit', 'xz'); fr = floorstep(np.clip(ref.H - np.median(ref.H), 0, None)); fo = floorstep(H)
check('Pas de rebord au pied des berms et des obstacles', fo <= fr + 0.02, f'marche max sol -> obstacle : {fo:.3f} ft (référence JGSX Detroit : {fr:.3f} ft ; ancien rebord des berms : 0.30 ft)')
lap = np.max(np.abs(ndi.laplace(H)))
check('Terrain sans pics ni trous', lap < 4.0, f'|laplacien| max {lap:.2f}')
json.dump(R, open(f'{BUILD}/validation.json', 'w'), indent=1, default=float)
print(sum(c['ok'] for c in R['checks']), '/', len(R['checks']))
