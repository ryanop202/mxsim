"""Saint-Thibéry v3 - from the user's drawing on the drone top view (the track drawn as a ribbon: both lane edges).
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
from layouts_sx import L, sec, _start, SA, SD, SC, BB, TABLE_A, TABLE9, RB, RS, BIG, BIG2, SMALL, SMALL2

STT_ORIGIN = (160.0, 100.0)
Z = dict(L1=0.0, L2=43.0, L3=86.0, L4=129.0, L6=206.0, L7=249.0)
XWL, XBOWL, XU, XMID, XEL, XU67 = -15.0, 295.0, 70.0, 364.0, 411.0, -5.0   # west lane, bowl centre, L3/L2 U, middle lane, east lane, L6/L7 U
ARENA = (-110.0, 440.0, -24.0, 274.0)                                     # fence box (x0, x1, z0, z1), local
ROWS = dict(L1=('L1', XU + 40), L2=('L2', XU + 40), L3=('L3', XU + 40), L4=('L4', 20.0), L6=('L6', 40.0), L7=('L7', 40.0))
FINISH_SEC = 'STT-L4 2 singles + grosse table centrale (arrivee)'

def stt():
    ox, oz = STT_ORIGIN
    p = Path(ox + XWL + RS, oz + Z['L4'], 0.0, 'STT')                  # L4, west end, eastbound
    p.straight(XBOWL - (XWL + RS), [sec(FINISH_SEC, [SA[0], SA[1], ('gap', 25.0), TABLE9], 90.0)], tag='L4 2 singles + big centre table')
    p.turn(+180, RB, BIG, tag='bowl (L4 -> L3)')
    p.straight(XBOWL - XU, [sec('STT-L3 triple on table, off', SD[2:4] + [TABLE_A] + SA[:2], 12.0)], tag='L3 triple on table / off')
    p.turn(-180, RB, BIG2, tag='U L3 -> L2 (rays)')
    p.straight((XMID - RS) - XU, [sec('STT-L2 rythmique, 2 gros singles', [SC[0], 'Arlington_g37_2', SC[1], SC[2], 'Arlington_g1_2'], 30.0)], tag='L2 rhythm + 2 big singles')
    p.turn(-90, RS, SMALL, tag='L2 -> middle lane')
    p.straight((Z['L6'] - RS) - (Z['L2'] + RS), [sec('STT-mid triple', SC[:3], 18.0)], tag='middle lane, triple')
    p.turn(-90, RS, SMALL2, tag='middle lane -> L6')
    p.straight((XMID - RS) - XU67, [], tag='L6 flat straight, westbound')
    p.turn(+180, RB, BIG, tag='U L6 -> L7')
    p.straight((XEL - RS) - XU67, [sec('STT-L7 12 whoops puis 2 petits singles', [('whoops', 'Custom_0', 12), ('gap', 40.0), 'Glendale_g40_2', SD[0]], 20.0)], tag='L7 whoops along the stands')
    p.turn(+90, RS, SMALL, tag='L7 -> east lane')
    p.straight((Z['L7'] - RS) - (Z['L1'] + RS), [sec('STT-east triple + petite bosse', SA[3:6] + [('gap', 10.0), 'Glendale_g40_2'], 20.0)], tag='east lane, triple')
    p.turn(+90, RS, SMALL2, tag='east lane -> L1')
    p.straight((XEL - RS) - (XWL + RS), [sec('STT-L1 longue rythmique', SA + SD, 18.0)], tag='L1 long rhythm along the north fence')
    p.turn(+90, RS, SMALL, tag='L1 -> west lane')
    p.straight((Z['L4'] - RS) - (Z['L1'] + RS), [sec('STT-west 2 singles', SA[4:6], 18.0)], tag='west lane, 2 singles')
    p.turn(+90, RS, SMALL2, tag='west lane -> L4')
    _start('STT', ox, oz, gate=(-100.0, 167.0), heading=0.0,
           route=[('S', 350.0), ('T', +90, 40.0, None), ('TO', (XBOWL + RB, Z['L4'] - RB))],
           narrow=[(0.0, None), (8.0, None), (42.0, 30.0)], end_w=30.0,
           finish=(FINISH_SEC, 2))
    return p
