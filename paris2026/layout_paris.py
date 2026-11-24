"""Tracé Supercross Paris 2026 dans l'arène agrandie (coordonnées monde MX, pieds).

Source : paris2026/lecture_photos.json (relevé du visuel officiel, 0,665 ft/px).
Passage visuel -> monde : la vue de dessus est tournée de 180° (le départ regarde -x dans MX) :
    x = X0 + (948 - x_px) * S        z = Z0 - (y_px - 302) * S
  948 px = pied de la tribune Est du visuel = bout Sud du sol de l'arène (FLOOR_X_SOUTH x 1,35).
Virages : rayons JGSX (21,5 ft, berms mesurés) ; les 180° imposent 43 ft entre deux couloirs voisins
(visuel : ~48 ft) -> L1 et L6 sont rapprochés de ~5 ft, rien d'autre ne bouge.
Chaque obstacle = une unité JGSX mesurée (lib/sx_units.json), centrée sur le milieu de l'obstacle du visuel ;
exceptions (formes créées, demandées par Ryan) : la grande table « SUPERCROSS Paris » (97 ft) et les 4 tremplins FMX.
"""
import os
import sys
import json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from engine import Path          # noqa: E402
from compose import lane, unit, whoops   # noqa: E402

D = json.load(open(os.path.join(HERE, "lecture_photos.json"), encoding="utf-8"))
S = D["echelle_ft_par_px"]
FT = 3.28084
PLAN_K = 1.624                    # agrandissement en plan de l'arène (stade_paris/src/build.py) ; v5 : 1,35 -> 1,45 (paddock) ; v10 : x1,12 -> 1,624
FLOOR_X_SOUTH = -60.0 * PLAN_K    # m (dims.FLOOR_X_SOUTH x K)
OX, OZ = 549.0, 593.5             # origine du repère de l'arène dans le terrain (ft) : bâtiment centré sur 1187 ft
X0 = OX + FLOOR_X_SOUTH * FT
Z0 = OZ
BIG, BIG2 = 'big_det_a', 'big_cle'
RB = 21.5
ZION = os.environ.get('PARIS_ZION') == '1'      # v15 : « version Zion » (paris2026/build_zion.py)
# v16 (« on garde pas les virages de ZION, ça fait un bug ») : virages USLAND (rayon 21,5 ft, berms JGSX) aussi en version Zion
XW_SHIFT = 23.0 if ZION else 0.0  # v15 : couloirs allongés vers l'est (place libre du sol agrandi) pour les écarts ZION ;
#   v20 (« baisse l'écart entre les bosses crête à crête, pas énorme ; du coup les virages aussi, les rapprocher ») : 55 -> 23 ft
# v19 (version Zion, « élargir un peu entre les pistes ; les enchaînements sont assez proches du public ; les whoops et l'enchaînement
# à côté sont collés ») : 180 L2 -> L1 et L6 -> L5 de rayon 27,5 ft (couloirs voisins à 55 ft au lieu de 43, berm JGSX décalé),
# couloir Est 10 ft plus à l'ouest (L1 / L6 plus longues, plus près de la tribune Ouest)
R180 = 24.5 if ZION else RB      # v20 (« réduire la largeur de la piste : les virages tournent un peu trop large ») : 27,5 -> 24,5 ft
#   (couloirs voisins à 49 ft comme RF Anaheim 1, ligne de course des 180 à 24,4 ft) ; L2 / L5 ne bougent pas, L1 / L6 se rapprochent
XLR_SHIFT = 10.0 if ZION else 0.0
TOP_W = 30.4                      # largeur du dessus des obstacles (JGSX)


def px_x(xp):
    return X0 + (948.0 - xp) * S


def px_z(yp):
    return Z0 - (yp - 302.0) * S


def arena_to_mx(X, Y):
    """repère local de l'arène (m) -> monde MX (ft) : identique à stade_paris mxtrack (même origine OX, OZ)."""
    return OX + X * FT, OZ - Y * FT


# ---------------------------------------------------------------- formes créées (pas des mesures JGSX : le dire)
def big_table():
    """Grande table « SUPERCROSS Paris » (réception FMX), d'après le visuel : 97 ft, montée raide (18 ft), plateau,
    descente longue (39 ft) vers l'est. Hauteur 8 ft = celle des plus gros sauts JGSX (7,9 ft). FORME CRÉÉE."""
    H, up, top, down = 8.0, 18.0, 40.0, 39.0
    x = np.arange(0, up + top + down, 0.1)
    h = np.where(x < up, H * 0.5 * (1 - np.cos(np.pi * x / up)),
                 np.where(x < up + top, H, H * 0.5 * (1 + np.cos(np.pi * (x - up - top) / down))))
    return h


def fmx_kicker(L=30.0, H=10.0):
    """Tremplin FMX : arc de cercle concave (lèvre à ~37°), dos quasi vertical (1 ft). FORME CRÉÉE."""
    R = (L * L + H * H) / (2 * H)
    x = np.arange(0, L, 0.1)
    up = R - np.sqrt(R * R - x * x)
    back = np.linspace(H, 0, 11)[1:]
    return np.r_[up, back]


# ---------------------------------------------------------------- sections
COMBOS = {}


def _sec(name, prof, u0, items=None):
    COMBOS[name] = dict(tokens=[], items=items or [(name, 0.0, len(prof) * 0.1)], length=len(prof) * 0.1)
    return (prof, float(u0), name)


def unit_sec(name, uid, u_centre):
    p, items = lane([uid])
    COMBOS[name] = dict(tokens=[uid], items=items, length=len(p) * 0.1)
    return (p, float(u_centre - len(p) * 0.1 / 2), name)


def lane_obstacles(lane_id, start, axis, sign, skip=()):
    """sections d'un couloir du relevé. start = abscisse monde du début de la ligne droite (x ou z),
    axis = 'x'/'z', sign = sens de parcours (+1 / -1) sur cet axe."""
    L = next(l for l in D["tour"] if l["id"] == lane_id)
    out, log = [], []
    for k, o in enumerate(L["obstacles"], 1):
        a, b = o["px"]
        if axis == 'x':
            ca, cb = px_x(a), px_x(b)
        else:
            ca, cb = px_z(a), px_z(b)
        c = (ca + cb) / 2
        u_c = (c - start) * sign
        name = "%s-%d %s" % (lane_id, k, o["jgsx"] if o["type"] != "whoops" else "whoops")
        if k in skip:
            log.append((name, u_c, abs(cb - ca)))
            continue
        if o["type"] == "whoops":
            p = whoops(o["jgsx"], o["n"])
            u0 = (min(ca, cb) - start) * sign if sign > 0 else (start - max(ca, cb))
            out.append(_sec(name, p, u0))
        else:
            out.append(unit_sec(name, o["jgsx"], u_c))
        log.append((name, u_c, abs(cb - ca)))
    return out, log


LOG = {}

