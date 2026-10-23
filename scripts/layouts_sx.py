"""SX1, SX2, SX3 layouts (v3): rhythm lanes composed of measured JGSX units (compose.py), Glendale sand stamps (SX3),
JGSX-style starts: 22 gates, dedicated start straight that funnels into the lap before a berm first turn."""
import numpy as np
from engine import Path, STAMPS
from compose import lane

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
MIXED_DET = 'Detroit_g35_0'                                                                                          # Detroit g35 rhythm lane (on-off 6.1/5.7 + 3.5s)
SAND = ['Glendale_g66_1', 'Glendale_g66_2', 'Glendale_g86_0', 'Glendale_g30_3', 'Glendale_g65_3', 'Glendale_g63_3', 'Glendale_g86_1', 'Glendale_g65_2']

COMBOS = {}
def L(name, tokens):
    p, items = lane(tokens); COMBOS[name] = dict(tokens=tokens, items=items, length=len(p) * 0.1); return p

def sec(name, tokens, u0):
    return (L(name, tokens), u0, name)

# Start definitions (world coords): gate row centre, heading (deg, 0 = +x/east, -90 = north), straight run before the
# funnel, and the merge point on the lap (start riders are on the lap lane from there on).
STARTS = {}
N_GATES, GATE_PITCH = 22, 4.0          # JGSX 2026: 22 gates at 4 ft

def _start(name, ox, oz, gate, heading, straight, merge):
    STARTS[name] = dict(gate=(ox + gate[0], oz + gate[1]), heading=heading, straight=straight, merge=(ox + merge[0], oz + merge[1]))

# ---------------------------------------------------------------- SX1 (counter-clockwise, E-W lanes 370 ft) - unchanged lanes
SX1_ORIGIN = (-8.0, -105.0)

def sx1():
    ox, oz = SX1_ORIGIN
    xe, xw, z0 = 520.0, 150.0, 395.0
    p = Path(ox + 77, oz + z0, 0.0, 'SX1')
    p.straight(xe - 77, [], tag='finish straight')
    p.turn(+180, RB, BIG, tag='T1 first turn')
    p.straight(xe - xw, [sec('SX1-A triple-triple-quad', SA + SC, 12.0)], tag='A triple-triple-quad')
    p.turn(-180, RB, BIG2, tag='T2')
    p.straight(xe - xw, [sec('SX1-B whoops (entry+11)', [('whoops', 'Custom_0', 12), BB[0]], 22.0)], tag='B 12 whoops + single')
    p.turn(+180, RB, BIG, tag='T3')
    p.straight(xe - xw, [sec('SX1-C triple on table, off quad, double', SD[:2] + [TABLE_A] + SA[:4] + [('gap', 14.0)] + SC[:2], 12.0)], tag='C triple on table / off quad')
    p.turn(-180, RB, BIG2, tag='T4')
    p.straight(xe - xw, [sec('SX1-D step-up, triple out', STEPUP + SC[:3], 22.0)], tag='D step-up + triple')
    p.turn(+180, RB, BIG, tag='T5')
    p.straight(xe - 77, [sec('SX1-E JGSX on-off lane + triple', [MIXED_DET, ('gap', 10.0)] + SA[3:6], 14.0)], tag='E on-off + triple')
    p.turn(+90, RS, SMALL, tag='T6')
    p.straight((oz + z0 - RS) - p.z, [sec('SX1-V quad', SC, 16.0)], tag='V quad')
    p.turn(+90, RS, SMALL2, tag='T7 (berm added)')
    _start('SX1', ox, oz, gate=(120.0, z0 + 70.0), heading=0.0, straight=220.0, merge=(470.0, z0))
    return p

# ---------------------------------------------------------------- SX2 (clockwise, N-S lanes, start straight in the middle)
SX2_ORIGIN = (609.0, 30.0)

