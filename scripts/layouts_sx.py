"""SX1, SX2, SX3 layouts (v3): rhythm lanes composed of measured JGSX units (compose.py), Glendale sand stamps (SX3),
JGSX-style starts: 22 gates, dedicated start straight that funnels into the lap before a berm first turn."""
import numpy as np
from engine import Path, STAMPS
from compose import lane
import compose

BIG, BIG2, SMALL, SMALL2 = 'big_det_a', 'big_cle', 'small_cus_a', 'small_arl'
RB, RS = 21.5, 11.0

# measured unit families (JGSX reference lanes)
SA = ['Arlington_g37_0', 'Arlington_g37_1', 'Arlington_g1_1', 'Arlington_g1_3', 'Arlington_g37_4', 'Arlington_g1_4']   # 3.4-4.0 ft
SD = ['Detroit_g36_1', 'Glendale_g36_1', 'Glendale_g84_2', 'Detroit_g36_4']                                            # 3.0-3.7 ft
SC = ['Custom1_g71_2', 'Custom1_g71_3', 'Custom1_g71_5', 'Custom_g55_2']                                              # 3.5-3.9 ft
BB = ['Arlington_g37_2', 'Arlington_g1_2', 'Custom1_g29_3']                                                          # 5.8-6.0 ft
TABLE_A, TABLE_B = 'Custom1_g71_1', 'Arlington_g49_2'                                                                # 6.2 ft tables (top ~20 ft)
TABLE9 = 'Arlington_g20_1'                                                                                           # 9.0 ft step table
TRIPLE = ['Detroit_g27_1', 'Arlington_g29_2']                                                                        # 7.9 / 6.0 / 7.4 trio
STEPUP = ['Arlington_g30_1', 'Arlington_g30_2']                                                                      # 8.8 -> 11.2
BIGDBL = ['Glendale_g83_1', 'Glendale_g83_2']                                                                        # 7.1 -> 7.9, 40.5 ft floor gap
BIG_TRIPLE = ['Custom1_g29_2', ('gap', 0.5), 'Custom1_g29_3', ('gap', 1.6), 'Arlington_g29_2']                    # Cleveland g29 big triple 7.9 / 6.0 / 7.4 (as built)
FINISH_DBL = ['Custom1_g30_2', ('gap', 21.9), 'Arlington_g30_2']                                                    # JGSX finish double 8.8 -> 11.2 (Cleveland / Test Track g30)
XE3 = 450.0                                                                                                           # SX3: start U-turn exit on the F lane (local x)
HARD_TRIPLE = ['Detroit_g0_2', 'Arlington_g28_2', 'Custom_g6_1']                                                    # 5.8 / 5.8 / 6.0 ft short big singles (v4)
MIXED_DET = 'Detroit_g35_0'                                                                                          # Detroit g35 rhythm lane (on-off 6.1/5.7 + 3.5s)
SAND = ['Glendale_g66_1', 'Glendale_g66_2', 'Glendale_g86_0', 'Glendale_g30_3', 'Glendale_g65_3', 'Glendale_g63_3', 'Glendale_g86_1', 'Glendale_g65_2']

COMBOS = {}
SPLITS = {}   # section name -> [(start_ft, prof_left, prof_right)] (double lines, see compose.lane)
def L(name, tokens):
    p, items = lane(tokens); COMBOS[name] = dict(tokens=tokens, items=items, length=len(p) * 0.1)
    if compose.LAST_SPLITS: SPLITS[name] = list(compose.LAST_SPLITS)
    return p

def sec(name, tokens, u0):
    return (L(name, tokens), u0, name)

# Start definitions (world coords): gate row centre, heading (deg, 0 = +x/east, -90 = north), straight run before the
# funnel, and the merge point on the lap (start riders are on the lap lane from there on).
STARTS = {}
N_GATES, GATE_PITCH = 22, 4.0          # JGSX 2026: 22 gates at 4 ft

def _start(name, ox, oz, gate, heading, route, narrow, finish=None, end_w=None):
    """route ops in LOCAL coords (see starts.py); merge = end of the route (must lie on the lap line)."""
    rt = [(op[0], (ox + op[1][0], oz + op[1][1])) if op[0] == 'TO' else op for op in route]
    S0 = dict(gate=(ox + gate[0], oz + gate[1]), heading=heading, route=rt, narrow=narrow, finish=finish)
    if end_w: S0['end_w'] = end_w
    from starts import StartRoute
    R = StartRoute(S0, N_GATES, GATE_PITCH); S0['merge'] = (float(R.merge[0]), float(R.merge[1])); S0['straight'] = R.s_straight
    S0['length'] = R.L; STARTS[name] = S0

