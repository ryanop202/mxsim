"""Saint-Thibéry (USLAND), from the user's drone photos and drawings. SX arena, no sand. North = top, stands = south,
START = west end. Every bump is a measured JGSX unit (lib/) unless marked 'scaled' (height scaled, same shape/length) or
'landing' (scaled, back side replaced by a gentle slope) - asked by the user after the in-game tests.

Lap (v6, after the 2nd in-game test):
  L7  along the stands, eastbound : tiny double, 9 whoops, triple (closer to the turn)
  real high berm turn (90, big radius) -> east lane northbound : big SX triple (Cleveland g29, as SX2)
  L1  north, westbound : triple, triple, bump, table, bump, 2 bumps (singles 20 % higher)    -- as close as the finish allows
  left turn -> west column southbound : JGSX finish double (finish line + arch)
  one 90 curve -> L4 eastbound, straight : roller, bump, roller, freestyle jump (steep kicker 10.5 ft, landing 18 ft with a
      gentle back side, 55 ft)
  bowl (left 180, half berm) -> L3 westbound : double, bump, table, bump, bump
  U (right 180, rays) -> L2 eastbound : right after the turn, big tight bumps: triple (1st bump split, lower on the inside),
      triple, double
  -> middle lane southbound : bump, table, bump
  -> L6 westbound : jumpable roller right at the turn exit, flat straight
  U (left 180, half berm) -> L7
Start: 22 gates at the west end, eastbound behind the freestyle jump (between L4 and L6), left into the bowl.
Local coords: x east, z south (image down)."""
import numpy as np
from engine import Path
import layouts_sx as LS
from layouts_sx import L, sec, _start, SA, SD, SC, BB, TABLE_A, TABLE_B, TABLE9, BIG_TRIPLE, RB, RS, BIG, BIG2, SMALL, SMALL2

STT_ORIGIN = (160.0, 170.0)
FIN = ['Custom1_g30_2', ('gap', 15.0), 'Arlington_g30_2']                 # JGSX finish double 8.8 -> 11.2 ft, landing a bit closer (approved)
R_CURVE = 21.5                                                              # one 90 deg curve west column -> L4, then straight
R_HIGH = 21.5                                                               # v6: the 90 after the whoops: big radius, big berm, higher
def _col(): return len(L('tmp', FIN)) * 0.1 + 4.0                          # west column straight: the finish double + 4 ft
Z = dict(L2=43.0, L3=86.0, L4=129.0, L6=206.0, L7=249.0); Z['L1'] = round(Z['L4'] - R_CURVE - _col() - RS, 1)   # L1 as close as the finish allows
XWL, XBOWL, XU, XMID, XEL, XU67 = -15.0, 295.0, 60.0, 364.0, 421.0, -5.0   # west column, bowl centre, L3/L2 U, middle lane, east lane, L6/L7 U
ARENA = (-110.0, 450.0, Z['L1'] - 24.0, 274.0)                            # fence box (x0, x1, z0, z1), local
ROWS = dict(L1=('L1', XU + 50), L2=('L2', XU + 50), L3=('L3', XU + 50), L4=('L4', 100.0), L6=('L6', 40.0), L7=('L7', 40.0))
FINISH_SEC = 'STT-ouest saut d arrivee (double JGSX)'
HALF_BERM = ('bowl (L4 -> L3)', 'U L6 -> L7')                             # berm only on the second half of these turns
BERM90_GAIN = 1.4                                                           # v6: berms of the 90 deg turns higher
ROLLER, ROLLER2, SMALL_B = 'Custom1_g30_1', 'Glendale_g65_2', 'Glendale_g40_2'   # 1.9 / 1.6 / 2.5 ft

def up(units, k):
    """measured singles scaled up by k (v6: L1 "un peu plus haut", L2 "plus grosses"); gaps kept."""
    out = []
    for u in units:
        if isinstance(u, tuple): out.append(u); continue
        LS.L('tmp', [u]); out.append(('scale', u, round(LS.COMBOS['tmp']['items'][0][3] * k, 2)))
    return out

