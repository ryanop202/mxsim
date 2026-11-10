"""Profils de côté de chaque couloir (hauteur lue dans le terrain exporté, sur l'axe du couloir), échelle réelle (1:1).
  py -3.15 -I paris2026/profils.py -> paris2026/apercu/profils.png"""
import os
import sys
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "scripts"))
import layout_paris as LP   # noqa: E402
import layouts_sx as LS     # noqa: E402

T = os.path.join(ROOT, "tracks", "USLAND2026SupercrossParis")
n, s, hmin, hmax = open(os.path.join(T, "terrain.hf")).read().split(); s, hmin, hmax = float(s), float(hmin), float(hmax)
H = np.asarray(Image.open(os.path.join(T, "terrain.png")), np.float64) / 65535 * (hmax - hmin) + hmin
p = LP.paris()
lanes = [g for g in p.segs if g['kind'] == 'S' and g['sections']]
fig, axs = plt.subplots(len(lanes), 1, figsize=(16, 3.0 * len(lanes)))
for ax, g in zip(axs, lanes):
    u = np.arange(0, g['L'], 0.25)
    x = g['x0'] + u * np.cos(g['t']); z = g['z0'] + u * np.sin(g['t'])
    h = H[np.clip(np.round(z / s).astype(int), 0, H.shape[0] - 1), np.clip(np.round(x / s).astype(int), 0, H.shape[1] - 1)]
    ax.fill_between(u, 0, h, color=(0.62, 0.45, 0.30)); ax.plot(u, h, color=(0.35, 0.22, 0.12), lw=1)
    for prof, u0, name in g['sections']:
        for it in LS.COMBOS[name]['items']:
            a, b = u0 + it[1], u0 + it[2]
            ax.text((a + b) / 2, max(h[(u >= a) & (u <= b)].max() if ((u >= a) & (u <= b)).any() else 0, 0) + 0.6,
                    it[0].split(' (')[0].replace('Arlington_', 'A').replace('Custom1_', 'C1').replace('Custom_', 'C'),
                    ha='center', fontsize=7)
        if name == LP.FINISH_SEC:
            it = LS.COMBOS[name]['items'][LP.start(p)['finish'][1]]; i0, i1 = int(it[1] / 0.1), int(it[2] / 0.1)
            uc = u0 + it[1] + float(np.argmax(prof[i0:i1])) * 0.1
            ax.axvline(uc, color='k', ls='--', lw=1); ax.text(uc, 19.5, 'ARRIVÉE', fontsize=8, ha='center')
    ax.set_xlim(0, g['L']); ax.set_ylim(0, 23); ax.set_aspect('equal'); ax.set_yticks([0, 5, 10, 15, 20])
    ax.set_title("%s  (%.0f ft, sens de course de gauche à droite)" % (g['tag'], g['L']), fontsize=10, loc='left')
axs[-1].set_xlabel("ft depuis la sortie du virage")
plt.tight_layout()
os.makedirs(os.path.join(HERE, "apercu"), exist_ok=True)
plt.savefig(os.path.join(HERE, "apercu", "profils.png"), dpi=110)
print("ok")
