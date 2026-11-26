"""v18 : formes MESURÉES sur RF Anaheim 1 2026 (refs/rf/sx2026r01anaheim1.medium.saf) pour la « version RF » de Paris.

Repère : terrain.png de la RF (1025 px, 0,5795 ft / px), x = colonne, z = ligne. Les couloirs sont pris sur les portes de chrono
de la RF (centre + sens de course) ; chaque profil = médiane de 3 lignes (-4, 0, +4 ft) dans l'axe du couloir.
  - bosse      : médiane de 9 bosses simples (ligne du haut, colonne de gauche, diagonale du bas) : 26 ft, 3,4 ft ;
  - grosse     : médiane de 4 grosses bosses : 40 ft, 5,5 ft ;
  - table      : médiane de 3 tables : 50 ft, 5,8 ft ;
  - whoop      : médiane de 6 whoops (couloir de droite, montant) : 19 ft, 3,0 ft, pas 20,6 ft ; bosse de lancement 2,5 ft ;
  - dtab       : la table à double étage entourée par l'utilisateur (1re après le virage haut-gauche, colonne de gauche) :
                 étage 2,8 ft, dessus 5,9 ft, lèvre 6,8 ft, 78 ft ;
  - arrivée    : appel 8,8 ft, 28 ft de vide, réception 10,7 ft (la ligne d'arrivée de la RF est entre les deux) ;
  - coupe      : dessus plat 34 ft, flancs 7 ft ;
  - virages    : profil radial (médiane +-30 deg autour du sommet) et hauteur de crête selon l'avancement dans le virage
                 (entrée -> sortie), 180 (centre (684, 875) px, ligne de course à 24,4 ft) et 90 (centre (120, 145) px, 22,6 ft).

  py -3.12 -I paris2026/mesure_rf.py [dossier extrait de la RF]
"""
import os
import sys
import json
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(ROOT), "rf_ext", "sx2026r01anaheim1")
t = open(os.path.join(SRC, "terrain.hf")).read().split(); S, LO, HI = float(t[1]), float(t[2]), float(t[3])
H = np.asarray(Image.open(os.path.join(SRC, "terrain.png")), float) / 65535 * (HI - LO) + LO

LANES = {'top': ((575, 107), (-1, 0)), 'left': ((87, 159), (2.8, 16.6)), 'rA': ((925, 230), (-5.0, 16.2)), 'rB': ((669, 789), (5.0, -16.1)),
         'r258': ((501, 258), (-1, 0)), 'd12': ((496, 829), (-14.1, -9.9))}
U = np.arange(-250, 650, 0.1)


def lane(P, d):
    P = np.array(P, float) * S; d = np.array(d, float); d /= np.linalg.norm(d); n = np.array([-d[1], d[0]])
    rows = []
    for v in (-4, 0, 4):
        x, z = P[0] + U * d[0] + v * n[0], P[1] + U * d[1] + v * n[1]
        r = map_coordinates(H, [z / S, x / S], order=1, cval=0.0); rows.append(r)
    return np.median(rows, axis=0)


Q = {k: lane(*v) for k, v in LANES.items()}


def cut(name, u0, L, pad=1.0):
    q = Q[name]; i0, i1 = int((u0 - pad + 250) * 10), int((u0 + L + pad + 250) * 10)
    p = q[i0:i1].copy(); return np.maximum(p - max(p[0], p[-1], 0.0), 0.0)


def med(items):
    ps = [cut(*it) for it in items]; n = int(np.median([len(p) for p in ps]))
    return np.median([np.interp(np.linspace(0, len(p) - 1, n), np.arange(len(p)), p) for p in ps], axis=0)


