"""Croquis (PAS construit) du virage après l'arrivée proposé en v22 : 90° à gauche, bosse basse en sortie, 2e bosse, plateau qui tourne
dans le 2e 90° à gauche, redescente sur la ligne du bas.  -> pistes/paris-2026/apercu_zion/croquis_virage_arrivee.png"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "commun/scripts"))
os.environ['PARIS_ZION'] = '1'
import build_paris as B, layout_paris as LP   # noqa: E402

p = LP.paris(); segs = p.segs
ga = next(g for g in segs if g['tag'].startswith('T_L5a')); gb = next(g for g in segs if g['tag'].startswith('T_L5b'))
s0 = ga['s0']; smp = p.samples(0.5); S_ = smp['s'] - s0
X = lambda s: np.interp(s, S_, smp['x']); Z = lambda s: np.interp(s, S_, smp['z'])
def frame(s):
    x0, z0, x1, z1 = X(s - 0.5), Z(s - 0.5), X(s + 0.5), Z(s + 0.5); t = np.array([x1 - x0, z1 - z0]); t /= np.linalg.norm(t)
    return np.array([X(s), Z(s)]), t, np.array([-t[1], t[0]])
L_a, L_m, L_b = ga['L'], next(g for g in segs if g['tag'].startswith('T_L5 milieu'))['L'], gb['L']
# profil proposé (s depuis l'entrée du 1er 90°) : bosse 1 basse en sortie, bosse 2, plateau dans le 2e 90°, redescente
e1 = L_a; e2 = L_a + L_m; e3 = e2 + L_b
PTS = [(0, 0), (e1 - 7, 0), (e1, 1.9), (e1 + 6, 0.2), (e1 + 10, 0.2), (e1 + 16, 2.8), (e1 + 21, 1.2), (e2 + 1, 1.0), (e2 + 6, 3.0),
       (e3 - 6, 3.0), (e3 + 6, 0.3), (e3 + 12, 0), (e3 + 25, 0)]
s_ = np.arange(0, PTS[-1][0], 0.1); from scipy.ndimage import gaussian_filter1d
h_ = gaussian_filter1d(np.interp(s_, *np.array(PTS).T), 12)

# --- vue de dessus (même cadrage que vue_dessus.png)
im = Image.open(os.path.join(HERE, "apercu_zion", "vue_dessus.png")).convert('RGB')
dims = B.arena_dims(); floor = B.mx_poly(dims.floor_outline(1.0)); S = 0.28975; k = 1 / (S * 4)
xs, zs = floor[:, 0] * k, floor[:, 1] * k; box = (int(xs.min()) - 30, int(zs.min()) - 30, int(xs.max()) + 30, int(zs.max()) + 30)
W, Hh = box[2] - box[0], box[3] - box[1]
P = lambda x, z: ((W - (x * k - box[0])) * 2, (Hh - (z * k - box[1])) * 2)
M = 3                                                                                   # agrandi x3 pour la lisibilité
xs_ = np.array([P(X(s), Z(s)) for s in np.linspace(-40, e3 + 40, 40)])
cb = (int(xs_[:, 0].min()) - 150, int(xs_[:, 1].min()) - 60, int(xs_[:, 0].max()) + 60, int(xs_[:, 1].max()) + 60)
im = im.crop(cb).resize(((cb[2] - cb[0]) * M, (cb[3] - cb[1]) * M), Image.LANCZOS).convert('RGBA')
Q = lambda x, z: ((P(x, z)[0] - cb[0]) * M, (P(x, z)[1] - cb[1]) * M)
ov = Image.new('RGBA', im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov); f = ImageFont.truetype('arialbd.ttf', 26)
def band(sa, sb, col, w=15.0):
    ss = np.linspace(sa, sb, 30); L = []; R = []
    for s in ss:
        c, t, n = frame(s); L.append(Q(*(c - n * w))); R.append(Q(*(c + n * w)))
    d.polygon(L + R[::-1], fill=col, outline=(0, 0, 0, 255))
band(e1 - 7, e1 + 6, (255, 190, 60, 200)); band(e1 + 10, e1 + 21, (240, 120, 30, 210)); band(e2 + 1, e3 + 6, (200, 50, 40, 170))
im = Image.alpha_composite(im, ov).convert('RGB'); d = ImageDraw.Draw(im)
for i, (s, txt) in enumerate(((e1, '1  bosse basse'), (e1 + 16, '2  2e bosse'), ((e2 + e3) / 2, '3  plateau qui tourne'), (e3 + 10, '4  redescend'))):
    c, t, n = frame(s); q = Q(*c); lab = (30, 40 + i * 60)
    d.line([(lab[0] + 300, lab[1] + 16), q], fill=(0, 0, 0), width=3); tb = d.textbbox(lab, txt, font=f)
    d.rectangle([tb[0] - 6, tb[1] - 4, tb[2] + 6, tb[3] + 4], fill=(0, 0, 0)); d.text(lab, txt, font=f, fill=(255, 230, 60))
crop = im
# --- profil déroulé
fig, ax = plt.subplots(figsize=(10, 3.2)); ax.fill_between(s_, 0, h_, color=(0.62, 0.45, 0.30)); ax.plot(s_, h_, color=(0.35, 0.22, 0.12))
for x0, x1, lab in ((0, e1, '1er 90° gauche'), (e1, e2, 'petite ligne droite'), (e2, e3, '2e 90° gauche'), (e3, s_[-1], 'ligne du bas')):
    ax.axvspan(x0, x1, color=(0.9, 0.9, 0.95) if lab.endswith('gauche') else (1, 1, 1), zorder=0); ax.text((x0 + x1) / 2, 6.3, lab, ha='center', fontsize=8)
for s, txt in ((e1, '1'), (e1 + 16, '2'), ((e2 + e3) / 2, '3'), (e3 + 7, '4')):
    ax.text(s, float(np.interp(s, s_, h_)) + 0.6, txt, ha='center', fontsize=11, fontweight='bold', color=(0.8, 0.2, 0.1))
ax.set_xlim(0, s_[-1]); ax.set_ylim(0, 7.5); ax.set_aspect('equal'); ax.set_xlabel("ft le long de la trajectoire, depuis l'entrée du 1er virage (échelle réelle)")
ax.set_title("Proposition : virage après l'arrivée (croquis, pas construit)", fontsize=10, loc='left'); plt.tight_layout()
fn = os.path.join(HERE, "apercu_zion", "_prof.png"); plt.savefig(fn, dpi=110); plt.close(fig)
pr = Image.open(fn).convert('RGB'); os.remove(fn)
w = max(crop.size[0], pr.size[0]); out = Image.new('RGB', (w, crop.size[1] + pr.size[1]), (255, 255, 255))
out.paste(crop, ((w - crop.size[0]) // 2, 0)); out.paste(pr, ((w - pr.size[0]) // 2, crop.size[1]))
out.save(os.path.join(HERE, "apercu_zion", "croquis_virage_arrivee.png")); print('ok', L_a, L_m, L_b)