def stt():
    ox, oz = STT_ORIGIN
    a_col = _col(); x_l4 = XWL + R_CURVE
    p = Path(ox + x_l4, oz + Z['L4'], 0.0, 'STT')                          # L4, after the curve, eastbound (straight)
    fmx = [('scale', 'Custom1_g30_2', 10.5), ('gap', 12.0), ('landing', TABLE9, 18.0, 55.0)]   # steep kicker, gentle back of the landing
    p.straight(XBOWL - x_l4, [sec('STT-L4 roller, bosse, roller, saut freestyle', [ROLLER, SA[1], 'Glendale_g63_3'] + fmx, 2.0)], tag='L4 roller, bump, roller, freestyle jump')
    p.turn(+180, RB, BIG, tag='bowl (L4 -> L3)')
    l3 = ['Glendale_g36_1', 'Arlington_g37_0', 'Custom_g47_1', 'Glendale_g30_0', 'Arlington_g37_1', 'Detroit_g34_0']   # double, bump, table, bump, bump
    p.straight(XBOWL - XU, [sec('STT-L3 double, bosse, table, bosse, bosse', l3, 4.0)], tag='L3 double, bump, table, bump, bump')
    p.turn(-180, RB, BIG2, tag='U L3 -> L2 (rays)')
    l2 = ([('split', 'Glendale_g28_2', SMALL_B), ('gap', 2.0)] + up([SA[1], ('gap', 2.0), SA[2]], 1.3) + [('gap', 6.0)]
          + up([SA[0], ('gap', 2.0), SA[1], ('gap', 2.0), SA[2]], 1.3) + [('gap', 6.0)] + up([SA[0], ('gap', 2.0), SA[1]], 1.3))
    p.straight((XMID - RS) - XU, [sec('STT-L2 triple, triple, double (gros, serres)', l2, 1.0)], tag='L2 triple, triple, double')
    p.turn(-90, RS, SMALL, tag='L2 -> middle lane')
    Lmid = (Z['L6'] - RS) - (Z['L2'] + RS); mid = [SC[2], TABLE_B, SC[3]]
    p.straight(Lmid, [sec('STT-mid bosse, table, bosse', mid, (Lmid - len(L('tmp', mid)) * 0.1) / 2)], tag='middle lane: bump, table, bump')
    p.turn(-90, RS, SMALL2, tag='middle lane -> L6')
    p.straight((XMID - RS) - XU67, [sec('STT-L6 roller a sauter (sortie de virage)', [SMALL_B], 3.0)], tag='L6 straight, jumpable roller at the turn exit')
    p.turn(+180, RB, BIG, tag='U L6 -> L7')
    L7 = (XEL - R_HIGH) - XU67
    l7 = [ROLLER, ('gap', 4.0), 'Custom_g32_1', ('gap', 20.0), ('whoops', 'Custom_0', 9), ('gap', 25.0)] + SA[3:6]   # tiny double, 9 whoops, triple
    n7 = len(L('tmp', l7)) * 0.1
    p.straight(L7, [sec('STT-L7 petit double, 9 whoops, triple', l7, L7 - n7 - 8.0)], tag='L7 tiny double, whoops, triple close to the turn')
    p.turn(+90, R_HIGH, BIG, tag='L7 -> east lane (real high berm)')
    Lns = (Z['L7'] - R_HIGH) - (Z['L1'] + RS)
    p.straight(Lns, [sec('STT-east gros triple SX', BIG_TRIPLE, (Lns - len(L('tmp', BIG_TRIPLE)) * 0.1) / 2)], tag='east lane, big SX triple (Cleveland g29, as SX2)')
    p.turn(+90, RS, SMALL2, tag='east lane -> L1')
    l1 = up(SA[:3] + SD[:3] + [SA[3]], 1.2) + [TABLE_B] + up([SA[0], SA[0], SA[0]], 1.2)
    p.straight((XEL - RS) - (XWL + RS), [sec('STT-L1 triple, triple, bosse, table, bosse, 2 bosses', l1, 16.0)], tag='L1 along the north fence')
    p.turn(+90, RS, SMALL, tag='L1 -> west column')
    p.straight(a_col, [sec(FINISH_SEC, FIN, 2.0)], tag='west column: finish double')
    p.turn(+90, R_CURVE, None, tag='curve west column -> L4')
    _start('STT', ox, oz, gate=(-100.0, 167.0), heading=0.0,
           route=[('S', 360.0), ('T', +90, 30.0, None), ('TO', (XBOWL + RB, Z['L4'] - RB))],
           narrow=[(0.0, None), (8.0, None), (42.0, 30.0)], end_w=30.0,
           finish=(FINISH_SEC, 0))
    return p
