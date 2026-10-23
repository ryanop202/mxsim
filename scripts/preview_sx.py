"""Preview + geometric checks for the v2 SX layouts (renders each track alone)."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, numpy as np; sys.path.insert(0, ROOT + '/scripts')
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
from engine import Grid, render_lane_block, render_berm_stamp, turn_mid_angle, LIB, render_stamp
import layouts_sx as LS
from scipy.spatial import cKDTree
S_GRID = 0.28975
def render(p, G):
    blocks = np.zeros_like(G.H); berms = np.zeros_like(G.H); log = []
    for g in p.segs:
        if g['kind'] == 'S':
            for prof, u0, name in g['sections']:
                render_lane_block(G, blocks, g, prof, u0, LIB['sx_lateral']['top_width'])
                end = u0 + len(prof) * 0.1; log.append((g['tag'], name, u0, end, g['L'], 'OK' if (u0 >= 0 and end <= g['L'] + 0.01) else 'OVERRUN'))
        elif g['kind'] == 'P': render_stamp(G, berms, None, g, {})
        elif g.get('berm'): render_berm_stamp(G, berms, g['berm'], g['cx'], g['cz'], turn_mid_angle(g))
    return blocks, berms, log
if __name__ == '__main__':
    name = sys.argv[1]; p = getattr(LS, name)(); G = Grid(11, S_GRID)
    blocks, berms, log = render(p, G); H = np.maximum(blocks, berms)
    smp = p.samples(1.0); x, z = smp['x'], smp['z']
    print(f'{name}: lap {p.s:.0f} ft, closure {np.hypot(p.x - x[0], p.z - z[0]):.2f} ft, heading {np.degrees(p.t) % 360:.1f}')
    for r in log: print('   %-34s %-48s u0=%6.1f end=%6.1f / %6.1f %s' % r)
    ov = ((blocks > 0.3) & (berms > 0.3)).sum() * G.s ** 2; print(f'   block/berm overlap {ov:.1f} ft2')
    tr = cKDTree(np.c_[x, z]); pr = tr.query_pairs(38.0, output_type='ndarray')
    far = np.abs(smp['s'][pr[:, 0]] - smp['s'][pr[:, 1]]); far = np.minimum(far, p.s - far); bad = pr[far > 140]
    print(f'   close pairs: {len(bad)}; bbox x[{x.min()-55:.0f},{x.max()+55:.0f}] z[{z.min()-55:.0f},{z.max()+55:.0f}] (terrain {G.size:.1f})')
    pad = 60; bx0, bx1, bz0, bz1 = max(x.min() - pad, 0), min(x.max() + pad, G.size), max(z.min() - pad, 0), min(z.max() + pad, G.size)
    j0, j1, i0, i1 = [int(v / G.s) for v in (bx0, bx1, bz0, bz1)]
    fig, ax = plt.subplots(figsize=(16, 16 * (bz1 - bz0) / (bx1 - bx0)))
    ax.imshow(LightSource(300, 40).hillshade(H[i0:i1, j0:j1], vert_exag=3 / G.s), cmap='gray', extent=[bx0, bx1, bz1, bz0])
    ax.imshow(np.ma.masked_less(H[i0:i1, j0:j1], 0.2), cmap='terrain', alpha=.4, extent=[bx0, bx1, bz1, bz0], vmin=0, vmax=12)
    ax.plot(x, z, 'r-', lw=.8)
    for k in range(0, len(x) - 2, 60): ax.annotate('', xy=(x[k + 1], z[k + 1]), xytext=(x[k], z[k]), arrowprops=dict(arrowstyle='->', color='r'))
    for g in p.segs:
        if g['kind'] == 'S' and g['tag']: ax.text(g['x0'] + g['L'] / 2 * np.cos(g['t']), g['z0'] + g['L'] / 2 * np.sin(g['t']) - 9, g['tag'], color='blue', fontsize=8, ha='center')
    if len(bad): ax.plot(x[bad.ravel()], z[bad.ravel()], 'mx', ms=3)
    st = LS.STARTS[p.name]; gx, gz = st['gate']; h = np.radians(st['heading']); f = np.array([np.cos(h), np.sin(h)]); n = np.array([-f[1], f[0]])
    offs = (np.arange(LS.N_GATES) - (LS.N_GATES - 1) / 2) * LS.GATE_PITCH
    G0 = np.array([gx, gz]) + offs[:, None] * n
    ax.plot(G0[:, 0], G0[:, 1], 'ys', ms=3, mec='k')
    M = np.array(st['merge'])
    for o in offs[[0, -1]]:
        a = np.array([gx, gz]) + o * n; b = a + f * st['straight']; c = M + np.sign(o) * 12 * n
        ax.plot([a[0], b[0], c[0]], [a[1], b[1], c[1]], 'y--', lw=1)
    plt.savefig(f'{ROOT}/analysis/pv2_{name}.png', dpi=55, bbox_inches='tight')
