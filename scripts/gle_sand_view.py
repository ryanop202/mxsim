import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, numpy as np; sys.path.insert(0, ROOT + '/scripts')
from mxs import Track, parse_gates, parse_tileinfo
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
f = REF + '/JGSX2026TestTracks/JGSX2026Glendale'; T = Track(f, 'xz'); H = T.H - np.median(T.H)
ti = parse_tileinfo(f + '/tileinfo'); names = [t.get('name', '?') for t in ti]
G = parse_gates(f + '/timing_gates')
for nm, (x0, x1, z0, z1) in (('L', (0, 200, 95, 465)), ('R', (400, 575, 235, 420))):
    j0, j1, i0, i1 = [int(v / T.s) for v in (x0, x1, z0, z1)]
    fig, ax = plt.subplots(1, 2, figsize=(22, 11 * (z1 - z0) / (x1 - x0)))
    Hc = H[i0:i1, j0:j1]
    ax[0].imshow(LightSource(300, 40).hillshade(Hc, vert_exag=4 / T.s), cmap='gray', extent=[x0, x1, z1, z0])
    cs = ax[0].contour(np.linspace(x0, x1, Hc.shape[1]), np.linspace(z0, z1, Hc.shape[0]), Hc, levels=np.arange(0.25, 12, 0.5), cmap='viridis', linewidths=0.6)
    ax[0].clabel(cs, fontsize=6, fmt='%.1f')
    tm = T.tiles[int(z0 / (2 * T.s)):int(z1 / (2 * T.s)), int(x0 / (2 * T.s)):int(x1 / (2 * T.s))]
    im = ax[1].imshow(tm, cmap='tab20', extent=[x0, x1, z1, z0], interpolation='nearest', vmin=0, vmax=19)
    u = np.unique(tm); ax[1].set_title(' | '.join(f'{k}:{names[k]}' for k in u), fontsize=8)
    for a in ax:
        for i, c in enumerate(G['cps']):
            L, x, y, z, dx, dy, dz = c[:7]
            if x0 - 20 < x < x1 + 20 and z0 - 20 < z < z1 + 20: a.plot([x - dx, x + dx], [z - dz, z + dz], 'm-'); a.text(x, z, f'cp{i}', color='r', fontsize=9)
        a.set_xlim(x0, x1); a.set_ylim(z1, z0); a.grid(alpha=.3)
    plt.tight_layout(); plt.savefig(f'{ROOT}/analysis/gle_sand_{nm}.png', dpi=60)
    print(nm, 'max H', Hc.max())
