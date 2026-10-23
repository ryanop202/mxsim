"""Recover MX reference lap centerline: least-cost path between consecutive checkpoints over on-track decal coverage."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, re, json, numpy as np; sys.path.insert(0,ROOT + '/scripts')
from mxs import *; from skimage.graph import route_through_array
from scipy.ndimage import gaussian_filter, distance_transform_edt, uniform_filter1d
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
f, tex, name = sys.argv[1], sys.argv[2], sys.argv[3]
T = Track(f, 'xz'); G = parse_gates(f + '/timing_gates')
cell = 2.0; n = int(T.size / cell) + 1
D = np.array([[float(v) for v in re.findall(r'-?\d+\.?\d*', l.split('@')[0])] for l in open(f + '/decals') if tex in l])
mask = np.zeros((n, n), bool)
for x, z, ang, size, *_ in D:
    if 0 <= x < T.size and 0 <= z < T.size:
        r = size / 2 / cell; ci, cj = int(z / cell), int(x / cell); R = int(r) + 1
        yy, xx = np.ogrid[-R:R + 1, -R:R + 1]; disk = xx**2 + yy**2 <= r * r
        i0, j0 = max(0, ci - R), max(0, cj - R); i1, j1 = min(n, ci + R + 1), min(n, cj + R + 1)
        mask[i0:i1, j0:j1] |= disk[i0 - (ci - R):i1 - (ci - R), j0 - (cj - R):j1 - (cj - R)]
# prefer the middle of the decal band
dist = distance_transform_edt(mask)
cost = np.where(mask, 1.0 / (1 + dist), 60.0)
C = np.array([[c[1], c[3]] for c in G['cps']]); lap = G['normal']
path = []
for k in range(len(lap)):
    a, b = C[lap[k]], C[lap[(k + 1) % len(lap)]]
    ia = (int(np.clip(a[1] / cell, 0, n - 1)), int(np.clip(a[0] / cell, 0, n - 1)))
    ib = (int(np.clip(b[1] / cell, 0, n - 1)), int(np.clip(b[0] / cell, 0, n - 1)))
    p, _ = route_through_array(cost, ia, ib, fully_connected=True, geometric=True)
    path += p[:-1]
P = np.array(path, float)[:, ::-1] * cell  # x,z
# resample at 1 ft and smooth
s = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
ss = np.arange(0, s[-1], 1.0)
X = np.interp(ss, s, P[:, 0]); Z = np.interp(ss, s, P[:, 1])
X = uniform_filter1d(X, 9, mode='wrap'); Z = uniform_filter1d(Z, 9, mode='wrap')
L = np.r_[0, np.cumsum(np.hypot(np.diff(X), np.diff(Z)))]
H = T.h(X, Z)
json.dump(dict(x=X.tolist(), z=Z.tolist(), s=L.tolist(), h=H.tolist()), open(f'{ROOT}/analysis/centerline_{name}.json', 'w'))
print(name, 'lap length ft', round(L[-1]), 'm', round(L[-1] * 0.3048), 'decal coverage cells', mask.sum())
fig, ax = plt.subplots(figsize=(12, 12))
from matplotlib.colors import LightSource
st = max(1, T.N // 2048); ls = LightSource(315, 35)
ax.imshow(ls.shade(T.H[::st, ::st], plt.cm.gray, vert_exag=2.0 / (T.s * st), blend_mode='hsv'), extent=[0, T.size, T.size, 0])
ax.imshow(np.ma.masked_where(~mask, mask), extent=[0, T.size, T.size, 0], alpha=0.25, cmap='autumn')
ax.plot(X, Z, 'c-', lw=1); ax.plot(C[lap, 0], C[lap, 1], 'r.', ms=5)
plt.savefig(f'{ROOT}/analysis/centerline_{name}.png', dpi=70, bbox_inches='tight')
