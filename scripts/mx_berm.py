"""Store the measured MX berm template (single measured Desert Sand turn, R=22 ft, wall 47 deg)."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import json, numpy as np
D = json.load(open(ROOT + '/analysis/mxfeat_Desert.json')); t = np.arange(-50, 50.01, 0.25)
for tr in D['turns']:
    if abs(tr['x'] - 718) < 1 and abs(tr['z'] - 398) < 1:
        xs = np.array(tr['xs']); L = xs[(t < 0) & (t > -35)]; R = xs[(t > 0) & (t < 35)]
        full = xs if R.max() > L.max() else xs[::-1]; o = full[t >= 0][:int(45 / 0.25)]
lib = json.load(open(ROOT + '/lib/library.json'))
lib['mx_berm'] = dict(src='JGMXDesertSand turn at (718,398), R=22 ft, wall 47 deg', step=0.25, prof=np.round(o - o[0], 3).tolist(),
                      note='outward cross-section from the decal-traced centreline (single measured turn, not averaged)')
json.dump(lib, open(ROOT + '/lib/library.json', 'w'), default=float); print('mx_berm stored')
