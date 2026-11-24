"""Aperçus v23c (rendu logiciel, PAS le jeu) : murs droits à l'entrée des virages, poteaux, ballots sponsors, bâches Milwaukee / AMV."""
import os, sys, json
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
os.environ['PARIS_ZION'] = '1'
import rendu_objets as RO
import apercu_v21 as A
import layout_paris as LP
T = os.path.join(os.path.dirname(HERE), "tracks", "USLANDParis"); RO.T = T; RO.D = os.path.join(T, "statue", "deco"); A.T = T
AP = os.path.join(HERE, "apercu_zion"); rep = json.load(open(os.path.join(AP, "build_report.json")))['deco_v21']['murs']
p = LP.paris(); L_ = A.deco_lines()


def scene(cx, cz, R=80):
    sc = RO.Scene(); h = RO.terrain_patch(sc, cx - R, cx + R, cz - R, cz + R, 1.0)
    for x, z, a, mdl, tex in L_:
        if abs(x - cx) < R and abs(z - cz) < R:
            sc.add_jm(mdl, tex, x, 0.0, z, a, ground=h(x, z))
    return sc, h


outs = []
for tag in ('T_E', 'T1 1', 'T_Bb'):
    g = next(g for g in p.segs if g['tag'].startswith(tag)); f0, f1 = next(r[2] for r in rep if r[0].startswith(tag[:4]))
    sg = 1.0 if g['ang'] > 0 else -1.0; th_in = g['t0'] + sg * np.pi / 2; th = lambda f: th_in - np.radians(g['ang']) * f
    sc, h = scene(g['cx'], g['cz']); fm = (f0 + f1) / 2; ims = []
    for fe, re_, ft in ((f0 - 0.05, g['r'] - 4, fm), (fm, g['r'] - 10, fm)):
        e = (g['cx'] + np.cos(th(fe)) * re_, g['cz'] + np.sin(th(fe)) * re_); t = (g['cx'] + np.cos(th(ft)) * (g['r'] + 14), g['cz'] + np.sin(th(ft)) * (g['r'] + 14))
        ims.append(sc.render((e[0], h(*e) + 5, e[1]), (t[0], h(*t) + 5, t[1]), 700, 440))
    out = Image.new('RGB', (1400, 440)); out.paste(ims[0], (0, 0)); out.paste(ims[1], (700, 0)); fn = os.path.join(AP, 'v23_mur_%s.png' % tag.replace(' ', '')); out.save(fn); outs.append(fn)
# bâches drapées + ballots
for tag, uf in (('LR', LP.CAMEL_U + 28), ('L3', None)):
    g = next(g for g in p.segs if g['kind'] == 'S' and g['tag'].startswith(tag)); c, s_ = np.cos(g['t']), np.sin(g['t']); nrm = np.array([-s_, c])
    if uf is None:
        prof, u0, name = g['sections'][0]; import layouts_sx as LS
        it = [i for i in LS.COMBOS[name]['items'] if 'butte' in i[0]][0]; uf = u0 + (it[1] + it[2]) / 2
    P = np.array([g['x0'] + uf * c, g['z0'] + uf * s_]); sc, h = scene(*P, R=90); ims = []
    for side, back in ((1, 0), (-1, -30)):
        e = P + nrm * side * 70 + np.array([c, s_]) * back; ims.append(sc.render((e[0], 8, e[1]), (P[0], 5, P[1]), 700, 440))
    out = Image.new('RGB', (1400, 440)); out.paste(ims[0], (0, 0)); out.paste(ims[1], (700, 0)); fn = os.path.join(AP, 'v23_bache_%s.png' % tag); out.save(fn); outs.append(fn)
print(outs)