# ---------------------------------------------------------------- v2 : formes de Saint-Thibéry / Saint-Georges (validées par Ryan)
# Chaque obstacle du visuel garde sa place (centre) ; sa FORME vient des bosses déjà réglées sur les autres pistes :
#   singles = Arlington (SA) redimensionnés comme Saint-Thibéry L1/L2 ; roller = Custom1_g30_1 (Saint-Georges) ;
#   table = Arlington_g49_2 à 6,6 ft (Saint-Georges L2) ; whoops = Custom_0 x1,15 (Saint-Georges L4) ;
#   triple serré = triple après les whoops de Saint-Georges ; saut d'arrivée = double de Saint-Georges (appel doux,
#   réception longue) ; grande table = réception freestyle de Saint-Thibéry (trapèze) ; tremplins FMX = modèle acier ramp_50.
#   Les rythmiques passent par rounded() (pieds remplis, réceptions pleines) comme à Saint-Thibéry / Saint-Georges.
import layouts_sx as LS                                     # noqa: E402
from layouts_stt import rounded, up                             # noqa: E402
from layouts_sgm import smooth_takeoff, whoops_up           # noqa: E402
SA, ROLLER, TABLE_B = LS.SA, 'Custom1_g30_1', 'Arlington_g49_2'
TABLE = ('scale', TABLE_B, 6.6)
TRIPLE_SGM = [('scale', SA[3], 3.9), ('gap', 2.5), ('scale', SA[4], 2.3), ('gap', 3.5), ('stretch', SA[5], 4.0, 1.3)]
FINISH_DBL = [smooth_takeoff(4.0, 10.0, 1.8, 9.0, 0.8, pad=0.4), ('gap', 24.5), ('stretch', SA[2], 5.4, 1.5)]
FMX_LANDING = ('trapeze', 8.0, 22.0, 40.0, 35.0, 'lin', 4.0)
BERM180_GAIN = 1.15                     # v9 (Ryan : « les extérieurs des 180 un petit peu plus gros, faut pas abuser ; les 90 sont bien »)
BERM90_GAIN = 1.0                       # v5 (Ryan : « les virages à 90 sont trop hauts ») : berms 90° tels que mesurés (était 1,4)
SOFT_FEET = dict(sigma=1.2, h=1.5)       # Saint-Georges v22 : pieds des bosses arrondis
FMX_MODEL = dict(model='ramp_50', model_len=18.47)   # tremplin acier de Ryan (assets/fmx_ramp_user), lèvre 9 ft, collision .shp
FINISH_SEC = 'PAR-L5 petit double, triple d arrivee (ZION 2025)'
# v5 (retours de Ryan) : petit double avant l'arrivée ; L1 : la 2e bosse après la table remise (table un peu plus courte) ;
# L6 : rythmique serrée (on peut faire double / quadruple, mais la 1re bosse est petite : pas de « 4 d'entrée »), table,
# puis un double derrière la table (« sur table, derrière double »). Formes = bosses Arlington déjà utilisées ici.
SMALL_DBL = [('scale', SA[0], 3.4), ('gap', 8.0), ('stretch', SA[1], 4.0, 1.25)]
PRE_FINISH = [('scale', SA[0], 3.4), ('gap', 16.0), ('stretch', SA[1], 4.0, 1.25)]   # v13 : double plus long (était SMALL_DBL)
PRE_FINISH_Z = [('stretch', SA[0], 4.8, 1.15), ('gap', 22.7), ('stretch', SA[1], 5.8, 1.6)]   # v20d (« l'appel du double plus plat, même
#   hauteur, moins raide, que ça envoie moins loin ; la réception plus haute, un peu plus de terre, un peu plus loin : rallonge le saut de
#   2 mètres ») : appel 0,9 -> 1,15 de long (30 -> 24°), réception 5,2 -> 5,8 ft, crête à crête +2 m (14,1 -> 16,1 m) ; avant :
PRE_FINISH_Z_V19D = [('stretch', SA[0], 4.8, 0.9), ('gap', 20.0), ('stretch', SA[1], 5.2, 1.6)]
# v21d (« l'appel est bien trop raide, trop haut ; plus bas et moins raide ; là ça saute facilement derrière l'appel du triple ; la récep
# est bien ») : appel 4,8 -> 4,0 ft, montée 40 % plus longue (30 -> ~20°) ; la réception ne bouge pas (l'écart reprend l'allongement)
_APP_OLD = ('stretch', SA[0], 4.8, 1.15)
_q = np.asarray(LS.L('tmp', [_APP_OLD]), float); _k = int(np.argmax(_q))
_q = np.r_[np.interp(np.linspace(0, _k, int(round(_k * 1.4)) + 1), np.arange(_k + 1), _q[:_k + 1]), _q[_k + 1:]] * (4.0 / _q.max())
_APP_NEW = ('raw', 'appel du petit double adouci 4,0 ft', _q, 'T')
PRE_FINISH_Z = [_APP_NEW, ('gap', round(22.7 - (len(LS.L('tmp', [_APP_NEW])) - len(LS.L('tmp', [_APP_OLD]))) * 0.1, 1)), ('stretch', SA[1], 5.8, 1.6)]
_APP_SGM = smooth_takeoff(4.0, 10.0, 1.8, 9.0, 0.8, pad=0.4)   # v23 (« l'appel plus raide, comme le double de Saint-Georges ») : appel du double L3 de Saint-Georges (~36°)
PRE_FINISH_Z = [_APP_SGM, ('gap', round(22.7 - (len(LS.L('tmp', [_APP_SGM])) - len(LS.L('tmp', [_APP_OLD]))) * 0.1, 1)), ('stretch', SA[1], 5.8, 1.6)]   # v19 (Zion) : vrai petit double, appel pointu ;
#   v19d (« la bosse entourée, mets-la 4 mètres plus loin ») : réception 13 ft plus loin (7 -> 20 ft)
TRIPLE_EARLY = 20.0
TABLE_PLUS = 3.3                  # v20d : table de L6 +50 cm de chaque côté
# v10 (ancien commentaire) : « avant le triple il manque une bosse, ça fait un double » (v9 : un seul roller) ;
#   la ligne d'arrivée (item 2) retombe ainsi sur l'APPEL du triple (avec le roller, l'item 2 était la réception -> FINISH mal placé)
TABLE_L1 = ('stretch', TABLE_B, 6.6, 0.85)
L6_RHYTHM = [('scale', SA[0], 2.6), ('gap', 3.0), ('scale', SA[2], 4.2), ('gap', 3.0), ('scale', SA[1], 4.4), ('gap', 3.0),
             ('scale', SA[3], 4.5), ('gap', 3.0), ('scale', SA[2], 4.4), ('gap', 3.0), ('scale', SA[1], 4.2), ('gap', 4.0),
             TABLE, ('gap', 12.0), ('scale', SA[0], 3.8), ('gap', 9.0), ('stretch', SA[1], 4.0, 1.25)]
L3_SEC = 'PAR-L3 appel, gros saut rond du milieu (ZION 2025)'

# ---------------------------------------------------------------- v3 (retours de Ryan sur l'étape 2)
# "l'arrivée le triple", "l'appel est plus gros et réception pareil", "le gros saut du milieu rond" : formes MESURÉES sur la
# piste ZION Paris 22 (ses captures, data/zion_p22_profils.json) ; "après les whoops la table trop proche et trop petite" ;
# couloir Est : "ça fait une bosse" (une seule longue bosse puis 2 bosses, relu sur la vue de côté refs/6.jpg).
_P22 = json.load(open(os.path.join(HERE, "data", "zion_p22_profils.json")))
P22_TRIPLE = ('raw', 'triple d arrivee ZION Paris 22 (3,3 / 2,2 / appel 10,9)', np.array(_P22['triple_arrivee']), 'T')
P22_APPEL = ('raw', 'appel ZION Paris 22 (10,9)', np.array(_P22['appel']), 'T')
P22_BUTTE = ('raw', 'butte gros saut rond ZION Paris 22 (21,2)', np.array(_P22['butte']), 'X')
P22_GAP = _P22['ecart_appel_butte']


def even(blocks, lane_len, u0, end):
    """v10 : même écart entre toutes les bosses (comme Saint-Thibéry / Saint-Georges), 1re à u0 ft du virage, dernière à end ft."""
    g = (lane_len - u0 - end - sum(tlen(b) for b in blocks)) / max(1, len(blocks) - 1)
    out = []
    for k, b in enumerate(blocks):
        out.append(b)
        if k < len(blocks) - 1:
            out.append(('gap', round(g, 1)))
    return out


P25_WHOOPS = json.load(open(os.path.join(HERE, "data", "p25_whoops.json"), encoding="utf-8"))
RAIL = dict(top=(15.5, 19.0), inner=1.0, outer=3.5, ramp=6.0)    # v14 : bord des whoops de 25 Paris SX (muret de chaque côté)


def whoops_zion(n=10, k=1.15, launch_m=0.60, pitch_m=6.20):   # v20 (« minimum 10 whoops ; réduis aussi à 6,2 l'écart des whoops »)
    """v19e (« baisse la bosse de lancement, mets-la à 0,60 m » ; puis « mets 6,3 [m] alors pour les whoops ») : les whoops de la
    version Zion (whoops_up(n, k), Saint-Georges) avec la 1re bosse ramenée à launch_m de haut (forme gardée, mise à l'échelle) et
    du sol plat ajouté dans chaque creux pour un pas crête à crête moyen de pitch_m (20,0 ft -> 6,30 m ; whoops inchangées)."""
    from scipy.signal import find_peaks
    p = np.asarray(whoops_up(n, k)[2], float); pk, _ = find_peaks(p, prominence=0.8, distance=60)
    lows = [pk[i] + int(np.argmin(p[pk[i]:pk[i + 1]])) for i in range(len(pk) - 1)]
    p[:lows[0]] *= (launch_m / 0.3048) / p[pk[0]]
    add = max(0, int(round((pitch_m / 0.3048 - np.mean(np.diff(pk)) * 0.1) / 0.1))); parts, a = [], 0
    for lo in lows:
        parts += [p[a:lo + 1], np.full(add, p[lo])]; a = lo + 1
    parts.append(p[a:])
    return ('raw', f'whoops x{n} (lancement {launch_m:.2f} m, pas {pitch_m:.2f} m)', np.concatenate(parts), 'W')


END_GAP = 4.0 if ZION else 8.0   # v23 Zion (« entre la dernière bosse de chaque enchaînement et le virage, réduis l'écart ») : 8 -> 4 ft
SPLIT_Z = {}      # v22 : section -> [(début ft, fin ft, k gauche, k droite)] ; obstacle plus bas d'un côté (gauche/droite du sens de course)
SAND_LR = None    # v22 : (u début, u fin) de la partie sable de LR (ornières) ; rempli par paris()


def pts_prof(pts, sig=0.8):
    """v22 : profil (pas de 0,1 ft) d'après des points (u ft, h ft) tirés des dessins de l'utilisateur, lissé (sig ft), bouts à 0."""
    from scipy.ndimage import gaussian_filter1d
    P = np.asarray(pts, float); u = np.arange(0, P[-1, 0] + 1e-9, 0.1)
    p = gaussian_filter1d(np.interp(u, P[:, 0], P[:, 1]), sig / 0.1, mode='nearest'); p = np.clip(p - max(p[0], p[-1]), 0, None)
    return p


# v22 (dessin sur le profil L3) : « pas un roller, une petite table creusée, un peu plus longue qu'une table de base ; un appel un peu
# raide, ça se recreuse un petit peu, et hop le plat avec la table »
def table_creusee(k=1.0):
    """v23 : la petite table creusée allongée k fois (moins raide), appel un peu plus haut (3,6 -> 4,0 ft)."""
    P = [(0, 0), (1.0, 0.1), (4.6, 4.0), (6.2, 3.95), (9, 3.0), (13, 2.8), (16, 3.2), (19.5, 4.3), (21.5, 4.4), (23.5, 4.0), (27.5, 2.2), (31, 0.5), (33, 0)]
    return pts_prof([(u * k, h) for u, h in P], 0.7 * k)


