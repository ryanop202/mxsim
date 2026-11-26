"""Profils de côté (version Zion), un fichier par couloir, échelle réelle 1:1, hauteur et angles de chaque bosse.
  PARIS_ZION=1 python -I pistes/paris-2026/profils_zion.py L1 LR ... -> pistes/paris-2026/apercu_zion/profils_v21d/profil_<tag>.png"""
import os, sys
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "commun/scripts"))
os.environ['PARIS_ZION'] = '1'
import layout_paris as LP   # noqa: E402

T = os.path.join(ROOT, "tracks", "USLANDParis")
OUT = os.path.join(HERE, "apercu_zion", "profils_v21d"); os.makedirs(OUT, exist_ok=True)
n, s, hmin, hmax = open(os.path.join(T, "terrain.hf")).read().split(); s, hmin, hmax = float(s), float(hmin), float(hmax)
H = np.asarray(Image.open(os.path.join(T, "terrain.png")), np.float64) / 65535 * (hmax - hmin) + hmin
p = LP.paris()
segs = p.segs
FMX = LP.fmx_ramps()


def sample(g, du=0.25):
    u = np.arange(0, g['L'], du)
    x = g['x0'] + u * np.cos(g['t']); z = g['z0'] + u * np.sin(g['t'])
    from scipy.ndimage import map_coordinates
    h = map_coordinates(H, [z / s, x / s], order=1)
    return u, x, z, h - np.percentile(h, 5)


def bumps(u, h, thr=0.8):
    """Bosses = zones au-dessus de thr ft ; renvoie (début, crête, fin, hauteur, angle montée, angle descente)."""
    on = h > thr; out = []; i = 0
    while i < len(u):
        if on[i]:
            j = i
            while j < len(u) and on[j]: j += 1
            a = i
            while a > 0 and h[a - 1] < h[a] and h[a - 1] > 0.05: a -= 1
            b = j - 1
            while b < len(u) - 1 and h[b + 1] < h[b] and h[b + 1] > 0.05: b += 1
            seg = h[a:b + 1]; k = a + int(np.argmax(seg))
            d = np.degrees(np.arctan(np.gradient(h, u)))
            out.append((u[a], u[k], u[b], h[k], d[a:k + 1].max() if k > a else 0, -d[k:b + 1].min() if b > k else 0))
            i = b + 1
        else:
            i += 1
    return out


def draw(tag):
    g = next(g for g in segs if g['kind'] == 'S' and g['tag'].startswith(tag + ' '))
    i = segs.index(g); nxt = segs[(i + 1) % len(segs)]
    u, x, z, h = sample(g)
    L = g['L']
    sides = any(LP.SPLIT_Z.get(sec[2]) for sec in g['sections'])
    fig, ax = plt.subplots(figsize=(max(14, L / 14), 4.2))
    ax.fill_between(u, -1, h, color=(0.62, 0.45, 0.30)); ax.plot(u, h, color=(0.35, 0.22, 0.12), lw=1)
    if sides:                     # v22 : bosse plus basse d'un côté : profil à 8 ft à gauche (vert) et à droite (violet) de l'axe
        from scipy.ndimage import map_coordinates
        h5 = np.percentile(map_coordinates(H, [z / s, x / s], order=1), 5)
        for vv, col, lab in ((-8.0, (0.1, 0.55, 0.2), 'gauche'), (8.0, (0.55, 0.15, 0.6), 'droite')):
            xs_, zs_ = x - vv * np.sin(g['t']), z + vv * np.cos(g['t'])
            ax.plot(u, map_coordinates(H, [zs_ / s, xs_ / s], order=1) - h5, color=col, lw=1.4, ls='--', label='côté ' + lab)
        ax.legend(loc='upper right', fontsize=8)
    for a, c, b, hh, up, dn in bumps(u, h):
        ax.annotate("%.1f ft" % hh, (c, hh), xytext=(c, hh + 2.4), ha='center', fontsize=10, fontweight='bold')
        ax.text((a + c) / 2 - 1, hh * 0.45, "%.0f°" % up, ha='right', fontsize=9.5, color=(0.05, 0.25, 0.65))
        ax.text((c + b) / 2 + 1, hh * 0.45, "%.0f°" % dn, ha='left', fontsize=9.5, color=(0.70, 0.10, 0.10))
    for f in FMX:     # tremplin freestyle (objet acier, pas dans le terrain) : position projetée sur l'axe du couloir
        lx, lz = f['lip']; uu = (lx - g['x0']) * np.cos(g['t']) + (lz - g['z0']) * np.sin(g['t'])
        off = abs(-(lx - g['x0']) * np.sin(g['t']) + (lz - g['z0']) * np.cos(g['t']))
        if 0 <= uu <= L and off < 25:
            ax.plot([uu - 18.5, uu], [0, 9], color='k', lw=2.5); ax.text(uu - 9, 10.5, "tremplin FMX\n(lèvre 9 ft, à côté de l'appel)", ha='center', fontsize=8)
    ax.set_xlim(0, L); ax.set_ylim(-1, 30); ax.set_aspect('equal'); ax.set_yticks([0, 5, 10, 15, 20, 25])
    ax.set_xticks(np.arange(0, L + 1, 10)); ax.tick_params(labelsize=7); ax.grid(alpha=0.25)
    ax.set_title("%s  (%.0f ft, sens de course de gauche à droite ; échelle réelle)   bleu = angle de montée, rouge = angle de descente ; après : virage %s"
                 % (g['tag'], L, nxt['tag']), fontsize=9.5, loc='left')
    ax.set_xlabel("ft depuis la sortie du virage")
    plt.tight_layout(); fn = os.path.join(OUT, "profil_%s.png" % tag); plt.savefig(fn, dpi=120); plt.close(fig)
    print(fn)


for t in sys.argv[1:]:
    draw(t)
