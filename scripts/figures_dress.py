"""Top view of the habillage (statues, decals, flaggers) read back from the exported SX1 folder (names.FOLDERS)."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
import sys, re, numpy as np
sys.path.insert(0, ROOT + '/scripts')
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from mxs import Track, parse_gates

from names import FOLDERS
D = ROOT + '/tracks/' + FOLDERS['SX1']; OUT = ROOT + '/viewer/figures'
T = Track(D, 'xz'); Hs = T.H[::3, ::3]; s = T.s * 3
gz, gx = np.gradient(Hs, s); sh = np.clip(0.55 - 0.35 * gx - 0.35 * gz, 0, 1)
num = lambda l: [float(v) for v in re.findall(r'-?\d+\.?\d*', l.split('@')[0])]
st = [(num(l), l.split()[4].split('/')[-1].replace('.jm', '')) for l in open(D + '/statues') if l.strip()]
dc = [(num(l), l.split()[-1].split('/')[-1].replace('.png', '')) for l in open(D + '/decals') if l.strip()]
COL = {'track': '#c08040', 'sand': '#e8d090', 'gravel': '#777777', 'single': '#ff9900', 'whoops': '#00cc66', 'table': '#3399ff',
       'tripleface': '#ff3333', 'triplemiddle': '#aa0000', '90': '#cc66ff', '180': '#9933cc', 'Tearoff': '#ff66cc'}
MK = {'tuff_usland': ('s', '#ff8800', 40), 'chainlink': ('|', 'k', 18), 'lightpole': ('*', 'yellow', 120), '2': ('o', '#ff3300', 70), 'transit': ('s', 'blue', 40),
      'watertruck': ('s', 'cyan', 40), 'watertank': ('s', 'teal', 60), 'semi_1': ('s', 'navy', 70), 'matrixa2': ('^', 'red', 50),
      'ezup': ('^', 'pink', 50), 'dozer': ('D', 'gold', 50), 'bobcat': ('D', 'khaki', 40)}

def draw(ax, crop=None, small=False):
    ax.imshow(sh, cmap='gray', extent=[0, T.size, T.size, 0], vmin=0, vmax=1)
    road = np.ma.masked_where(T.tiles != 8, np.ones(T.tiles.shape)); ax.imshow(road, cmap='Blues', vmin=0, vmax=1.5, alpha=0.45, extent=[0, T.size, T.size, 0])
    sandt = np.ma.masked_where(~np.isin(T.tiles, (4, 5, 6, 7)), np.ones(T.tiles.shape)); ax.imshow(sandt, cmap='YlOrBr', vmin=0, vmax=3, alpha=0.4, extent=[0, T.size, T.size, 0])
    for tex, c in COL.items():
        pts = np.array([p[:2] for p, t in dc if t == tex])
        if len(pts): ax.scatter(pts[:, 0], pts[:, 1], s=(1 if tex in ('track', 'sand', 'gravel', 'Tearoff') else 25), c=c, alpha=0.5 if tex in ('track', 'sand') else 0.9,
                                marker='.' if tex in ('track', 'sand', 'gravel', 'Tearoff') else 'x', label=f'decal {tex}')
    for m, (mk, c, sz) in MK.items():
        pts = np.array([[p[0], p[2]] for p, t in st if t == m])
        if len(pts): ax.scatter(pts[:, 0], pts[:, 1], marker=mk, c=c, s=sz if not small else sz / 3, label=m, edgecolors='k', linewidths=0.3)
    for key, folder in FOLDERS.items():
        G = parse_gates(ROOT + f'/tracks/{folder}/timing_gates'); g = np.array([x[:3] for x in G['start']])
        ax.plot(g[:, 0], g[:, 2], 'r', lw=3)
        fl = [num(l) for l in open(ROOT + f'/tracks/{folder}/flaggers') if l.startswith('[')][:3]
        ax.scatter([f[0] for f in fl], [f[2] for f in fl], marker='P', c='lime', s=60, edgecolors='k')
    if crop: ax.set_xlim(crop[0], crop[1]); ax.set_ylim(crop[3], crop[2])
    else: ax.set_xlim(0, T.size); ax.set_ylim(T.size, 0)

fig, ax = plt.subplots(figsize=(16, 16)); draw(ax)
ax.set_title('Habillage v11 : routes béton (bleu), tuff blocks USLAND (carrés orange), cônes (ronds orange), grillages (|), poteaux (*), paddock, grilles (rouge), drapeaux (+), decals')
h, l = ax.get_legend_handles_labels(); ax.legend(h, l, loc='upper left', fontsize=8, ncol=2, markerscale=1.5)
plt.tight_layout(); plt.savefig(OUT + '/05_habillage.jpg', dpi=70, pil_kwargs=dict(quality=82)); plt.close()
for nm, crop in (('SX1', (0, 600, 0, 480)), ('SX2', (560, 1060, 0, 560)), ('SX3', (180, 1080, 600, 1080))):
    fig, ax = plt.subplots(figsize=(14, 12)); draw(ax, crop=crop)
    ax.set_title(f'Habillage {nm} (zoom)'); plt.tight_layout(); plt.savefig(OUT + f'/05_habillage_{nm}.jpg', dpi=80, pil_kwargs=dict(quality=82)); plt.close()
print('figures ok', len(st), 'statues', len(dc), 'decals')
