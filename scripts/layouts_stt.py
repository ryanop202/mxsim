"""Saint-Thibéry v4 (corrections drawn on v3) / v3 - from the user's drawing on the drone top view (the track drawn as a ribbon: both lane edges).
SX arena, no sand. North = top, stands = south, START = west end. Rows of bumps = lanes (photo px x 0.48 ft):
    L1  north fence         westbound   long rhythm (singles)
    L2                      eastbound   rhythm with two big singles
    L3                      westbound   triple on table, off           (the start joins it, after the bowl)
    L4                      eastbound   two singles, then the big centre table -> finish line on the table
    L6                      westbound   flat straight (the start runs along its north side, eastbound, behind the big table)
    L7  along the stands    eastbound   12 whoops, then two small singles (none bigger than the whoops)
  + east lane (east fence) northbound L7 -> L1, triple
  + west lane (west side)  southbound L1 -> L4, two singles
  + middle lane            southbound L2 -> L6 (east of the bowl), triple
  turns: bowl L4 -> L3 (east, left 180, big berm), U L3 -> L2 (west, right 180, berm with the user's rays),
         L2 -> middle lane -> L6 (right 90s), U L6 -> L7 (west, left 180), 90s at the four corners.
  start: 22 gates at the west end, eastbound behind the big table (between L4 and L6), left into the bowl, joins the lap
         on the bowl (the user's white tick on L3).
Every bump is a measured JGSX unit (lib/), no new shape. Local coords: x east, z south (image down)."""
import numpy as np
from engine import Path
import layouts_sx as LS
from layouts_sx import L, sec, _start, SA, SD, SC, BB, TABLE_A, TABLE_B, TABLE9, RB, RS, BIG, BIG2, SMALL, SMALL2

STT_ORIGIN = (160.0, 100.0)
Z = dict(L1=0.0, L2=43.0, L3=86.0, L4=129.0, L6=206.0, L7=249.0)
XWL, XBOWL, XU, XMID, XEL, XU67 = -15.0, 295.0, 70.0, 364.0, 411.0, -5.0   # west column, bowl centre, L3/L2 U, middle lane, east lane, L6/L7 U
ARENA = (-110.0, 440.0, -24.0, 274.0)                                     # fence box (x0, x1, z0, z1), local
ROWS = dict(L1=('L1', XU + 40), L2=('L2', XU + 40), L3=('L3', XU + 40), L4=('L4', 100.0), L6=('L6', 40.0), L7=('L7', 40.0))
FINISH_SEC = 'STT-ouest saut d arrivee'
# v4: berm only on the second half of these turns (user: "un virage 180 mais qu'il n'y ait que la moitie de l'appui")
HALF_BERM = ('bowl (L4 -> L3)', 'U L6 -> L7', 'L7 -> east lane')
TINY, SMALL_B, MED = 'Custom_g32_1', 'Glendale_g40_2', 'Detroit_g34_0'      # 1.9 / 2.5 / 4.1 ft
R45 = 30.0                                                                   # the curve west column -> L4: two 45 deg bends

def stt():
    ox, oz = STT_ORIGIN
    a_col = 54.0                                                             # west column straight (finish jump)
    d_diag = (Z['L4'] - (Z['L1'] + RS) - a_col - R45 * np.sin(np.radians(45)) - R45 * (1 - np.cos(np.radians(45)))) / np.sin(np.radians(45))
    x_l4 = XWL + R45 * (1 - np.cos(np.radians(45))) + d_diag * np.sin(np.radians(45)) + R45 * np.sin(np.radians(45))
    p = Path(ox + x_l4, oz + Z['L4'], 0.0, 'STT')                         # L4, after the curve, eastbound
    p.straight(XBOWL - x_l4, [sec('STT-L4 moyenne, petite, gros appel + gros dome', [MED, SMALL_B, ('gap', 12.0), 'Arlington_g37_2', TABLE9], 12.0)], tag='L4 medium, small, big kicker + big dome')
    p.turn(+180, RB, BIG, tag='bowl (L4 -> L3)')
    p.straight(XBOWL - XU, [sec('STT-L3 triple on table, off', SD[2:4] + [TABLE_A] + SA[:2], 12.0)], tag='L3 triple on table / off')
    p.turn(-180, RB, BIG2, tag='U L3 -> L2 (rays)')
    p.straight((XMID - RS) - XU, [sec('STT-L2 rythmique, 2 gros singles', [SC[0], 'Arlington_g37_2', SC[1], SC[2], 'Arlington_g1_2'], 30.0)], tag='L2 rhythm + 2 big singles')
    p.turn(-90, RS, SMALL, tag='L2 -> middle lane')
    p.straight((Z['L6'] - RS) - (Z['L2'] + RS), [sec('STT-mid triple', SC[:3], 18.0)], tag='middle lane, triple')
    p.turn(-90, RS, SMALL2, tag='middle lane -> L6')
    p.straight((XMID - RS) - XU67, [], tag='L6 flat straight, westbound')
    p.turn(+180, RB, BIG, tag='U L6 -> L7')
    p.straight((XEL - RS) - XU67, [sec('STT-L7 12 whoops puis petit triple', [('whoops', 'Custom_0', 12), ('gap', 35.0), 'Custom1_g30_1', SMALL_B, TINY], 16.0)], tag='L7 whoops + small triple')
    p.turn(+90, RS, SMALL, tag='L7 -> east lane')
    Lns = (Z['L7'] - RS) - (Z['L1'] + RS); tri = SA[3:6]
    p.straight(Lns, [sec('STT-east triple central', tri, (Lns - len(L('tmp', tri)) * 0.1) / 2)], tag='east lane, central triple')
    p.turn(+90, RS, SMALL2, tag='east lane -> L1')
    p.straight((XEL - RS) - (XWL + RS), [sec('STT-L1 triple, triple, bosse, table, bosse, 2 bosses', SA[:3] + SD[:3] + [SA[3], TABLE_B, SA[4], SA[0], 'Custom_g47_1'], 2.0)], tag='L1 along the north fence')
    p.turn(+90, RS, SMALL, tag='L1 -> west column')
    p.straight(a_col, [sec(FINISH_SEC, ['Custom1_g29_3'], 3.0)], tag='west column: finish jump')
    p.turn(+45, R45, None, tag='curve 1/2')
    p.straight(d_diag, [sec('STT-courbe toute petite bosse', [TINY], (d_diag - len(L('tmp', [TINY])) * 0.1) / 2)], tag='curve: very small bump')
    p.turn(+45, R45, None, tag='curve 2/2')
    _start('STT', ox, oz, gate=(-100.0, 167.0), heading=0.0,
           route=[('S', 350.0), ('T', +90, 40.0, None), ('TO', (XBOWL + RB, Z['L4'] - RB))],
           narrow=[(0.0, None), (8.0, None), (42.0, 30.0)], end_w=30.0,
           finish=(FINISH_SEC, 0))
    return p