F = dict(
    single=med([('top', 23.9, 23.2), ('top', 100.9, 24.1), ('top', 130.5, 23.7), ('top', 205.0, 23.0), ('top', 240.2, 22.6),
                ('left', 191.2, 24.1), ('left', 226.1, 24.1), ('d12', 24.6, 24.7), ('d12', 94.9, 24.4)]),
    big=med([('top', 55.3, 39.3), ('top', 162.8, 37.4), ('left', 148.4, 36.7), ('rA', 275.8, 40.6)]),
    table=med([('r258', 60.6, 48.2), ('rA', 76.8, 47.5), ('rB', 206.1, 43.2)]),
    whoop=med([('rB', 14.3, 17.5), ('rB', 34.9, 16.9), ('rB', 55.1, 17.9), ('rB', 76.3, 17.1), ('rB', 96.5, 17.7), ('rB', 117.3, 17.3)]),
    wlaunch=cut('rB', -7.5, 18.5),
    dtab=cut('left', -9.0, 76.0))
# arrivée : couloir entre les portes 32 (406, 513) et 33 (571, 362) px
a, b = np.array((406, 513.)) * S, np.array((571, 362.)) * S; d = (b - a) / np.linalg.norm(b - a); n = np.array([-d[1], d[0]])
u = np.arange(-60, np.linalg.norm(b - a) + 60, 0.1)
fin = np.median([map_coordinates(H, [(a[1] + u * d[1] + v * n[1]) / S, (a[0] + u * d[0] + v * n[0]) / S], order=1) for v in (-3, 0, 3)], axis=0)
F['fin_app'] = np.maximum(fin[int(36 * 10):int(84 * 10)], 0.0); F['fin_land'] = np.maximum(fin[int(112 * 10):int(190 * 10)], 0.0)
F['fin_gap'] = np.array(28.0)


# virages : profil radial + crête selon l'avancement (entrée -1 -> sortie +1)
def ray(c, ang, r):
    c = np.array(c, float) * S; return map_coordinates(H, [(c[1] + r * np.sin(ang)) / S, (c[0] + r * np.cos(ang)) / S], order=1)


R = np.arange(0, 70, 0.5)
F['b180_r'] = R; F['b90_r'] = R
F['b180_p'] = np.median([ray((684, 875), np.pi / 2 + np.radians(da), R) for da in np.linspace(-30, 30, 7)], axis=0)
F['b90_p'] = np.median([ray((120, 145), np.radians(225) + np.radians(da), R) for da in np.linspace(-15, 15, 7)], axis=0)
# 180 : la course tourne dans le sens des angles croissants autour du centre (entrée à l'est) ; 90 : sens décroissant
F['b180_t'] = np.linspace(-1, 1, 13); F['b180_c'] = np.array([ray((684, 875), np.pi / 2 + np.radians(90 * t_), R).max() for t_ in F['b180_t']])
F['b180_c'][-1] = min(F['b180_c'][-1], F['b180_c'][-2] * 0.6)          # au-delà de la sortie : le bloc voisin, pas le berm
F['b90_t'] = np.linspace(-1, 1, 7); F['b90_c'] = np.array([ray((120, 145), np.radians(225) - np.radians(45 * t_), R).max() for t_ in F['b90_t']])
F['b180_ride'] = np.array(24.4); F['b90_ride'] = np.array(22.6)
F['lat'] = np.array([34.0, 7.0])

np.savez(os.path.join(HERE, "data", "rf_a1_formes.npz"), **F)
info = {k: (dict(L_ft=round(len(v) * 0.1, 1), H_ft=round(float(v.max()), 2)) if v.ndim == 1 and k not in ('b180_r', 'b90_r', 'b180_t', 'b90_t', 'b180_c', 'b90_c', 'lat')
            else np.round(v, 2).tolist()) for k, v in F.items() if not k.endswith(('_p', '_r'))}
info['source'] = "RF sx2026r01anaheim1 (Anaheim 1 2026), terrain.png 0,5795 ft/px ; voir mesure_rf.py"
json.dump(info, open(os.path.join(HERE, "data", "rf_a1_formes.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
for k, v in info.items():
    print(k, v)
