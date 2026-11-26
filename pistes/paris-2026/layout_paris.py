"""Tracé Supercross Paris 2026 dans l'arène agrandie (coordonnées monde MX, pieds).

Source : pistes/paris-2026/lecture_photos.json (relevé du visuel officiel, 0,665 ft/px).
Passage visuel -> monde : la vue de dessus est tournée de 180° (le départ regarde -x dans MX) :
    x = X0 + (948 - x_px) * S        z = Z0 - (y_px - 302) * S
  948 px = pied de la tribune Est du visuel = bout Sud du sol de l'arène (FLOOR_X_SOUTH x 1,35).
Virages : rayons JGSX (21,5 ft, berms mesurés) ; les 180° imposent 43 ft entre deux couloirs voisins
(visuel : ~48 ft) -> L1 et L6 sont rapprochés de ~5 ft, rien d'autre ne bouge.
Chaque obstacle = une unité JGSX mesurée (commun/lib/sx_units.json), centrée sur le milieu de l'obstacle du visuel ;
exceptions (formes créées, demandées par Ryan) : la grande table « SUPERCROSS Paris » (97 ft) et les 4 tremplins FMX.
"""
import os
import sys
import json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "commun/scripts"))
from engine import Path          # noqa: E402
from compose import lane, unit, whoops   # noqa: E402

D = json.load(open(os.path.join(HERE, "lecture_photos.json"), encoding="utf-8"))
S = D["echelle_ft_par_px"]
FT = 3.28084
PLAN_K = 1.55                     # v28 (« le stade plus autour de la piste » ; x1,52 demandé, x1,55 pour que le paddock tienne sans serrer les stands) ; avant 1,624 ; agrandissement en plan de l'arène (pistes/paris-2026/stade_paris/src/build.py) ; v5 : 1,35 -> 1,45 (paddock) ; v10 : x1,12 -> 1,624
FLOOR_X_SOUTH = -60.0 * PLAN_K    # m (dims.FLOOR_X_SOUTH x K)
OX, OZ = 549.0, 593.5             # origine du repère de l'arène dans le terrain (ft) : bâtiment centré sur 1187 ft
# v28 (stade x1,55) : piste centrée en z dans le sol (68 ft entre la ligne de course et la tribune en haut et en bas) ; 35 ft
# côté sable (était 48,5) pour garder la place du paddock derrière les virages Ouest
TRACK_DX, TRACK_DZ = -13.5, -24.69
X0 = OX + FLOOR_X_SOUTH * FT + TRACK_DX
Z0 = OZ + TRACK_DZ
BIG, BIG2 = 'big_det_a', 'big_cle'
RB = 21.5
ZION = os.environ.get('PARIS_ZION') == '1'      # v15 : « version Zion » (pistes/paris-2026/build_zion.py)
# v16 (« on garde pas les virages de ZION, ça fait un bug ») : virages USLAND (rayon 21,5 ft, berms JGSX) aussi en version Zion
XW_SHIFT = 3.0 if ZION else 0.0   # v23c (« les virages sont encore trop loin ; les whoops doivent être en sortie de virage ») : 23 -> 3 ft (L5, L6, L2, L1 20 ft plus courts) ; # v15 : couloirs allongés vers l'est (place libre du sol agrandi) pour les écarts ZION ;
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
FMX_MODEL = dict(model='ramp_50', model_len=18.47)   # tremplin acier de Ryan (commun/assets/fmx_ramp_user), lèvre 9 ft, collision .shp
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
_APP_SGM = smooth_takeoff(4.5, 10.5, 1.8, 13.0, 0.8, pad=0.4)   # v23e : un peu plus haut, plus de terre derrière (4,0 -> 4,5 ft ; dos 9 -> 13 ft)   # v23 (« l'appel plus raide, comme le double de Saint-Georges ») : appel du double L3 de Saint-Georges (~36°)
PRE_FINISH_Z = [_APP_SGM, ('gap', round(22.7 - (len(LS.L('tmp', [_APP_SGM])) - len(LS.L('tmp', [_APP_OLD]))) * 0.1, 1)), ('stretch', SA[1], 7.0, 1.9)]   # v23c : réception plus haute, plus ronde, plus de terre (5,8 -> 7,0 ft)   # v19 (Zion) : vrai petit double, appel pointu ;
#   v19d (« la bosse entourée, mets-la 4 mètres plus loin ») : réception 13 ft plus loin (7 -> 20 ft)
TRIPLE_EARLY = 12.0 if ZION else 20.0   # v23f : L5 8 ft plus court, le triple ne bouge pas par rapport au double
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


# v24 : panneaux des sauts (contours dessinés par l'utilisateur sur les vues de côté) ; v24b (« un contour en bois avec une bâche autour,
# incrusté dans la bosse, collé, pas trop fin ; le Milwaukee un peu plus haut ») : plan du panneau à BOARD_VB ft de l'axe (bord du dessus
# du saut), épaisseur BOARD_TH ; la terre du flanc au-delà est enlevée (build_paris.board_cut)
# v25c (« de près ça fait des trucs bizarres ») : trapèzes de l'utilisateur élargis juste ce qu'il faut pour couvrir toute la terre du saut
# (pentes droites, plateau), sinon la terre traverse la bâche
BOARD_POLY = dict(milwaukee=[(142.0, 0.0), (153.5, 13.1), (163.5, 13.1), (181.0, 0.0)],   # v25e : haut au ras du saut (13,1 ft)
                  amv=[(133.0, 0.0), (163.8, 23.4), (184.0, 23.4), (232.0, 0.0)])
BOARD_LANE = dict(milwaukee='LR', amv='L3')
BOARD_VB = dict(milwaukee=18.5, amv=28.0)
BOARD_TH = 1.0
RB_L5B = 32.0   # v27d : remis comme la v25f (« remets comme avant l'après-arrivée ») ; v27b (« après l'arrivée, que ça aille plus loin, la partie gauche un peu plus longue, et tourne à gauche ») : 32 -> 26 ft, ligne droite entre les 2 virages 6 ft plus longue ; v23f (« l'angle du virage encore un peu plus ouvert ») : 26 -> 32 ft
XW_BOT = 8.0 if ZION else 0.0   # v23f (« avant le saut d'arrivée, après l'enchaînement, le virage est trop loin ») : L5 et L6 8 ft plus courts
XW_TOP = 9.0 if ZION else 0.0   # v23e (« les whoops commencent encore trop tard après le virage ; le virage encore trop loin de l'enchaînement ») : L2 et L1 10 ft plus courts
END_GAP = 4.0 if ZION else 8.0   # v23 Zion (« entre la dernière bosse de chaque enchaînement et le virage, réduis l'écart ») : 8 -> 4 ft
SPLIT_Z = {}      # v22 : section -> [(début ft, fin ft, k gauche, k droite)] ; obstacle plus bas d'un côté (gauche/droite du sens de course)
SAND_HW = 14.0    # v25e (« pas sur le bord de la piste, vraiment dans la piste, coupé droit ») : demi-largeur du sable (ft)
SAND_TURN_F = 0.6   # v25e (« ça part du truc à l'intérieur ») : le sable commence dans le virage avant LR, à 60 % du virage
SAND_LR = None    # v22 : (u début, u fin) de la partie sable de LR (ornières) ; rempli par paris()


def pts_prof(pts, sig=0.8):
    """v22 : profil (pas de 0,1 ft) d'après des points (u ft, h ft) tirés des dessins de l'utilisateur, lissé (sig ft), bouts à 0."""
    from scipy.ndimage import gaussian_filter1d
    P = np.asarray(pts, float); u = np.arange(0, P[-1, 0] + 1e-9, 0.1)
    p = gaussian_filter1d(np.interp(u, P[:, 0], P[:, 1]), sig / 0.1, mode='nearest'); p = np.clip(p - max(p[0], p[-1]), 0, None)
    return p


# v22 (dessin sur le profil L3) : « pas un roller, une petite table creusée, un peu plus longue qu'une table de base ; un appel un peu
# raide, ça se recreuse un petit peu, et hop le plat avec la table »
def table_creusee(k=1.0, hb=4.4):
    """v23 : la petite table creusée allongée k fois (moins raide), appel un peu plus haut (3,6 -> 4,0 ft) ; hb = hauteur du bout."""
    P = [(0, 0), (1.0, 0.1), (4.6, 4.0), (6.2, 3.95), (9, 3.0), (13, 2.8), (16, 3.2), (19.5, hb - 0.1), (21.5, hb), (23.5, hb - 0.4), (27.5, 2.2), (31, 0.5), (33, 0)]
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
POST_FIN_V23B = dict(b1=[(25, 0), (28.5, 0.7), (31.5, 1.9), (33.5, 2.2), (35.5, 1.9), (38.5, 0.6), (41, 0)],
                     b23=[(43, 0), (47, 0.8), (52, 2.9), (56, 3.9), (58, 4.0), (60, 3.7), (63, 2.9), (66, 2.6), (88, 2.6), (94, 1.6), (100, 0.4), (105, 0)],
                     out_k=1.0)
# v23c (« la même forme, plus gros : 1re bosse un peu plus haute ; x2 l'espace entre la 1re et la 2e (à peine une moto passe) ; la 2e
# légèrement plus haute ; le truc qui tourne moins sur place, plus large ») : 2,6 ft ; creux 2x plus long ; 4,3 ft ; plateau plus long
POST_FIN_V23C = dict(b1=[(24, 0), (27.5, 0.8), (30.5, 2.2), (32.5, 2.6), (34.5, 2.2), (37.5, 0.7), (40, 0)],
                     b23=[(48, 0), (52, 0.9), (57, 3.1), (61, 4.2), (63, 4.3), (65, 4.0), (68, 3.1), (71, 2.8), (96, 2.8), (102, 1.7), (108, 0.4), (113, 0)],
                     out_k=1.0)
# v23e (« la 1re bosse un peu plus haute, moins ronde : un appel, surtout à droite ; garde-la comme ça à l'intérieur ; encore plus d'écart
# entre la 1re et la 2e ; la 2e un peu plus raide ») : b1 (intérieur) = v23c, b1o (extérieur, droite) = appel 3,0 ft ; 2e bosse 10 ft
# après la fin de la 1re, montée sur 6 ft ; virage T_L5b plus large (rayon 26)
POST_FIN_V23E = dict(b1=[(24, 0), (27.5, 0.8), (30.5, 2.2), (32.5, 2.6), (34.5, 2.2), (37.5, 0.7), (40, 0)],
                     b1o=[(25, 0), (28, 0.5), (30.5, 1.5), (32.5, 2.6), (33.6, 3.0), (34.6, 2.7), (37, 1.2), (40, 0)],
                     b23=[(50, 0), (52.5, 0.8), (55.5, 3.0), (57.5, 4.2), (59, 4.4), (61, 4.1), (64, 3.2), (67, 2.9), (92, 2.9), (98, 1.8), (104, 0.4), (109, 0)],
                     out_k=1.0)
# v23f (« encore plus d'espace entre la 1re et la 2e bosse, bien plus ») : 2e bosse 15 ft après la fin de la 1re ; virage T_L5b rayon 32
POST_FIN_V23F = dict(b1=POST_FIN_V23E['b1'], b1o=POST_FIN_V23E['b1o'],
                b23=[(55, 0), (57.5, 0.8), (60.5, 3.0), (62.5, 4.2), (64, 4.4), (66, 4.1), (69, 3.2), (72, 2.9), (96, 2.9), (102, 1.8), (108, 0.4), (113, 0)],
                out_k=1.0)
