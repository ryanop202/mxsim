import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
sys.path.insert(0, ROOT + '/scripts'); from mxs import Track, parse_gates
from matplotlib.colors import LightSource
name, folder, out = sys.argv[1], sys.argv[2], sys.argv[3]
crop = [float(v) for v in sys.argv[4].split(',')] if len(sys.argv) > 4 else None
T = Track(folder, 'xz'); G = parse_gates(folder + '/timing_gates')
fig, ax = plt.subplots(1, 2, figsize=(20, 10))
ls = LightSource(azdeg=315, altdeg=35)
step = max(1, T.N // 2048)
Hs = T.H[::step, ::step]
rgb = ls.shade(Hs, cmap=plt.cm.terrain, vert_exag=2.0 / (T.s * step), blend_mode='overlay')
ext = [0, T.size, T.size, 0]
ax[0].imshow(rgb, extent=ext)
ax[1].imshow(T.tiles, extent=ext, cmap='tab20', interpolation='nearest')
for a in ax:
    for i, cp in enumerate(G['cps']):
        L, x, y, z, dx, dy, dz = cp[:7]
        a.plot([x - dx, x + dx], [z - dz, z + dz], 'r-', lw=1.5); a.text(x, z, str(i), color='yellow', fontsize=8)
    for g in T.gradients:
        a.plot([g['a'][0], g['b'][0]], [g['a'][1], g['b'][1]], 'c-', lw=0.6)
    if G['start']:
        st = np.array([s[:3] for s in G['start']]); a.plot(st[:, 0], st[:, 2], 'm.', ms=3)
    if crop: a.set_xlim(crop[0], crop[1]); a.set_ylim(crop[3], crop[2])
ax[0].set_title(f'{name} hillshade (x right, z down) + checkpoints(red) + gradients(cyan)'); ax[1].set_title('tilemap')
plt.tight_layout(); plt.savefig(out, dpi=80)
