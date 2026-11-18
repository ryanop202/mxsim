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
XW_SHIFT = 55.0 if ZION else 0.0  # v15 : couloirs allongés vers l'est (place libre du sol agrandi) pour les écarts ZION
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


def table_double_rf(k=1.10):
    """v17 (« je sais qu'il y a des terrains RF qui ont des doubles tables, reprends celle de la RF ») : table à double étage MESURÉE
    sur RF Anaheim 1 2026 (paris2026/data/rf_table_double.*) : étage à 2,8 ft, petit creux, dessus à 5,8 ft, 103 ft ; hauteur x k
    comme les bosses ZION de la version Zion."""
    p = np.load(os.path.join(HERE, "data", "rf_table_double.npy")).astype(float)
    i = max(0, int(np.nonzero(p > 0.3)[0][0]) - 10); p = p[i:] * k; p[0] = p[-1] = 0.0
    return ('raw', 'table double etage RF %.1f ft' % p.max(), p, 'T')


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
    zL5, zLD, zL3, zL2 = px_z(481.0), px_z(370.0) - LD_SHIFT, px_z(226.5) + L3_SHIFT, px_z(130.0) + L3_SHIFT + L2_SHIFT
    zL1, zL6 = zL2 + 2 * RB, zL5 - 2 * RB            # 180° JGSX : couloirs voisins à 43 ft
    xW = px_x(312.0) + XW_SHIFT                        # virages Ouest (T1, T_C) : x des sorties de 180°
    xLR, xC, xT5 = px_x(860.0), px_x(778.0), px_x(785.0)
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
        pre = [t if t[0] == 'gap' else ('raw', 'double USLAND', np.asarray(LS.L('tmp', [t]), float), 'T') for t in PRE_FINISH]; ue = 7.0
    toks = pre + [('gap', round(u_app - ue - tlen(pre), 1))] + toks[i_t:]; u0 = ue
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
    p.straight(x3 - x_end3, [LS.sec(L3_SEC, toks, u0)], tag='L3 grande table')
    p.turn(180, R3, BIG, tag='T_D 180 gauche (berm 2e moitié)'); p.segs[-1]['berm_from'] = 0.5
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
            toks += [('gap', 15.0), b_]
        u0z = (xW - x_end3) - 8.0 - tlen(toks)
    u0 = u0z if ZION else L2_U0
    p.straight(xW - x_end3, [lane_sec('PAR-L2 triple, triple (7 bosses, meme ecart)', toks, u0)], tag='L2 singles')
    p.turn(-180, RB, BIG2, tag='T1 180 droite (berm)')
    # v10 : 11 whoops (une petite + 10) plus hautes, plus rondes, plus de terre ; la table + 2 bosses gardées (« pas mal »)
    lL1 = xW - (xLR + RB)
    toks = [whoops_paris(), ('gap', 15.0), TABLE_L1, ('gap', 1.5), ('scale', SA[1], 4.0), ('gap', 1.5), ('scale', SA[0], 3.6)]
    if ZION:   # v16 : nos whoops comme Saint-Georges (lancement normal) ; table + 2 bosses ZION plus grosses, écarts ZION (8 ft)
        toks = [whoops_up(11, 1.15), ('gap', 15.0), ('scale', TABLE_B, 7.0), ('gap', 8.0), ('scale', SA[1], 4.3), ('gap', 8.0), ('scale', SA[0], 4.1)]
    u0 = lL1 - 8.0 - tlen(toks); assert u0 >= 0.5, u0
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
    if ZION:   # v16 (dessin de l'utilisateur) : la bosse + la table remplacées par une table à double étage ; v17 : celle de la RF
        rh = [table_double_rf()] + [t if t[0] != 'gap' else ('gap', 7.5) for t in rh[3:]]
    kick = [('scale', SA[1], 4.0)]
    u0 = EXIT_U0                                           # v13 : plus collé au berm (marque entre l'appui et la bosse)
    toks = kick + [('gap', round(lLR - u0 - 8.0 - tlen(kick) - tlen(rh), 1))] + rh
    p.straight((zL1 - RB) - (zL6 + RB), [lane_sec('PAR-LR saut de sortie, bosse, table, 3 bosses', toks, u0)], tag='LR tribune Est')
    p.turn(-90, RB, BIG, tag='T_E 90 droite (berm)')
    # v10 (« triple : 3 bosses, 2 bosses, une table, 2 bosses ») : bosses de Saint-Thibéry, même écart partout, 8 ft du virage
    # v13 : appel (1re bosse) un peu plus raide et un peu plus haut (« tu creuses un peu plus le bas »), sans aller plus loin ;
    # les autres bosses un peu plus hautes et plus rondes ; plus de marque berm / 1re bosse (EXIT_U0)
    L6B = [('stretch', SA[0], 4.2, 0.85), ('stretch', SA[2], 4.7, 1.15), ('stretch', SA[1], 4.9, 1.15), ('stretch', SA[3], 4.7, 1.15),
           ('stretch', SA[2], 4.9, 1.15), TABLE, ('stretch', SA[0], 4.3, 1.15), ('stretch', SA[1], 4.5, 1.15)]
    toks, u0 = even(L6B, xW - (xLR + RB), EXIT_U0, 8.0), EXIT_U0
    p.straight(xW - (xLR + RB), [lane_sec('PAR-L6 triple, double, table, double', toks, u0)], tag='L6 tribune Sud')
    p.turn(-180, RB, BIG, tag='T_C 180 droite (berm)')
    p.lanes = dict(x_end3=x_end3, R3=R3, zL5=zL5, zLD=zLD, zL3=zL3, zL2=zL2, zL1=zL1, zL6=zL6, xW=xW, xLR=xLR, xC=xC, xT5=xT5, xTB=xTB)
    return p


