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
PLAN_K = 1.45                     # agrandissement en plan de l'arène (stade_paris/src/build.py) ; v5 : 1,35 -> 1,45 (paddock)
FLOOR_X_SOUTH = -60.0 * PLAN_K    # m (dims.FLOOR_X_SOUTH x K)
OX, OZ = 549.0, 593.5             # origine du repère de l'arène dans le terrain (ft) : bâtiment centré sur 1187 ft
X0 = OX + FLOOR_X_SOUTH * FT
Z0 = OZ
BIG, BIG2 = 'big_det_a', 'big_cle'
RB = 21.5
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
from layouts_stt import rounded                             # noqa: E402
from layouts_sgm import smooth_takeoff, whoops_up           # noqa: E402
SA, ROLLER, TABLE_B = LS.SA, 'Custom1_g30_1', 'Arlington_g49_2'
TABLE = ('scale', TABLE_B, 6.6)
TRIPLE_SGM = [('scale', SA[3], 3.9), ('gap', 2.5), ('scale', SA[4], 2.3), ('gap', 3.5), ('stretch', SA[5], 4.0, 1.3)]
FINISH_DBL = [smooth_takeoff(4.0, 10.0, 1.8, 9.0, 0.8, pad=0.4), ('gap', 24.5), ('stretch', SA[2], 5.4, 1.5)]
FMX_LANDING = ('trapeze', 8.0, 22.0, 40.0, 35.0, 'lin', 4.0)
BERM90_GAIN = 1.0                       # v5 (Ryan : « les virages à 90 sont trop hauts ») : berms 90° tels que mesurés (était 1,4)
SOFT_FEET = dict(sigma=1.2, h=1.5)       # Saint-Georges v22 : pieds des bosses arrondis
FMX_MODEL = dict(model='ramp_50', model_len=18.47)   # tremplin acier de Ryan (assets/fmx_ramp_user), lèvre 9 ft, collision .shp
FINISH_SEC = 'PAR-L5 petit double, triple d arrivee (ZION 2025)'
# v5 (retours de Ryan) : petit double avant l'arrivée ; L1 : la 2e bosse après la table remise (table un peu plus courte) ;
# L6 : rythmique serrée (on peut faire double / quadruple, mais la 1re bosse est petite : pas de « 4 d'entrée »), table,
# puis un double derrière la table (« sur table, derrière double »). Formes = bosses Arlington déjà utilisées ici.
SMALL_DBL = [('scale', SA[0], 3.4), ('gap', 8.0), ('stretch', SA[1], 4.0, 1.25)]
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
    k = pk[0] + int(np.argmin(p[pk[0]:pk[1]]))
    return [('raw', name1, p[:k + 1], 'T'), ('gap', 0.0), ('raw', name2, p[k:], kind2)]


