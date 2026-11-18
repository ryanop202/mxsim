"""Aperçus (rendu logiciel rendu_objets.py, PAS le jeu) des objets v21 de la version Zion : ballot en U, arche 50 Factory, et un virage
avec son mur bâché + filets + ballots, sur le vrai terrain construit.  -> paris2026/apercu_zion/v21_*.png"""
import os
import re
import sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
os.environ['PARIS_ZION'] = '1'
import rendu_objets as RO      # noqa: E402

T = os.path.join(ROOT, "tracks", "USLAND2026SupercrossParisZion"); RO.T = T; RO.D = os.path.join(T, "statue", "deco")
AP = os.path.join(HERE, "apercu_zion")


def flat(sc):
    g = np.ones((2, 2, 4)); g[..., :3] = np.array([166, 113, 68]) / 255
    sc.add([(-80, -0.01, -90), (80, -0.01, -90), (80, -0.01, 60), (-80, -0.01, 60)], [(0, 1, 0)] * 4, np.zeros((4, 2)), [(0, 2, 1), (0, 3, 2)], g)


def pair(name, tex, views, W=700, H=460):
    ims = []
    for eye, tgt in views:
        sc = RO.Scene(); flat(sc); sc.add_jm(name, tex); ims.append(sc.render(eye, tgt, W, H))
    out = Image.new('RGB', (W * len(ims), H))
    for k, im in enumerate(ims):
        out.paste(im, (k * W, 0))
    return out


def deco_lines():
    out = []
    for l in open(os.path.join(T, "statues")):
        m = re.match(r'\[([-\d.]+) ([-\d.]+) ([-\d.]+)\] ([-\d.]+) @\S+?/statue/deco/(\S+) @\S+?/statue/deco/(\S+)', l)
        if m:
            out.append((float(m.group(1)), float(m.group(3)), float(m.group(4)), m.group(5), m.group(6)))
    return out


if __name__ == "__main__":
    pair('bale_u.jm', 'bale_u_noir.png', [((5, 3.5, 7), (0, 1, 0)), ((-7, 2.0, -3), (0, 1, 0))]).save(os.path.join(AP, 'v21_ballot_u.png'))
    import deco_v21 as DV
    DV.bale_u(RO.D, 'honda')
    pair('bale_u.jm', 'bale_u_honda.png', [((5, 3.5, 7), (0, 1, 0)), ((-6, 2.5, -6), (0, 1, 0))]).save(os.path.join(AP, 'v21_ballot_u_honda.png'))
    pair('arche_50f.jm', 'arche_50f.png', [((10, 7, -55), (0, 8, 0)), ((40, 10, 30), (0, 8, 0))]).save(os.path.join(AP, 'v21_arche_50.png'))
    import layout_paris as LP
    p = LP.paris(); L_ = deco_lines()
    for tag in ('T1 1', 'T_TR'):
        g = next(g for g in p.segs if g['tag'].startswith(tag)); sg = 1.0 if g['ang'] > 0 else -1.0; th_in = g['t0'] + sg * np.pi / 2
        sc = RO.Scene(); h = RO.terrain_patch(sc, g['cx'] - 75, g['cx'] + 75, g['cz'] - 75, g['cz'] + 75, 1.5)
        for x, z, a, mdl, tex in L_:
            if abs(x - g['cx']) < 75 and abs(z - g['cz']) < 75:
                sc.add_jm(mdl, tex, x, 0.0, z, a, ground=h(x, z))
        ims = []
        for f_eye, f_tgt in ((0.75, 0.25), (0.0, 0.4)):
            te, tt = th_in - np.radians(g['ang']) * f_eye, th_in - np.radians(g['ang']) * f_tgt
            e = (g['cx'] + np.cos(te) * (g['r'] - 2), g['cz'] + np.sin(te) * (g['r'] - 2)); t = (g['cx'] + np.cos(tt) * (g['r'] + 22), g['cz'] + np.sin(tt) * (g['r'] + 22))
            ims.append(sc.render((e[0], h(*e) + 6, e[1]), (t[0], h(*t) + 4, t[1]), 700, 460))
        out = Image.new('RGB', (1400, 460)); out.paste(ims[0], (0, 0)); out.paste(ims[1], (700, 0))
        out.save(os.path.join(AP, 'v21_virage_%s.png' % tag.strip().replace(' ', '')))
        print(tag)