# v27c (« l'écart entre la 1re et la 2e bosse doit être plus long, pour qu'on tourne derrière ») : 1re bosse 4 ft plus tôt, 2e bosse et
# plateau 4 ft plus tard (8 ft de plus entre les deux)
_sh = lambda pts, d: [(a + d, b) for a, b in pts]
POST_FIN_V27C = dict(b1=_sh(POST_FIN_V23F['b1'], -4.0), b1o=_sh(POST_FIN_V23F['b1o'], -4.0), b23=_sh(POST_FIN_V23F['b23'], 4.0), out_k=1.0)
POST_FIN = POST_FIN_V23F          # v27d : remis comme la v25f
# v28m (croquis vert sur la vue de dessus : le virage T_L5b avec un appui à l'extérieur) : plus de 2e bosse + plateau qui tournait
# dans T_L5b (la trace passait au milieu) ; T_L5b porte un berm JGSX à l'extérieur (comme T_L5a) ; la 1re bosse (roller dans T_L5a) reste
L5B_BERM = False   # v28n (« pas du tout, remets comme avant ») : False = comme la v25f
if L5B_BERM:
    POST_FIN = dict(POST_FIN_V23F, b23=[(0, 0), (1, 0), (2, 0), (3, 0)])
# v28o (« la 2e bosse un angle légèrement plus doux, avec l'intérieur ça fait un à-coup ; la petite ligne droite doit faire 21 ft, le plateau ») :
# montée de la 2e bosse sur 12 ft au lieu de 9 (crête au même endroit, 4,4 ft), plateau 2,9 ft sur 21 ft au lieu de 24, descente identique
POST_FIN_V28O = dict(POST_FIN_V23F, b23=[(52, 0), (55.5, 0.7), (59.5, 2.8), (62.3, 4.1), (64, 4.4), (66, 4.1), (69, 3.2), (72, 2.9), (93, 2.9),   # v28q : remis à 26° (v28o, « c'était bien »)
                                         (99, 1.8), (105, 0.4), (110, 0)])
if not L5B_BERM:
    POST_FIN = POST_FIN_V28O
# v31 (photo IRL annotée : « plus long, garde l'angle rouge mais plus loin ; la sortie pour aller dans la ligne droite ne doit pas être au même
# endroit ») : après l'arrivée, ligne droite (T_L5 milieu) 15 -> 36 ft ; T_L5b (rayon 32) et sa bosse / plateau (b23) gardés, décalés d'autant ;
# la ligne de départ du TOUR passe AF_EXT ft plus au nord (les grilles et le couloir de départ ne bougent pas), T_B milieu raccourci d'autant
AF_EXT = 6.0 if ZION else 0.0     # v32 (« beaucoup trop long, 36 ft, mets 21 ») : 21 -> 6 (ligne droite 15,3 + 6 = 21,3 ft)
# v32 (« l'arrivée est un peu trop longue : l'appel tu touches rien, les 2 bosses du triple avance-les de ~10 ft, le virage aussi ; la ligne du
# freestyle, du saut jusqu'au virage, recule-la de 10 ft (les plots avec) ; comme ça la ligne LR (sable) rentre de 10 ft vers l'intérieur »)
FIN_SHORT = 10.0 if ZION else 0.0
# v33 (capture depuis le début de LR : « le virage entouré (T_D), pousse-le un peu ; la ligne LR (sable), bouge-la au maximum jusqu'à ce
# que ça touche l'appui ; ça va décaler toute la partie jusqu'au départ ») : T_D (+ freestyle, L2, T1) 5 ft de plus ; LR 12 ft de plus
# (bord de LR au pied de l'appui de T_D) ; tout le bas (L6, T_C, L5, après-arrivée) suit LR : mêmes distances, la ligne de départ raccourcit
L3_SHORT = 15.0 if ZION else 0.0   # v33 : 10 -> 15
LR_WEST = 22.0 if ZION else 0.0    # v33 : 10 -> 22
TC_EAST = 10.0 if ZION else 0.0    # v35 : encore 5 ft (5 -> 10) ; v34 : T_C 5 ft plus près (L6 et L5 5 ft plus courtes côté T_C)
BOT_UP = 5.0 if ZION else 0.0      # v34 : le bas remonte de 5 ft (LR 5 ft plus courte après le triple, U du bout de la ligne de départ 5 ft plus court)
if L3_SHORT:   # le saut du freestyle recule de L3_SHORT ft : ses panneaux AMV (BOARD_POLY, u depuis la sortie de T_Bb) avec lui
    BOARD_POLY['amv'] = [(u_ - L3_SHORT, y_) for u_, y_ in BOARD_POLY['amv']]
if AF_EXT:
    POST_FIN = dict(POST_FIN, b23=[(s_ + AF_EXT, h_) for s_, h_ in POST_FIN['b23']])
# v31 (2 points orange de Ryan sur sa capture en jeu, projetés sur le plan : grille de départ + panneaux AMV comme repères, ±5 ft) :
# 2 poteaux gonflables dans le U du bout de la ligne de départ (T_Ba / T_Bb), à la place du poteau automatique de T_Bb
T_B_PYLONS = [(608.5, 600.2), (608.3, 622.0)] if ZION else []   # 2e point projeté à z 630 = sur le flanc de L3 (socle pas à plat) : 8 ft vers l'intérieur du U
CAMEL_V22D = CAMEL
# v23 (« un peu plus haut ; la face beaucoup plus raide, le bas toujours smooth ; un petit creux avant, que ça redescende presque au sol du stade
# avant la face ; plus de cran ; la réception moins raide ») : replat de terre 0,4 ft, creux à 0,05, face concave jusqu'à ~60°, 11,6 ft,
# dessus 6 ft, réception ~25° sur 27 ft
CAMEL = pts_prof([(0, 0), (2, 0.35), (7, 0.4), (9.5, 0.05), (11, 0.15), (13, 0.9), (15, 2.4), (16.5, 4.3), (17.8, 6.6), (18.8, 8.8),
                  (19.6, 10.6), (20.4, 11.4), (21.5, 11.6), (27.5, 11.6), (29, 11.3), (33, 9.6), (38, 7.0), (44, 4.0), (50, 1.5), (54, 0.3),
                  (56, 0)], 0.5)
CAMEL_V23 = CAMEL
# v23c (dessin sur la vue en jeu : « garde l'appel aussi raide, fais le petit étage qu'il a de base : raide, un petit plat, et la pente
# reprend avec le même angle ») : face raide jusqu'à ~6,5 ft, palier de ~2,8 ft, face raide jusqu'à 11,6 ft ; dessus et réception inchangés
CAMEL = pts_prof([(0, 0), (2, 0.35), (7, 0.4), (9.5, 0.05), (11, 0.15), (13, 0.9), (14.6, 2.6), (15.8, 4.6), (16.8, 6.0), (17.6, 6.4),
                  (19.6, 6.6), (20.6, 7.4), (21.6, 9.4), (22.4, 11.0), (23.2, 11.5), (24.2, 11.6), (30, 11.6), (31.5, 11.3), (35.5, 9.6),
                  (40.5, 7.0), (46.5, 4.0), (52.5, 1.5), (56.5, 0.3), (58.5, 0)], 0.45)
CAMEL_V23C = CAMEL
# v23e (« la réception moins douce, plus raide ; légèrement plus haut ; l'appel aussi bas, la 2e partie monte plus haut ») : palier inchangé,
# haut 13 ft, réception ~33° sur 20 ft
CAMEL = pts_prof([(0, 0), (2, 0.35), (7, 0.4), (9.5, 0.05), (11, 0.15), (13, 0.9), (14.6, 2.6), (15.8, 4.6), (16.8, 6.0), (17.6, 6.4),
                  (19.6, 6.6), (20.6, 7.6), (21.6, 10.0), (22.4, 12.0), (23.2, 12.8), (24.2, 13.0), (30, 13.0), (31.2, 12.7), (34.5, 10.6),
                  (38.5, 7.6), (42.5, 4.4), (46.5, 1.6), (49.5, 0.3), (51, 0)], 0.45)
CAMEL_U = 131.0   # v22d (« mets le saut Milwaukee plus centré vers mon trait », trait à ~158 ft) : centre du saut à 158 ft (était 118 -> 134)
# v28p (croquis : 2 traits sur le sable de LR, « coupe, toute la partie du bas remonte, le reste identique ») : 32 ft de sable plat
# enlevés dans LR (entre u 48 et 80, avant le 2e roller) ; tout le bas (L5, après-arrivée, LD + départ, L6, T_C, T_E) remonte de 32 ft
SAND_CUT = 32.0
# v28q (croquis : cadre vert autour de T_Bb + L3, flèche « 15 » vers T_D : « la ligne avec le saut freestyle, avance-la de 15 ft, même
# le virage, toute cette partie ») : T_Bb et tout L3 15 ft plus près de T_D
L3_EAST = 15.0
L3_TO_L2 = 6.0   # v28t : T_Bb + L3 6 ft plus près de L2 -> T_D plus serré (rayons -3 ft)
T_D_CUT = 15.0   # v28q : T_D commence 15 ft plus tard (voir paris())
T_D_PYLON = (-16.7, 8.4)   # v28v : replacé au 2e point (était -22,2 / 11,7) ; v28u (« replace le plot de l'inter à mon point ») : position du poteau de T_D, relevée sur le croquis
CAMEL_U -= SAND_CUT
# v29b (capture en jeu : « le saut Milwaukee est complètement buggé ») : en v28p le saut a reculé de 32 ft mais pas ses panneaux
# (BOARD_POLY, utilisé aussi pour les bâches, les ballots du dessus et la coupe) -> panneaux 32 ft devant la terre ; décalés avec lui
BOARD_POLY['milwaukee'] = [(u_ - SAND_CUT, y_) for u_, y_ in BOARD_POLY['milwaukee']]
# v22 (dessin sur L1) : « après les whoops, comme une whoops en plus, sauf que ça fait une table plate d'à peu près la longueur d'une
# table normale ; ça redescend »
TABLE_PLATE_L1_V23C = pts_prof([(0, 0), (3, 1.0), (6, 2.9), (8.5, 3.4), (19, 3.6), (29, 4.25), (31.5, 4.4), (34.5, 3.6), (39, 0.9), (42, 0)], 0.8)
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