# ---------------------------------------------------------------- SX1 (counter-clockwise, E-W lanes 370 ft) - unchanged lanes
SX1_ORIGIN = (-8.0, -105.0)

def sx1():
    ox, oz = SX1_ORIGIN
    xe, xw, z0 = 520.0, 150.0, 395.0
    p = Path(ox + 77, oz + z0, 0.0, 'SX1')
    p.straight(xe - 77, [sec('SX1-F petite bosse, gros single, single + on-off (ligne d arrivee)', [('split', 'Glendale_g40_2', SA[0]), 'Arlington_g1_2', SA[1], ('gap', 12.0), 'Detroit_g35_2'], 18.0)], tag='finish straight: triple + on-off Detroit (v5)')
    p.turn(+180, RB, BIG, tag='T1 first turn')
    p.straight(xe - xw, [sec('SX1-A S-GROS-S ecarte, 3 S, GROS, S, GROS', [SA[0], ('gap', 8.5), 'Arlington_g37_2', ('gap', 5.0), SA[1], SA[2], SC[0], SC[1], 'Custom1_g29_3', SC[3], 'Arlington_g37_2'], 6.0)], tag='A 2e, 7e et derniere bosses grosses, entree ecartee (v7)')
    p.turn(-180, RB, BIG2, tag='T2')
    p.straight(xe - xw, [sec('SX1-B whoops (entry+11), single 5 ft', [('whoops', 'Custom_0', 12), ('gap', 30.0), 'Glendale_g40_3'], 22.0)], tag='B 12 whoops + single (v4: +10 ft, 5.0 ft)')
    p.turn(+180, RB, BIG, tag='T3')
    p.straight(xe - xw, [sec('SX1-C triple on table, off quad, double', SD[:2] + [TABLE_A] + SA[:4] + [('gap', 14.0)] + SC[:2], 12.0)], tag='C triple on table / off quad')
    p.turn(-180, RB, BIG2, tag='T4')
    p.straight(xe - xw, [sec('SX1-D step-up, triple on table (longer), off', STEPUP + [SC[0], ('gap', 11.0), SC[1], ('gap', 11.0), TABLE_B, SC[2]], 22.0)], tag='D step-up + triple sur table, off (v4)')
    p.turn(+180, RB, BIG, tag='T5')
    p.straight(xe - 77, [sec('SX1-E JGSX on-off lane + triple', [MIXED_DET, ('gap', 10.0)] + SA[3:6], 14.0)], tag='E on-off + triple')
    p.turn(+90, RS, SMALL, tag='T6')
    p.straight((oz + z0 - RS) - p.z, [sec('SX1-V petite bosse + triple', ['Glendale_g40_2'] + SC[1:], 16.0)], tag='V quad')
    p.turn(+90, RS, SMALL2, tag='T7 (berm added)')
    _start('SX1', ox, oz, gate=(120.0, z0 + 70.0), heading=0.0, route=[('S', 220.0), ('TO', (470.0, z0))], narrow=(220.0, 368.0))
    return p

# ---------------------------------------------------------------- SX2 (clockwise, N-S lanes, start straight in the middle)
SX2_ORIGIN = (609.0, 30.0)

