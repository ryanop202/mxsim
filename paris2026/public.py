"""Public dans les tribunes du stade (étape 4, « refaire le stade beau ») : les silhouettes de Saint-Thibéry
(tracks/USLAND2026SaintThiberybyBazo/billboard/crowd_Crowd*.png), en billboards, assises rang par rang.

Rangs : bowl.tier_profile (tribune basse 24 rangs, tribune haute ses 12 premiers rangs - au moins 14 partout), sur le contour du
sol de l'arène AGRANDIE ; une personne tous les ~1,6 m (~3 sièges), 15 % de places vides, rien dans les escaliers (axes tous les
8 m). Hauteur du billboard = assis (4,2 ft), posé sur le rang (y = hauteur du rang). Billboards : [x y z] taille rapport @image.
"""
import os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STT_BB = os.path.join(ROOT, "tracks", "USLAND2026SaintThiberybyBazo", "billboard")
NAMES = ['Crowd1', 'Crowd2', 'Crowd3', 'Crowd4', 'Crowd5', 'Crowd6', 'Crowd8', 'Crowd9']
SEATED_FT = 4.2
STEP_M = 1.6
EMPTY = 0.15


def sprites(out, folder):
    """silhouettes recadrées sur leur contour (rapport largeur / hauteur exact) -> <piste>/billboard/."""
    os.makedirs(os.path.join(out, "billboard"), exist_ok=True); asp = {}
    for n in NAMES:
        im = Image.open(os.path.join(STT_BB, "crowd_%s.png" % n)).convert("RGBA")
        a = np.asarray(im)[..., 3]; ys, xs = np.nonzero(a > 20)
        im = im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
        im.save(os.path.join(out, "billboard", "crowd_%s.png" % n)); asp[n] = im.size[0] / im.size[1]
    return asp


def build(out, folder, arena_to_mx, FT):
    import sys
    sys.path.insert(0, os.path.join(ROOT, "stade_paris", "src"))
    from arena import bowl
    asp = sprites(out, folder)
    ref = bowl.floor_ref(); S = ref.length
    aisles = bowl.segments(ref)
    rng = np.random.default_rng(77); lines = []
    tiers = [(bowl.LOWER, bowl.LOWER['rows']), (bowl.UPPER, 12)]
    for tier, nrows in tiers:
        d, z = bowl.tier_profile(tier, nrows)
        for k in range(nrows):
            dk = (d[k] + d[k + 1]) / 2 + 0.15; zk = z[k]
            ss = np.arange(0.4, S - 0.4, STEP_M) + rng.uniform(-0.25, 0.25, int(np.ceil((S - 0.8) / STEP_M)))[:len(np.arange(0.4, S - 0.4, STEP_M))]
            for s in ss:
                if np.min(np.abs(aisles - s)) < 0.9 or rng.random() < EMPTY:
                    continue
                p, _ = ref.at(s, dk)
                x, zz = arena_to_mx(p[0], p[1])
                n = NAMES[rng.integers(len(NAMES))]; h = SEATED_FT * rng.uniform(0.92, 1.06)
                lines.append("[%.4f %.4f %.4f] %.4f %.4f @%s/billboard/crowd_%s.png" % (x, zk * FT + 0.2, zz, h, asp[n], folder, n))
    return lines