RF = os.environ.get('PARIS_RF') == '1'           # v18 : « version RF » (pistes/paris-2026/build_rf.py)
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
    zL5 += SAND_CUT if zL3 > zL5 else -SAND_CUT; zLD += SAND_CUT if zL3 > zLD else -SAND_CUT   # v28p : le bas remonte (vers L3)
    if ZION:   # v34 (zone entourée en bleu : « tu coupes 5 ft là (LR après le triple), puis tu pousses 5 ft vers le haut ») : le bas (L5, L6, ligne de départ + grilles) remonte de BOT_UP ft
        zL5 += BOT_UP if zL3 > zL5 else -BOT_UP; zLD += BOT_UP if zL3 > zLD else -BOT_UP
    if ZION:   # v23c (« le virage plus tôt, rapprocher le virage de la bosse » ; déjà « plus serré ») : L3 12 ft plus près de L2 (180 de rayon -6 ft)
        zL3 += 12.0 if zL2 > zL3 else -12.0
        zL3 += L3_TO_L2 if zL2 > zL3 else -L3_TO_L2   # v28t (« la section entourée, pousse-la un peu du côté L2 pour que le virage soit plus serré »)
        if T_D_RF:   # v28 (« le virage, mets un virage de la RF, ça passe trop vite ») : 180 au rayon de la RF (A1 : 24,4 ft), L3 plus près de L2
            zL3 = zL2 - 2 * T_D_RF if zL2 > zL3 else zL2 + 2 * T_D_RF
    zL1, zL6 = zL2 + 2 * R180, zL5 - 2 * R180        # 180° JGSX : couloirs voisins à 43 ft (v19 Zion : 55 ft)
    xW = px_x(312.0) + XW_SHIFT                        # virages Ouest (T1, T_C) : x des sorties de 180°
    xLR, xC, xT5 = px_x(860.0) - XLR_SHIFT, px_x(778.0), px_x(785.0)
    if ZION:   # v32 : ligne LR (sable) LR_WEST ft vers l'intérieur ; virage après l'arrivée FIN_SHORT ft plus tôt (triple raccourci)
        xLR += LR_WEST; xT5 += FIN_SHORT + LR_WEST - TC_EAST   # v33 : le bas suit LR (après-arrivée décalé d'autant) ; v34 : L5 suit T_C (mêmes distances)
    xTB = px_x(315.0) - (L3_EAST if ZION else 0.0)   # v28q : T_Bb + L3 avancés de L3_EAST ft vers T_D (la ligne de départ raccourcit d'autant)
    R3 = (zL2 - zL3) / 2
    xWb = xW - XW_BOT + (LR_WEST - TC_EAST if ZION else 0.0)   # v33 : T_C suit LR -> L6 et L5 gardent leur longueur ; v34 : T_C TC_EAST ft plus près
    p = Path(xWb, zL5, 180.0, 'PARIS')
    # L5 : single, single, SAUT D'ARRIVÉE (obstacles 3 + 4 du visuel = un double : appel / réception), table longue
    toks, u0 = from_render('L5', xWb, 'x', -1, {(1, 2): SMALL_DBL, (3, 5): Z25_TRIPLE},
                           lane_len=xWb - (xT5 + RB))   # v4 : le triple d'arrivée de ZION 2025 couvre les obstacles 3 à 5 du visuel
    # v13 (« le double plus en sortie de virage et un peu plus long ; le triple est bien ») : le triple reste où il est, le double
    # commence à EXIT_U0 de la sortie du virage, plus long (écart 8 -> 16 ft)
    i_t = next(i for i, t in enumerate(toks) if t[0] == 'raw'); u_app = u0 + tlen(toks[:i_t]) - XW_SHIFT
    pre, ue = PRE_FINISH, EXIT_U0
    if ZION:                    # v16 (« garde le double qu'on avait fait nous, pas celui de ZION ; rapproche-le du virage »)
        # v19 (« le petit double avant l'arrivée, plus raide, un peu plus haut ; là on dirait deux vagues ; un vrai double avec un appel
        # un peu pointu, comme à Saint-Georges, qui décolle pas trop, qui va pas loin ») : appel étroit 4,8 ft, réception 5,2 ft, 7 ft
        pre = [t if t[0] == 'gap' else ('raw', 'double USLAND', np.asarray(LS.L('tmp', [t]), float), 'T') for t in PRE_FINISH_Z]; ue = 1.0   # v23e : vraiment en sortie de virage
        # v19 (« plus d'espace entre le petit double et le triple d'arrivée, moins de ligne droite après le triple ») : le triple finit
        # à 8 ft du virage
        if FIN_SHORT:   # v32 (« l'appel tu touches rien ; les 2 bosses du triple tu les avances de ~10 ft, le virage aussi ») : FIN_SHORT ft
            # enlevés dans le creux plat entre l'appel et la bosse du milieu (fin de l'appel + début de la suite, là où c'est < 0,3 ft) :
            # l'appel ne bouge pas (u_app ci-dessous inchangé : L5 et le triple raccourcis d'autant), bosse du milieu + réception avancent
            a_ = np.asarray(toks[i_t][2], float); r_ = np.asarray(toks[i_t + 2][2], float); assert toks[i_t + 1][0] == 'gap'
            na_ = 0
            while na_ < int(round(FIN_SHORT / 2 / 0.1)) and a_[len(a_) - 1 - na_] < 0.3: na_ += 1
            nr_ = int(round(FIN_SHORT / 0.1)) - na_; assert np.all(r_[:nr_] < 0.3), r_[:nr_].max()
            toks = toks[:i_t] + [(toks[i_t][0], toks[i_t][1], a_[:len(a_) - na_], toks[i_t][3]), toks[i_t + 1],
                                 (toks[i_t + 2][0], toks[i_t + 2][1], r_[nr_:], toks[i_t + 2][3])] + toks[i_t + 3:]
            LOG['finish_cut'] = (round(na_ * 0.1, 1), round(nr_ * 0.1, 1))
        u_app = (xWb - (xT5 + RB)) - END_GAP - tlen(toks[i_t:]) - TRIPLE_EARLY   # v19d (« la pointe de l'appel du triple au trait orange,
        #   là il est un peu trop dans le virage ») : 20 ft plus tôt
    toks = pre + [('gap', round(u_app - ue - tlen(pre), 1))] + toks[i_t:]; u0 = ue
    if ZION:   # v22c (« le triple du saut d'arrivée comme à Saint-Georges : la bosse du milieu et la réception, une fusion entre les deux »)
        toks = [fuse_raw(t, 0.45) if t[0] == 'raw' and t[1].startswith('triple arrivee') else t for t in toks]   # v23f : creux un peu plus creusé (0,6 -> 0,45)
    p.straight(xWb - (xT5 + RB), [lane_sec(FINISH_SEC, toks, u0, finish=True)], tag='L5 arrivée')
    # v30 (photo IRL entourée : « change ces 2 endroits », choix « un grand demi-tour rond ») : après l'arrivée, T_L5a + T_L5b = un seul
    # demi-tour de rayon (zLD - zL5) / 2, sans ligne droite (2 moitiés de 90° gardées pour les murs / sponsors) ; L5 ne bouge pas,
    # la ligne de départ s'allonge côté est
    RL5_ = (zLD - zL5) / 2 if (ZION and ROUND_L5) else RB
    p.turn(90, RL5_, BIG, tag='T_L5a 90 gauche (berm)')
    RBb = RB_L5B if ZION else RB      # v23e (« le virage, ne le fais pas tourner aussi sec derrière, plus large, plus facile ») : rayon 21,5 -> 26 ft
    if ZION and AF_V28:
        # v28f (croquis de Ryan, trait B : « la nouvelle ligne pour traverser le départ en roulant ») : après T_L5a, plus de petite ligne
        # droite + 2e 90° + ligne de départ + 2 virages à droite : une grande courbe à gauche (AF_R1), une diagonale qui traverse la zone
        # de départ, une courbe à droite (AF_R2) qui arrive dans T_Bb (inchangé). Départ vers le nord (+z) -> vers +x, puis retour au nord.
        # v28g (« reprends la base d'avant, refais-la comme demandé plus longue ») : la traversée de la v28f d'origine (grande courbe,
        # longue diagonale) et les bosses RF (mesurées sur A1) sur le début de la diagonale, même écart de crête à crête
        bb_ = []
        for h_ in AF_BUMPS['h']:
            q_ = np.asarray(RFF['single'], float); q_ = np.maximum(q_, 0.0) * (h_ / q_.max()); bb_.append(('raw', 'bosse RF %.1f ft' % h_, q_, 'T'))
        toks_ = [bb_[0]]
        for b_ in bb_[1:]:
            toks_ += [('gap', round(AF_BUMPS['pitch'] - tlen(bb_[0]), 1)), b_]
        AF_SECS_ = lambda L: [lane_sec('PAR-LB bosses RF (traversee)', toks_, AF_BUMPS['u0'])] if AF_BUMPS['u0'] + tlen(toks_) < L - 10 else []
        X1, Z1 = xTB, zL3 - RB                                     # entrée de T_Bb (comme avant : fin de T_B milieu)
        dx_, dz_ = X1 - p.x, Z1 - p.z; Rs_ = AF_R1 + AF_R2
        assert abs(np.cos(p.t)) < 1e-6 and np.sin(p.t) > 0 and dx_ > 0, (p.t, dx_)
        lo_, hi_ = np.radians(5.0), np.radians(89.95)
        for _ in range(60):                                      # dx(θ) = Rs (1 - cos θ) + Ld sin θ, avec Ld tiré de dz
            m_ = (lo_ + hi_) / 2; Ld_ = (dz_ - Rs_ * np.sin(m_)) / np.cos(m_)
            if Rs_ * (1 - np.cos(m_)) + Ld_ * np.sin(m_) < dx_: lo_ = m_
            else: hi_ = m_
        th_ = np.degrees(m_); Ld_ = (dz_ - Rs_ * np.sin(m_)) / np.cos(m_); assert Ld_ > 20.0, Ld_
        LOG['B_v28f'] = dict(angle=round(th_, 1), diagonale=round(Ld_, 1))
        p.turn(th_, AF_R1, None, tag='T_LBa courbe gauche (traversee)')
        secB_ = AF_SECS_(Ld_); assert secB_, Ld_
        p.straight(Ld_, secB_, tag='LB traversee du depart')
        p.turn(-th_, AF_R2, None, tag='T_LBb courbe droite (traversee)')
    else:
        if ZION and ROUND_L5:
            RBb = RL5_
        if zLD - zL5 - RL5_ - RBb + AF_EXT > 0.05:   # v31 : + AF_EXT (ligne droite après l'arrivée plus longue)
            p.straight(zLD - zL5 - RL5_ - RBb + AF_EXT, tag='T_L5 milieu')
        p.turn(90, RBb, BIG if (ZION and L5B_BERM) else None, tag='T_L5b 90 gauche' + (' (berm)' if (ZION and L5B_BERM) else ''))
        p.straight((xTB - RB) - (xT5 + RB) - (RBb - RL5_), tag='LD ligne de départ (vers l ouest)')
        # v30 : bout de la ligne de départ -> L3 = un seul demi-tour de rayon (zL3 - zLD) / 2 (49 ft), sans ligne droite ; même sortie
        # (L3 et le saut du freestyle ne bougent pas), le sommet va ~28 ft plus loin vers l'ouest (côté grilles)
        RTB_ = (zL3 - zLD) / 2 if (ZION and ROUND_TB) else RB
        p.turn(-90, RTB_, None, tag='T_Ba 90 droite')
        if zL3 - zLD - 2 * RTB_ - AF_EXT > 0.05:   # v31 : la ligne de départ du tour est AF_EXT ft plus au nord -> T_B milieu plus court
            p.straight(zL3 - zLD - 2 * RTB_ - AF_EXT, tag='T_B milieu')
    p.turn(-90, RTB_ if not (ZION and AF_V28) else RB, BIG, tag='T_Bb 90 droite (berm)')
    x3 = xTB - RB
    # v9 (Ryan : « après le saut du milieu, aller plus dans le virage ; on peut pas tourner direct ; le virage en 1 fois pas 2,
    # un seul bloc à l'intérieur ») : T_C3 + colonne + T_D -> UN 180 à gauche de rayon (zL2 - zL3) / 2 = 32 ft, sommet 6 ft plus
    # loin que l'ancienne colonne, saut du milieu avancé de 8 ft (place pour poser puis tourner). Berm (gros croissant JGSX, décalé
    # au rayon 32 ft) sur la 2e moitié seulement : le départ arrive par l'extérieur de la 1re moitié (comme avant par la colonne).
    x_end3 = xC - X_APEX_SHIFT + R3 - (T_D_EAST if ZION else 0.0)   # v28b : T_D reculé vers le sable (LR)
    x_end3 += L3_SHORT if ZION else 0.0   # v32 : fin de L3 (saut du freestyle -> T_D) L3_SHORT ft plus courte : T_D et son plot reculent d'autant
    toks, u0 = from_render('L3', x3, 'x', -1, {(1, 2): Z25_MILIEU}, lane_len=x3 - x_end3 + (L3_SHORT if ZION else 0.0))   # v32 : même placement qu'avant, puis -L3_SHORT
    u0 -= L3_ADVANCE
    u0 += L3_EAST if ZION else 0.0                       # v28q : les obstacles de L3 avancent avec T_Bb (même u depuis sa sortie)
    u0 -= L3_SHORT if ZION else 0.0                      # v32 (« tout l'ensemble, du virage jusqu'à la réception du gros saut, recule de 10 ft ») : le saut du freestyle recule avec T_D
    if ZION:   # v23 (« baisse légèrement la hauteur de la réception » du saut freestyle) : butte x0,93
        toks = [('raw', t[1].replace('(24,2)', '(22,5)'), np.asarray(t[2], float) * 0.93, t[3]) if t[0] == 'raw' and 'butte' in t[1] else t for t in toks]
        # v23c (photo de côté : « le plat sur le dessus un peu plus long, en gardant la même distance de saut ; le plat vers la pelle, mêmes
        # angles ») : 7 ft de plat en plus devant le dessus, pris sur le creux avant la face (la descente de réception ne bouge pas)
        def _plat_devant(t, E=7.0):
            q = np.asarray(t[2], float); it_ = int(np.argmax(q > 0.97 * q.max())); k_ = int(round(E / 0.1))
            q2 = np.r_[q[k_:it_], np.full(k_, q[it_]), q[it_:]]
            # v23d (« tu fais un peu en 2 étages la récep ; le même plat, de l'angle de descente à l'angle en haut de la montée ; tu peux
            # laisser un peu bomber ») : un seul plateau entre les deux arêtes (>= 95 % du haut), légèrement bombé (+0,35 ft au milieu)
            ix_ = np.nonzero(q2 >= 0.95 * q2.max())[0]; a_, b_ = int(ix_[0]), int(ix_[-1]); tt = np.linspace(0, 1, b_ - a_ + 1)
            q2[a_:b_ + 1] = q2[a_] + (q2[b_] - q2[a_]) * tt + 1.0 * np.sin(np.pi * tt)   # v23f (« fais-le encore un peu bomber ») : +1,0 ft
            from scipy.ndimage import gaussian_filter1d   # v23f (« des angles très obtus : arrondis ») : arêtes adoucies sur ~4 ft
            w_ = np.zeros_like(q2); w_[max(0, a_ - 40):a_ + 40] = 1; w_[max(0, b_ - 40):b_ + 40] = 1; w_ = gaussian_filter1d(w_, 10)
            q2 = q2 * (1 - w_) + gaussian_filter1d(q2, 18) * w_
            return ('raw', t[1] + ' plat +7', q2, t[3])
        toks = [_plat_devant(t) if t[0] == 'raw' and 'butte' in t[1] else t for t in toks]
    secs3 = [LS.sec(L3_SEC, toks, u0)]
    if ZION:   # v20c (« ajoute un roller en sortie de virage avant le saut de freestyle ») : le roller de Saint-Georges (Custom1_g30_1,
        #   1,9 ft) à EXIT_U0 de la sortie de T_Bb, ~50 ft de plat avant l'appel
        rl_ = [('raw', 'roller Saint-Georges', np.asarray(LS.L('tmp', [ROLLER]), float), 'T')]
        rl_ = [('raw', 'petite table creusee 4,4 ft', TABLE_CREUSEE, 'T')]   # v22 : à la place du roller
        # v23 (« un peu moins raide, l'appel un peu plus haut, longueur x2,25 ») : x2,25 si ça tient avant l'appel du freestyle (22 ft d'élan)
        # v23c (« rallonge-le de la moitié ; la réception un peu plus haute ») : x1,74 -> x2,6 si ça tient (14 ft d'élan avant l'appel du freestyle)
        kL = min(2.6, (u0 - 14.0 - EXIT_U0) / tlen(rl_)); rl_ = [('raw', 'petite table creusee x%.2f' % kL, table_creusee(kL, 5.6), 'T')]
        LOG['table_creusee_k'] = round(kL, 2)
        assert EXIT_U0 + tlen(rl_) + 13.0 < u0, u0
        secs3.append(LS.sec('PAR-L3 petite table creusee', rl_, EXIT_U0))
    if ZION and T_D_CUT:   # v28q (« coupe le début du virage pour qu'il commence plus tard, on est obligé de tourner plus avant d'y rentrer ») :
        p.straight(x3 - x_end3 + T_D_CUT, secs3, tag='L3 grande table')
        # v28r (« remets le virage qu'on avait au début, mais juste court comme maintenant ») : plus de ligne droite ni de 90° serré :
        #   une seule courbe continue (comme le 180 d'origine), 90° de rayon R3 - cut/2 puis 90° à berm de rayon R3 + cut/2 ;
        #   même sortie sur L2 ; sommet 7,5 ft plus loin vers le sable (le départ y rejoint)
        p.turn(90, R3 - T_D_CUT / 2, None, tag='TD1 90 gauche (1re moitie de T_D)')
        apex_TD = (p.x, p.z)
        p.turn(90, R3 + T_D_CUT / 2, BIG, tag='T_D 90 gauche (berm 2e moitie)')
        p.segs[-1]['pylon_mid'] = float(np.arctan2(apex_TD[1] - p.segs[-1]['cz'], apex_TD[0] - p.segs[-1]['cx']))   # poteau au sommet, comme avant
        p.segs[-1]['pylon_dxz'] = T_D_PYLON   # v28u (point vert de Ryan) : poteau gonflable placé à la main (ft depuis le centre du berm)
    else:
        p.straight(x3 - x_end3, secs3, tag='L3 grande table')
        p.turn(180, R3, BIG, tag='T_D 180 gauche (berm 2e moitié)'); p.segs[-1]['berm_from'] = T_D_BERM_FROM if (ZION and T_D_RF) else (0.4 if ZION else 0.5)   # v23 : appui qui commence plus tôt
    # v7 (Ryan : « ça fait 4 d'entrée, ça doit faire 3, 4 et le 4 dur où faut pousser ») : les 7 bosses du visuel = un triple
    # serré (écarts 3 ft, bosses Arlington x1,2) puis un quad dur (écarts 7 ft, bosses x1,35), 20 ft entre les deux ;
    # près de la sortie du virage (pas d'élan trop long) - unités et réglages de Saint-Thibéry (up, rounded)
    # v9 (Ryan : « t'as fait un espace, nan, c'est le même espace entre chaque saut ; le but c'est que ça fasse 3 d'entrée et le 4
    # après dur, limite à passer que pour les bons ; là ça fait encore 4 d'entrée ») : 7 bosses identiques (celles du quad v7,
    # Arlington x1,35), même écart partout (L2_GAP), la 1re collée à la sortie du 180 (pas d'élan : pas de 4 d'entrée)
    # v10 (« le but c'est triple, triple et pas plus, ou triple 4 si très bon ; pas de 4 d'entrée ; comme Saint-Thibéry ») :
    # 7 bosses de la taille de Saint-Thibéry L2 (4,0 - 5,0 ft), même écart partout = toute la ligne (~12,5 ft au sol, ~40 ft de
    # crête à crête comme STT L2 « long triple, triple »), la 1re plus basse à 3 ft de la sortie du 180, la dernière à 8 ft du virage
    xWt = xW - XW_TOP + (L2_EXT if ZION else 0.0)   # v29b : L2 et L1 10 ft plus longs (place libre à l'ouest)
    B7 = [('scale', SA[1], 4.0), ('scale', SA[2], 4.6), ('scale', SA[0], 5.0), ('scale', SA[1], 4.8), ('scale', SA[2], 5.0),
          ('scale', SA[1], 4.6), ('scale', SA[2], 4.8)]
    B7 = [('stretch', b[1], b[2], 1.25) for b in B7]      # v13 (« un peu trop pointues : bosse, plat, bosse, plat ») : plus rondes,
    toks = even(B7, xWt - x_end3, L2_U0, 8.0)               #   même hauteur, même écart de crête à crête
    if ZION:                                               # v15 : écart ZION (15 ft au sol, ZION 9 - 16), le reste avant la 1re bosse
        toks = [B7[0]]
        for b_ in B7[1:]:
            toks += [('gap', L2_GAP_Z), b_]
        u0z = (xWt - x_end3) - 8.0 - tlen(toks)
        # v22 (« la 1re bosse très basse à gauche et basse à droite, double à droite, enrouler à gauche ; double-triple-triple ou
        # simple-triple-quadruple : rajoute une bosse ») : 8 bosses (ZION, 92 % de long), même écart, la 1re 2,8 ft à droite / 1,3 à gauche
        zb_ = lambda h: ('raw', 'bosse ZION %.1f ft' % h, resample(np.asarray(zsingle(h / ZH)[2], float), 0.92), 'T')
        B8 = [zb_(h) for h in (2.8, 4.6, 5.0, 4.8, 5.0, 4.6, 4.8, 4.6)]; u0z = 3.0
        # v23 (« moins d'écart entre la bosse haute à droite et la basse à gauche ; baisse la droite, moins raide, vrai double par-dessus »)
        B8[0] = ('raw', 'bosse ZION 2,3 ft (longue)', resample(np.asarray(zsingle(2.3 / ZH)[2], float), 1.1), 'T')
        # v23e (« la 2e bosse légèrement plus basse, plus ronde, plus de terre devant et derrière, surtout à droite ») : plus longue, droite 90 %
        B8[1] = ('raw', 'bosse ZION 4,6 ft (ronde)', resample(np.asarray(zsingle(4.6 / ZH)[2], float), 1.1), 'T'); u0z = 0.0   # v23f : même hauteur qu'avant, un peu plus ronde
        # v23c (« plus d'écart entre la 2e et la 3e bosse ») : +5 ft là, pris sur les autres écarts
        # v25d (« la 3e à 5 -> 4,8 ; la 6e à 4,6 -> 4,8 » ; « trop de distance à la sortie du virage et à la fin » ; « espace les 4
        # dernières bosses (3 cuvettes) un peu plus que les autres, un peu moins que l'écart entre la 4,6 et la 5 ») : bosses sans leur plat
        # aux bouts, 0,5 ft du virage au début et 1,5 ft à la fin ; écarts : G23 = g + 5, les 3 derniers G23 - 1, les autres g
        B8[2] = zb_(4.8); B8[5] = zb_(4.8)
        trim_ = lambda t: ('raw', t[1], np.asarray(t[2], float)[np.nonzero(np.asarray(t[2]) > 0.03)[0][0]:np.nonzero(np.asarray(t[2]) > 0.03)[0][-1] + 1], t[3])
        B8 = [trim_(b) for b in B8]; u0z = 0.5
        free_ = (xWt - x_end3) - 1.5 - u0z - sum(tlen(b) for b in B8); gz_ = (free_ - 17.0) / 7; assert gz_ > 2.0, gz_
        gaps_ = [gz_, gz_ + 5.0, gz_, gz_, gz_ + 4.0, gz_ + 4.0, gz_ + 4.0]
        # v25e (« le petit double en sortie de virage, la 1re bosse vraiment plus près du virage ; le double même taille ; plus d'écart entre
        # les bosses, presque autant que la ligne avant l'arrivée (~8,3 ft) mais moins ») : 1re bosse plus courte (crête plus près du virage),
        # écart du double gardé, les 6 autres écarts égaux (~8 ft)
        B8[0] = trim_(('raw', 'bosse ZION 2,3 ft', resample(np.asarray(zsingle(2.3 / ZH)[2], float), 1.0), 'T'))   # v25f : moins raide, plus ronde
        B8[1] = trim_(zb_(4.4))                                                       # v25f : 1re bosse de l'enchaînement un tout petit peu plus basse
        g_dbl = 3.6; free_ = (xWt - x_end3) - 1.5 - u0z - sum(tlen(b) for b in B8); g_o = (free_ - g_dbl) / 6
        gaps_ = [g_dbl] + [g_o] * 6
        toks = [B8[0]]
        for g__, b_ in zip(gaps_, B8[1:]):
            toks += [('gap', round(g__, 1)), b_]
        LOG['L2_gaps'] = [round(x, 1) for x in gaps_]
        SPLIT_Z[L2_NAME] = [(0.0, tlen(B8[0]), 1.5 / 2.3, 1.0)]   # v23f : 2e bosse plus coupée (« ça fait double, quadruple »)
        if L2_V26:
            # v26 (vidéos Roczen Paris 2026, « double technique mais propre pour enchaîner triple ; pas de triple d'entrée ; double bien et
            # triple sans faire double 4 ; à gauche simple triple ; la 1re bosse un peu plus tôt ») : 3 sauts comme en vrai (petit double,
            # triple, triple, puis on roule au virage). Bosses ZION posées à des crêtes fixées (ft depuis la sortie du 180) ; rôles :
            # 0 petite bosse d'entrée (droite 2,3 / gauche 0,8 : on l'enroule), 1 bosse coupée (droite = réception du double 3,9 ft,
            # gauche = appel du triple intérieur 5,6 ft), 2 appel du triple, 3 milieu bas (3 ft), 4 réception longue, 5-7 2e triple
            # (élan plus long avant, réception longue). Réglé avec pistes/paris-2026/sim_rythme.py (ESTIMATION balistique, pas le jeu).
            bb_ = [trim_(('raw', 'bosse ZION %.1f ft' % h, resample(np.asarray(zsingle(h / ZH)[2], float), k), 'T')) for h, k in zip(L2_V26['h'], L2_V26['k'])]
            # bosses qui se chevauchent (pieds) : comme un max des deux, la 1re coupée là où la 2e passe au-dessus, la 2e part de là
            pl_ = []                                                     # [début (ft depuis la sortie du 180), profil, nom]
            for c_, b_ in zip(L2_V26['crest'], bb_):
                p_ = np.asarray(b_[2], float); st_ = round(c_ - float(np.argmax(p_)) * 0.1, 1)
                if pl_ and st_ < pl_[-1][0] + len(pl_[-1][1]) * 0.1 - 0.05:
                    a0, pa = pl_[-1][0], pl_[-1][1]; i_a = int(round((st_ - a0) / 0.1)); n_ = len(pa) - i_a
                    cut = next(j for j in range(n_) if p_[j] >= pa[i_a + j])          # 1er point où la nouvelle bosse est au-dessus
                    pl_[-1][1] = pa[:i_a + cut]; p_ = p_[cut:]; st_ = round(st_ + cut * 0.1, 1)
                pl_.append([st_, p_, b_[1]])
            toks = []; sp26 = []; u0z = pl_[0][0]
            for i_, (st_, p_, nm_) in enumerate(pl_):
                if i_:
                    toks += [('gap', round(st_ - (pl_[i_ - 1][0] + len(pl_[i_ - 1][1]) * 0.1), 1))]
                kk = L2_V26['split'].get(i_)
                if kk:
                    sp26.append((st_ - u0z, st_ - u0z + len(p_) * 0.1, kk[0], kk[1]))
                toks += [('raw', nm_, p_, 'T')]
            assert all(t[1] > -0.05 for t in toks if t[0] == 'gap'), toks
            SPLIT_Z[L2_NAME] = sp26; LOG['L2_v26'] = [round(t[1], 1) for t in toks if t[0] == 'gap']
        if L2_V27:
            # v27 (test v26 : « ça va pas du tout, je fais 4-3-1 ; reprends les bosses du grand enchaînement L6, avant l'arrivée ; la bosse
            # dès la sortie du virage, qu'on n'ait pas le temps de prendre de la vitesse ; on rentre en double, pas en triple ») : les 5 bosses
            # de L6 (mêmes formes ZION, mêmes hauteurs, même écart de 8,3 ft et le 5,3 ft entre la 2e et la 3e... comme L6) + ses 2 bosses
            # d'après la table, la 1re à 0,5 ft de la sortie du 180, pas de coupe gauche / droite
            hz_ = [4.2, 4.7, 4.9, 4.7, 4.9, 4.3, 4.5]; bb_ = [zsingle(h) for h in hz_]
            free_ = (xWt - x_end3) - 0.5 - END_GAP - sum(tlen(b) for b in bb_); g_ = (free_ + 3.0) / 6     # 5,3 ft entre 3e et 4e comme L6
            gaps_ = [g_, g_, g_ - 3.0, g_, g_, g_]
            sp27 = []
            if L2_V27B:
                # v27b (test v27 : « la 1re 3,5 ft, celle d'après 4,7 ; la 1re plus basse à gauche ; après, ça fait 2-4 : des bosses plus
                # petites, moins kickantes, qu'on soit obligé de faire 3-3 ») : 8 bosses, 3,5 / 4,7 puis 6 bosses ZION de L2_V27B ft
                # rallongées x1,15 (face moins raide, envoient moins haut), même écart partout
                hz_ = [3.5, 4.7] + [L2_V27B] * 6
                bb_ = [('raw', 'bosse ZION %.1f ft' % h, resample(np.asarray(zsingle(h / ZH)[2], float), 1.0 if i < 2 else 1.15), 'T') for i, h in enumerate(hz_)]
                free_ = (xWt - x_end3) - 0.5 - END_GAP - sum(tlen(b) for b in bb_); gaps_ = [free_ / 7] * 7
                if L2_V27C:
                    # v27c (test v27b : « les autres bosses plus grosses, comme avant (L6) ; la 1re même grandeur, la 2e 4 ft, ensuite 4,5 ;
                    # que ça commence dès la sortie du virage ; on doit pouvoir faire 2-3 à l'entrée ») : 7 bosses ZION telles quelles (formes
                    # de L6, pas rallongées), 1re plus courte (crête plus près du virage), même écart partout
                    hz_ = [3.5, 4.0] + [4.5] * 5
                    bb_ = [('raw', 'bosse ZION %.1f ft' % h, resample(np.asarray(zsingle(h / ZH)[2], float), 0.8 if i == 0 else 1.0), 'T') for i, h in enumerate(hz_)]
                    free_ = (xWt - x_end3) - 0.5 - END_GAP - sum(tlen(b) for b in bb_); gaps_ = [free_ / 6] * 6
                if L2_V27D:
                    # v27d (capture en jeu : « la bosse dès la sortie du virage ; la 1re 20° d'angle, que ça fasse double ; la 2e 4,3 ft ; la 3e
                    # 21° pour pas que ça fasse 4 ; une bosse de plus à la fin : double, 3, 3 ») : 8 bosses ZION, angle de montée réglé en
                    # rallongeant la bosse (pente max de la face), même écart partout
                    def k_ang(h, deg):
                        q0 = np.asarray(zsingle(h / ZH)[2], float); lo, hi = 0.5, 3.0
                        for _ in range(30):
                            m = (lo + hi) / 2; q = resample(q0, m)
                            if 0.55 * np.max(np.diff(q)) / 0.1 > np.tan(np.radians(deg)): lo = m   # pente sur le terrain fini ~0,55 x la pente brute (pieds adoucis, coupe) : mesuré sur profil_L2 v27c
                            else: hi = m
                        return hi
                    spec_ = [(3.5, 20.0), (4.3, None), (4.5, 21.0)] + [(4.5, None)] * 5
                    bb_ = [('raw', 'bosse ZION %.1f ft%s' % (h, ' %d°' % a if a else ''), resample(np.asarray(zsingle(h / ZH)[2], float), k_ang(h, a) if a else 1.0), 'T') for h, a in spec_]
                    free_ = (xWt - x_end3) - 0.5 - END_GAP - sum(tlen(b) for b in bb_); gaps_ = [free_ / 7] * 7
                    sp27 = [(0.0, tlen(bb_[0]), 2.6 / 3.5, 1.0)]                 # 1re bosse : gauche 2,6 ft
                sp27 = [(0.0, tlen(bb_[0]), 2.6 / 3.5, 1.0)]                 # 1re bosse : gauche 2,6 ft, droite 3,5 ft
            toks = [bb_[0]]
            for g__, b_ in zip(gaps_, bb_[1:]):
                toks += [('gap', round(g__, 1)), b_]
            u0z = 0.5; SPLIT_Z[L2_NAME] = sp27; LOG['L2_v27'] = [round(x, 1) for x in gaps_]
        if L2_V28:
            # v28 (« mets les bosses de la RF ; 1re bosse dès la sortie du virage ; double sans pouvoir faire triple d'entrée ; à gauche
            # simple, double ; le but : extérieur double - triple - triple sans pouvoir faire autre chose, genre un quadruple ») : formes
            # MESURÉES sur RF Anaheim 1 (bosse 26 ft / 3,4 ft, grosse bosse 40 ft / 5,5 ft, mesure_rf.py), mises à l'échelle ; les 2 appels
            # des triples = grosse bosse RF, bosses du milieu plus basses ; crêtes réglées avec sim_rythme.py (ESTIMATION, pas le jeu)
            def rfb(h, key, k_=None):
                p_ = np.asarray(RFF[key], float); k_ = k_ or float(np.clip(np.sqrt(h / p_.max()), 0.9, 1.2))
                q_ = np.interp(np.linspace(0, len(p_) - 1, max(2, int(round(len(p_) * k_)))), np.arange(len(p_)), p_) * (h / p_.max())
                q_ = np.maximum(q_, 0.0)
                sm_ = L2_V28.get('smooth')
                if sm_:   # v28d (« trop d'angles, pas smooth ») : profil lissé (gaussienne de sm_ ft), même hauteur, pieds qui partent de 0
                    from scipy.ndimage import gaussian_filter1d
                    pad_ = int(round(3 * sm_ / 0.1)); q_ = gaussian_filter1d(np.r_[np.zeros(pad_), q_, np.zeros(pad_)], sm_ / 0.1)
                    q_ = q_[np.nonzero(q_ > 0.01)[0][0]:np.nonzero(q_ > 0.01)[0][-1] + 1] - 0.01; q_ = np.maximum(q_, 0.0) * (h / q_.max())
                return q_
            def land_trim_(q):
                # v34 (« T1 avancé de 5 ft pour le rapprocher », L2 ne change pas) : les LT ft du bout de la réception (bas, < ~0,7 ft) enlevés,
                # fondu à 0 sur 2 ft : la réception finit LT ft plus tôt, T1 arrive juste après (mêmes crêtes, même écart)
                LT = L2_V28.get('land_trim') or 0.0
                if not LT:
                    return q
                q = np.asarray(q, float)[:len(q) - int(round(LT / 0.1))].copy(); n_ = min(20, len(q) // 4)
                q[-n_:] *= (1 + np.cos(np.linspace(0, np.pi, n_))) / 2
                return q
            def bump_(i_, bsp_):
                # v29d (test v29c : « beaucoup trop lisse, ça fait des vagues ; des vrais enchaînements comme avant, mais 2 degrés de moins
                # d'angle sur chaque bosse ; la dernière fait une vraie réception, comme la table de L6 ») : bosses RF de la v29b (face
                # d'appel x spec 'front'), face encore étirée pour 'front_dd' degrés de moins (pente max) ; la 1re reste telle quelle
                q_ = rfb(bsp_[0], bsp_[1], bsp_[2] if len(bsp_) > 2 else None)
                if i_ == 0:
                    return q_
                zf_ = L2_V28.get('zion_from')
                if zf_ is not None and i_ >= zf_:
                    # v29e (« ensuite les bosses de ZION, de l'enchaînement L6, à la même taille qu'on a maintenant ») : forme ZION de L6
                    # (zsingle, même longueur auto que L6), à la hauteur de la spec ; pas d'étirement d'appel ; réception de la dernière gardée
                    q_ = np.asarray(zsingle(bsp_[0] / ZH)[2], float)
                    if L2_V28.get('land_last') and i_ == len(L2_V28['bumps']) - 1:
                        t_ = np.asarray(table_stt(7.0, extra=TABLE_PLUS)[2], float); kt_ = int(np.nonzero(t_ > t_.max() - 0.05)[0][-1])
                        ic_ = int(np.argmax(q_)); q_ = np.r_[q_[:ic_ + 1], t_[kt_ + 1:] * (q_[ic_] / t_[kt_])]; q_ = land_trim_(q_)
                    return q_
                def front_(q, k):
                    ic = int(np.argmax(q)); n = int(round(ic * k))
                    return np.r_[np.interp(np.linspace(0, ic, n + 1), np.arange(ic + 1), q[:ic + 1]), q[ic + 1:]]
                ang_ = lambda q: np.degrees(np.arctan(np.max(np.diff(q[:int(np.argmax(q)) + 1])) / 0.1))
                k0_ = L2_V28.get('front') or 1.0; dd_ = L2_V28.get('front_dd') or 0.0
                a_t = ang_(front_(q_, k0_)) - dd_; lo, hi = k0_, 3.0 * k0_
                for _ in range(40):
                    m_ = (lo + hi) / 2
                    if ang_(front_(q_, m_)) > a_t: lo = m_
                    else: hi = m_
                q_ = front_(q_, hi if dd_ else k0_)
                if L2_V28.get('land_last') and i_ == len(L2_V28['bumps']) - 1:
                    # réception de la table de L6 (Saint-Thibéry Arlington_g49_2 à 7 ft + 3,3 ft) : sa descente (21 ft), à la hauteur de la bosse
                    t_ = np.asarray(table_stt(7.0, extra=TABLE_PLUS)[2], float); kt_ = int(np.nonzero(t_ > t_.max() - 0.05)[0][-1])
                    ic_ = int(np.argmax(q_)); q_ = np.r_[q_[:ic_ + 1], t_[kt_ + 1:] * (q_[ic_] / t_[kt_])]; q_ = land_trim_(q_)
                return q_
            spec_ = dict(L2_V28)
            if spec_.get('fill'):
                # v28c (« l'enchaînement commence juste à la sortie du virage et finit juste avec le virage d'après, comme L6 ») :
                # 1re bosse à fill['start'] ft de la sortie, dernière à fill['end'] ft de T1 (L6 : 4,7 ft), même écart partout
                F_ = spec_['fill']; q0_, q1_ = rfb(*spec_['bumps'][0]), bump_(len(spec_['bumps']) - 1, spec_['bumps'][-1])
                k0t_ = int(np.argmax(q0_ > spec_['toe'])) if spec_.get('toe') else 0; c0_ = F_['start'] + (float(np.argmax(q0_)) - k0t_) * 0.1 * (spec_.get('front1') or 1.0); c1_ = (xWt - x_end3) - F_['end'] - (len(q1_) - float(np.argmax(q1_))) * 0.1
                r12_ = F_.get('r12', 1.0); sp_ = (c1_ - c0_) / (len(spec_['bumps']) - 2 + r12_)   # r12 : 1er écart = r12 x les autres
                if F_.get('pitch'):   # v28h (« 36 ft entre chaque ») : écart imposé, crêtes depuis la 1re
                    sp_ = F_['pitch']; r12_ = 1.0
                LOG['L2_fill'] = dict(c0=round(c0_, 1), c1_max=round(c1_, 1), last=round(c0_ + sp_ * (len(spec_['bumps']) - 1), 1))
                spec_['crest'] = [c0_] + [c0_ + sp_ * (r12_ + i) for i in range(len(spec_['bumps']) - 1)]
            pl_ = []                                                     # [début (ft depuis la sortie du 180), profil, nom]
            for c_, bsp_ in zip(spec_['crest'], spec_['bumps']):
                h_, key_ = bsp_[0], bsp_[1]; p_ = bump_(len(pl_), bsp_)
                frn_ = spec_.get('front')
                if False:   # v29d : fait dans bump_ (avec front_dd) ; v29b :   # v29b (« trop d'angle à l'appel, ça envoie hyper haut ; adoucis un tout petit peu ») : face d'appel étirée x frn_, crête au même endroit
                    ic_ = int(np.argmax(p_)); n_ = int(round(ic_ * frn_))
                    p_ = np.r_[np.interp(np.linspace(0, ic_, n_ + 1), np.arange(ic_ + 1), p_[:ic_ + 1]), p_[ic_ + 1:]]
                st_ = round(c_ - float(np.argmax(p_)) * 0.1, 1); nm_ = '%s %s %.1f ft' % ('grosse bosse' if key_ == 'big' else 'bosse', 'ZION' if L2_V28.get('zion_from') is not None and len(pl_) >= L2_V28['zion_from'] else 'RF', h_)
                if pl_ and st_ < pl_[-1][0] + len(pl_[-1][1]) * 0.1 - 0.05:   # pieds qui se chevauchent : comme un max des deux
                    a0, pa = pl_[-1][0], pl_[-1][1]; i_a = int(round((st_ - a0) / 0.1)); n_ = len(pa) - i_a
                    cut = next(j for j in range(n_) if p_[j] >= pa[i_a + j])
                    pl_[-1][1] = pa[:i_a + cut]; p_ = p_[cut:]; st_ = round(st_ + cut * 0.1, 1)
                pl_.append([st_, p_, nm_])
            fr_ = spec_.get('front1')
            if fr_:    # v28g (« la 1re plus douce à l'avant ») : face avant de la 1re bosse étirée x fr_ (crête au même endroit, début plus tôt)
                q_ = pl_[0][1]; ic_ = int(np.argmax(q_)); n_ = int(round(ic_ * fr_))
                fq_ = np.interp(np.linspace(0, ic_, n_ + 1), np.arange(ic_ + 1), q_[:ic_ + 1])
                pl_[0][1] = np.r_[fq_, q_[ic_ + 1:]]; pl_[0][0] = round(pl_[0][0] - (n_ - ic_) * 0.1, 1)
            toe_ = spec_.get('toe')
            if toe_:   # v28f (trait vert de Ryan : « la 1re bosse commence à mon trait », la sortie du virage) : pied de la 1re bosse coupé sous toe_ ft
                k0_ = int(np.argmax(pl_[0][1] > toe_)); pl_[0][1] = pl_[0][1][k0_:]; pl_[0][0] = round(pl_[0][0] + k0_ * 0.1, 1)   # v28h : le pied coupé commence à la sortie
            assert pl_[0][0] >= (spec_.get('fill') or {}).get('start', 0.0) - 0.05 and pl_[-1][0] + len(pl_[-1][1]) * 0.1 <= (xWt - x_end3) - ((spec_.get('fill') or {}).get('end', END_GAP)) + 0.05, pl_[-1][0]
            toks = []; u0z = pl_[0][0]
            for i_, (st_, p_, nm_) in enumerate(pl_):
                if i_:
                    toks += [('gap', round(st_ - (pl_[i_ - 1][0] + len(pl_[i_ - 1][1]) * 0.1), 1))]
                toks += [('raw', nm_, p_, 'T')]
            SPLIT_Z[L2_NAME] = [(0.0, len(pl_[0][1]) * 0.1, spec_['left1'], 1.0)]   # 1re bosse plus basse à gauche
            LOG['L2_v28'] = [round(t[1], 1) for t in toks if t[0] == 'gap']
    u0 = u0z if ZION else L2_U0                           # v18 (RF) : même écart partout comme la version USLAND (~8,5 ft, A1 : 8 - 13)
    sec2 = lane_sec(L2_NAME if ZION else 'PAR-L2 triple, triple (7 bosses, meme ecart)', toks, u0)
    if False:  # v23c : creux remontés (v23e : retiré, « des petits étages, des escaliers entre chaque bosse »)
        from scipy.ndimage import gaussian_filter1d
        from scipy.signal import find_peaks
        pr_ = sec2[0]; pk_, _ = find_peaks(pr_, prominence=1.0); a_, b_ = int(pk_[0]), int(pk_[-1])
        pr_[a_:b_] = np.maximum(pr_[a_:b_], 0.5 * gaussian_filter1d(pr_, 45)[a_:b_])
    p.straight(xWt - x_end3, [sec2], tag='L2 singles')
    p.segs[-1]['u_min'] = min(0.0, u0)   # v28j : la 1re bosse de L2 peut commencer dans la sortie de T_D (contrôle 2 de build_paris)
    p.turn(-180, R180, BIG2, tag='T1 180 droite (berm)')
    # v10 : 11 whoops (une petite + 10) plus hautes, plus rondes, plus de terre ; la table + 2 bosses gardées (« pas mal »)
    lL1 = xWt - (xLR + RB)
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
        # v23c (« table légèrement plus courte ; 1re bosse un tout petit peu plus haute ; plus d'espace entre les 2 dernières ; le roller plus haut »)
        toks = [whoops_zion(11), ('gap', 5.5), ('raw', 'table montante 4,4 ft', TABLE_PLATE_L1_V23C, 'T'), ('gap', 5.0), zb_(3.4), ('gap', 10.0), zb_(2.2)]
        # v25 (« la petite table après les whoops à la même distance que si c'était un whoops d'après ; décale tout le reste derrière ») :
        # le haut de l'appel de la table (~3,4 ft, comme une crête de whoops) au pas des whoops après la dernière crête ; les whoops ne
        # bougent pas (u0 gardé), la table et les 2 bosses avancent, la place gagnée va avant le virage
        from scipy.signal import find_peaks
        wq_ = np.asarray(toks[0][2], float); pk_, _ = find_peaks(wq_, prominence=0.8); pitch_ = float(np.median(np.diff(pk_))) * 0.1
        g_new = round(pk_[-1] * 0.1 + pitch_ - 8.5 - len(wq_) * 0.1, 1); u0_keep = lL1 - END_GAP - tlen(toks)
        toks = [toks[0], ('gap', max(0.5, g_new))] + toks[2:]
        LOG['L1_table_gap'] = (round(pitch_, 1), g_new)
    if RF:     # v18 : « garde nos whoops dans la version RF » : celles de la version Zion, 9 (11 : 39 ft de trop) ; table + 2 bosses RF
        toks = [whoops_up(9, 1.15), ('gap', 15.0), ('scale', TABLE_B, 6.6), ('gap', RF_GAP), ('scale', SA[1], 4.0), ('gap', RF_GAP), ('scale', SA[0], 3.6)]
    u0 = lL1 - END_GAP - tlen(toks); assert u0 >= 0.5, u0
    if ZION:
        u0 = u0_keep                                       # v25 : les whoops restent où elles sont
        u0 += LR_WEST if ZION else 0.0                     # v32 : LR rentrée de LR_WEST ft : L1 plus courte côté LR, les whoops restent à la même distance de T1
        u0 -= L2_EXT                                       # v29b : L1 rallongé de 10 ft : les whoops restent à la même distance de T1, la place va avant le virage NE
    p.straight(xWt - (xLR + RB), [LS.sec('PAR-L1 whoops, table, bosse', toks, u0)], tag='L1 whoops')
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
        zb2_ = lambda h: ('raw', 'bosse ZION %.1f ft' % h, resample(np.asarray(zsingle(h / ZH)[2], float), 0.94), 'T')
        tri_ = [zb2_(4.0), ('gap', 5.5), zb2_(4.1), ('gap', 5.5), zb2_(3.9)]   # v23c : entre les deux tailles, juste derrière le Milwaukee
        free = lLR - u0 - END_GAP - tlen([r1]) - tlen([r2]) - tlen([cam]) - tlen(tri_); creux = 3.0
        g1 = round(CAMEL_U - u0 - tlen([r1]) - tlen([r2]) - creux, 1)   # v22c : le saut commence à CAMEL_U ft du virage
        assert g1 > 15.0, free
        toks = [r1, ('gap', g1), r2, ('gap', creux), cam, ('gap', 13.5)] + tri_   # v23e : triple un peu plus près du virage (8 -> 12 ft) ; v25 : +1,5 ft
        SAND_LR = (0.0, u0 + tlen([r1]) + g1 + tlen([r2]) + creux + 2.0)
        SAND_LR = (0.0, CAMEL_U + 9.0)   # v25e (« arrête la sortie au trait rouge, au bas de la pelle Milwaukee »)
    p.straight((zL1 - RB) - (zL6 + RB), [lane_sec('PAR-LR sable, saut Milwaukee, triple' if ZION else 'PAR-LR saut de sortie, bosse, table, 3 bosses', toks, u0)], tag='LR tribune Est')
    p.turn(-90, RB, BIG, tag='T_E 90 droite (berm)')
    # v10 (« triple : 3 bosses, 2 bosses, une table, 2 bosses ») : bosses de Saint-Thibéry, même écart partout, 8 ft du virage
    # v13 : appel (1re bosse) un peu plus raide et un peu plus haut (« tu creuses un peu plus le bas »), sans aller plus loin ;
    # les autres bosses un peu plus hautes et plus rondes ; plus de marque berm / 1re bosse (EXIT_U0)
    L6B = [('stretch', SA[0], 4.2, 0.85), ('stretch', SA[2], 4.7, 1.15), ('stretch', SA[1], 4.9, 1.15), ('stretch', SA[3], 4.7, 1.15),
           ('stretch', SA[2], 4.9, 1.15), TABLE, ('stretch', SA[0], 4.3, 1.15), ('stretch', SA[1], 4.5, 1.15)]
    toks, u0 = even(L6B, xWb - (xLR + RB), EXIT_U0, 8.0), EXIT_U0
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
        g_ = (xWb - (xLR + RB) - EXIT_U0 - END_GAP - sum(tlen(b) for b in B_) - sum(adj_.values())) / (len(B_) - 1)
        toks = []
        for k, b in enumerate(B_):
            toks.append(b)
            if k < len(B_) - 1:
                toks.append(('gap', round(g_ + adj_.get(k, 0.0), 1)))
    if ZION:   # v22 (« baisse le 1er appel, plus bas à droite, comme Saint-Thibéry, voire encore plus bas ») : droite 55 %
        SPLIT_Z['PAR-L6 triple, double, table, double'] = [(0.0, tlen(toks[:1]), 1.0, 0.8)]   # v23 : intérieur (droite) relevé 0,55 -> 0,8
    p.straight(xWb - (xLR + RB), [lane_sec('PAR-L6 triple, double, table, double', toks, u0)], tag='L6 tribune Sud')
    p.turn(-180, R180, BIG, tag='T_C 180 droite (berm)')
    p.lanes = dict(apex_TD=(apex_TD if (ZION and T_D_CUT) else None), x_end3=x_end3, R3=R3, zL5=zL5, zLD=zLD, zL3=zL3, zL2=zL2, zL1=zL1, zL6=zL6, xW=xW, xLR=xLR, xC=xC, xT5=xT5, xTB=xTB)
    return p


# ---------------------------------------------------------------- départ (22 grilles, comme JGSX)
N_GATES, GATE_PITCH = 22, 4.0
X_APEX_SHIFT, L3_ADVANCE = 6.0, 8.0     # v9 : sommet du 180 après le saut du milieu / avance du saut (ft)
L3_SHIFT, L2_SHIFT = 12.0, 10.0          # v13 (« plus d'espace entre chaque enchaînement ») : L3 12 ft et L2 / L1 22 ft plus au sud
#                                         -> couloir Est 22 ft plus long, 180 L3 -> L2 de rayon 37 ft
EXIT_U0 = 6.0 if ZION else 10.0          # v23 Zion (« moins d'élan sur toutes les sorties de virage ») : 10 -> 6 ft ; v13 : 1re bosse à 10 ft de la sortie des virages (plus de marque berm / appel)
L2_U0_V13 = 10.0
BERM_END_FADE = {'T_D ': (12.0, 40.0), **({'T1 1': (-1.0, 15.0)} if ZION else {})}   # v35 (capture : « corrige ce cran », début de L1) : la queue du berm de T1 touchait le pied du 1er whoop (pli) -> berm fondu sur ses 15 derniers degrés ; T_D :   # v28k (« adoucis l'angle du virage ») : 8 -> 12°, fondu 35 -> 40° (la 1re bosse de L2 part dans la courbe)
#     # v20c (« le virage à gauche avant l'enchaînement finit dans la bosse, il y a un trait ; le faire
#   finir un peu plus tôt, en restant doux, limite moins haut ») : berm à zéro 8° avant la sortie, fondu sur les 35° d'avant
BERM_SOFT_TAG = {'T_D ': 4.0} if ZION else {}   # v28k : flou 2,5 -> 4 ft   # v27d : berm adouci (flou de 2,5 ft, même hauteur max) -> face moins raide
BERM_GAIN_TAG = {'T_D ': 1.05 if ZION else 0.95, **({'T_Bb': 1.15} if ZION else {})}   # v27d (« le virage à la même hauteur qu'avant mais moins d'angle ; remets l'après-arrivée comme avant ») : T_D 1,05 adouci (BERM_SOFT_TAG), T_L5 comme la v25f ; v27c (« on passe trop vite dans le virage avant L2 ») : T_D 1,05 -> 0,8 ; v27b (« baisse un petit peu l'appui ») : T_L5a 1,3 -> 1,15 ; v26 Zion : T_L5a (après l'arrivée) en cuvette plus haute comme en vrai (vidéos) ; v23 Zion : T_D plus haut ; T_Bb entrée plus haute   # v13 : appui après le saut du milieu un peu moins haut (était 1,15) ; v22 Zion : « plus bas » 0,95 -> 0,75
# v28s (croquis : le virage T_Bb entouré, flèche vers T_D : « reprends ce virage pour le mettre avant L2, adapte-le juste ») : berm de T_D
# comme T_Bb (croissant JGSX tel quel, x1,15, pas de flou) ; fondu de fin gardé léger (la 1re bosse de L2 part dans la courbe)
if ZION and T_D_CUT:
    BERM_GAIN_TAG['T_D '] = BERM_GAIN_TAG['T_Bb']; BERM_SOFT_TAG['T_D '] = 1.5   # v28w : léger flou (bouts arrondis)
    BERM_SOFT_TAG['T_D '] = 0.0   # v29b (« on dirait un gros bout de tas de terre, c'est pas carré ») : plus de flou, croissant JGSX net comme T_Bb
    BERM_END_FADE['T_D '] = (4.0, 20.0)
    BERM_START_FADE = {'T_D ': (6.0, 28.0)}   # v28w (« adoucis, ça fait carré ») : fondu 8 -> 28°, commence à 6° ; v28v (trait vert : « coupe le début du virage ») : berm coupé sur les 11 premiers degrés (au trait), fondu sur 8°
BERM_REGULAR = {'T_D ': dict(rin=28.0, rout=20.0)} if ZION else {}   # v35 (« la gueule du virage pas belle, fais que ce soit linéaire, même hauteur ; la sortie pas belle ») : berm régulier (build_zion.berm_regular), montée / descente = fondus d'avant
LD_SHIFT = 5.0                          # v10 : ligne de départ 5 ft plus loin du saut du milieu (place pour les tremplins FMX ;
#                                         plus loin, le bout des 22 grilles monte sur le pied du berm T_C : grilles plus plates)
L2_GAP, L2_U0 = 5.0, 10.0               # v9 : écart identique entre les 7 bosses de L2 ; v13 : 1re bosse à 10 ft du 180 (était 3 : marque)


def start(p):
    ln = p.lanes
    gx, gz = px_x(D["depart"]["grilles_x"]), ln['zLD']
    xm = ln['x_end3'] - ln['R3']                                       # v9 : sommet du 180 L3 -> L2 (sur le tour)
    merge = (xm, (ln['zL3'] + ln['zL2']) / 2)
    if ln.get('apex_TD'):                                              # v28r : sommet du T_D raccourci
        merge = tuple(float(v) for v in ln['apex_TD']); xm = merge[0]
    route = [('S', gx - (xm + RB)), ('T', 90, RB, None), ('TO', merge)]
    if ZION and AF_V28:   # v28f (croquis, traits A / C) : grilles plus haut, virage du départ plus large vers T_D
        gz = ln['zLD'] + START_DZ
        route = [('S', gx - (xm + START_R)), ('T', 90, START_R, None), ('TO', merge)]
    xv_ = xm
    if ZION and T_D_RF and not T_D_BERM_FROM:
        # v28d (« le virage comme celui avant LR, avec le RF ») : berm RF sur tout T_D -> le départ ne peut plus arriver par
        # l'extérieur de la 1re moitié (7 ft de berm dessus). Il monte entre la réception du freestyle et T_D, tourne à droite
        # et rejoint L3 juste avant T_D : les pilotes du départ prennent tout le virage, comme un vrai 1er virage.
        g3 = next(g for g in p.segs if g['kind'] == 'S' and g['tag'].startswith('L3'))
        u_end = max(u0_ + np.nonzero(np.asarray(pr_) > 0.05)[0][-1] * 0.1 for pr_, u0_, nm_ in g3['sections'])
        x_land = g3['x0'] - u_end                                       # bout de la réception du freestyle (x du monde)
        xv_ = x_land - START_CLEAR                                       # montée du départ, dégagée de la réception
        zj_ = ln['zL3']; xj_ = ln['x_end3'] + 1.0
        assert xv_ - RB > xj_ + 2.0, (xv_, xj_)
        route = [('S', gx - (xv_ + RB)), ('T', 90, RB, None), ('S', (zj_ - RB) - (gz + RB)), ('T', -90, RB, None), ('TO', (xj_, zj_))]
    S0 = dict(gate=(gx, gz), heading=180.0, route=route, narrow=[(150.0, None), (gx - xv_, 30.0)],
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
# Formes MESURÉES sur ZION.2025.SupercrossParis (pistes/paris-2026/data/zion_formes.npz / .json) : bosse (29,8 ft, 4,27 ft), table (62 ft,
# 7,04 ft), whoop (19,8 ft, 3,14 ft, pas 22,6 ft) ; saut central et triple d'arrivée ZION non retouchés ; les obstacles de 2026
# (nombre, ordre, hauteurs) restent ceux de la version USLAND.
L2_NAME = 'PAR-L2 double triple triple (8 bosses)'
# v26 : L2 refait d'après les vidéos (voir le bloc L2 dans paris()) ; crêtes en ft depuis la sortie du 180, hauteur construite (côté le
# plus haut), longueur (x forme ZION), coupe gauche / droite (facteurs kl, kr) ; None = L2 v25f
# v28f (croquis de Ryan : « B la nouvelle ligne pour traverser le départ en roulant ; A et C sont les lignes qui font le départ ») :
# le tour après l'arrivée traverse la zone de départ en diagonale (B) ; départ : grilles sur le trait A (plus haut), entonnoir vers T_D
ROUND_L5 = False   # v30 : après l'arrivée = un seul grand demi-tour rond (False = T_L5a / ligne droite / T_L5b v28i)
ROUND_TB = False   # v30 : bout de la ligne de départ -> L3 = un seul grand demi-tour rond (False = T_Ba / 55 ft / T_Bb)
if ZION and ROUND_TB:   # v30 : le pied du berm de T_Bb (sommet du grand demi-tour) touchait le bout des grilles (0,42 ft) : berm à 0 au début de T_Bb, fondu sur 30°
    BERM_START_FADE = {**globals().get('BERM_START_FADE', {}), 'T_Bb': (0.0, 30.0)}
AF_V28 = False   # v28i (« après l'arrivée remets comme la version d'hier ») ; True = traversée B (v28f-g)
AF_R1, AF_R2 = 40.0, 30.0          # B : grande courbe à gauche en sortie de T_L5a, courbe à droite avant T_Bb (ft)
AF_SECS = lambda L: []             # B : diagonale plate (elle traverse le couloir de départ)
AF_BUMPS = dict(h=[3.4] * 4, pitch=34.0, u0=2.0)   # v28g : 4 bosses RF (la 5e tombait sur la ligne de départ) sur le début de la diagonale   # B : bosses RF en sortie de T_L5a (traits bleus) ; pitch = crête à crête
START_DZ, START_R = 44.0, 45.0     # départ : centre des grilles 44 ft au-dessus de l'ancienne ligne (A : 546 -> 632), virage du départ
T_D_RF = None   # v28 : rayon du 180 avant L2 (None = (zL2 - zL3) / 2 = 31 ft, v27d)
# v28b (« il est trop en avant, il doit être plus reculé vers le sable, qu'on tourne et qu'on sorte pas au milieu du terrain ») :
# 180 avant L2 décalé vers LR ; limite = le berm RF (46 ft du centre) ne doit pas toucher les bosses de LR
T_D_EAST = 0.0                   # v28f (« remets l ancien virage JGSX ») : position d avant
T_D_BERM_FROM = 0.0              # v28d (« comme le virage avant LR, avec le RF ») : berm RF sur tout le 180 ; le départ rejoint L3 avant T_D (start())
START_CLEAR = 4.0                # v28d : écart entre la réception du freestyle et la montée du départ (ft)
RF_BERM_TAGS = ()         # v28 : virages au berm RF mesuré (build_zion.berm_rf) au lieu du croissant JGSX
# v28b (« les 2 premières un tout petit peu plus petites, limite ça se voit pas ; ensuite les autres même distance et même hauteur ») :
# bosse RF à 5,8 ft partout (les 2 premières 5,4 ft), crête à crête 36 ft entre les 2 premières puis 30 ft
# v28c (« l'enchaînement est trop serré : il commence à la sortie du virage et finit juste avec le virage d'après, comme L6 ») :
# bosses RF un peu plus courtes (x0,85 = 22 ft, face plus raide), 5,0 / 5,0 puis 5,4 ft, même écart partout de la sortie de T_D à
# 5 ft de T1 ; estimation (sim_rythme) : double - triple - triple tout juste, quadruple et triple d'entrée impossibles
# v28g (« les bosses un peu trop hautes ; la 1re plus douce à l'avant et plus tôt à la sortie du virage ; même longueur entre chaque
# bosse toujours ; la 1re plus petite pour faire 2 précis puis 3 ») : 1re 4,6 ft face avant x1,6, les 7 autres 5,0 ft, même écart partout
# v28h (« 1re bosse 3,5 ft à droite, 2 ft à gauche ; 36 ft entre chaque ; les autres 5 ft ; l'enchaînement commence plus près du
# virage ») : 1re sans face étirée et pied coupé (crête plus tôt), écart fixe 36 ft
# v28j (« avance l'enchaînement de 15 ft », choix « tout avancer ») : start -15 = la 1re bosse commence 15 ft avant la sortie de T_D (dans la courbe), 15 ft de plat avant T1
# v28k (« recule l'enchaînement de 6 ft et adoucis l'angle du virage et la bosse pour que ça rentre plus smooth ») : crêtes 6 ft plus
# loin (1re à la sortie de T_D), face avant de la 1re étirée x1,4 sans pied coupé (pente douce qui part dans la courbe)
# v29 (« recule l'enchaînement de 8 ft ») : start -16,6 -> -8,6, toutes les crêtes 8 ft plus loin (écart de 36 ft inchangé)
# v29b (« ça fait triple d'entrée : adoucis l'appel à droite ; toutes les bosses un peu moins d'angle à l'appel, sans abuser ; plus
# d'espace entre chaque bosse, l'enchaînement finit plus tard, juste devant le virage : on pose et on tourne ») : 1re bosse 3,5 -> 3,2 ft
# à droite (gauche toujours 2,0 ft) ; faces d'appel des 7 autres étirées x1,15 ; L2 (et L1) 10 ft plus longs (L2_EXT) ; plus d'écart
# imposé : même écart partout de la 1re crête (inchangée) à la dernière bosse qui finit à 4 ft de T1 (~38 ft au lieu de 36)
L2_EXT = 29.5      # v35 (« les 2 virages, encore 5 ft ; pas d'à-coup à la réception avant les whoops ») : 34,5 -> 29,5, réception de la dernière bosse presque entière (land_trim 5 -> 2) ; v34 (« T1 et T_C, avance-les de 5 ft pour les rapprocher ; les whoops gardent la même distance avec T1 ») : 39,5 -> 34,5 ; v33 :      # v33 : T_D 5 ft de plus -> 34,5 -> 39,5 ; v32 :      # v32 : T_D 10 ft plus à l'ouest, L2 suit (mêmes bosses, même écart), T1 juste à la fin de la réception (fin 4 -> 0) : 28,5 -> 34,5 ; v29e :      # v29e (« plus d'écart entre chaque, que ça finisse bien 10 ft plus tard, on rentre direct dans le virage ») : 18,5 -> 28,5 ft ;      # v29c : 10 -> 18,5 ft (bosses smooth plus longues : on garde ~38 ft de crête à crête)
# v29c (« ça fait triple d'entrée ; la 1re, l'entre-deux de gauche et droite, en plein milieu, que ce soit cet appel-là, qu'il faille
# impulser ; ensuite des bosses plus smooth, là tu tapes, tu peux perdre les pieds ») : 1re bosse 2,6 ft sur toute la largeur (milieu de
# 2,0 / 3,2) ; bosses 2 à 8 : forme smooth (trap) à la place de la bosse RF (appel ~21°, réception ~22°, sommet de ~19 ft de rayon au lieu de ~11)
L2_V28 = dict(fill=dict(start=-8.6, end=0.2, pitch=None),   # v32 (« rapproche le virage : on pose et on est directement dans le virage ») : fin 4 -> 0 ft
              front1=1.4, toe=None, front=1.15,   # v28 : bosses RF (voir paris()) ; None = v27d
              bumps=[(2.6, 'single', 0.8), (4.6, 'single', 1.0),   # v29e : 2e 4,7 -> 4,6 ft
                     (4.8, 'single', 1.0), (5.0, 'single', 1.0), (5.0, 'single', 1.0),   # v28l : 2e 4,7, 3e 4,8, 6e 4,8, dernière 4,7
                     (4.8, 'single', 1.0), (5.0, 'single', 1.0), (4.7, 'single', 0.85)],
              smooth=1.5,          # v28e : forme RF de longueur normale, lissage léger
              left1=2.0 / 2.6,     # v35 (« la 1re bosse, comme dans la vraie vie : à gauche elle doit être plus basse ») : gauche 2,0 ft, droite 2,6 ft ; v29c : même hauteur partout (v29b : gauche 2,0 / droite 3,2 ft)
              front_dd=2.0,        # v29d : 2° de moins à l'appel sur chaque bosse (après la 1re)
              zion_from=2,         # v29e : bosses 3 à 8 = forme ZION de L6 (mêmes hauteurs)
              land_last=True,
              land_trim=2.0)       # v35 : plus que les 2 derniers ft (< 0,2 ft) : la coupe de 5 ft finissait en marche de 0,9 ft à l'entrée de T1 (à-coup) ; v34 : bout de la réception de la dernière bosse raccourci de 5 ft (T1 5 ft plus près)      # v29d : la dernière avec la réception de la table de L6 ; v29c : trap=dict(deg=22, deg_back=23, top=8, sm=3,5) (vagues, refusé)
L2_V27 = True     # v27 : L2 = bosses de L6 (voir paris())
L2_V27D = True    # v27d : 8 bosses, 1re 20°, 2e 4,3 ft, 3e 21°
L2_V27C = True    # v27c : 3,5 / 4 / 4,5 x5, formes L6
L2_V27B = 3.8     # v27b : hauteur des 6 bosses après 3,5 / 4,7 (None = v27)
L2_V26 = None and dict(crest=[9.0, 37.0, 67.0, 93.5, 120.0, 163.0, 202.0, 241.0], h=[2.3, 5.6, 4.8, 3.0, 4.4, 4.8, 3.8, 4.4],
              k=[0.75, 1.15, 1.0, 0.92, 1.3, 1.0, 0.92, 1.1], split={0: (0.8 / 2.3, 1.0), 1: (1.0, 3.9 / 5.6)})
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