def sx2():
    ox, oz = SX2_ORIGIN
    p = Path(ox + 111.0, oz + 140.0, -90.0, 'SX2')          # merge point on the finish lane F (heading north)
    p.straight(140.0 - 46.5, [], tag='F to first turn')
    p.turn(-90, RB, BIG, tag='T1 first turn')                # north -> east
    p.straight(355.0 - 132.5, [sec('SX2-top big triple Cleveland g29', BIG_TRIPLE, 20.0)], tag='top big triple Cleveland (v10)')
    p.turn(-90, RS, SMALL2, tag='T2')                        # east -> south
    p.straight(400.0 - 36.0, [sec('SX2-E1 single single table single table single + 2', [SA[0], SA[1], TABLE_A, SA[3], TABLE_B, SA[4], 'Arlington_g1_4', 'Arlington_g43_1'], 14.0)], tag='E1 bosse bosse table bosse table bosse (v4)')
    p.turn(-180, RB, BIG, tag='T3')                          # south -> north
    p.straight(400.0 - 120.0, [sec('SX2-E2 big double, triple into the turn', BIGDBL + SC[:3], 20.0)], tag='E2 gros double + triple dans le virage (v4)')
    p.turn(+180, RB, BIG2, tag='T4')                         # north -> south
    p.straight(429.0 - 120.0, [sec('SX2-E3 triple on table, triple off', SC[:2] + [TABLE_B] + SD[:2] + [SC[2]], 24.0)], tag='E3 triple on / triple off')
    p.turn(-90, RS, SMALL, tag='T5')                         # south -> west
    p.straight(269.0 - 36.0, [sec('SX2-bottom whoops (entry+7)', [('whoops', 'Custom_0', 8)], 34.0)], tag='bottom 8 whoops, sans bosse (v4)')
    p.turn(-90, RS, SMALL2, tag='T6')                        # west -> north
    p.straight(429.0 - 60.0, [sec('SX2-W1 double ligne, gros, S, table, S, gros, S', [('split', SD[0], 'Custom1_g30_1'), 'Arlington_g37_2', SD[1], TABLE_A, SC[0], 'Custom1_g29_3', SC[2]], 34.0)], tag='W1 double ligne (petite bosse a droite) + table au milieu (v7)')
    p.turn(-180, RB, BIG, tag='T7')                          # north -> south
    # v11b: first triple = the first three bumps of W1 (double ligne Detroit g36_1 | low Custom1 g30_1, Arlington g37_2,
    # Glendale g36_1, measured gaps) with the double ligne mirrored (low bump on the LEFT); big triple at the same place as before
    p.straight(345.0 - 60.0, [sec('SX2-W2 small big small + big triple', [('split', 'Custom1_g30_1', SD[0]), 'Arlington_g37_2', SD[1], ('gap', 6.8)] + BIG_TRIPLE, 22.0)], tag='W2 small (double ligne)-big-small (depart) + big triple (arrivee) (v11)')
    p.turn(+180, RB, BIG2, tag='T8')                         # south -> north (finish lane F)
    p.straight(345.0 - 140.0, [sec('SX2-F triple (singles d avant + 1)', SC[:3], 8.0)], tag='F triple de singles normaux (v5)')
    # v10: grid in the infield heading north, flat left turn, crosses the (flat) top of the F lane, flat left turn into W2
    # right after T7: the start rejoins on the small-big-small; finish line on the W2 big triple (first jump crest)
    # v11b (Ryan's drawing): the corridor runs slightly north-west while narrowing regularly (right edge = one straight line),
    # flat left turn R 51 across the top of F, flat left turn R 8 into W2
    R1, R2, zl = 50.0, 8.0, 70.0                                 # local: westward leg at z 70 (world 100), 26 ft wide: between the T7 berm skirt and the W2 double ligne
    s_t1 = 20.0 + float(np.hypot(206.0 - 173.0, 375.0 - 170.0)) + 50.0
    _start('SX2', ox, oz, gate=(206.0, 395.0), heading=-90.0,
           route=[('S', 20.0), ('TO', (173.0, 170.0)), ('TO', (173.0, zl + R1)), ('T', +90, R1), ('TO', (68.0 + R2, zl)), ('T', +90, R2)],
           narrow=[(0.0, None), (15.0, None), (s_t1, 40.0), (s_t1 + 78.5, 36.0), (s_t1 + 94.0, 26.0)], end_w=26.0,
           finish=('SX2-W2 small big small + big triple', 3))
    return p

# ---------------------------------------------------------------- SX3 (long, Glendale sand: GR sweeper + GL J-turn)
SX3_ORIGIN = (8.0, 560.0)

