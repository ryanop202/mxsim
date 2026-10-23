"""SX rhythm library: every floor-separated obstacle unit of every reference SX lane, sampled on the true lane axis,
with the floor gaps measured between consecutive units (pair statistics for composing new combos)."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, json, numpy as np; sys.path.insert(0, ROOT + '/scripts')
from mxs import *; from scipy.signal import find_peaks
R = REF + '/JGSX2026TestTracks/'
COMP = json.load(open(ROOT + '/lib/sx_components.json'))
CAT = json.load(open(ROOT + '/analysis/catalog_raw.json'))
lanes = sorted({(c['ref'], c['grad']) for c in CAT if c['mode'] == 'sx'})
REFN = {'SX_Detroit': 'JGSX2026Detroit', 'SX_Custom': 'JGSX2026Custom', 'SX_Arlington': 'JGSX2026Arlington', 'SX_Glendale': 'JGSX2026Glendale', 'SX_Cleveland': 'JGSX2026Custom1'}
TR = {}
units = []; seqs = []
for refk, gi in lanes:
    ref = REFN[refk]; T = TR.setdefault(ref, Track(R + ref, 'xz')); g = T.gradients[gi]
    a = np.array(g['a']); u = (np.array(g['b']) - a) / g['len']
    crossed = []
    for c in COMP:
        if c['ref'] != ref or c['npeaks'] != 1 or c['solidity'] < 1.3 or not (30 < c['width_lane'] < 45): continue
        pv = np.array([c['cx'], c['cz']]) - a; t = pv @ u; perp = pv[0] * (-u[1]) + pv[1] * u[0]
        if -5 < t < g['len'] + 5 and abs(perp) < 22: crossed.append(c)
    axis = 'gradient line (no isolated block to verify)'; ax = u; nrm = np.array([-u[1], u[0]]); P0 = a
    if crossed:
        angs = np.array([c['lane_ang'] for c in crossed]); dirs = np.c_[np.cos(angs), np.sin(angs)]; dirs *= np.sign(dirs @ u)[:, None]
        ax2 = np.median(dirs, 0); ax2 /= np.linalg.norm(ax2)
        if np.degrees(np.arccos(np.clip(ax2 @ u, -1, 1))) <= 6:
            ax = ax2; nrm = np.array([-ax[1], ax[0]])
            off = float(np.median([(np.array([c['cx'], c['cz']]) - a) @ nrm for c in crossed]))
            if abs(off) < 16: P0 = a + nrm * off; axis = f'lane axis from {len(crossed)} block(s), offset {off:+.1f} ft'
    A = P0 - ax * 40; B = P0 + ax * (g['len'] + 40)
    d, h = T.line(*A, *B, step=0.1); h = np.clip(h - np.median(T.H), 0, None)
    # lap direction along this lane
    G = parse_gates(R + ref + '/timing_gates'); C = np.array([[c_[1], c_[3]] for c_ in G['cps']]); lap = G['normal']
    on = [(k, (C[i] - A) @ ax) for k, i in enumerate(lap) if abs((C[i] - A) @ nrm) < 18 and -10 < (C[i] - A) @ ax < d[-1] + 10]
    dirn = sum(np.sign(t2 - t1) for (k1, t1), (k2, t2) in zip(on, on[1:]) if k2 == k1 + 1)
    if dirn < 0: h = h[::-1]
    # floor-separated units
    onf = h > 0.06; idx = np.nonzero(onf)[0]
    if len(idx) == 0: continue
    br = np.nonzero(np.diff(idx) > 1)[0]
    starts = np.r_[idx[0], idx[br + 1]]; ends = np.r_[idx[br], idx[-1]]
    seq = []
    for s0, s1 in zip(starts, ends):
        if s0 < 5 or s1 > len(h) - 7: seq.append(None); continue          # cut by the sampled window -> unusable
        p = h[s0 - 5:s1 + 6]
        if p.max() < 0.8 or (s1 - s0) * 0.1 < 6: seq.append(None); continue
        pk, _ = find_peaks(np.r_[0, p, 0], prominence=0.5); crest = [float(p[k - 1]) for k in pk]
        sig = (round(float(p.max()), 1), round(len(p) * 0.1))
        uid = f'{ref[8:]}_g{gi}_{len(seq)}'
        un = dict(uid=uid, ref=ref, grad=gi, axis=axis, lane_dir='lap' if dirn != 0 else 'gradient', start=float(d[s0]), prof=np.round(p, 3).tolist(),
                  L=len(p) * 0.1, H=float(p.max()), npk=len(pk), crests=crest, sig=sig)
        units.append(un); seq.append(uid)
    gaps = [(d[s] - d[e]) for s, e in zip(starts[1:], ends[:-1])]
    if dirn < 0: gaps = gaps[::-1]
    seqs.append(dict(ref=ref, grad=gi, units=seq, gaps=[float(x) for x in gaps]))
# de-duplicate identical units (the JGSX test tracks share many lanes)
uniq = {}; alias = {}
for un in units:
    key = None
    for k, v in uniq.items():
        if abs(v['L'] - un['L']) < 1.0 and abs(v['H'] - un['H']) < 0.15 and v['npk'] == un['npk']:
            n = min(len(v['prof']), len(un['prof'])); 
            if np.abs(np.array(v['prof'][:n]) - np.array(un['prof'][:n])).max() < 0.35: key = k; break
    if key is None: uniq[un['uid']] = un; alias[un['uid']] = un['uid']
    else: alias[un['uid']] = key
for sq in seqs: sq['units'] = [alias.get(x) if x else None for x in sq['units']]
def kind(un):
    if un['npk'] >= 3 and un['H'] < 3.5: return 'whoops'
    if un['npk'] >= 2: return 'combo'
    H = un['H']; L = un['L']
    if H < 2.5: return 'low'
    if H < 4.3: return 'S'
    if H < 6.6: return 'B' if L < 62 else 'T'
    return 'X'
for un in uniq.values(): un['kind'] = kind(un)
json.dump(dict(units=uniq, seqs=seqs, alias=alias), open(ROOT + '/lib/sx_units.json', 'w'), default=float)
print('lanes', len(seqs), 'units', len(units), 'unique', len(uniq))
from collections import Counter
print(Counter(u['kind'] for u in uniq.values()))
for u in sorted(uniq.values(), key=lambda u: (u['kind'], u['H'])):
    print(f"{u['kind']:6s} {u['uid']:22s} H{u['H']:5.2f} L{u['L']:6.1f} peaks {u['npk']} {np.round(u['crests'],1).tolist()}")
for sq in seqs:
    print(sq['ref'][8:], sq['grad'], [ (x.split('_g')[0]+'..'+x.split('_')[-1]) if x else '-' for x in sq['units']], [round(g) for g in sq['gaps']])
