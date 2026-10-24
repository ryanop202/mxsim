"""Compose SX rhythm lanes from measured units (lib/sx_units.json).

Every unit keeps its exact measured profile (0.1 ft samples, travel direction of the reference lap).
Floor gaps between units default to the medians measured between consecutive units of the same kinds
in the JGSX reference lanes; pairs that exist as such in a reference keep their own measured gap.
"""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import json, numpy as np

D = json.load(open(ROOT + '/lib/sx_units.json')) if _os.path.exists(ROOT + '/lib/sx_units.json') else {}
U, ALIAS = D.get('units', {}), D.get('alias', {})
W = json.load(open(ROOT + '/lib/sx_whoops.json')) if _os.path.exists(ROOT + '/lib/sx_whoops.json') else {}

# measured floor gaps (ft) between consecutive units, by kind pair (medians, JGSX rhythm lanes, whoops excluded)
GAP = {('S', 'S'): 5.3, ('S', 'B'): 5.3, ('B', 'S'): 2.75, ('B', 'B'): 2.75, ('low', 'low'): 8.9,
       ('S', 'combo'): 3.8, ('combo', 'S'): 3.75, ('combo', 'B'): 0.5, ('B', 'combo'): 2.75,
       ('X', 'S'): 16.25, ('S', 'X'): 16.25, ('low', 'S'): 8.9, ('S', 'low'): 8.9}
# pairs measured as such in a reference lane (exact gap kept)
PAIR = {('Detroit_g27_1', 'Arlington_g29_2'): 1.6,      # triple trio 7.9/6.0 -> 7.4 (Detroit g27)
        ('Arlington_g30_1', 'Arlington_g30_2'): 24.0,   # step-up 8.8 -> 11.2 (Arlington g30)
        ('Glendale_g83_1', 'Glendale_g83_2'): 40.5}     # big double 7.1 -> 7.9 (Glendale g83)

def unit(uid):
    u = U[ALIAS.get(uid, uid)]
    return u, np.asarray(u['prof'], float)

def whoops(key, n):
    """first n whoops (entry bump included) of a measured whoops lane, cut on the floor after the n-th crest"""
    w = W[key]; p = np.asarray(w['prof'], float)
    from scipy.signal import find_peaks
    pk, _ = find_peaks(p, prominence=0.8, distance=60)
    # start on the floor just before the entry bump (first crest < 2.2 ft followed by 20 ft pitch)
    e = [k for k in range(len(pk) - 1) if p[pk[k]] < 2.2 and 18 < (pk[k + 1] - pk[k]) * 0.1 < 22][0]
    i0 = pk[e]
    while i0 > 0 and p[i0] > 0.06: i0 -= 1
    p = p[max(i0 - 5, 0):]; pk = pk[e:] - max(i0 - 5, 0)
    if n > len(pk): raise ValueError(f'{key} has only {len(pk)} whoops')
    # whoops are floor-separated (1-2 ft gaps): cut on the floor right after the n-th crest
    i = pk[n - 1]
    while i < len(p) - 1 and p[i] > 0.06: i += 1
    return p[:i + 5]

LAST_SPLITS = []   # filled by lane(): [(start_ft, prof_left, prof_right)] for ('split', left_uid, right_uid) tokens


def lane(tokens):
    """tokens: list of uid strings, ('gap', ft), ('whoops', key, n), ('split', left_uid, right_uid).
    A split = double line: two measured units side by side, each on half of the lane width (left / right in the riding
    direction). Its slot in the returned (full-width) profile is left at 0; the halves are rendered separately (LAST_SPLITS).
    Returns (profile, items[(name, start_ft, end_ft, H)])."""
    prof = [np.zeros(1)]; items = []; prev = None; pos = 0.0
    LAST_SPLITS.clear()
    for t in tokens:
        if isinstance(t, tuple) and t[0] == 'gap':
            n = int(round(t[1] / 0.1)); prof.append(np.zeros(n)); pos += n * 0.1; prev = None; continue
        split = None
        if isinstance(t, tuple) and t[0] == 'whoops':
            p = whoops(t[1], t[2]); kind = 'W'; name = f'whoops {t[1]} x{t[2]}'; uid = None
        elif isinstance(t, tuple) and t[0] == 'split':
            pa, pb = unit(t[1])[1], unit(t[2])[1]; n = max(len(pa), len(pb))
            if len(t) > 3 and t[3] == 'end':      # v11: both bumps END together (keeps the rhythm of the next jump on both lines)
                pa = np.pad(pa, (n - len(pa), 0)); pb = np.pad(pb, (n - len(pb), 0))
            else:
                pa = np.pad(pa, (0, n - len(pa))); pb = np.pad(pb, (0, n - len(pb)))
            split = (pa, pb); p = np.zeros(n); kind = 'S'; name = f'split {t[1]} | {t[2]}'; uid = None
        else:
            u, p = unit(t); kind = u['kind']; name = t; uid = ALIAS.get(t, t)
        if prev is not None:
            g = PAIR.get((prev[0], uid), GAP.get((prev[1], kind), 5.3))
            n = int(round(g / 0.1)); prof.append(np.zeros(n)); pos += n * 0.1
        if split is not None: LAST_SPLITS.append((pos, split[0], split[1]))
        prof.append(p); items.append((name, pos, pos + len(p) * 0.1, float(max(p.max(), *(q.max() for q in split)) if split else p.max()))); pos += len(p) * 0.1
        prev = (uid, kind)
    return np.concatenate(prof), items