def sx3():
    """v4: U1 mixed heights + Detroit triple brought closer + small bump; whoops without the bump after them; GR sand
    70 ft closer; U3 drift moved before its combo; GL J tucked right behind the T2 berm (U3 no longer runs 400 ft empty);
    F combo moved east so it ends near the start merge (no long empty straight before T1)."""
    ox, oz = SX3_ORIGIN
    Zf = 330.0
    p = Path(ox + 890.0, oz + Zf, 0.0, 'SX3')                # merge point on the finish lane F (heading east)
    p.straight(980.0 - 890.0, [], tag='F to first turn')
    p.turn(+180, RB, BIG, tag='T1 first turn')               # east -> west, z = Zf - 43
    u1 = SA[:3] + ['Arlington_g37_2', 'Detroit_g36_1', 'Glendale_g84_2', 'Detroit_g36_4', 'Glendale_g36_1', 'Custom1_g29_3', ('gap', 30.0)] + [TRIPLE[0], ('gap', 8.0), TRIPLE[1], ('gap', 35.0), 'Glendale_g40_2']   # v8: Detroit triple lengthened (1.6 -> 8 ft)
    p.straight(980.0 - 320.0, [sec('SX3-U1 triple, big, triple, big, Detroit triple, small bump', u1, 3.0)], tag='U1 triple-gros-triple-gros + triple Detroit + petite bosse (v5)')
    p.turn(-180, RB, BIG2, tag='T2')                          # west -> east, z = Zf - 86
    u2 = [('whoops', 'Detroit_0', 10), ('gap', 30.0), SA[1], BB[2], SD[3], ('gap', 30.0)] + STEPUP
    p.straight(910.0 - 320.0, [sec('SX3-U2 whoops (entry+9), on-off, step-up', u2, 16.0)], tag='U2 10 whoops sans bosse + on-off + step-up (v4)')
    p.stamp('GR', tag='GR Glendale sand sweeper (left-hand)', mirror=True)   # east -> west, 114 ft north: Glendale sand berm, mirrored
    # closure: lane spacing 43 ft + GR 114 ft + GL 187 ft (+ exit bend) do not land on z = Zf by themselves -> U3 drifts
    # south by d with two flat 12 deg bends, in the empty run right after the GR exit (before the combo)
    X_GL = 335.0                                              # GL entry: its J leg passes right behind (west of) the T2 berm
    gl = np.asarray(STAMPS['GL']['line']); dGL = gl[-1, 1] - gl[0, 1]
    hGL = -np.arctan2(gl[-1, 1] - gl[-6, 1], gl[-1, 0] - gl[-6, 0]); Rx = 80.0
    d = (oz + Zf) - p.z - dGL + Rx * (1 - np.cos(hGL))
    alpha, Rd = 15.0, 120.0
    Ld = (d - 2 * Rd * (1 - np.cos(np.radians(alpha)))) / np.sin(np.radians(alpha))
    u3 = SC[:2] + [TABLE_B] + SA[:4] + [('gap', 10.0), SD[0], 'Custom1_g29_3', SD[2], 'Arlington_g1_2']
    Lu3 = len(L('SX3-U3 triple on table, off quad, S-big-S-big', u3)) * 0.1 + 4.0
    p.straight(Lu3, [sec('SX3-U3 triple on table, off quad, S-big-S-big', u3, 2.0)], tag='U3 combo des la sortie du sable (v5)')
    p.turn(+alpha, Rd, None, tag='U3 drift (flat, 15 deg)')
    p.straight(Ld, [], tag='U3 drift')
    p.turn(-alpha, Rd, None, tag='U3 drift back (flat, 15 deg)')
    p.straight(p.x - (ox + X_GL), [], tag='U3 to sand')
    p.stamp('GL', tag='GL Glendale sand J-turn', snap=False)  # west -> south -> NE (Glendale sand, as built)
    p.turn(-np.degrees(-p.t), Rx, None, tag='sand exit bend (flat, R 80, as in Glendale)')
    # v11: pain de sucre right at the sand exit (lap only: the start rejoins after it), then the triple and the JGSX finish double
    # (Cleveland g30_2 8.8 -> Arlington g30_2 11.2) where the v9 triple + double were (double ends 108 ft before the turn)
    x_pds, x_tri = 400.0, ox + 890.0 - 108.0 - 132.3 - 24.0 - 106.0           # v9: triple start, from the v9 double end
    g1 = x_tri - (x_pds + 30.4)
    f3 = ['Custom1_g59_1', ('gap', g1)] + SC[:3] + [('gap', 24.0)] + FINISH_DBL
    Lf = ox + 890.0 - p.x
    p.straight(Lf, [sec('SX3-F pain de sucre, triple, double d arrivee JGSX', f3, x_pds - p.x)], tag='F pain de sucre (sortie du sable) + triple + double d arrivee (v11)')
    # v11: grid under the F lane heading WEST, gradual taper (no funnel), FLAT right U-turn (no berm) -> F heading east,
    # merging between the pain de sucre and the triple
    xc, R3 = 472.0, 24.0                    # corridor north edge kept straight at z ~918 (clear of the triple's skirt), width 92 -> 40
    s_t = 15.0 + float(np.hypot(765.0 - (xc + 20.0), 405.0 - (Zf + 2 * R3))) + 20.0
    _start('SX3', ox, oz, gate=(780.0, Zf + 75.0), heading=180.0, route=[('S', 15.0), ('TO', (xc + 20.0, Zf + 2 * R3)), ('TO', (xc, Zf + 2 * R3)), ('T', -180, R3, None)],
           narrow=[(0.0, None), (15.0, None), (s_t, 40.0)], finish=('SX3-F pain de sucre, triple, double d arrivee JGSX', 4))
    return p

SAND_TAGS = ()
