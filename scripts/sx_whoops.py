"""Whoops variants: every WhoopsV2-tile region of the JGSX references, sampled along the axis fitted through its whoops."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, json, numpy as np; sys.path.insert(0, ROOT + '/scripts')
from mxs import *; from scipy import ndimage as ndi; from scipy.signal import find_peaks
R = REF + '/JGSX2026TestTracks/'
COMP = json.load(open(ROOT + '/lib/sx_components.json'))
out = {}
for ref in ['JGSX2026Detroit', 'JGSX2026Custom', 'JGSX2026Glendale', 'JGSX2026Custom1']:
    T = Track(R + ref, 'xz'); ti = parse_tileinfo(R + ref + '/tileinfo'); tm = T.tiles
    wid = [i for i, t in enumerate(ti) if t.get('name') == 'WhoopsV2'][0]
    lab, n = ndi.label(ndi.binary_closing(tm == wid, iterations=3))
    for k, sl in enumerate(ndi.find_objects(lab)):
        area = (lab[sl] == k + 1).sum()
        if area < 500: continue
        x0, x1 = sl[1].start * 2 * T.s, sl[1].stop * 2 * T.s; z0, z1 = sl[0].start * 2 * T.s, sl[0].stop * 2 * T.s
        W = [c for c in COMP if c['ref'] == ref and x0 - 5 < c['cx'] < x1 + 5 and z0 - 5 < c['cz'] < z1 + 5 and c['hmax'] < 3.6 and c['npeaks'] == 1]
        if len(W) < 4: continue
        P = np.array([[c['cx'], c['cz']] for c in W]); P0 = P.mean(0); _, _, Vt = np.linalg.svd(P - P0); ax = Vt[0]
        t = (P - P0) @ ax; A = P0 + ax * (t.min() - 45); B = P0 + ax * (t.max() + 45)
        d, h = T.line(*A, *B, step=0.1); h = np.clip(h - np.median(T.H), 0, None)
        G = parse_gates(R + ref + '/timing_gates'); C = np.array([[c_[1], c_[3]] for c_ in G['cps']]); lap = G['normal']
        nrm = np.array([-ax[1], ax[0]])
        on = [(j, (C[i] - A) @ ax) for j, i in enumerate(lap) if abs((C[i] - A) @ nrm) < 18 and 0 < (C[i] - A) @ ax < d[-1]]
        dirn = sum(np.sign(b2 - b1) for (j1, b1), (j2, b2) in zip(on, on[1:]) if j2 == j1 + 1)
        if dirn < 0: h = h[::-1]
        nz = np.nonzero(h > 0.05)[0]; p = h[max(nz.min() - 20, 0):nz.max() + 21]
        pk, pr = find_peaks(p, prominence=0.8, distance=60)
        pitch = np.diff(pk) * 0.1; heights = p[pk]
        key = f'{ref[8:]}_{k}'
        out[key] = dict(ref=ref, axis_from=len(W), dir=int(np.sign(dirn)), prof=np.round(p, 3).tolist(), n=len(pk), heights=np.round(heights, 2).tolist(),
                        pitch=np.round(pitch, 1).tolist(), length=len(p) * 0.1, bbox=[x0, x1, z0, z1])
        print(f"{key:12s} {len(W)} whoops blocks, n={len(pk)}, H {heights.min():.2f}-{heights.max():.2f}, pitch {pitch.min():.1f}-{pitch.max():.1f} (median {np.median(pitch):.1f}), length {len(p)*0.1:.0f} ft, dir {dirn:+.0f}")
json.dump(out, open(ROOT + '/lib/sx_whoops.json', 'w'))
