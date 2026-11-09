"""Vue de dessus + objets posés (couleur par objet) -> paris2026/apercu/vue_dessus_objets.png
  py -3.15 -I paris2026/vue_objets.py"""
import os
import sys
import re
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "scripts"))
import build_paris as B   # noqa: E402

T = os.path.join(ROOT, "tracks", "USLAND2026SupercrossParis")
im = Image.open(os.path.join(HERE, "apercu", "vue_dessus.png")).convert("RGB")
dims = B.arena_dims(); floor = B.mx_poly(dims.floor_outline(1.0)); S = 0.28975; k = 1 / (S * 4)
xs, zs = floor[:, 0] * k, floor[:, 1] * k
box = (int(xs.min()) - 30, int(zs.min()) - 30, int(xs.max()) + 30, int(zs.max()) + 30)
W, Hh = box[2] - box[0], box[3] - box[1]
P = lambda x, z: ((W - (x * k - box[0])) * 2, (Hh - (z * k - box[1])) * 2)          # même cadrage que build_paris.top_view
COL = {'bale.jm': ((240, 60, 160), 3, 'tuff block ZION'), 'tuff-bent.jm': ((120, 30, 100), 3, 'gros bloc de virage ZION'),
       'pylon_round.jm': ((255, 255, 255), 6, 'poteau rond (Saint-Georges)'), 'finishbanner.jm': ((0, 0, 0), 7, 'banderole FINISH (ZION)'),
       'flag_cage.jm': ((255, 200, 0), 7, 'cage du drapeau (Saint-Georges)'), 'start_grids.jm': ((90, 90, 90), 7, 'grilles de départ (Saint-Georges)'),
       'start.jm': ((0, 0, 0), 7, 'structure de départ (ZION)'), 'monster1.jm': ((0, 200, 0), 7, 'arche Monster (ZION)'),
       'semi.jm': ((40, 90, 200), 9, 'camion paddock (ZION)'), 'tent_carre.jm': ((230, 230, 230), 6, 'tente paddock (ZION)'),
       'ramp_50.jm': ((20, 20, 20), 6, 'tremplin FMX (acier)')}
d = ImageDraw.Draw(im)
for l in open(os.path.join(T, "statues")):
    m = re.match(r'\[([-\d.]+) [-\d.]+ ([-\d.]+)\] \S+ (\S+)', l)
    if m and m.group(3).split('/')[-1] in COL:
        c, r, _ = COL[m.group(3).split('/')[-1]]; x, y = P(float(m.group(1)), float(m.group(2)))
        d.ellipse([x - r, y - r, x + r, y + r], fill=c, outline=(0, 0, 0))
f = ImageFont.truetype("arial.ttf", 13); y = 6
for name, (c, r, lab) in COL.items():
    d.ellipse([8, y + 2, 18, y + 12], fill=c, outline=(0, 0, 0)); d.text((24, y), lab, fill=(0, 0, 0), font=f); y += 16
im.save(os.path.join(HERE, "apercu", "vue_dessus_objets.png")); print("ok")
