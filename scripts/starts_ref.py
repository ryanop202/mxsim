"""How the JGSX references build their start: gate row, start straight, where the lap joins, first-lap-only gates."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, numpy as np; sys.path.insert(0, ROOT + '/scripts')
from mxs import Track, parse_gates
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
R = REF + '/JGSX2026TestTracks/'
refs = ['JGSX2026Detroit', 'JGSX2026Custom', 'JGSX2026Arlington', 'JGSX2026Glendale', 'JGSX2026Custom1']
fig, axs = plt.subplots(len(refs), 1, figsize=(16, 10 * len(refs)))
for ax, r in zip(axs, refs):
    T = Track(R + r, 'xz'); G = parse_gates(R + r + '/timing_gates')
    st = np.array([g[:4] for g in G['start']]); C = G['cps']
    first_only = [i for i in G['first'] if i not in G['normal']]; lap_only = [i for i in G['normal'] if i not in G['first']]
    print(f"{r[8:]}: {len(st)} gates x={st[:,0].min():.0f}-{st[:,0].max():.0f} z={st[:,2].min():.0f}-{st[:,2].max():.0f} pitch {np.median(np.diff(st[:,2])):.1f} ft, angle {st[0,3]:.3f}")
    print('   first lap', G['first']); print('   normal lap', G['normal']); print('   first-only', first_only, 'lap-only', lap_only)
    for i in G['first'][:3]: L, x, y, z, dx, dy, dz = C[i][:7]; print(f'   cp{i}: ({x:.0f},{z:.0f}) half {L:.1f}')
    hs = LightSource(300, 40).hillshade(T.H, vert_exag=3 / T.s)
    ax.imshow(hs, cmap='gray', extent=[0, T.size, T.size, 0])
    for i, c in enumerate(C):
        L, x, y, z, dx, dy, dz = c[:7]
        col = 'orange' if i in first_only else ('cyan' if i in lap_only else 'magenta')
        ax.plot([x - dx, x + dx], [z - dz, z + dz], color=col, lw=1.5); ax.text(x, z, str(i), color='red', fontsize=8)
    ax.plot(st[:, 0], st[:, 2], 'ys', ms=3); ax.set_title(f'{r}: orange=1er tour seulement, cyan=tours suivants seulement, magenta=les deux')
    ax.set_xlim(0, 620); ax.set_ylim(480, 60)
plt.tight_layout(); plt.savefig(ROOT + '/analysis/starts_ref.png', dpi=45)
