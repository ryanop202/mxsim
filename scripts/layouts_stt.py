"""Saint-Thibéry v5 (user's corrections after the first in-game test of v4) / v4 (corrections drawn on v3) / v3 - from the user's drawing on the drone top view (the track drawn as a ribbon: both lane edges).
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
from layouts_sx import L, sec, _start, SA, SD, SC, BB, TABLE_A, TABLE_B, TABLE9, BIG_TRIPLE, RB, RS, BIG, BIG2, SMALL, SMALL2

STT_ORIGIN = (160.0, 170.0)
# v5: L1 moved 70 ft north (room for a real finish double + the curve), east lane 10 ft further east (room after the turn)
Z = dict(L1=-70.0, L2=43.0, L3=86.0, L4=129.0, L6=206.0, L7=249.0)
XWL, XBOWL, XU, XMID, XEL, XU67 = -15.0, 295.0, 70.0, 364.0, 421.0, -5.0   # west column, bowl centre, L3/L2 U, middle lane, east lane, L6/L7 U
ARENA = (-110.0, 450.0, -94.0, 274.0)                                     # fence box (x0, x1, z0, z1), local
ROWS = dict(L1=('L1', XU + 40), L2=('L2', XU + 40), L3=('L3', XU + 40), L4=('L4', 100.0), L6=('L6', 40.0), L7=('L7', 40.0))
FINISH_SEC = 'STT-ouest saut d arrivee (double JGSX)'
HALF_BERM = ('bowl (L4 -> L3)', 'U L6 -> L7', 'L7 -> east lane')         # v4: berm only on the second half of these turns
ROLLER, ROLLER2, SMALL_B = 'Custom1_g30_1', 'Glendale_g65_2', 'Glendale_g40_2'   # 1.9 / 1.6 / 2.5 ft
R45 = 30.0                                                                   # the curve west column -> L4: two 45 deg bends
FIN_TAKEOFF, FIN_LANDING = 'Custom1_g30_2', 'Arlington_g30_2'               # JGSX finish double 8.8 -> 11.2 ft (Cleveland / Test Track g30)

def stt():
    ox, oz = STT_ORIGIN
    fin = [FIN_TAKEOFF, ('gap', 15.0), FIN_LANDING]                          # v5: real finish jump, landing a bit closer (JGSX gap 21.9)
    a_col = len(L('tmp', fin)) * 0.1 + 10.0                                  # west column straight: the finish double + 10 ft
    d_diag = (Z['L4'] - (Z['L1'] + RS) - a_col - R45 * np.sin(np.radians(45)) - R45 * (1 - np.cos(np.radians(45)))) / np.sin(np.radians(45))
    x_l4 = XWL + R45 * (1 - np.cos(np.radians(45))) + d_diag * np.sin(np.radians(45)) + R45 * np.sin(np.radians(45))
    p = Path(ox + x_l4, oz + Z['L4'], 0.0, 'STT')                         # L4, after the curve, eastbound
    # v5: normal bump, roller, then the freestyle jump: finish-jump take-off, landing twice as high as v4 (dome 9 -> 18 ft, scaled)
    p.straight(XBOWL - x_l4, [sec('STT-L4 bosse, roller, saut freestyle', [SA[1], ROLLER2, ('gap', 12.0), FIN_TAKEOFF, ('gap', 15.0), ('scale', TABLE9, 18.0)], 4.0)], tag='L4 bump, roller, freestyle jump')
    p.turn(+180, RB, BIG, tag='bowl (L4 -> L3)')
    p.straight(XBOWL - XU, [sec('STT-L3 triple on table, off', [SD[0], SD[3], TABLE_A] + SA[:2], 12.0)], tag='L3 (first bump lower) triple on table / off')
    p.turn(-180, RB, BIG2, tag='U L3 -> L2 (rays)')
    p.straight((XMID - RS) - XU, [sec('STT-L2 triple, triple, double', SA[:3] + SD[:3] + [SC[0], SC[1]], 3.0)], tag='L2 triple, triple, double right after the U')
    p.turn(-90, RS, SMALL, tag='L2 -> middle lane')
    Lmid = (Z['L6'] - RS) - (Z['L2'] + RS); mid = [SC[2], TABLE_B, SC[3]]
    p.straight(Lmid, [sec('STT-mid bosse, table, bosse', mid, (Lmid - len(L('tmp', mid)) * 0.1) / 2)], tag='middle lane: bump, table, bump')
    p.turn(-90, RS, SMALL2, tag='middle lane -> L6')
    L6 = (XMID - RS) - XU67
    p.straight(L6, [sec('STT-L6 roller a sauter', [SMALL_B], L6 / 2 - 14.0)], tag='L6 straight with a jumpable roller')
    p.turn(+180, RB, BIG, tag='U L6 -> L7')
    p.straight((XEL - RS) - XU67, [sec('STT-L7 12 whoops puis triple', [('whoops', 'Custom_0', 12), ('gap', 30.0)] + SA[3:6], 12.0)], tag='L7 whoops + triple')
    p.turn(+90, RS, SMALL, tag='L7 -> east lane')
    Lns = (Z['L7'] - RS) - (Z['L1'] + RS)
    p.straight(Lns, [sec('STT-east gros triple SX', BIG_TRIPLE, (Lns - len(L('tmp', BIG_TRIPLE)) * 0.1) / 2)], tag='east lane, big SX triple (Cleveland g29, as SX2)')
    p.turn(+90, RS, SMALL2, tag='east lane -> L1')
    p.straight((XEL - RS) - (XWL + RS), [sec('STT-L1 triple, triple, bosse, table, bosse, 2 bosses', SA[:3] + SD[:3] + [SA[3], TABLE_B, SA[0], SA[0], SA[0]], 16.0)], tag='L1 along the north fence')
    p.turn(+90, RS, SMALL, tag='L1 -> west column')
    p.straight(a_col, [sec(FINISH_SEC, fin, 4.0)], tag='west column: finish double')
    p.turn(+45, R45, None, tag='curve 1/2')
    p.straight(d_diag, [sec('STT-courbe roller', [ROLLER], (d_diag - len(L('tmp', [ROLLER])) * 0.1) / 2)], tag='curve: roller')
    p.turn(+45, R45, None, tag='curve 2/2')
    _start('STT', ox, oz, gate=(-100.0, 167.0), heading=0.0,
           route=[('S', 350.0), ('T', +90, 40.0, None), ('TO', (XBOWL + RB, Z['L4'] - RB))],
           narrow=[(0.0, None), (8.0, None), (42.0, 30.0)], end_w=30.0,
           finish=(FINISH_SEC, 0))
    return p
