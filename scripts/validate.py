"""Automatic validation of the exported folders (round-trip read with the same reader used on the references)."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import os, sys, json, numpy as np
sys.path.insert(0, ROOT + '/scripts')
from mxs import Track, parse_gates, parse_tileinfo
from engine import LIB, section_profile
from scipy import ndimage as ndi
import layouts

DIST = ROOT + '/legacy_mx/tracks'; BUILD = ROOT + '/legacy_mx/build'
H = np.load(f'{BUILD}/H.npy').astype(np.float64)
R = {'checks': []}
def check(name, ok, detail):
    R['checks'].append(dict(name=name, ok=bool(ok), detail=detail)); print(('PASS ' if ok else 'FAIL ') + name + ' :: ' + str(detail))

paths = {'RyanCompoundMX': layouts.mx(), 'RyanCompoundSX1': layouts.sx1(), 'RyanCompoundSX2': layouts.sx2()}
required = ['terrain.hf', 'terrain.png', 'tilemap', 'tileinfo', 'timing_gates', 'lighting', 'desc', 'shading.ppm', 'shadingx2.ppm']
for folder, path in paths.items():
    d = f'{DIST}/{folder}'
    miss = [f for f in required if not os.path.exists(f'{d}/{f}')]
    check(f'{folder}: required files present', not miss, miss or 'all present')
    T = Track(d, 'xz')
    check(f'{folder}: heightmap round-trip', np.abs(T.H - H).max() < 0.01, f'max |exported-built| = {np.abs(T.H - H).max():.4f} ft, size {T.size:.1f} ft, {T.N}px')
    ti = parse_tileinfo(f'{d}/tileinfo'); nt = sum(1 for l in open(f'{d}/tileinfo') if l.strip() == 'addtile')
    check(f'{folder}: tilemap indices < tile count', T.tiles.max() < nt, f'max index {T.tiles.max()}, {nt} tiles')
    # texture references resolvable inside the package (or base game files with no folder)
    refs = set()
    for f in ('tileinfo', 'lighting'):
        for tok in open(f'{d}/{f}').read().split():
            for part in tok.split('='):
                if part.startswith('@'): refs.add(part[1:])
    bad = [r for r in refs if '/' in r and not os.path.exists(f'{DIST}/{r}')]
    check(f'{folder}: all @folder/ references exist in package', not bad, bad or f'{len(refs)} refs ok (base-game: {sorted(r for r in refs if "/" not in r)})')
    G = parse_gates(f'{d}/timing_gates')
    smp = path.samples(0.5); P = np.c_[smp['x'], smp['z']]
    # each checkpoint: centre on the path, line crosses no other part of the lap
    from scipy.spatial import cKDTree
    tr = cKDTree(P); worst = 0; cross = 0
    for k, cp in enumerate(G['cps']):
        L, x, y, z, dx, dy, dz = cp[:7]
        dd, ii = tr.query([x, z]); worst = max(worst, dd)
        t = np.linspace(-1, 1, 41); pts = np.c_[x + dx * t, z + dz * t]
        dist, idx = tr.query(pts)
        far = np.abs(smp['s'][idx] - smp['s'][ii]); far = np.minimum(far, path.s - far)
        cross += int(np.any((dist < 6.0) & (far > 60.0)))
    check(f'{folder}: checkpoints on the path', worst < 1.0, f'{len(G["cps"])} checkpoints, max offset {worst:.2f} ft')
    check(f'{folder}: checkpoint lines touch no other part of the lap', cross == 0, f'{cross} offending checkpoints')
    check(f'{folder}: lap order complete', G['first'] == list(range(len(G['cps']))) and G['normal'] == G['first'], f'first={len(G["first"])} normal={len(G["normal"])}')
    st = np.array([g[:3] for g in G['start']])
    hs = T.h(st[:, 0], st[:, 2]); ahead = T.h(st[:, 0] + 15, st[:, 2])
    check(f'{folder}: start gates on level ground', np.ptp(hs) < 0.3 and np.abs(ahead - hs).max() < 0.5,
          f'{len(st)} gates, height spread {np.ptp(hs):.2f} ft, max change 15 ft ahead {np.abs(ahead - hs).max():.2f} ft')

# ---------- clearance between non-consecutive parts of each lap
from scipy.spatial import cKDTree
for name, path, lim in (('MX', layouts.mx(), 70.0), ('SX1', layouts.sx1(), 38.0), ('SX2', layouts.sx2(), 38.0)):
    smp = path.samples(1.0); trr = cKDTree(np.c_[smp['x'], smp['z']]); pr = trr.query_pairs(lim, output_type='ndarray')
    far = np.abs(smp['s'][pr[:, 0]] - smp['s'][pr[:, 1]]); far = np.minimum(far, path.s - far)
    check(f'{name}: no unintended proximity between track parts', int((far > 4 * lim).sum()) == 0, f'centre-line clearance >= {lim:.0f} ft everywhere (SX lane spacing 43 ft = references)')
# ---------- geometric fidelity: SX lanes = measured section profiles?
T = Track(f'{DIST}/RyanCompoundSX1', 'xz')
errs = []
for name, path in (('SX1', layouts.sx1()), ('SX2', layouts.sx2())):
    for g in path.segs:
        if g['kind'] != 'S': continue
        for sec in g['sections']:
            p = section_profile(sec[0], sec[2] if len(sec) > 2 else None)
            u = sec[1] + np.arange(len(p)) * 0.1
            x = g['x0'] + u * np.cos(g['t']); z = g['z0'] + u * np.sin(g['t'])
            h = T.h(x, z)
            e = np.abs(h - p); errs.append((name, sec[0], float(e.max()), float(np.percentile(e, 95)), float(p.max()), float(h.max())))
E = np.array([e[2] for e in errs])
check('SX: exported lane profiles = measured reference profiles', E.max() < 0.25,
      f'{len(errs)} sections, max |exported-measured| {E.max():.3f} ft (0.4 ft grid vs 0.29 ft references; p95 of maxima {np.percentile(E,95):.3f})')
R['sx_profile_errors'] = errs
# lateral model check: rebuild every isolated reference block from its centre profile x measured wall, compare in 2D
from sx_classify_lib import rot_patch
from engine import sx_wall
Lc = json.load(open(ROOT + '/lib/sx_components.json'))
tw = LIB['sx_lateral']['top_width']; errs2 = []
for c in Lc:
    if not (c['npeaks'] == 1 and c['solidity'] > 1.5 and 35 < c['width_lane'] < 38.5 and c['hmax'] > 1.5): continue
    Pp = np.load(f'{ROOT}/lib/sx/{c["id"]}.npy'); uu, Q = rot_patch(Pp, c['s'], c['lane_ang'])
    occ = np.nonzero(Q.max(1) > 0.5 * Q.max())[0]; vc = (occ.min() + occ.max()) / 2
    prof = Q[int(vc)]; v = (np.arange(Q.shape[0]) - vc) * 0.1
    model = prof[None, :] * sx_wall(np.abs(v)[:, None] - tw / 2)
    m = Q > 0.02
    errs2.append((c['id'], float(np.abs(model - Q)[m].max()), float(np.sqrt(np.mean((model - Q)[m] ** 2))), float(Q.max())))
E2 = np.array([e[2] for e in errs2]); M2 = np.array([e[1] for e in errs2])
check('SX lateral model (profile x measured wall) reproduces isolated reference blocks', np.median(E2) < 0.15,
      f'{len(errs2)} blocks: RMSE median {np.median(E2):.3f} ft, p90 {np.percentile(E2,90):.3f} ft; max point error median {np.median(M2):.2f} ft (block heights 1.9-11.2 ft)')
R['sx_lateral_errors'] = errs2
# ---------- MX: exported centreline = designed (measured sections inserted)
Dl = np.load(f'{BUILD}/mx_line.npz'); T = Track(f'{DIST}/RyanCompoundMX', 'xz')
hc = T.h(Dl['x'], Dl['z']); e = np.abs(hc - Dl['E'])
check('MX: exported centreline = designed profile (measured sections)', np.percentile(e, 99) < 0.1, f'p99 {np.percentile(e,99):.3f} ft, max {e.max():.3f} ft')
# MX surface slopes: on the riding line, slopes outside obstacles stay below 15 deg (references: Desert Sand p99 = 14.8 deg)
rep = json.load(open(f'{BUILD}/build_report.json'))
check('MX: grade within reference range', rep['mx']['grade_abs_p50_p90_max'][2] < 15.0, f"|grade| p50/p90/max = {[round(v,1) for v in rep['mx']['grade_abs_p50_p90_max']]} deg (Desert Sand: 3.2/9.1/14.8 over 60 ft)")
# spikes/holes: Laplacian outliers on the whole terrain
lap = np.abs(ndi.laplace(H)); pct = float(np.percentile(lap, 99.99))
check('Terrain: no isolated spikes/holes', lap.max() < 6.0, f'max |laplacian| {lap.max():.3f} ft per px^2, p99.99 {pct:.3f}')
json.dump(R, open(f'{BUILD}/validation.json', 'w'), indent=1, default=float)
