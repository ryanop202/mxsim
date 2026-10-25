"""Saint-Thibéry (USLAND), from the user's drone photos and drawings. SX arena, no sand. North = top, stands = south,
START = west end. Every bump is a measured JGSX unit (lib/) unless marked 'scaled' (height scaled, same shape/length),
'landing' (scaled, back side replaced by a gentle slope) or 'trapeze' (synthetic mound) - asked by the user in game tests.

Lap (v8, after the 4th in-game test):
  L7  along the stands, eastbound : small double right at the turn exit, 11 whoops, triple close to the turn
  high berm turn (90, big radius) -> east lane northbound : bigger SX triple (Cleveland g29 x1.15), less run-up
  tight turn (L1 10 ft lower: turns earlier) -> L1 north, westbound : triple, triple, bump, table, bump, 2 bumps (approved)
  left turn -> west column southbound : finish double (same distance, normal landing back 24 ft), curve right after
  one 90 curve (r 16) -> L4 eastbound : roller, bump, roller, freestyle jump (approved)
  bowl (left 180, half berm) -> L3 westbound : 3 bumps (1st lower), lower table, 2 bumps, same gaps, longer lane
  U (right 180, 20 ft further west) -> L2 eastbound : long triple right at the turn exit, triple, double, same gaps
  -> middle lane southbound : bump, table, bump (approved)
  -> L6 westbound : jumpable roller right at the turn exit, flat straight (approved)
  U (left 180, half berm) -> L7
Start: 22 gates at the west end, eastbound behind the freestyle jump (between L4 and L6), left into the bowl.
Local coords: x east, z south (image down)."""
import numpy as np
from engine import Path
import layouts_sx as LS
from layouts_sx import L, sec, _start, SA, SD, SC, BB, TABLE_A, TABLE_B, TABLE9, BIG_TRIPLE, RB, RS, BIG, BIG2, SMALL, SMALL2

STT_ORIGIN = (175.0, 170.0)
FIN = ['Custom1_g30_2', ('gap', 4.0), ('landing', 'Arlington_g30_2', 11.2, 24.0)]   # v8: same distance, normal landing back (15 -> 24 ft)
R_CURVE = 16.0                                                              # one 90 deg curve west column -> L4 (v8: 21.5 -> 16, room for L1 lower)
R_HIGH = 21.5                                                               # the 90 after the whoops: big radius, big berm
R_TIGHT = 8.0                                                               # v7: east lane -> L1 "plus serre"
Z = dict(L1=-21.3, L2=43.0, L3=86.0, L4=129.0, L6=206.0, L7=249.0)        # v8: L1 10 ft lower (east lane turns earlier)
XWL, XBOWL, XU, XMID, XEL, XU67 = -35.0, 295.0, 40.0, 364.0, 445.0, -5.0   # v8: U L3 -> L2 20 ft west (L3 and L2 longer)
ARENA = (-110.0, 475.0, Z['L1'] - 24.0, 274.0)                            # fence box (x0, x1, z0, z1), local
ROWS = dict(L1=('L1', XU + 50), L2=('L2', XU + 50), L3=('L3', XU + 50), L4=('L4', 100.0), L6=('L6', 40.0), L7=('L7', 40.0))
FINISH_SEC = 'STT-ouest saut d arrivee (court)'
HALF_BERM = ('bowl (L4 -> L3)', 'U L6 -> L7')                             # berm only on the second half of these turns
BERM90_GAIN = 1.4                                                           # berms of the 90 deg turns higher (v6)
BERM_GAIN = {'L7 -> east lane (real high berm)': 1.2}                      # v7: that one a bit lower
ROLLER, SMALL_B = 'Custom1_g30_1', 'Glendale_g40_2'                        # 1.9 / 2.5 ft

def up(units, k):
    """measured singles scaled by k; gaps kept."""
    out = []
    for u in units:
        if isinstance(u, tuple): out.append(u); continue
        LS.L('tmp', [u]); out.append(('scale', u, round(LS.COMBOS['tmp']['items'][0][3] * k, 2)))
    return out

def spread(groups, lane, u0, end, g_in):
    """v7: groups of singles (triple, triple, double...) spread over the lane: g_in ft inside a group, the rest shared
    evenly between the groups (the user: no long run-up left before the next turn)."""
    unit_len = lambda u: len(L('tmp', [u])) * 0.1
    items_ = [[u for u in g if not (isinstance(u, tuple) and u[0] == 'gap')] for g in groups]
    body = sum(unit_len(u) for it in items_ for u in it) + g_in * sum(len(it) - 1 for it in items_)
    g_out = max(g_in, (lane - u0 - end - body) / max(1, len(groups) - 1))
    toks = []
    for k, g in enumerate(groups):
        items = [u for u in g if not (isinstance(u, tuple) and u[0] == 'gap')]
        for j, u in enumerate(items):
            toks.append(u)
            if j < len(items) - 1: toks.append(('gap', g_in))
        if k < len(groups) - 1: toks.append(('gap', g_out))
    return toks

def even(units, lane, u0, end):
    """v8: same gap between every bump of the lane (the user: not 3, 3, 2)."""
    unit_len = lambda u: len(L('tmp', [u])) * 0.1
    g = (lane - u0 - end - sum(unit_len(u) for u in units)) / max(1, len(units) - 1)
    toks = []
    for j, u in enumerate(units):
        toks.append(u)
        if j < len(units) - 1: toks.append(('gap', round(g, 1)))
    return toks

