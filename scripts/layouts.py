"""Original layouts of the compound (MX + SX1 + SX2). Obstacles = measured sections from the library."""
import numpy as np
from engine import Path, BERMS, LIB

BIG = 'big_det_a'; BIG2 = 'big_cle'; SMALL = 'small_cus_a'; SMALL2 = 'small_arl'
RB = 21.5   # riding radius in a big 180 crescent (measured 21.2-22.8)
RS = 11.0   # riding radius in a small crescent (measured 10.5-11.3)
LANE = 2 * RB  # lane spacing implied by a 180 big berm (43 ft, same as references)

# ---------------------------------------------------------------- SX1
SX1_ORIGIN = (20.0, 1175.0)


def sx1():
    ox, oz = SX1_ORIGIN
    xe, xw = 470.0, 150.0  # east / west 180-turn centres (local X)
    z0 = 395.0
    p = Path(ox + 77, oz + z0, 0.0, 'SX1')
    # start / finish straight (shared with the start), flat floor
    p.straight(xe - 77, [], tag='start-finish')
    p.turn(+180, RB, BIG, tag='T1 first turn')
    # lane A (west): triple then three singles
    p.straight(xe - xw, [('triple_det', 40.0), ('rhythm5_det', 205.0, (0, 2))], tag='A triple+rhythm')
    p.turn(-180, RB, BIG2, tag='T2')
    p.straight(xe - xw, [('whoops_cus', 24.0)], tag='B whoops')
    p.turn(+180, RB, BIG, tag='T3')
    p.straight(xe - xw, [('bigdouble_gle', 30.0, (0, 1)), ('rhythm3_cus', 190.0, (0, 1))], tag='C big double + rhythm')
    p.turn(-180, RB, BIG2, tag='T4')
    p.straight(xe - xw, [('stepup_det', 26.0, (0, 1)), ('rhythm5_gle', 160.0, (0, 3))], tag='D step-up + rhythm')
    p.turn(+180, RB, BIG, tag='T5')
    p.straight(xe - 77, [('longtable_cus', 14.0)], tag='E long table')
    p.turn(+90, RS, SMALL, tag='T6')
    p.straight((oz + z0 - RS) - p.z, [('mixed5_cle', 18.0, (0, 2))], tag='V return rhythm')
    p.turn(+90, RS, None, tag='T7 flat merge corner')
    return p


# ---------------------------------------------------------------- SX2
SX2_ORIGIN = (640.0, 1175.0)


def sx2():
    """Clockwise; vertical (N-S) serpentine; small 90-degree corners; different section set and order from SX1."""
    ox, oz = SX2_ORIGIN
    zt = 25.0          # start/finish straight (top, heading east)
    zb = 350.0         # bottom 180-turn centres (local Z)
    ztop = zt + RS     # top of the vertical lanes
    x1 = 470.0         # first vertical lane (local X)
    p = Path(ox + 60, oz + zt, 0.0, 'SX2')
    p.straight(x1 - RS - 60, [], tag='start-finish')
    p.turn(-90, RS, SMALL2, tag='T1 first turn')
    L = zb - ztop
    p.straight(L, [('rhythm5_det', 18.0), ('mixed5_cle', 225.0, (0, 1))], tag='V1 rhythm')
    p.turn(-180, RB, BIG, tag='T2')
    Li = zb - 95.0  # inner lanes stop 95 ft below the start straight so the top crescents clear it
    p.straight(Li, [('table9_arl', 26.0, (0, 1))], tag='V2 9ft table')
    p.turn(+180, RB, BIG2, tag='T3')
    p.straight(Li, [('whoops_det', 22.0)], tag='V3 whoops')
    p.turn(-180, RB, BIG, tag='T4')
    p.straight(Li, [('mixed4_arl', 26.0, (1, 3))], tag='V4 rhythm/table')
    p.turn(+180, RB, BIG2, tag='T5')
    p.straight(Li, [('mixed5_arl', 22.0, (0, 3))], tag='V5 mixed rhythm')
    p.turn(-90, RS, SMALL, tag='T6')
    p.straight(p.x - (ox + 60 - RS) - RS, [('rhythm_gap_gle', 26.0)], tag='H bottom rhythm')
    p.turn(-90, RS, SMALL2, tag='T7')
    p.straight(p.z - (oz + zt + RS), [('mixed7_det', 12.0, (0, 4))], tag='W long mixed')
    p.turn(-90, RS, None, tag='T8 flat merge corner')
    return p


# ---------------------------------------------------------------- MX
from engine import fillet_path
MX_CORNERS = [
    (640, 1060, 40), (740, 820, 30), (460, 790, 25), (440, 600, 30), (820, 620, 30), (850, 960, 35),
    (1180, 1000, 30), (1200, 700, 25), (980, 690, 25), (960, 450, 30), (1270, 430, 30),
    (1305, 760, 150), (1290, 1190, 40), (1430, 1200, 35),
    (1420, 650, 30), (1570, 630, 30), (1580, 120, 60),
    (1150, 110, 30), (1130, 300, 25), (760, 300, 30), (520, 340, 140), (300, 300, 40), (300, 520, 25),
    (120, 470, 30), (120, 1060, 25)]
MX_START = (300.0, 1060.0)
# edge i = straight leading INTO corner i (edge 0 starts at MX_START); last edge (n) returns to MX_START
MX_SECTIONS = {
    1: [('ds_s2796_roller', 25.0)],
    2: [('ds_s5459_jump', 35.0)],
    4: [('dd_g43', 70.0)],
    5: [('ds_s8552_jump', 75.0)],
    6: [('ds_s9173_table', 35.0)],
    7: [('ds_s7981_step', 45.0)],
    8: [('ds_s4671_step', 30.0)],
    9: [('dd_g8', 60.0)],
    10: [('ds_s6256_step', 70.0)],
    11: [('dd_g125', 95.0)],
    12: [('ds_s6470_jump', 120.0)],
    14: [('ds_s7006_step', 80.0), ('dd_g132', 260.0)],
    16: [('ds_s10356_step', 150.0)],
    17: [('ds_s8736_step', 40.0), ('ds_s2649_step', 200.0)],      # sand
    19: [('ds_s4671_step', 40.0), ('ds_s9681_step', 190.0)],      # sand
    20: [('ds_s3795_step', 40.0)],                                # sand
    24: [('dd_g18', 80.0), ('ds_double31', 300.0)],
}
SAND_EDGES = (17, 18, 19, 20)


def mx():
    n = len(MX_CORNERS)
    tags = {('c', n - 1): f'corner{n-1} merge flat'}
    for e in SAND_EDGES: tags[('e', e)] = f'edge{e} sand'
    return fillet_path(MX_CORNERS, MX_START, 'MX', sections=MX_SECTIONS, tags=tags)
