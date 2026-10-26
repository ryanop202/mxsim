"""usland race track - layout (plan v1 approved 26/10/2026, doc 13).

Own terrain: 2049 px x 0.28975 ft = 593.4 ft (the JGSX grid; same side as the RF Anaheim stadium floor, which therefore sits on it
without any offset). Lanes north-south, 43 ft apart, JGSX berm stamps (180 deg big R 21.5, 90 deg small R 11), first turn = flat,
open bowl R 90 (no berm), USLAND start (22 gates at 4 ft, corridor narrowing 92 -> 40 -> 30 ft, no funnel) that drops into the bowl.
Rhythm lanes = measured units only: JGSX (lib/sx_units.json, lib/sx_whoops.json) + RF (lib/rf_units.json, scripts/rf_units.py).
World: x = column, z = row (down on top views), heading 0 = +x (east), 90 = +z (south); turn angle > 0 = LEFT."""
import os, sys, json
import numpy as np
ROOT = os.environ.get('MXSIM_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
from engine import Path
import compose

FOLDER = 'USLANDRaceTrack'                 # MX Simulator folder (no spaces, like the other USLAND folders)
DESC = 'usland race track'                 # name shown in game
N_EXP, S = 10, 0.28975                     # 2049 px, 593.4 ft
N_GATES, GATE_PITCH = 22, 4.0

RF = json.load(open(ROOT + '/lib/rf_units.json'))['units']

# ---------------------------------------------------------------------------------------------- geometry (plan v1)
# v1b (build): the RF Anaheim floor is not the 17-591 x 21-583 rectangle of the plan (bounding box of the wall models) but
# a shield: the right-hand stands run diagonally (x ~ 554 at z 220, 481 at z 430, 437 at z 540, measured on stadium-crowd /
# seats / seatingarea / green0x vertices), rocks bottom-left. Same lanes and sections, the layout moves 60 ft west, the C -> D
# top link becomes 2 small berms + 34 ft (D 56 ft from C, so the D -> E bottom berm clears lane C) and D -> E becomes one big
# 180 berm raised to z 450 (clear of the stands); D and E are shorter. Doc 13.
XF, R1, ZC = 65.0, 90.0, 380.0             # finish lane F (south) / first-turn bowl radius / bowl centre z
SPC, RB, RS, GH = 43.0, 21.5, 11.0, 34.0   # lane spacing, big / small berm riding radius, straight between two small berms
ZT, ZB, ZTOP, ZDE = 145.0, 514.0, 63.0, 450.0
XA = XF + 2 * R1; XB, XC = XA + SPC, XA + 2 * SPC; XD = XC + 2 * RS + GH; XE = XD + SPC
GATE = (XF + R1, 112.0)                    # centre of the gate row (faces south, on the bowl axis)
STADIUM_FLOOR = (17.0, 591.0, 21.0, 583.0) # bounding box of the RF Anaheim wall models (the real outline is checked on the vertices)
ROCKS = [(40, 470), (60, 466), (80, 479), (100, 497), (120, 535), (140, 541), (160, 539), (180, 535)]   # RF rocks, min z per 20 ft of x


def kind_of(tok):
    if isinstance(tok, tuple) and tok[0] == 'rf': return RF[tok[1]]['kind']
    if isinstance(tok, tuple) and tok[0] == 'whoops': return 'W'
    return compose.U[compose.ALIAS.get(tok, tok)]['kind']


def lane(tokens):
    """compose.lane for mixed RF + JGSX lanes. tokens: JGSX uid | ('rf', uid) | ('whoops', key, n) | ('gap', ft).
    Floor gaps: two RF units that follow each other in the same RF lane keep their measured gap; JGSX pairs measured as such
    keep theirs (compose.PAIR); otherwise the JGSX medians by kinds (compose.GAP), 16.25 ft next to a big jump (X).
    Returns (profile, items[(name, start_ft, end_ft, H, source)])."""
    prof = [np.zeros(1)]; items = []; pos = 0.0; prev = None; forced = None
    for t in tokens:
        if isinstance(t, tuple) and t[0] == 'gap': forced = t[1]; continue
        if isinstance(t, tuple) and t[0] == 'rf':
            u = RF[t[1]]; p = np.asarray(u['prof'], float); name = t[1]; src = 'RF'
        elif isinstance(t, tuple) and t[0] == 'whoops':
            p = compose.whoops(t[1], t[2]); name = f'whoops {t[1]} x{t[2]}'; src = 'JGSX'
        else:
            u, p = compose.unit(t); name = t; src = 'JGSX'
        k = kind_of(t)
        if prev is not None:
            if forced is not None: g = forced
            elif isinstance(t, tuple) and t[0] == 'rf' and isinstance(prev[0], tuple) and prev[0][0] == 'rf' \
                    and RF[prev[0][1]]['track'] == RF[t[1]]['track'] and RF[prev[0][1]]['cp'] == RF[t[1]]['cp'] \
                    and RF[prev[0][1]]['index'] == RF[t[1]]['index'] - 1:
                g = RF[t[1]]['gap_before']
            else:
                pu = None if isinstance(prev[0], tuple) else compose.ALIAS.get(prev[0], prev[0]); cu = None if isinstance(t, tuple) else compose.ALIAS.get(t, t)
                g = compose.PAIR.get((pu, cu), compose.GAP.get((prev[1], k), 16.25 if 'X' in (prev[1], k) else 5.3))
            n = int(round(g / 0.1)); prof.append(np.zeros(n)); pos += n * 0.1
        prof.append(p); items.append((name, pos, pos + len(p) * 0.1, float(p.max()), src)); pos += len(p) * 0.1
        prev = (t, k); forced = None
    return np.concatenate(prof), items


# ---------------------------------------------------------------------------------------------- sections (lap order)
SECTIONS = {
 'A': ('URT-A whoops JGSX Cleveland (entry + 8)', 25.0, [('whoops', 'Custom1_0', 9)]),
 'B': ('URT-B JGSX entry + RF Anaheim 1 rhythm (big-big-mid-double) + RF on-off', 6.0,
       ['Arlington_g37_0'] + [('rf', f'RF_A1_cp22_{i}') for i in range(5)] + [('rf', 'RF_A1_cp22_6')]),
 'C': ('URT-C JGSX double + RF Houston (double 4-4, on-off 6.0) + JGSX round big', 8.0,
       ['Custom1_g71_3', 'Custom1_g71_5'] + [('rf', f'RF_HOU_cp12_{i}') for i in (3, 4, 5, 6)] + ['Glendale_g30_0']),
 'D': ('URT-D JGSX single + RF big triple 8.5/5.5/7.3 + JGSX double', 6.0,
       ['Arlington_g43_1', ('gap', 29.0)] + [('rf', f'RF_A1_cp10_{i}') for i in range(3)] + ['Custom_g55_2', 'Arlington_g43_2']),
 'E': ('URT-E JGSX small bump + full RF Anaheim 1 lane + RF mid single 4.8', 10.0,
       ['Custom1_g30_1'] + [('rf', f'RF_A1_cp3_{i}') for i in range(6)] + [('rf', 'RF_A1_cp7_1')]),
 'R': ('URT-R top lane: JGSX Arlington triple + RF Houston big-single-big-single + JGSX single', 8.0,
       ['Arlington_g1_1', 'Arlington_g1_3', 'Arlington_g37_4'] + [('rf', f'RF_HOU_cp4_{i}') for i in (2, 3, 4, 5)] + ['Custom1_g29_1']),
 'F': ('URT-F finish lane: small bump + RF Anaheim 2 step-up (finish on the take-off) + single', 14.0,
       ['Glendale_g40_2', ('rf', 'RF_A2_cp21_0'), ('rf', 'RF_A2_cp21_1'), 'Custom_g55_2']),
}
FINISH = ('F', 1)                          # finish line on the crest of the 2nd item of section F (RF step-up take-off, 8.75 ft)

COMBOS = {}
def sec(key):
    name, u0, toks = SECTIONS[key]; p, items = lane(toks)
    COMBOS[name] = dict(tokens=[t if isinstance(t, str) else list(t) for t in toks], items=[it[:4] for it in items],
                        sources=[it[4] for it in items], length=len(p) * 0.1)
    return (p, u0, name)


def track():
    p = Path(XF, ZTOP + RS, 90.0, 'URT')                                       # top of F, heading south
    p.straight(ZC - (ZTOP + RS), [sec('F')], tag='F finish lane')
    p.turn(+180, R1, None, tag='T1 first turn: flat open bowl (no berm)')
    p.straight(ZC - ZT, [sec('A')], tag='A whoops')
    p.turn(-180, RB, 'big_det_a', tag='T2')
    p.straight(ZB - ZT, [sec('B')], tag='B')
    p.turn(+180, RB, 'big_cle', tag='T3')
    p.straight(ZB - ZT, [sec('C')], tag='C')
    p.turn(-90, RS, 'small_arl', tag='T4')
    p.straight(GH, [], tag='C-D link')
    p.turn(-90, RS, 'small_cus_b', tag='T5')
    p.straight(ZDE - ZT, [sec('D')], tag='D')
    p.turn(+180, RB, 'big_cus', tag='T6')
    p.straight(ZDE - (ZTOP + RS), [sec('E')], tag='E')
    p.turn(+90, RS, 'small_arl', tag='T7')
    p.straight(XE - RS - (XF + RS), [sec('R')], tag='R top lane')
    p.turn(+90, RS, 'small_cus_a', tag='T8')
    return p


L1 = ZC - GATE[1]                          # start straight: gate row -> bowl centre level, then flat LEFT 180 at R1/2 inside the bowl
START = dict(gate=GATE, heading=90.0, route=[('S', L1), ('T', +180, R1 / 2)],
             narrow=[(0.0, None), (15.0, None), (L1, 40.0)], end_w=30.0, finish=(SECTIONS[FINISH[0]][0], FINISH[1]))


def start_route():
    from starts import StartRoute
    R = StartRoute(START, N_GATES, GATE_PITCH); START['merge'] = (float(R.merge[0]), float(R.merge[1])); START['length'] = R.L
    return R


if __name__ == '__main__':
    p = track(); R = start_route()
    print(f'lap {p.s:.1f} ft, closure {np.hypot(p.x - XF, p.z - (ZTOP + RS)):.4f} ft, start {R.L:.1f} ft, merge {R.merge.round(2)}')
    for n, c in COMBOS.items(): print(f"  {c['length']:6.1f} ft  {n}")