def stt():
    ox, oz = STT_ORIGIN
    a_col = Z['L4'] - R_CURVE - RS - Z['L1']                               # west column straight
    x_l4 = XWL + R_CURVE
    p = Path(ox + x_l4, oz + Z['L4'], 0.0, 'STT')                          # L4, after the curve, eastbound (straight)
    fmx = ['Detroit_g31_1', ('gap', 12.0), ('trapeze', 18.0, 30.0, 8.0, 35.0)]   # v7: steep short kicker, one clean landing mound
    l4 = [ROLLER, SA[1], 'Glendale_g63_3'] + fmx
    p.straight(XBOWL - x_l4, [sec('STT-L4 roller, bosse, roller, saut freestyle', l4, 14.0)], tag='L4 roller, bump, roller, freestyle jump')
    p.turn(+180, RB, BIG, tag='bowl (L4 -> L3)')
    l3 = [('scale', SA[0], 2.8), SA[1], SA[2], ('scale', TABLE_B, 5.2), SA[1], SA[0]]   # v8: 1st bump lower (no triple in), table lower
    p.straight(XBOWL - XU, [sec('STT-L3 3 bosses, table, 2 bosses', even(l3, XBOWL - XU, 4.0, 16.0), 4.0)], tag='L3 3 bumps, table, 2 bumps')
    p.turn(-180, RB, BIG2, tag='U L3 -> L2 (rays)')
    L2 = (XMID - RS) - XU
    first = ('split', ('scale', SA[1], 4.8), ('scale', SA[1], 3.0))         # v7: normal rhythm bump, lower on the right (inside)
    l2 = even([first] + up([SA[2], SA[0]], 1.35) + up([SA[1], SA[2], SA[0]], 1.35) + up([SA[1], SA[2]], 1.35), L2, 0.0, 12.0)
    p.straight(L2, [sec('STT-L2 long triple, triple, double (ecarts egaux)', l2, 0.0)], tag='L2 long triple, triple, double, same gaps')
    p.turn(-90, RS, SMALL, tag='L2 -> middle lane')
    Lmid = (Z['L6'] - RS) - (Z['L2'] + RS); mid = [SC[2], TABLE_B, SC[3]]
    p.straight(Lmid, [sec('STT-mid bosse, table, bosse', mid, (Lmid - len(L('tmp', mid)) * 0.1) / 2)], tag='middle lane: bump, table, bump')
    p.turn(-90, RS, SMALL2, tag='middle lane -> L6')
    p.straight((XMID - RS) - XU67, [sec('STT-L6 roller a sauter (sortie de virage)', [SMALL_B], 3.0)], tag='L6 straight, jumpable roller at the turn exit')
    p.turn(+180, RB, BIG, tag='U L6 -> L7')
    L7 = (XEL - R_HIGH) - XU67
    l7 = [('scale', ROLLER, 2.6), ('gap', 4.0), ('scale', 'Custom_g32_1', 2.6), ('gap', 10.0), ('whoops', 'Custom_0', 11), ('gap', 20.0)] + SA[3:6]
    p.straight(L7, [sec('STT-L7 petit double, 11 whoops, triple', l7, 1.5)], tag='L7 small double at the turn exit, 11 whoops, triple')
    p.turn(+90, R_HIGH, BIG, tag='L7 -> east lane (real high berm)')
    Lns = (Z['L7'] - R_HIGH) - (Z['L1'] + R_TIGHT)
    big3 = [('scale', 'Custom1_g29_2', 9.1), ('gap', 0.5), ('scale', 'Custom1_g29_3', 6.9), ('gap', 1.6), ('scale', 'Arlington_g29_2', 8.45)]  # v8: x1.15
    p.straight(Lns, [sec('STT-east gros triple SX (plus gros)', big3, 30.0)], tag='east lane, bigger SX triple, less run-up')
    p.turn(+90, R_TIGHT, SMALL2, tag='east lane -> L1 (tight)')
    L1 = (XEL - R_TIGHT) - (XWL + RS)
    l1 = spread([up(SA[:3], 1.2), up(SD[:3], 1.2), up([SA[3]], 1.2), [TABLE_B], up([SA[0]], 1.2), up([SA[0], SA[0]], 1.2)], L1, 16.0, 22.0, 8.0)
    p.straight(L1, [sec('STT-L1 triple, triple, bosse, table, bosse, 2 bosses', l1, 16.0)], tag='L1 along the north fence, wider gaps')
    p.turn(+90, RS, SMALL, tag='L1 -> west column')
    nf = len(L('tmp', FIN)) * 0.1
    p.straight(a_col, [sec(FINISH_SEC, FIN, a_col - nf - 3.0)], tag='west column: room after the turn, short finish double, curve right after')
    p.turn(+90, R_CURVE, None, tag='curve west column -> L4')
    _start('STT', ox, oz, gate=(-100.0, 167.0), heading=0.0,
           route=[('S', 360.0), ('T', +90, 30.0, None), ('TO', (XBOWL + RB, Z['L4'] - RB))],
           narrow=[(0.0, None), (8.0, None), (42.0, 30.0)], end_w=30.0,
           finish=(FINISH_SEC, 0))
    return p