TABLE_CREUSEE = pts_prof([(0, 0), (1.0, 0.1), (4.6, 3.6), (6.2, 3.55), (9, 2.85), (13, 2.7), (16, 3.1), (19.5, 4.3), (21.5, 4.4),
                          (23.5, 4.0), (27.5, 2.2), (31, 0.5), (33, 0)], 0.7)
# v22 (dessin sur LR + photos du saut Milwaukee) : « un mur, genre un camel, un appel très raide, une table très haute » ; dessinée à
# ~21 ft mais les rollers du même dessin sont ~2x plus hauts que dans le message (« un quart de la bosse ») : hauteur des photos, ~10,6 ft
CAMEL_V22B = pts_prof([(0, 0), (3, 0.5), (9, 3.3), (14, 7.3), (17.5, 9.8), (20, 10.5), (22, 10.6), (40, 10.65), (43, 10.2), (50, 7.0),
                       (58, 3.2), (64, 0.8), (68, 0)], 1.2)   # appel ~40°
# v22c (« plus dans ce style la bosse », dessin sur le profil v22b) : appel creusé qui se redresse en haut (kick), plateau court (~6 ft),
# dos raide ; hauteur gardée à 10,6 ft (le dessin monte à ~15 ft : forme du dessin x0,69) ; commence vers 118 ft du virage
CAMEL = pts_prof([(0, 0), (5, 0.7), (8, 2.8), (10.5, 6.4), (12, 7.0), (14, 10.3), (15, 10.6), (21, 10.6), (22, 10.3), (26, 4.8),
                  (28.5, 1.4), (32, 0)], 0.7)
# v22d : virage après l'arrivée (s en ft depuis l'entrée de T_L5a ; T_L5a 33,8 ft, ligne droite 25,8, T_L5b 33,8 -> e3 = 93,4)
POST_FIN_V22D = dict(b1=[(23.8, 0), (27, 0.35), (31, 1.5), (33.8, 1.9), (36.5, 1.5), (39.5, 0.3), (41.5, 0)],
                b23=[(40.0, 0), (43, 0.6), (47, 2.2), (49.5, 2.8), (52, 2.4), (54.5, 1.5), (60, 1.45), (88, 1.45), (93, 0.9), (99, 0.2), (103, 0)],
                out_k=0.12)
# v23 (« la 1re bosse normale, celle de la 2e actuelle un peu plus raide ; la 2e un peu plus grosse et plus espacée ; le plateau plus
# haut : tu agrandis tout ») : bosse 1 pleine largeur 2,6 ft, bosse 2 3,3 ft (crêtes 20 ft d'écart), plateau 2,05 ft
POST_FIN_V23 = dict(b1=[(26, 0), (29, 0.8), (32, 2.2), (34, 2.6), (36.5, 2.0), (39.5, 0.5), (42, 0)],
                    b23=[(44, 0), (47, 0.8), (51, 2.8), (54, 3.3), (57, 2.8), (60, 2.1), (64, 2.05), (88, 2.05), (94, 1.2), (100, 0.3), (104, 0)],
                    out_k=1.0)
# v23b (dessin sur la vue en jeu : « la 1re a la taille d'un roller, un peu plus haut ; la 2e un peu plus espacée, presque la taille d'une
# bosse d'enchaînement ; et après le plateau, tac, qui tourne ») : 2,2 ft ; 4,0 ft (crêtes 24 ft d'écart) ; plateau 2,6 ft dès sa descente
POST_FIN = dict(b1=[(25, 0), (28.5, 0.7), (31.5, 1.9), (33.5, 2.2), (35.5, 1.9), (38.5, 0.6), (41, 0)],
                b23=[(43, 0), (47, 0.8), (52, 2.9), (56, 3.9), (58, 4.0), (60, 3.7), (63, 2.9), (66, 2.6), (88, 2.6), (94, 1.6), (100, 0.4), (105, 0)],
                out_k=1.0)
CAMEL_V22D = CAMEL
# v23 (« un peu plus haut ; la face beaucoup plus raide, le bas toujours smooth ; un petit creux avant, que ça redescende presque au sol du stade
# avant la face ; plus de cran ; la réception moins raide ») : replat de terre 0,4 ft, creux à 0,05, face concave jusqu'à ~60°, 11,6 ft,
# dessus 6 ft, réception ~25° sur 27 ft
CAMEL = pts_prof([(0, 0), (2, 0.35), (7, 0.4), (9.5, 0.05), (11, 0.15), (13, 0.9), (15, 2.4), (16.5, 4.3), (17.8, 6.6), (18.8, 8.8),
                  (19.6, 10.6), (20.4, 11.4), (21.5, 11.6), (27.5, 11.6), (29, 11.3), (33, 9.6), (38, 7.0), (44, 4.0), (50, 1.5), (54, 0.3),
                  (56, 0)], 0.5)
CAMEL_U = 133.5   # v22d (« mets le saut Milwaukee plus centré vers mon trait », trait à ~158 ft) : centre du saut à 158 ft (était 118 -> 134)
# v22 (dessin sur L1) : « après les whoops, comme une whoops en plus, sauf que ça fait une table plate d'à peu près la longueur d'une
# table normale ; ça redescend »
TABLE_PLATE_L1_V23 = pts_prof([(0, 0), (3, 1.0), (6, 2.9), (8.5, 3.4), (22, 3.6), (33, 4.25), (35.5, 4.4), (38.5, 3.6), (43, 0.9), (46, 0)], 0.8)
TABLE_PLATE_L1 = pts_prof([(0, 0), (3, 1.0), (6, 2.9), (8.5, 3.5), (30, 3.6), (33, 2.9), (38, 0.7), (41, 0)], 0.8)


def fuse_raw(t, bottom=0.6):
    """v22c : fusion des 2 bosses d'un profil (comme le 'fuse' de Saint-Georges / Saint-Thibéry) : le creux entre la 1re crête et la
    dernière est remonté à bottom x la 1re crête (descente et remontée en cosinus), les faces extérieures ne bougent pas."""
    from scipy.signal import find_peaks
    p = np.asarray(t[2], float).copy(); pk, _ = find_peaks(p, prominence=0.8); i1, i2 = int(pk[0]), int(pk[-1])
    im = i1 + int(np.argmin(p[i1:i2 + 1])); H1, H2 = p[i1], p[i2]; bo = bottom * H1
    e1 = bo + (H1 - bo) * (1 + np.cos(np.linspace(0, np.pi, im - i1 + 1))) / 2
    e2 = bo + (H2 - bo) * (1 - np.cos(np.linspace(0, np.pi, i2 - im + 1))) / 2
    p[i1:i2 + 1] = np.maximum(p[i1:i2 + 1], np.r_[e1, e2[1:]])
    return ('raw', t[1] + ' fusionne', p, t[3])


def whoops_paris(n=11, H=3.6, first=0.6, pitch=18.6):
    """v14 (« regarde les whoops de 25 Paris SX, smooth à l'intérieur, bien rondes, et fais pareil ») : la forme MESURÉE d'une whoop de
    25 Paris SX (20 ft, crête ronde, creux remplis à 0,2 ft / 2,8 ft), mise à notre hauteur H (v11 : « un peu plus hautes ») et au pas
    de la ligne (18,6 ft, place de la table + 2 bosses) ; la 1re = bosse de lancement (first x H), raccords au sol en douceur."""
    w = np.asarray(P25_WHOOPS['whoop_profil_0p5ft'], float)
    w = np.interp(np.linspace(0, len(w) - 1, int(round(pitch / 0.1)) + 1), np.arange(len(w)), w); w = w / w.max()
    out = []
    for k in range(n):
        seg = w * H * (first if k == 0 else 1.0)
        out.append(seg[:-1] if k < n - 1 else seg)
    q = np.concatenate(out)
    from scipy.ndimage import gaussian_filter1d
    q = gaussian_filter1d(q, 0.4 / 0.1)                     # raccords entre whoops (1re plus basse) sans cassure
    r = int(2.0 / 0.1); q[:r] *= np.linspace(0, 1, r); q[-r:] *= np.linspace(1, 0, r); q[0] = q[-1] = 0.0
    return ('raw', 'whoops 25 Paris SX x%d (%.1f ft)' % (n, H), q, 'W')


def whoops_paris_v13(n=11, k=1.25, first=0.85, sx=0.93, sm=1.0, base=0.45):   # v13 : bosse de lancement plus haute (0,55 -> 0,85)
    """v10 (« un peu plus hauts et plus ronds, plus de terre, un peu plus durs ; 11 = la petite bosse + 10 whoops ») : whoops
    Custom_0 x1,25 (3,7 ft), pas x0,93 (18,6 ft), la 1re à 55 %, crêtes arrondies (gaussienne 1 ft), creux remontés à 0,45 ft."""
    import compose
    from scipy.ndimage import gaussian_filter1d
    p = compose.whoops('Custom_0', n) * k
    p = np.interp(np.linspace(0, len(p) - 1, int(len(p) * sx)), np.arange(len(p)), p)
    w = len(p) / n; p[:int(w)] *= first
    q = gaussian_filter1d(p, sm / 0.1); q *= p.max() / q.max()
    t = np.arange(len(q)) / len(q); env = np.clip(np.minimum(t * n - 0.5, (1 - t) * n - 0.5), 0, 1)
    q = np.maximum(q, base * env * env * (3 - 2 * env)); q[0] = q[-1] = 0.0
    return ('raw', 'whoops Custom_0 x%d (x%.2f, ronds, creux %.2f)' % (n, k, base), q, 'W')


