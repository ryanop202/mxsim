"""Embed exported-terrain samples for the 3D viewer (sub-sampled exported heightmap + tile ids + paths)."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, json, base64, numpy as np
sys.path.insert(0, ROOT + '/scripts')
from mxs import Track, parse_gates
import layouts
T = Track(ROOT + '/legacy_mx/tracks/RyanCompoundMX', 'xz'); s = T.s
regions = {'MX': ((0, 1638, 0, 1300), 4, layouts.mx, 'RyanCompoundMX'),
           'SX1': ((10, 600, 1290, 1638), 2, layouts.sx1, 'RyanCompoundSX1'),
           'SX2': ((620, 1190, 1135, 1638), 2, layouts.sx2, 'RyanCompoundSX2')}
out = {}
for k, ((x0, x1, z0, z1), st, fn, folder) in regions.items():
    j0, j1, i0, i1 = [int(round(v / s)) for v in (x0, x1, z0, z1)]
    Hs = T.H[i0:i1 + 1:st, j0:j1 + 1:st]
    hmin, hmax = float(Hs.min()), float(Hs.max())
    q = np.round((Hs - hmin) / (hmax - hmin) * 65535).astype('<u2')
    tl = T.tiles[(np.arange(i0, i1 + 1, st) // 2).clip(0, 2047)][:, (np.arange(j0, j1 + 1, st) // 2).clip(0, 2047)].astype(np.uint8)
    p = fn(); smp = p.samples(3.0)
    G = parse_gates(f'{ROOT}/legacy_mx/tracks/{folder}/timing_gates')
    out[k] = dict(w=int(Hs.shape[1]), h=int(Hs.shape[0]), x0=x0, z0=z0, step=st * s, hmin=hmin, hmax=hmax,
                  hb64=base64.b64encode(q.tobytes()).decode(), tb64=base64.b64encode(tl.tobytes()).decode(),
                  path=np.round(np.c_[smp['x'], smp['z']], 1).ravel().tolist(), lap_ft=round(p.s),
                  gates=[[round(g[0], 1), round(g[2], 1)] for g in G['start']])
js = 'const TERRAIN=' + json.dumps(out, separators=(',', ':')) + ';'
open(ROOT + '/legacy_mx/deliver/web/terrain_data.js', 'w').write(js)
print(len(js) / 1e6, 'MB', {k: (v['w'], v['h'], v['step']) for k, v in out.items()})