Z25_TRIPLE = _split_after_first(_P25['triple_arrivee'], 'appel arrivee ZION 2025 (10,0)', 'triple arrivee ZION 2025 (6,0 / 11,2)', 'T')
Z25_MILIEU = _split_after_first(_P25['milieu'], 'appel gros saut ZION 2025 (10,0)', 'butte gros saut rond ZION 2025 (24,2)', 'X')
Z25_BUTTE_W = (44.0, 46.0)               # v5 (Ryan) : réception CARRÉE (dessus 42 ft, flancs presque verticaux) pour la bâche AMV ; était (68, 90)
Z25_BUTTE_W_ZION = (_P25['largeur_butte_mi_hauteur'], 90.0)   # 68 ft à mi-hauteur comme ZION ; pied 90 ft au lieu de 110 :
#   entre les singles (L2) et la ligne de départ il n'y a que ~98 ft -> flancs un peu plus raides que ZION


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
    LS.COMBOS.clear(); LS.SPLITS.clear()
    zL5, zLD, zL3, zL2 = px_z(481.0), px_z(370.0), px_z(226.5), px_z(130.0)
    zL1, zL6 = zL2 + 2 * RB, zL5 - 2 * RB            # 180° JGSX : couloirs voisins à 43 ft
    xW = px_x(312.0)                                   # virages Ouest (T1, T_C) : x des sorties de 180°
    xLR, xC, xT5 = px_x(860.0), px_x(778.0), px_x(785.0)
    xTB = px_x(315.0)
    p = Path(xW, zL5, 180.0, 'PARIS')
    # L5 : single, single, SAUT D'ARRIVÉE (obstacles 3 + 4 du visuel = un double : appel / réception), table longue
    toks, u0 = from_render('L5', xW, 'x', -1, {(1, 2): SMALL_DBL, (3, 5): Z25_TRIPLE},
                           lane_len=xW - (xT5 + RB))   # v4 : le triple d'arrivée de ZION 2025 couvre les obstacles 3 à 5 du visuel
    p.straight(xW - (xT5 + RB), [lane_sec(FINISH_SEC, toks, u0, finish=True)], tag='L5 arrivée')
    p.turn(90, RB, BIG, tag='T_L5a 90 gauche (berm)')
    p.straight(zLD - zL5 - 2 * RB, tag='T_L5 milieu')
    p.turn(90, RB, None, tag='T_L5b 90 gauche')
    p.straight((xTB - RB) - (xT5 + RB), tag='LD ligne de départ (vers l ouest)')
    p.turn(-90, RB, None, tag='T_Ba 90 droite')
    p.straight(zL3 - zLD - 2 * RB, tag='T_B milieu')
    p.turn(-90, RB, BIG, tag='T_Bb 90 droite (berm)')
    x3 = xTB - RB
    toks, u0 = from_render('L3', x3, 'x', -1, {(1, 2): Z25_MILIEU}, lane_len=x3 - (xC + RB))
    p.straight(x3 - (xC + RB), [LS.sec(L3_SEC, toks, u0)], tag='L3 grande table')
    p.turn(90, RB, None, tag='T_C3 90 gauche')
    p.straight(zL2 - zL3 - 2 * RB, tag='C colonne')
    p.turn(90, RB, BIG, tag='T_D 90 gauche (berm)')
    toks, u0 = from_render('L2', xC + RB, 'x', +1, {1: ('scale', SA[0], 3.6), 2: ('scale', SA[1], 4.4), 3: ('scale', SA[2], 4.5),
                                                    4: ('scale', SA[1], 4.4), 5: ('scale', SA[4], 4.9), 6: ('scale', SA[2], 4.5),
                                                    7: ('scale', SA[0], 4.0)}, lane_len=xW - (xC + RB))
    p.straight(xW - (xC + RB), [lane_sec('PAR-L2 7 bosses', toks, u0)], tag='L2 singles')
    p.turn(-180, RB, BIG2, tag='T1 180 droite (berm)')
    toks, u0 = from_render('L1', xW, 'x', -1, {1: [whoops_up(10, 1.15)], 2: TABLE_L1, 3: ('scale', SA[1], 4.0), 4: ('scale', SA[0], 3.6)},   # v5 : la 2e bosse remise
                           lane_len=xW - (xLR + RB), min_gaps={0: 22.0})   # Ryan : la table plus loin des whoops et plus grosse
    p.straight(xW - (xLR + RB), [LS.sec('PAR-L1 whoops, table, bosse', toks, u0)], tag='L1 whoops')
    p.turn(-90, RB, BIG, tag='T_TR 90 droite (berm)')
    toks, u0 = from_render('LR', zL1 - RB, 'z', -1, {1: ('scale', ROLLER, 1.8), (2, 3): long_bump(), 4: ('scale', SA[1], 4.0), 5: ('scale', SA[0], 3.6)},
                           lane_len=(zL1 - RB) - (zL6 + RB))
    p.straight((zL1 - RB) - (zL6 + RB), [lane_sec('PAR-LR roller, longue bosse, 2 bosses', toks, u0)], tag='LR tribune Est')
    p.turn(-90, RB, BIG, tag='T_E 90 droite (berm)')
    toks, u0 = L6_RHYTHM, 4.0
    p.straight(xW - (xLR + RB), [lane_sec('PAR-L6 8 bosses dont une table', toks, u0)], tag='L6 tribune Sud')
    p.turn(-180, RB, BIG, tag='T_C 180 droite (berm)')
    p.lanes = dict(zL5=zL5, zLD=zLD, zL3=zL3, zL2=zL2, zL1=zL1, zL6=zL6, xW=xW, xLR=xLR, xC=xC, xT5=xT5, xTB=xTB)
    return p


# ---------------------------------------------------------------- départ (22 grilles, comme JGSX)
N_GATES, GATE_PITCH = 22, 4.0


def start(p):
    ln = p.lanes
    gx, gz = px_x(D["depart"]["grilles_x"]), ln['zLD']
    merge = (ln['xC'], (ln['zL3'] + RB + ln['zL2'] - RB) / 2)        # milieu de la colonne C (sur le tour)
    route = [('S', gx - (ln['xC'] + RB)), ('T', 90, RB, None), ('TO', merge)]
    S0 = dict(gate=(gx, gz), heading=180.0, route=route, narrow=[(150.0, None), (gx - ln['xC'], 30.0)],
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
    for du, v in ((-30.0, 30.0), (-14.0, 40.0), (-22.0, -25.0), (-40.0, -31.0)):   # v < 0 = nord (L2 à 64 ft seulement)
        lip = P(ub + du, v); d = tgt - lip
        out.append(dict(lip=(float(lip[0]), float(lip[1])), heading=float(np.arctan2(d[1], d[0]))))
    return out


if __name__ == "__main__":
    p = paris()
    print("tour : %.0f ft ; fermeture : (%.2f, %.2f, %.1f°)" % (p.s, p.x - p.segs[0]['x0'], p.z - p.segs[0]['z0'], np.degrees(p.t) % 360))
    for k, v in LOG.items():
        for name, u, L in v:
            print("  %-34s centre u=%6.1f ft  (L visuel %.1f ft)" % (name, u, L))
    print(start(p)['merge'], fmx_ramps())