def table_double(H=7.6, up1=10.0, tier=13.0, up2=9.0, top=24.0, rise=0.25, down=17.0, sm=0.6):
    """v16 (dessin de l'utilisateur : « une petite table en premier, à peu près à mi-hauteur, et après la table au-dessus ;
    fais un truc droit ») : table à double étage, faces droites, arêtes juste arrondies (gaussienne sm ft). FORME CRÉÉE."""
    from scipy.ndimage import gaussian_filter1d
    xs = [0.0, up1, up1 + tier, up1 + tier + up2, up1 + tier + up2 + top, up1 + tier + up2 + top + down]
    hs = [0.0, H / 2, H / 2, H - rise, H, 0.0]
    x = np.arange(0.0, xs[-1] + 0.05, 0.1); p = np.interp(x, xs, hs)
    p = np.r_[np.zeros(20), p, np.zeros(20)]; p = gaussian_filter1d(p, sm / 0.1); p = np.maximum(p - p[0], 0.0); p[0] = p[-1] = 0.0
    return ('raw', 'table double etage %.1f ft' % H, p, 'T')


RF = os.environ.get('PARIS_RF') == '1'           # v18 : « version RF » (paris2026/build_rf.py)
RFF = np.load(os.path.join(HERE, "data", "rf_a1_formes.npz"))   # formes mesurées sur RF Anaheim 1 2026 (mesure_rf.py)


def table_double_rf(kl=1.15, kh=1.12):
    """v18 (« la table à double étage, je t'ai envoyé laquelle c'est sur A1 ; un peu plus longue, un peu plus grande, là elle est en
    sortie de virage ») : la table entourée par l'utilisateur, MESURÉE sur RF Anaheim 1 2026 (mesure_rf.py, dtab : étage 2,8 ft,
    dessus 5,9 ft, lèvre 6,8 ft, 78 ft), longueur x kl, hauteur x kh. (v17 : mauvaise mesure, une coupe en travers de 2 couloirs.)"""
    p = np.asarray(RFF['dtab'], float); i = max(0, int(np.nonzero(p > 0.3)[0][0]) - 10); p = p[i:]
    p = np.interp(np.linspace(0, len(p) - 1, int(round(len(p) * kl))), np.arange(len(p)), p) * kh; p[0] = p[-1] = 0.0
    return ('raw', 'table double etage RF A1 %.1f ft' % p.max(), p, 'T')


def resample(p, k_len=1.0, H=None):
    """profil 0,1 ft rééchantillonné (longueur x k_len), hauteur ramenée à H."""
    p = np.asarray(p, float); n = max(2, int(round(len(p) * k_len)))
    q = np.interp(np.linspace(0, len(p) - 1, n), np.arange(len(p)), p)
    return q * (H / q.max()) if H else q


# réception de l'arrivée : la butte ZION à la hauteur de l'appel (10,9 ft) et 0,55 de sa longueur (~69 ft) - « pareil »
FINISH_LANDING = ('raw', 'reception arrivee (butte ZION Paris 22 a 10,9 ft)', resample(_P22['butte'], 0.45, 10.9), 'X')


def long_bump(L=86.0, H=5.8, crest=0.75, rip=0.0, n_rip=3):     # v5 : sans ondulations (« la bosse est mal faite »)
    """couloir Est, « une bosse » (vue de côté refs/6.jpg) : longue montée douce avec de petites ondulations jusqu'à une
    crête arrondie aux ~80 % de la longueur, puis une descente raide. FORME CRÉÉE d'après la vue de côté (pas une mesure)."""
    x = np.arange(0, L, 0.1); xc = crest * L
    up = H * (1 - np.cos(np.pi * np.clip(x / xc, 0, 1))) / 2 + rip * np.sin(2 * np.pi * n_rip * np.clip(x / xc, 0, 1)) * np.clip(x / xc, 0, 1) * (1 - np.clip(x / xc, 0, 1)) * 4
    down = H * (1 + np.cos(np.pi * np.clip((x - xc) / (L - xc), 0, 1))) / 2
    p = np.where(x < xc, up, down)
    from scipy.ndimage import gaussian_filter1d
    p = np.maximum(gaussian_filter1d(p, 8), 0.0); p[0] = p[-1] = 0.0
    return ('raw', 'longue bosse ondulee (couloir Est)', p, 'T')


# ---------------------------------------------------------------- v4 (Ryan : « reprends directement le saut d'arrivée et du milieu »)
# Mesurés TELS QUELS sur ZION.2025.SupercrossParis (son archive, data/zion_p25_profils.json) - aucune retouche :
#   arrivée = triple 10,0 / 6,0 / 11,2 ft (168 ft), la ligne d'arrivée sur la crête du 1er saut (porte 17 de ZION) ;
#   milieu = appel 10,0 ft puis butte ronde 24,2 ft (165 ft), 68 ft de large à mi-hauteur, 110 ft au pied.
_P25 = json.load(open(os.path.join(HERE, "data", "zion_p25_profils.json")))


def _split_after_first(prof, name1, name2, kind2):
    """coupe un profil au creux qui suit sa 1re crête : 2 items (la ligne d'arrivée va sur le 1er)."""
    from scipy.signal import find_peaks
    from scipy.ndimage import gaussian_filter1d
    p = np.asarray(prof, float)
    q = gaussian_filter1d(p, 15)               # v5 : lissé (marches de la mesure ZION = « sortes de bosses » vues par Ryan)
    p = np.maximum(q * (p.max() / q.max()), 0.0); p[0] = p[-1] = 0.0
    pk, _ = find_peaks(p, prominence=1.0, distance=60)
    # v9 (Ryan : « avant le gros saut du milieu il y a un bug, un trou, un truc cassant ») : la mesure ZION commence par une
    # fine arête de 0,4 ft séparée de l'appel ; on remet à zéro tout ce qui précède le pied de l'appel (idem après la réception)
    i = pk[0]
    while i > 0 and p[i] > 0.02:
        i -= 1
    p[:i] = 0.0
    j = pk[-1]
    while j < len(p) - 1 and p[j] > 0.02:
        j += 1
    p[j:] = 0.0
    k = pk[0] + int(np.argmin(p[pk[0]:pk[1]]))
    return [('raw', name1, p[:k + 1], 'T'), ('gap', 0.0), ('raw', name2, p[k:], kind2)]


Z25_TRIPLE = _split_after_first(_P25['triple_arrivee'], 'appel arrivee ZION 2025 (10,0)', 'triple arrivee ZION 2025 (6,0 / 11,2)', 'T')
# v9 (Ryan : « le triple d'arrivée est trop gros, on voit beaucoup trop haut ; un peu plus petit, pas beaucoup ») :
# hauteurs x0,87 et longueurs x0,93 (pentes presque inchangées : 0,87 / 0,93 = 0,94), soit 8,7 / 5,2 / 9,7 ft
FINISH_KH, FINISH_KL = 0.87, 0.93
Z25_TRIPLE = [t if t[0] != 'raw' else ('raw', t[1].replace('(10,0)', '(8,7)').replace('(6,0 / 11,2)', '(5,2 / 9,7)'),
                                       np.asarray(t[2], float)[np.round(np.linspace(0, len(t[2]) - 1, int(round(len(t[2]) * FINISH_KL)))).astype(int)] * FINISH_KH, t[3])
              for t in Z25_TRIPLE]
Z25_MILIEU = _split_after_first(_P25['milieu'], 'appel gros saut ZION 2025 (10,0)', 'butte gros saut rond ZION 2025 (24,2)', 'X')
# v10 (« fais le plus large sur les côtés, l'appel légèrement plus raide ») : réception plus large, appel 15 % plus court (même hauteur)
Z25_BUTTE_W = (60.0, 66.0)               # v5 : (44, 46) réception carrée pour la bâche AMV (retirée en v10)
# v13 (« l'appel juste un peu moins haut, légèrement plus raide ») : 92 % de la hauteur, 80 % de la longueur
Z25_MILIEU[0] = ('raw', Z25_MILIEU[0][1] + ' raidi', resample(Z25_MILIEU[0][2], 0.80, 0.92 * float(np.max(Z25_MILIEU[0][2]))), 'T')
Z25_BUTTE_W_ZION = (_P25['largeur_butte_mi_hauteur'], 90.0)   # 68 ft à mi-hauteur comme ZION ; pied 90 ft au lieu de 110 :
#   entre les singles (L2) et la ligne de départ il n'y a que ~98 ft -> flancs un peu plus raides que ZION


def table_stt(h, extra=0.0):
    """v20 : la table de Saint-Thibéry (Arlington_g49_2, mesurée JGSX) à h ft, en 'raw' pour que la version Zion ne la remplace pas ;
    v20d : extra ft de plateau en plus (inséré au milieu du dessus)."""
    p = np.asarray(LS.L('tmp', [('scale', TABLE_B, h)]), float)
    if extra > 0:
        top = np.nonzero(p > p.max() - 0.25)[0]; a_, b_ = int(top[0]), int(top[-1]) + 1   # v23 (« une marche / bande claire sur le dessus ») : dessus étiré
        p = np.r_[p[:a_], np.interp(np.linspace(0, b_ - a_ - 1, b_ - a_ + int(round(extra / 0.1))), np.arange(b_ - a_), p[a_:b_]), p[b_:]]
    return ('raw', 'table Saint-Thibery %.1f ft%s' % (h, ' +%.1f ft' % extra if extra else ''), p, 'T')


