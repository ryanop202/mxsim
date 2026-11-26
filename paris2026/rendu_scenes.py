"""v9 : vues de vérification de l'habillage SUR le terrain exporté (rendu logiciel rendu_objets.py, pas le jeu).
  py -3.15 -I paris2026/rendu_scenes.py   -> paris2026/apercu/v9_scene_*.png"""
import os
import sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "scripts"))
import rendu_objets as RO     # noqa: E402
import layout_paris as LP     # noqa: E402

p = LP.paris(); st = LP.start(p)
seg = lambda tag: next(g for g in p.segs if g['tag'].startswith(tag))


def P(g, u, v=0.0):
    c, s = np.cos(g['t']), np.sin(g['t']); return np.array([g['x0'] + u * c - v * s, g['z0'] + u * s + v * c])


def view(name, centre, half, shots, step=1.0):
    sc, h = RO.scene_at(centre[0], centre[1], half, step)
    ims = [sc.render((e[0], e[1], e[2]), (t[0], t[1], t[2]), 760, 480) for e, t in shots]
    out = Image.new('RGB', (760 * len(ims), 480))
    for k, im in enumerate(ims):
        out.paste(im, (760 * k, 0))
    out.save(os.path.join(RO.AP, 'v9_scene_%s.png' % name)); print(name)


def xyz(q, y):
    return (float(q[0]), float(y), float(q[1]))


g3 = seg('L3'); gD = seg('T_D'); g1 = seg('L1'); g2 = seg('L2'); gT1 = seg('T1')
# saut du milieu : de l'approche (vue pilote) et de côté (bâche AMV)
c3 = P(g3, 190.0)
view('saut_milieu', c3, 130.0, [(xyz(P(g3, 95.0, 0.0), 7.0), xyz(P(g3, 190.0, 0.0), 14.0)),
                                (xyz(P(g3, 185.0, 75.0), 18.0), xyz(P(g3, 185.0, 0.0), 10.0))])
# 180 après le saut du milieu (un seul virage, un bloc à l'intérieur, ballots + filet)
cD = np.array([gD['cx'], gD['cz']])
view('virage_180_milieu', cD, 90.0, [(xyz(P(g3, g3['L'] - 30.0, 0.0), 6.0), xyz(cD, 2.0)),
                                     (xyz(cD + np.array([25.0, 0.0]), 30.0), xyz(cD - np.array([30.0, 0.0]), 2.0))])
# whoops : boudins FLY alignés
w0 = P(g1, 40.0)
view('whoops', P(g1, 80.0), 110.0, [(xyz(P(g1, 10.0, 0.0), 6.0), xyz(P(g1, 90.0, 0.0), 1.0)),
                                    (xyz(P(g1, 60.0, 45.0), 22.0), xyz(P(g1, 75.0, 0.0), 0.0))])
# L2 : 7 bosses au même écart
view('L2', P(g2, 120.0), 150.0, [(xyz(P(g2, 120.0, -70.0), 14.0), xyz(P(g2, 120.0, 0.0), 2.0))])
# grand virage T1 (ballots Honda + filet)
cT = np.array([gT1['cx'], gT1['cz']])
view('virage_T1', cT, 75.0, [(xyz(cT, 12.0), xyz(cT + 30.0 * np.array([np.cos(np.pi), np.sin(np.pi)]), 3.0)),
                             (xyz(cT + np.array([30.0, 0.0]), 8.0), xyz(cT - np.array([20.0, 0.0]), 3.0))])
# départ (grilles, START, Minerva Oil) vu de derrière les grilles comme la caméra du jeu
G0 = np.array(st['gate']); h0 = np.radians(st['heading']); f0 = np.array([np.cos(h0), np.sin(h0)])
view('depart', G0 + f0 * 30, 110.0, [(xyz(G0 - f0 * 14.0, 7.0), xyz(G0 + f0 * 60.0, 3.0)),
                                      (xyz(G0 + f0 * 70.0 + np.array([-f0[1], f0[0]]) * 30.0, 18.0), xyz(G0, 6.0))])