# ---------------------------------------------------------------- départ (22 grilles, comme JGSX)
N_GATES, GATE_PITCH = 22, 4.0
X_APEX_SHIFT, L3_ADVANCE = 6.0, 8.0     # v9 : sommet du 180 après le saut du milieu / avance du saut (ft)
L3_SHIFT, L2_SHIFT = 12.0, 10.0          # v13 (« plus d'espace entre chaque enchaînement ») : L3 12 ft et L2 / L1 22 ft plus au sud
#                                         -> couloir Est 22 ft plus long, 180 L3 -> L2 de rayon 37 ft
EXIT_U0 = 10.0                           # v13 : 1re bosse à 10 ft de la sortie des virages (plus de marque berm / appel)
L2_U0_V13 = 10.0
BERM_GAIN_TAG = {'T_D ': 0.95}            # v13 : appui après le saut du milieu un peu moins haut (était 1,15)
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
if ZION:
    ZF = np.load(os.path.join(HERE, "data", "zion_formes.npz"))
    Z25_TRIPLE = _split_after_first(_P25['triple_arrivee'], 'appel arrivee ZION 2025 (10,0)', 'triple arrivee ZION 2025 (6,0 / 11,2)', 'T')
    Z25_MILIEU = _split_after_first(_P25['milieu'], 'appel gros saut ZION 2025 (10,0)', 'butte gros saut rond ZION 2025 (24,2)', 'X')
    Z25_BUTTE_W = Z25_BUTTE_W_ZION
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
                out.append(whoops_up(11, 1.15))
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


if __name__ == "__main__":
    p = paris()
    print("tour : %.0f ft ; fermeture : (%.2f, %.2f, %.1f°)" % (p.s, p.x - p.segs[0]['x0'], p.z - p.segs[0]['z0'], np.degrees(p.t) % 360))
    for k, v in LOG.items():
        for name, u, L in v:
            print("  %-34s centre u=%6.1f ft  (L visuel %.1f ft)" % (name, u, L))
    print(start(p)['merge'], fmx_ramps())