def tlen(tok):
    toks = tok if isinstance(tok, list) else [tok]
    return len(LS.L('tmp', toks)) * 0.1


def from_render(lane_id, start, axis, sign, picks, min_gap=1.5, lane_len=None, start_min=3.0, end_margin=8.0, min_gaps=None):
    """picks = {n° d'obstacle (1..n) ou (k1, k2) fusionnés : token ou liste de tokens} ; centre de chaque bloc = centre du
    visuel. Renvoie (tokens, u0) avec les écarts au sol tirés du visuel (>= min_gap)."""
    L_ = next(l for l in D["tour"] if l["id"] == lane_id)
    pos = (lambda v: px_x(v)) if axis == 'x' else (lambda v: px_z(v))
    blocks = []
    for key, tok in picks.items():
        ks = key if isinstance(key, tuple) else (key, key)
        a = L_["obstacles"][ks[0] - 1]["px"]; b = L_["obstacles"][ks[1] - 1]["px"]
        ends = [(pos(v) - start) * sign for v in (a[0], a[1], b[0], b[1])]
        toks = tok if isinstance(tok, list) else [tok]
        blocks.append(((min(ends) + max(ends)) / 2, toks, tlen(toks)))
    blocks.sort(key=lambda t: t[0])
    u0 = blocks[0][0] - blocks[0][2] / 2; prev_end = u0; gaps = []
    for i, (c, toks, ln) in enumerate(blocks):
        st = c - ln / 2
        if i:
            g = max(min_gap, st - prev_end); gaps.append(g); st = prev_end + g
        prev_end = st + ln
    # calage (comme Saint-Georges) : >= start_min ft après la sortie du virage, fin >= end_margin ft avant le virage suivant ;
    # ce qui manque est pris sur le plus grand espace plat du couloir
    if u0 < start_min:
        prev_end += start_min - u0; u0 = start_min
    floor = [min_gap] * len(gaps)                       # écarts imposés (ex. Ryan : la table plus loin des whoops)
    for k, v in (min_gaps or {}).items():
        floor[k] = v
        if gaps[k] < v:
            prev_end += v - gaps[k]; gaps[k] = v
    over = prev_end - (lane_len - end_margin) if lane_len else 0.0
    if over > 0.05 and not gaps:                       # un seul bloc : on le recule
        u0 = max(0.0, u0 - over); over = 0.0
    while over > 0.05 and gaps:
        room = [g - f for g, f in zip(gaps, floor)]
        k = int(np.argmax(room)); take = min(over, room[k])
        if take <= 0.05:
            u0 = max(0.0, u0 - over); break
        gaps[k] -= take; over -= take
    out = []
    for i, (c, toks, ln) in enumerate(blocks):
        if i:
            out.append(('gap', round(gaps[i - 1], 1)))
        out += toks
    LOG[lane_id] = [(round(c, 1), round(ln, 1)) for c, _, ln in blocks]
    return out, u0


def lane_sec(name, toks, u0, finish=False, **kw):
    s = LS.sec(name, toks, u0)
    if finish:
        return rounded(s, interior=False)
    return rounded(s, **({'full': 0.3, 'lead_in': True, 'R_in': 15.0} | kw))