def sx2():
    ox, oz = SX2_ORIGIN
    p = Path(ox + 111.0, oz + 140.0, -90.0, 'SX2')          # merge point on the finish lane F (heading north)
    p.straight(140.0 - 46.5, [], tag='F to first turn')
    p.turn(-90, RB, BIG, tag='T1 first turn')                # north -> east
    p.straight(355.0 - 132.5, [sec('SX2-top JGSX Arlington rhythm', ['Arlington_g37_0', 'Arlington_g37_1', 'Arlington_g37_2', 'Arlington_g1_3'], 20.0)], tag='top rhythm')
    p.turn(-90, RS, SMALL2, tag='T2')                        # east -> south
    p.straight(400.0 - 36.0, [sec('SX2-E1 on-off double-double', [SA[0], BB[0], SA[1], BB[1], SA[3]], 30.0)], tag='E1 on-off')
    p.turn(-180, RB, BIG, tag='T3')                          # south -> north
    p.straight(400.0 - 120.0, [sec('SX2-E2 big double, double out', BIGDBL + SC[:2], 30.0)], tag='E2 big double + double')
    p.turn(+180, RB, BIG2, tag='T4')                         # north -> south
    p.straight(429.0 - 120.0, [sec('SX2-E3 triple on table, triple off', SC[:2] + [TABLE_B] + SD[:2] + [SC[2]], 24.0)], tag='E3 triple on / triple off')
    p.turn(-90, RS, SMALL, tag='T5')                         # south -> west
    p.straight(269.0 - 36.0, [sec('SX2-bottom whoops (entry+6), single', [('whoops', 'Custom_0', 7), SA[2]], 24.0)], tag='bottom 7 whoops + single')
    p.turn(-90, RS, SMALL2, tag='T6')                        # west -> north
    p.straight(429.0 - 60.0, [sec('SX2-W1 quad-quad', SD + SC, 40.0)], tag='W1 quad-quad')
    p.turn(-180, RB, BIG, tag='T7')                          # north -> south
    p.straight(345.0 - 60.0, [sec('SX2-W2 9 ft table, triple off', [TABLE9] + SD[:3], 30.0)], tag='W2 9 ft table + triple')
    p.turn(+180, RB, BIG2, tag='T8')                         # south -> north (finish lane F)
    p.straight(345.0 - 140.0, [sec('SX2-F finish double', SC[:2], 20.0)], tag='F finish double')
    _start('SX2', ox, oz, gate=(200.0, 395.0), heading=-90.0, straight=95.0, merge=(111.0, 140.0))
    return p

# ---------------------------------------------------------------- SX3 (long, Glendale sand: GR sweeper + GL J-turn)
SX3_ORIGIN = (8.0, 560.0)

def sx3():
    ox, oz = SX3_ORIGIN
    Zf = 330.0
    p = Path(ox + 890.0, oz + Zf, 0.0, 'SX3')                # merge point on the finish lane F (heading east)
    p.straight(980.0 - 890.0, [], tag='F to first turn')
    p.turn(+180, RB, BIG, tag='T1 first turn')               # east -> west, z = Zf - 43
    p.straight(980.0 - 320.0, [sec('SX3-U1 triple-triple-quad, Detroit triple', SA + SD + [('gap', 30.0)] + TRIPLE, 16.0)], tag='U1 triple-triple-quad + triple')
    p.turn(-180, RB, BIG2, tag='T2')                          # west -> east, z = Zf - 86
    p.straight(980.0 - 320.0, [sec('SX3-U2 whoops (entry+9), on-off, step-up', [('whoops', 'Detroit_0', 10), SC[3], ('gap', 24.0), SA[1], BB[2], SD[3], ('gap', 30.0)] + STEPUP, 16.0)], tag='U2 10 whoops + on-off + step-up')
    p.stamp('GR', tag='GR Glendale sand sweeper (left-hand)', mirror=True)   # east -> west, 114 ft north: Glendale sand berm, mirrored
    # U3 drifts 8 deg south over its empty end so that, after the Glendale J and the Glendale-like flat exit bend,
    # the finish lane lands exactly on z = Zf (lane spacing 43 ft + GR 114 ft + GL 187 ft do not close by themselves)
    gl = np.asarray(STAMPS['GL']['line']); dGL = gl[-1, 1] - gl[0, 1]
    hGL = -np.arctan2(gl[-1, 1] - gl[-6, 1], gl[-1, 0] - gl[-6, 0]); Rx = 80.0
    d = (oz + Zf) - p.z - dGL + Rx * (1 - np.cos(hGL))
    alpha, Rd = 8.0, 250.0
    Ld = (d - 2 * Rd * (1 - np.cos(np.radians(alpha)))) / np.sin(np.radians(alpha))
    u3 = SC[:2] + [TABLE_B] + SA[:4] + [('gap', 30.0)] + SD
    L3 = len(L('SX3-U3 triple on table, off quad, quad', u3)) * 0.1 + 16.0 + 30.0
    p.straight(L3, [sec('SX3-U3 triple on table, off quad, quad', u3, 16.0)], tag='U3 table combo + quad')
    p.turn(+alpha, Rd, None, tag='U3 lane drift (flat, 8 deg)')
    p.straight(Ld, [], tag='U3 drift')
    p.turn(-alpha, Rd, None, tag='U3 lane drift back (flat, 8 deg)')
    p.straight(p.x - (ox + 200.0), [], tag='U3 to sand')
    p.stamp('GL', tag='GL Glendale sand J-turn', snap=False)  # west -> south -> NE (Glendale sand, as built)
    p.turn(-np.degrees(-p.t), Rx, None, tag='sand exit bend (flat, R 80, as in Glendale)')
    p.straight(ox + 890.0 - p.x, [sec('SX3-F triple, big double', SC[:3] + [('gap', 34.0)] + BIGDBL, 20.0)], tag='F triple + big double')
    _start('SX3', ox, oz, gate=(630.0, Zf + 70.0), heading=0.0, straight=140.0, merge=(890.0, Zf))
    return p

SAND_TAGS = ()
