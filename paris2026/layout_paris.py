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
PLAN_K = 1.35                     # agrandissement en plan de l'arène (stade_paris/src/build.py)
FLOOR_X_SOUTH = -60.0 * PLAN_K    # m (dims.FLOOR_X_SOUTH x K)
OX, OZ = 549.0, 593.5             # origine du repère de l'arène dans le terrain (ft) : bâtiment centré sur 1187 ft
X0 = OX + FLOOR_X_SOUTH * FT
Z0 = OZ
BIG = 'big_det_a'
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


def paris():
    """Le tour (sens de course), départ du tour au début de L5 (sortie de T_C)."""
    zL5, zLD, zL3, zL2 = px_z(481.0), px_z(370.0), px_z(226.5), px_z(130.0)
    zL1, zL6 = zL2 + 2 * RB, zL5 - 2 * RB            # 180° JGSX : couloirs voisins à 43 ft
    xW = px_x(312.0)                                   # virages Ouest (T1, T_C) : x des sorties de 180°
    xLR, xC, xT5 = px_x(860.0), px_x(778.0), px_x(785.0)
    xTB = px_x(315.0)
    p = Path(xW, zL5, 180.0, 'PARIS')

    secs, LOG['L5'] = lane_obstacles('L5', xW, 'x', -1)
    p.straight(xW - (xT5 + RB), secs, tag='L5 arrivée')
    p.turn(90, RB, BIG, tag='T_L5a 90 gauche (berm)')
    p.straight(zLD - zL5 - 2 * RB, tag='T_L5 milieu')
    p.turn(90, RB, None, tag='T_L5b 90 gauche')
    p.straight((xTB - RB) - (xT5 + RB), tag='LD ligne de départ (vers l ouest)')
    p.turn(-90, RB, None, tag='T_Ba 90 droite')
    p.straight(zL3 - zLD - 2 * RB, tag='T_B milieu')
    p.turn(-90, RB, BIG, tag='T_Bb 90 droite (berm)')
    x3 = xTB - RB
    secs, LOG['L3'] = lane_obstacles('L3', x3, 'x', -1, skip=(2,))
    a, b = D["tour"][[l["id"] for l in D["tour"]].index("L3")]["obstacles"][1]["px"]
    t = big_table()
    secs.append(_sec('L3-2 grande table SUPERCROSS Paris (forme créée)', t, x3 - px_x(a)))
    p.straight(x3 - (xC + RB), secs, tag='L3 grande table')
    p.turn(90, RB, None, tag='T_C3 90 gauche')
    p.straight(zL2 - zL3 - 2 * RB, tag='C colonne')
    p.turn(90, RB, BIG, tag='T_D 90 gauche (berm)')
    secs, LOG['L2'] = lane_obstacles('L2', xC + RB, 'x', +1)
    p.straight(xW - (xC + RB), secs, tag='L2 singles')
    p.turn(-180, RB, BIG, tag='T1 180 droite (berm)')
    secs, LOG['L1'] = lane_obstacles('L1', xW, 'x', -1)
    p.straight(xW - (xLR + RB), secs, tag='L1 whoops')
    p.turn(-90, RB, BIG, tag='T_TR 90 droite (berm)')
    secs, LOG['LR'] = lane_obstacles('LR', zL1 - RB, 'z', -1)
    p.straight((zL1 - RB) - (zL6 + RB), secs, tag='LR tribune Est')
    p.turn(-90, RB, BIG, tag='T_E 90 droite (berm)')
    secs, LOG['L6'] = lane_obstacles('L6', xLR + RB, 'x', +1)
    p.straight(xW - (xLR + RB), secs, tag='L6 tribune Sud')
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
              finish=('L5-3 Detroit_g29_3', 0))
    from starts import StartRoute
    R = StartRoute(S0, N_GATES, GATE_PITCH)
    S0['merge'] = (float(R.merge[0]), float(R.merge[1])); S0['straight'] = R.s_straight; S0['length'] = R.L
    return S0


def fmx_ramps():
    """4 tremplins FMX (2 paires de part et d'autre de L3), lèvre à l'extrémité Est des bandes claires du visuel,
    orientés vers la grande table. (x_lèvre_px, y_px, direction visée en px)."""
    tgt = (634.0, 224.5)
    out = []
    for xp, yp in ((447.0, 190.0), (575.0, 181.0), (535.0, 280.0), (620.0, 263.0)):
        x, z = px_x(xp), px_z(yp)
        tx, tz = px_x(tgt[0]), px_z(tgt[1])
        h = np.arctan2(tz - z, tx - x)
        out.append(dict(lip=(x, z), heading=float(h)))
    return out


if __name__ == "__main__":
    p = paris()
    print("tour : %.0f ft ; fermeture : (%.2f, %.2f, %.1f°)" % (p.s, p.x - p.segs[0]['x0'], p.z - p.segs[0]['z0'], np.degrees(p.t) % 360))
    for k, v in LOG.items():
        for name, u, L in v:
            print("  %-34s centre u=%6.1f ft  (L visuel %.1f ft)" % (name, u, L))
    print(start(p)['merge'], fmx_ramps())