def paris():
    """Le tour (sens de course), départ du tour au début de L5 (sortie de T_C)."""
    LS.COMBOS.clear(); LS.SPLITS.clear(); SPLIT_Z.clear()
    zL5, zLD, zL3, zL2 = px_z(481.0), px_z(370.0) - LD_SHIFT, px_z(226.5) + L3_SHIFT, px_z(130.0) + L3_SHIFT + L2_SHIFT
    zL1, zL6 = zL2 + 2 * R180, zL5 - 2 * R180        # 180° JGSX : couloirs voisins à 43 ft (v19 Zion : 55 ft)
    xW = px_x(312.0) + XW_SHIFT                        # virages Ouest (T1, T_C) : x des sorties de 180°
    xLR, xC, xT5 = px_x(860.0) - XLR_SHIFT, px_x(778.0), px_x(785.0)
    xTB = px_x(315.0)
    R3 = (zL2 - zL3) / 2
    p = Path(xW, zL5, 180.0, 'PARIS')
    # L5 : single, single, SAUT D'ARRIVÉE (obstacles 3 + 4 du visuel = un double : appel / réception), table longue
    toks, u0 = from_render('L5', xW, 'x', -1, {(1, 2): SMALL_DBL, (3, 5): Z25_TRIPLE},
                           lane_len=xW - (xT5 + RB))   # v4 : le triple d'arrivée de ZION 2025 couvre les obstacles 3 à 5 du visuel
    # v13 (« le double plus en sortie de virage et un peu plus long ; le triple est bien ») : le triple reste où il est, le double
    # commence à EXIT_U0 de la sortie du virage, plus long (écart 8 -> 16 ft)
    i_t = next(i for i, t in enumerate(toks) if t[0] == 'raw'); u_app = u0 + tlen(toks[:i_t]) - XW_SHIFT
    pre, ue = PRE_FINISH, EXIT_U0
    if ZION:                    # v16 (« garde le double qu'on avait fait nous, pas celui de ZION ; rapproche-le du virage »)
        # v19 (« le petit double avant l'arrivée, plus raide, un peu plus haut ; là on dirait deux vagues ; un vrai double avec un appel
        # un peu pointu, comme à Saint-Georges, qui décolle pas trop, qui va pas loin ») : appel étroit 4,8 ft, réception 5,2 ft, 7 ft
        pre = [t if t[0] == 'gap' else ('raw', 'double USLAND', np.asarray(LS.L('tmp', [t]), float), 'T') for t in PRE_FINISH_Z]; ue = 4.0
        # v19 (« plus d'espace entre le petit double et le triple d'arrivée, moins de ligne droite après le triple ») : le triple finit
        # à 8 ft du virage
        u_app = (xW - (xT5 + RB)) - END_GAP - tlen(toks[i_t:]) - TRIPLE_EARLY   # v19d (« la pointe de l'appel du triple au trait orange,
        #   là il est un peu trop dans le virage ») : 20 ft plus tôt
    toks = pre + [('gap', round(u_app - ue - tlen(pre), 1))] + toks[i_t:]; u0 = ue
    if ZION:   # v22c (« le triple du saut d'arrivée comme à Saint-Georges : la bosse du milieu et la réception, une fusion entre les deux »)
        toks = [fuse_raw(t) if t[0] == 'raw' and t[1].startswith('triple arrivee') else t for t in toks]
    p.straight(xW - (xT5 + RB), [lane_sec(FINISH_SEC, toks, u0, finish=True)], tag='L5 arrivée')
    p.turn(90, RB, BIG, tag='T_L5a 90 gauche (berm)')
    p.straight(zLD - zL5 - 2 * RB, tag='T_L5 milieu')
    p.turn(90, RB, None, tag='T_L5b 90 gauche')
    p.straight((xTB - RB) - (xT5 + RB), tag='LD ligne de départ (vers l ouest)')
    p.turn(-90, RB, None, tag='T_Ba 90 droite')
    p.straight(zL3 - zLD - 2 * RB, tag='T_B milieu')
    p.turn(-90, RB, BIG, tag='T_Bb 90 droite (berm)')
    x3 = xTB - RB
    # v9 (Ryan : « après le saut du milieu, aller plus dans le virage ; on peut pas tourner direct ; le virage en 1 fois pas 2,
    # un seul bloc à l'intérieur ») : T_C3 + colonne + T_D -> UN 180 à gauche de rayon (zL2 - zL3) / 2 = 32 ft, sommet 6 ft plus
    # loin que l'ancienne colonne, saut du milieu avancé de 8 ft (place pour poser puis tourner). Berm (gros croissant JGSX, décalé
    # au rayon 32 ft) sur la 2e moitié seulement : le départ arrive par l'extérieur de la 1re moitié (comme avant par la colonne).
    x_end3 = xC - X_APEX_SHIFT + R3
    toks, u0 = from_render('L3', x3, 'x', -1, {(1, 2): Z25_MILIEU}, lane_len=x3 - x_end3)
    u0 -= L3_ADVANCE
    if ZION:   # v23 (« baisse légèrement la hauteur de la réception » du saut freestyle) : butte x0,93
        toks = [('raw', t[1].replace('(24,2)', '(22,5)'), np.asarray(t[2], float) * 0.93, t[3]) if t[0] == 'raw' and 'butte' in t[1] else t for t in toks]
    secs3 = [LS.sec(L3_SEC, toks, u0)]
    if ZION:   # v20c (« ajoute un roller en sortie de virage avant le saut de freestyle ») : le roller de Saint-Georges (Custom1_g30_1,
        #   1,9 ft) à EXIT_U0 de la sortie de T_Bb, ~50 ft de plat avant l'appel
        rl_ = [('raw', 'roller Saint-Georges', np.asarray(LS.L('tmp', [ROLLER]), float), 'T')]
        rl_ = [('raw', 'petite table creusee 4,4 ft', TABLE_CREUSEE, 'T')]   # v22 : à la place du roller
        # v23 (« un peu moins raide, l'appel un peu plus haut, longueur x2,25 ») : x2,25 si ça tient avant l'appel du freestyle (22 ft d'élan)
        kL = min(2.25, (u0 - 22.0 - EXIT_U0) / tlen(rl_)); rl_ = [('raw', 'petite table creusee x%.2f' % kL, table_creusee(kL), 'T')]
        LOG['table_creusee_k'] = round(kL, 2)
        assert EXIT_U0 + tlen(rl_) + 21.0 < u0, u0
        secs3.append(LS.sec('PAR-L3 petite table creusee', rl_, EXIT_U0))
    p.straight(x3 - x_end3, secs3, tag='L3 grande table')
    p.turn(180, R3, BIG, tag='T_D 180 gauche (berm 2e moitié)'); p.segs[-1]['berm_from'] = 0.4 if ZION else 0.5   # v23 : appui qui commence plus tôt
    # v7 (Ryan : « ça fait 4 d'entrée, ça doit faire 3, 4 et le 4 dur où faut pousser ») : les 7 bosses du visuel = un triple
    # serré (écarts 3 ft, bosses Arlington x1,2) puis un quad dur (écarts 7 ft, bosses x1,35), 20 ft entre les deux ;
    # près de la sortie du virage (pas d'élan trop long) - unités et réglages de Saint-Thibéry (up, rounded)
    # v9 (Ryan : « t'as fait un espace, nan, c'est le même espace entre chaque saut ; le but c'est que ça fasse 3 d'entrée et le 4
    # après dur, limite à passer que pour les bons ; là ça fait encore 4 d'entrée ») : 7 bosses identiques (celles du quad v7,
    # Arlington x1,35), même écart partout (L2_GAP), la 1re collée à la sortie du 180 (pas d'élan : pas de 4 d'entrée)
    # v10 (« le but c'est triple, triple et pas plus, ou triple 4 si très bon ; pas de 4 d'entrée ; comme Saint-Thibéry ») :
    # 7 bosses de la taille de Saint-Thibéry L2 (4,0 - 5,0 ft), même écart partout = toute la ligne (~12,5 ft au sol, ~40 ft de
    # crête à crête comme STT L2 « long triple, triple »), la 1re plus basse à 3 ft de la sortie du 180, la dernière à 8 ft du virage
    B7 = [('scale', SA[1], 4.0), ('scale', SA[2], 4.6), ('scale', SA[0], 5.0), ('scale', SA[1], 4.8), ('scale', SA[2], 5.0),
          ('scale', SA[1], 4.6), ('scale', SA[2], 4.8)]
    B7 = [('stretch', b[1], b[2], 1.25) for b in B7]      # v13 (« un peu trop pointues : bosse, plat, bosse, plat ») : plus rondes,
    toks = even(B7, xW - x_end3, L2_U0, 8.0)               #   même hauteur, même écart de crête à crête
    if ZION:                                               # v15 : écart ZION (15 ft au sol, ZION 9 - 16), le reste avant la 1re bosse
        toks = [B7[0]]
        for b_ in B7[1:]:
            toks += [('gap', L2_GAP_Z), b_]
        u0z = (xW - x_end3) - 8.0 - tlen(toks)
        # v22 (« la 1re bosse très basse à gauche et basse à droite, double à droite, enrouler à gauche ; double-triple-triple ou
        # simple-triple-quadruple : rajoute une bosse ») : 8 bosses (ZION, 92 % de long), même écart, la 1re 2,8 ft à droite / 1,3 à gauche
        zb_ = lambda h: ('raw', 'bosse ZION %.1f ft' % h, resample(np.asarray(zsingle(h / ZH)[2], float), 0.92), 'T')
        B8 = [zb_(h) for h in (2.8, 4.6, 5.0, 4.8, 5.0, 4.6, 4.8, 4.6)]; u0z = 3.0
        # v23 (« moins d'écart entre la bosse haute à droite et la basse à gauche ; baisse la droite, moins raide, vrai double par-dessus »)
        B8[0] = ('raw', 'bosse ZION 2,3 ft (longue)', resample(np.asarray(zsingle(2.3 / ZH)[2], float), 1.1), 'T')
        gz_ = ((xW - x_end3) - END_GAP - u0z - sum(tlen(b) for b in B8)) / 7; assert gz_ > 4.0, gz_
        toks = [B8[0]]
        for b_ in B8[1:]:
            toks += [('gap', round(gz_, 1)), b_]
        SPLIT_Z[L2_NAME] = [(0.0, tlen(B8[0]), 1.5 / 2.3, 1.0)]
    u0 = u0z if ZION else L2_U0                            # v18 (RF) : même écart partout comme la version USLAND (~8,5 ft, A1 : 8 - 13)
    p.straight(xW - x_end3, [lane_sec(L2_NAME if ZION else 'PAR-L2 triple, triple (7 bosses, meme ecart)', toks, u0)], tag='L2 singles')
    p.turn(-180, R180, BIG2, tag='T1 180 droite (berm)')
    # v10 : 11 whoops (une petite + 10) plus hautes, plus rondes, plus de terre ; la table + 2 bosses gardées (« pas mal »)
    lL1 = xW - (xLR + RB)
    toks = [whoops_paris(), ('gap', 15.0), TABLE_L1, ('gap', 1.5), ('scale', SA[1], 4.0), ('gap', 1.5), ('scale', SA[0], 3.6)]
    if ZION:   # v16 : nos whoops comme Saint-Georges (lancement normal) ; table + 2 bosses ZION plus grosses, écarts ZION (8 ft)
        # v19 (« plus d'espace entre la dernière whoops et la table, quitte à sacrifier un peu entre la table et la 1re bosse ») : 15 -> 22 ft,
        # table -> bosse 8 -> 6 ft, bosse -> bosse 8 -> 6,5 ft
        # v20 (« la table après les whoops : l'appel moins raide, un peu plus plat, pour que ça envoie plus loin, pas vers le haut » ;
        # « réduis l'écart des bosses derrière la table pour pouvoir écarter entre les whoops et la table » ; « garde toujours un petit
        # couloir entre les bosses ») : table de Saint-Thibéry (Arlington_g49_2, appel 29° au lieu de 34°) à 7 ft, bosses derrière à 4 ft
        toks = [whoops_zion(), ('gap', 26.0), table_stt(7.0), ('gap', 4.0), ('scale', SA[1], 4.3), ('gap', 4.0), ('scale', SA[0], 4.1)]
        # v22 (dessin sur L1) : une whoops de plus ; table plate 3,6 ft ; 2 bosses : la 1re un peu plus haute que la table, la 2e pareil
        zb_ = lambda h: ('raw', 'bosse ZION %.1f ft' % h, np.asarray(zsingle(h / ZH)[2], float), 'T')
        toks = [whoops_zion(11), ('gap', 4.0), ('raw', 'table plate 3,6 ft', TABLE_PLATE_L1, 'T'), ('gap', 5.0), zb_(4.1), ('gap', 6.0), zb_(3.6)]
        # v23 (« table un tout petit peu plus loin, un peu plus longue, la fin relevée ; les 2 bosses beaucoup moins hautes, la dernière presque un roller »)
        toks = [whoops_zion(11), ('gap', 5.5), ('raw', 'table montante 4,4 ft', TABLE_PLATE_L1_V23, 'T'), ('gap', 5.0), zb_(3.2), ('gap', 6.0), zb_(1.7)]
    if RF:     # v18 : « garde nos whoops dans la version RF » : celles de la version Zion, 9 (11 : 39 ft de trop) ; table + 2 bosses RF
        toks = [whoops_up(9, 1.15), ('gap', 15.0), ('scale', TABLE_B, 6.6), ('gap', RF_GAP), ('scale', SA[1], 4.0), ('gap', RF_GAP), ('scale', SA[0], 3.6)]
    u0 = lL1 - END_GAP - tlen(toks); assert u0 >= 0.5, u0
    p.straight(xW - (xLR + RB), [LS.sec('PAR-L1 whoops, table, bosse', toks, u0)], tag='L1 whoops')
    p.turn(-90, RB, BIG, tag='T_TR 90 droite (berm)')
    # v7 (Ryan, son tracé rouge : montée, long plateau, puis des bosses) : roller, table (plateau, pas d'ondulations), 3 bosses
    # v9 (Ryan : « là tu as enlevé l'appel, on peut plus faire [le saut] d'entrée ; remets comme avant, cet enchaînement est bien ») :
    # retour à la v6 (roller, longue bosse, 2 bosses)
    # v10 (« le saut en sortant du virage, une ligne droite, puis bosse, table, bosse, bosse, bosse ; la 1re plus basse pour aller
    # sur la table, pas de quadruple ») : single à 3 ft de la sortie, plat, puis l'enchaînement (écarts 7,5 ft comme STT L1), 8 ft du virage
    lLR = (zL1 - RB) - (zL6 + RB)
    GR_ = 10.0 if ZION else 7.5                            # v15 : écart ZION (~10 ft) dans la version Zion
    rh = [('scale', SA[0], 3.0), ('gap', GR_), TABLE, ('gap', GR_), ('scale', SA[1], 4.2), ('gap', GR_), ('scale', SA[2], 4.2), ('gap', GR_), ('scale', SA[1], 4.0)]
    if ZION or RF:   # v16 (dessin de l'utilisateur) : la bosse + la table remplacées par une table à double étage ; v18 : celle de A1
        rh = [table_double_rf()] + [t if t[0] != 'gap' else ('gap', RF_GAP if RF else 7.5) for t in rh[3:]]
    kick = [('scale', SA[1], 4.0)]
    u0 = EXIT_U0                                           # v13 : plus collé au berm (marque entre l'appui et la bosse)
    toks = kick + [('gap', round(lLR - u0 - 8.0 - tlen(kick) - tlen(rh), 1))] + rh
    if ZION:   # v22 (dessin + photos Milwaukee) : sable du virage jusqu'au mur : 2 rollers très bas (1/4 de la bosse), ornières ; léger
        #   creux smooth ; saut Milwaukee (table haute, appel raide) ; le triple d'avant (mêmes bosses)
        global SAND_LR
        r1 = ('raw', 'roller sable 1,1 ft', pts_prof([(0, 0), (5, 0.55), (10, 1.1), (15, 0.55), (20, 0)], 1.5), 'T')
        r2 = ('raw', 'roller sable 1,3 ft', pts_prof([(0, 0), (8, 0.7), (16, 1.3), (24, 0.7), (32, 0)], 2.0), 'T')
        cam = ('raw', 'saut Milwaukee 11,6 ft', CAMEL, 'T'); tri_ = rh[2:]
        zb_ = lambda h: ('raw', 'bosse ZION %.1f ft' % h, resample(np.asarray(zsingle(h / ZH)[2], float), 0.88), 'T')
        tri_ = [zb_(3.4), ('gap', 3.5), zb_(3.6), ('gap', 3.5), zb_(3.4)]   # v23 (« triple moins gros, bosses plus serrées, facile »)
        free = lLR - u0 - END_GAP - tlen([r1]) - tlen([r2]) - tlen([cam]) - tlen(tri_); creux = 3.0
        g1 = round(CAMEL_U - u0 - tlen([r1]) - tlen([r2]) - creux, 1)   # v22c : le saut commence à CAMEL_U ft du virage
        assert g1 > 15.0, free
        toks = [r1, ('gap', g1), r2, ('gap', creux), cam, ('gap', round(free - creux - g1, 1))] + tri_
        SAND_LR = (0.0, u0 + tlen([r1]) + g1 + tlen([r2]) + creux + 2.0)
    p.straight((zL1 - RB) - (zL6 + RB), [lane_sec('PAR-LR sable, saut Milwaukee, triple' if ZION else 'PAR-LR saut de sortie, bosse, table, 3 bosses', toks, u0)], tag='LR tribune Est')
    p.turn(-90, RB, BIG, tag='T_E 90 droite (berm)')
    # v10 (« triple : 3 bosses, 2 bosses, une table, 2 bosses ») : bosses de Saint-Thibéry, même écart partout, 8 ft du virage
    # v13 : appel (1re bosse) un peu plus raide et un peu plus haut (« tu creuses un peu plus le bas »), sans aller plus loin ;
    # les autres bosses un peu plus hautes et plus rondes ; plus de marque berm / 1re bosse (EXIT_U0)
    L6B = [('stretch', SA[0], 4.2, 0.85), ('stretch', SA[2], 4.7, 1.15), ('stretch', SA[1], 4.9, 1.15), ('stretch', SA[3], 4.7, 1.15),
           ('stretch', SA[2], 4.9, 1.15), TABLE, ('stretch', SA[0], 4.3, 1.15), ('stretch', SA[1], 4.5, 1.15)]
    toks, u0 = even(L6B, xW - (xLR + RB), EXIT_U0, 8.0), EXIT_U0
    if ZION:   # v19 (« la table, éloigne-la un peu, mets-la bien entre les deux bosses ») : 6 ft de plus avant ET après la table
        B_ = list(L6B); it_ = B_.index(TABLE)   # v19d (« elle n'a jamais été trop haute, remets la taille d'origine ») : 4,2 (4,6 ft en ZION)
        # v19d (« la table raccourcie un peu ; la bosse après la table est trop loin, rapproche ; la bosse avant légèrement ; surtout la
        # réception ») : table ZION à 88 % de sa longueur, +3 ft avant (était +6), -2 ft après (était +6)
        tb_ = ztable(TABLE[2]); B_[it_] = ('raw', tb_[1] + ' raccourcie', resample(tb_[2], 0.88), 'T')
        # v20 (« l'appel de la table est trop raide ; prends la table qu'on met d'habitude sur Saint-Thibéry, adapte un peu la hauteur ») :
        # Arlington_g49_2 à 7,0 ft (ZION : 7,3 ft, appel 36°)
        B_[it_] = table_stt(7.0)
        eb_, ea_ = 3.0, -2.0
        # v20d (capture, bosse entourée = 2e avant la table : « un tout petit peu plus basse, qu'elle kick moins, un peu moins raide en bas,
        # que ça envoie moins vers la hauteur et plus sur la longueur ; petite correction ») : montée 20 % plus longue, hauteur x0,96
        # (pente max 42 -> 36°) ; sa crête ne bouge pas (la montée prend sur l'espace d'avant). « La table, rallonge-la de 50 cm de chaque
        # côté » : plateau +3,3 ft, pris sur l'espace avant et après la table (les autres bosses ne bougent pas)
        ib_ = it_ - 2; q_ = np.asarray(zionize([B_[ib_]])[0][2], float); kq = int(np.argmax(q_))
        q2 = np.r_[resample(q_[:kq + 1], 1.2), q_[kq + 1:]] * 0.96; d_b = (len(q2) - len(q_)) * 0.1
        B_[ib_] = ('raw', 'bosse ZION adoucie %.1f ft' % q2.max(), q2, 'T')
        B_[ib_] = zionize([B_[ib_ + 0] if False else L6B[ib_]])[0]   # v23 (« la 4e bosse, refais une bosse normale ; garde cet écart ») 
        B_[it_] = table_stt(7.0, extra=TABLE_PLUS)
        adj_ = {ib_ - 1: -d_b, it_ - 1: eb_ - TABLE_PLUS / 2, it_: ea_ - TABLE_PLUS / 2}
        g_ = (xW - (xLR + RB) - EXIT_U0 - END_GAP - sum(tlen(b) for b in B_) - sum(adj_.values())) / (len(B_) - 1)
        toks = []
        for k, b in enumerate(B_):
            toks.append(b)
            if k < len(B_) - 1:
                toks.append(('gap', round(g_ + adj_.get(k, 0.0), 1)))
    if ZION:   # v22 (« baisse le 1er appel, plus bas à droite, comme Saint-Thibéry, voire encore plus bas ») : droite 55 %
        SPLIT_Z['PAR-L6 triple, double, table, double'] = [(0.0, tlen(toks[:1]), 1.0, 0.8)]   # v23 : intérieur (droite) relevé 0,55 -> 0,8
    p.straight(xW - (xLR + RB), [lane_sec('PAR-L6 triple, double, table, double', toks, u0)], tag='L6 tribune Sud')
    p.turn(-180, R180, BIG, tag='T_C 180 droite (berm)')
    p.lanes = dict(x_end3=x_end3, R3=R3, zL5=zL5, zLD=zLD, zL3=zL3, zL2=zL2, zL1=zL1, zL6=zL6, xW=xW, xLR=xLR, xC=xC, xT5=xT5, xTB=xTB)
    return p


# ---------------------------------------------------------------- départ (22 grilles, comme JGSX)
N_GATES, GATE_PITCH = 22, 4.0
X_APEX_SHIFT, L3_ADVANCE = 6.0, 8.0     # v9 : sommet du 180 après le saut du milieu / avance du saut (ft)
L3_SHIFT, L2_SHIFT = 12.0, 10.0          # v13 (« plus d'espace entre chaque enchaînement ») : L3 12 ft et L2 / L1 22 ft plus au sud
#                                         -> couloir Est 22 ft plus long, 180 L3 -> L2 de rayon 37 ft
EXIT_U0 = 6.0 if ZION else 10.0          # v23 Zion (« moins d'élan sur toutes les sorties de virage ») : 10 -> 6 ft ; v13 : 1re bosse à 10 ft de la sortie des virages (plus de marque berm / appel)
L2_U0_V13 = 10.0
BERM_END_FADE = {'T_D ': (8.0, 35.0)}     # v20c (« le virage à gauche avant l'enchaînement finit dans la bosse, il y a un trait ; le faire
#   finir un peu plus tôt, en restant doux, limite moins haut ») : berm à zéro 8° avant la sortie, fondu sur les 35° d'avant
BERM_GAIN_TAG = {'T_D ': 1.05 if ZION else 0.95, **({'T_Bb': 1.15} if ZION else {})}   # v23 Zion : T_D plus haut ; T_Bb entrée plus haute   # v13 : appui après le saut du milieu un peu moins haut (était 1,15) ; v22 Zion : « plus bas » 0,95 -> 0,75
LD_SHIFT = 5.0                          # v10 : ligne de départ 5 ft plus loin du saut du milieu (place pour les tremplins FMX ;
#                                         plus loin, le bout des 22 grilles monte sur le pied du berm T_C : grilles plus plates)
L2_GAP, L2_U0 = 5.0, 10.0               # v9 : écart identique entre les 7 bosses de L2 ; v13 : 1re bosse à 10 ft du 180 (était 3 : marque)


def start(p):
    ln = p.lanes
    gx, gz = px_x(D["depart"]["grilles_x"]), ln['zLD']
    xm = ln['x_end3'] - ln['R3']                                       # v9 : sommet du 180 L3 -> L2 (sur le tour)
    merge = (xm, (ln['zL3'] + ln['zL2']) / 2)
    route = [('S', gx - (xm + RB)), ('T', 90, RB, None), ('TO', merge)]
    S0 = dict(gate=(gx, gz), heading=180.0, route=route, narrow=[(150.0, None), (gx - xm, 30.0)],
              finish=(FINISH_SEC, 2))
    from starts import StartRoute
    R = StartRoute(S0, N_GATES, GATE_PITCH)
    S0['merge'] = (float(R.merge[0]), float(R.merge[1])); S0['straight'] = R.s_straight; S0['length'] = R.L
    return S0


def fmx_ramps(path=None):
    """4 tremplins FMX (modèle acier ramp_50), 2 de chaque côté de L3, juste AVANT la butte (elle prend 90 ft de large : les
    places du visuel tombaient sur ses flancs), lèvres hors du couloir, visées sur le sommet de la butte."""
    path = path or paris()
    import layouts_sx as LS_
    g = next(g for g in path.segs if g['kind'] == 'S' and any(n == L3_SEC for _, _, n in g['sections']))
    prof, u0, name = next(sc for sc in g['sections'] if sc[2] == L3_SEC)
    it = [i for i in LS_.COMBOS[name]['items'] if 'butte' in i[0]][0]
    ub = u0 + it[1]                                         # pied amont de la butte
    i0, i1 = int(it[1] / 0.1), int(it[2] / 0.1); uc = u0 + it[1] + float(np.argmax(prof[i0:i1])) * 0.1
    c, s_ = np.cos(g['t']), np.sin(g['t']); n_ = np.array([-s_, c])
    P = lambda u, v: np.array([g['x0'] + u * c, g['z0'] + u * s_]) + n_ * v
    tgt = P(uc, 0.0)
    out = []
    # v10 (« les rampes plus collées, pas au milieu de la ligne droite de départ ») : plus près de l'appel (v 22 - 28 ft au lieu de 25 - 40)
    # v13 (« les 4 rampes, mais en que 2, d'un côté ») : 2 tremplins, côté L2 (plus d'espace depuis v13), loin du départ
    for du, v in ((-22.0, -24.0), (-38.0, -30.0)):
        lip = P(ub + du, v); d = tgt - lip
        out.append(dict(lip=(float(lip[0]), float(lip[1])), heading=float(np.arctan2(d[1], d[0]))))
    return out


# ---------------------------------------------------------------- v15 : version Zion
# Formes MESURÉES sur ZION.2025.SupercrossParis (paris2026/data/zion_formes.npz / .json) : bosse (29,8 ft, 4,27 ft), table (62 ft,
# 7,04 ft), whoop (19,8 ft, 3,14 ft, pas 22,6 ft) ; saut central et triple d'arrivée ZION non retouchés ; les obstacles de 2026
# (nombre, ordre, hauteurs) restent ceux de la version USLAND.
L2_NAME = 'PAR-L2 double triple triple (8 bosses)'
L2_GAP_Z = 10.0                   # v20 (« l'enchaînement après le saut du freestyle : moins d'écart ») : 15 -> 10 ft au sol (13 m crête à crête)
RF_GAP = 10.5                     # v18 : écart au sol entre bosses de la RF (A1 : 8 à 13 ft)
if ZION:
    ZF = np.load(os.path.join(HERE, "data", "zion_formes.npz"))
    Z25_TRIPLE = _split_after_first(_P25['triple_arrivee'], 'appel arrivee ZION 2025 (10,0)', 'triple arrivee ZION 2025 (6,0 / 11,2)', 'T')
    # v18 (« le double central, mets le double central du mien, du track qu'on a fait nous de base ») : saut du milieu de la version
    # USLAND (appel raidi v13, butte élargie v10), plus celui de ZION tel quel
    ZW_H = [2.58] + [3.14] * 7 + [2.87, 2.34, 1.17]          # 11 whoops sur le modèle des 10 de ZION (lancement, pleines, sortie)

    ZH = 1.10                                                  # v16 (« légèrement plus hautes, même forme »)

    def zsingle(h):
        h = h * ZH; p = ZF['single'] * (h / ZF['single'].max()); k = float(np.clip(np.sqrt(h / ZF['single'].max()), 0.85, 1.12))
        return ('raw', 'bosse ZION %.1f ft' % h, np.interp(np.linspace(0, len(p) - 1, int(len(p) * k)), np.arange(len(p)), p), 'T')

    def ztable(h):   # v17 (« les tables sont à l'envers ») : profil ZION retourné (sens de course inverse de ma mesure)
        h = h * ZH
        return ('raw', 'table ZION %.1f ft' % h, (ZF['table'] * (h / ZF['table'].max()))[::-1].copy(), 'T')

    def zwhoops():
        w = ZF['whoop'] / ZF['whoop'].max(); flat = np.zeros(int(round((22.6 - len(w) * 0.1) / 0.1)))
        parts = []
        for k, hh in enumerate(ZW_H):
            parts.append(w * hh)
            if k < len(ZW_H) - 1:
                parts.append(flat)
        return ('raw', 'whoops ZION x%d' % len(ZW_H), np.concatenate(parts), 'W')

    def zionize(toks):
        out = []
        for t in (toks if isinstance(toks, list) else [toks]):
            if not isinstance(t, tuple):
                out.append(zsingle(4.0)); continue
            if t[0] in ('scale', 'stretch'):
                out.append(ztable(t[2]) if t[1] == TABLE_B else zsingle(t[2]))
            elif t[0] == 'raw' and t[1].startswith('whoops 25 Paris'):   # v16 : nos whoops (Saint-Georges), pas celles de ZION
                out.append(whoops_zion())
            else:
                out.append(t)
        return out
    _tlen0 = tlen

    def tlen(tok):
        return _tlen0(zionize(tok if isinstance(tok, list) else [tok]))
    _sec0 = LS.sec
    LS.sec = lambda name, toks, u0: _sec0(name, zionize(toks), u0)

    def lane_sec(name, toks, u0, finish=False, **kw):                 # formes ZION telles quelles (pas de rounded())
        return LS.sec(name, toks, u0)


# ---------------------------------------------------------------- v18 : version RF
# « fais une troisième version avec les bosses de la RF, les virages RF aussi, tout RF ; juste le saut du freestyle, tu le gardes
# comme on a fait de base ». Formes MESURÉES sur RF Anaheim 1 2026 (mesure_rf.py) : bosse (26 ft, 3,4 ft), table (50 ft, 5,8 ft),
# whoop (19 ft, 3,0 ft, pas 20,6 ft), saut d'arrivée (appel 8,8 / réception 10,7 ft), table à double étage ; le saut du milieu
# (appel + butte) et les tremplins FMX restent ceux de la version USLAND ; le nombre, l'ordre et la hauteur des obstacles de 2026 aussi.
if RF:
    def _len_k(p, k):
        return np.interp(np.linspace(0, len(p) - 1, max(2, int(round(len(p) * k)))), np.arange(len(p)), p)

    def rf_single(h):
        p = np.asarray(RFF['single'], float); k = float(np.clip(np.sqrt(h / p.max()), 0.9, 1.2))
        return ('raw', 'bosse RF %.1f ft' % h, _len_k(p, k) * (h / p.max()), 'T')

    def rf_table(h):
        p = np.asarray(RFF['table'], float); k = float(np.clip(np.sqrt(h / p.max()), 0.9, 1.15))
        return ('raw', 'table RF %.1f ft' % h, _len_k(p, k) * (h / p.max()), 'T')

    def rf_whoops(n=8, pitch=20.6):
        """lancement RF (2,5 ft) puis n whoops RF au pas de la RF (20,6 ft de crête à crête)."""
        w = np.asarray(RFF['whoop'], float); la = np.asarray(RFF['wlaunch'], float)
        step = int(round(pitch / 0.1)); q = np.zeros(len(la) + step * n + len(w))
        q[:len(la)] = la; i0 = len(la) + int(round(1.0 / 0.1))
        for k in range(n):
            j = i0 + k * step; q[j:j + len(w)] = np.maximum(q[j:j + len(w)], w)
        q = np.trim_zeros(q, 'b'); q = np.r_[q, 0.0]; q[0] = 0.0
        return ('raw', 'whoops RF x%d (lancement + %d)' % (n + 1, n), q, 'W')

    Z25_TRIPLE = [('raw', 'appel arrivee RF A1 (8,8)', np.asarray(RFF['fin_app'], float), 'T'), ('gap', float(RFF['fin_gap'])),
                  ('raw', 'reception arrivee RF A1 (10,7)', np.asarray(RFF['fin_land'], float), 'T')]

    def rfize(toks):
        out = []
        for t in (toks if isinstance(toks, list) else [toks]):
            if not isinstance(t, tuple):
                out.append(rf_single(4.0)); continue
            if t[0] in ('scale', 'stretch'):
                out.append(rf_table(t[2]) if t[1] == TABLE_B else rf_single(t[2]))
            elif t[0] == 'raw' and t[1].startswith('whoops 25 Paris'):
                out.append(whoops_up(9, 1.15))
            else:
                out.append(t)
        return out
    _tlen0 = tlen

    def tlen(tok):
        return _tlen0(rfize(tok if isinstance(tok, list) else [tok]))
    _sec0 = LS.sec
    LS.sec = lambda name, toks, u0: _sec0(name, rfize(toks), u0)

    def lane_sec(name, toks, u0, finish=False, **kw):                 # formes RF telles quelles (pas de rounded())
        return LS.sec(name, toks, u0)


if __name__ == "__main__":
    p = paris()
    print("tour : %.0f ft ; fermeture : (%.2f, %.2f, %.1f°)" % (p.s, p.x - p.segs[0]['x0'], p.z - p.segs[0]['z0'], np.degrees(p.t) % 360))
    for k, v in LOG.items():
        for name, u, L in v:
            print("  %-34s centre u=%6.1f ft  (L visuel %.1f ft)" % (name, u, L))
    print(start(p)['merge'], fmx_ramps())
