"""Saint-Thibéry (track map v2, from the user's drawing on v1): SX arena from the drone photos (Saint-Thibéry SX, France),
no sand. v2 = direction reversed + new start (user's drawing), obstacles kept at the same places as v1.
Rows east-west (north = top, stands = south, START = west end), JGSX lane spacing 43 ft:
    A  north fence     westbound   long rhythm (~12 singles)
    B                  eastbound   rhythm with two big singles
    C  (shorter west)  westbound   triple on table, off
    D  (shorter west)  eastbound   two singles, then the big centre table (9 ft)  -> finish line on the table
    E                  westbound   flat
    F  along stands    eastbound   12 whoops, then three small singles (none bigger than the whoops, 40 ft after them)
  + east lane south -> north (F -> A) with a triple.
  turns: D->E east (right, two 90s with a short straight: the big east berm), E->F west (left 180), F -> east lane (left 90),
         east lane -> A (left 90), A->B west (left 180), B->C east (right 180), C->D west (left 180).
  start (user's drawing): 22 gates at the west end, eastbound along the south side of the big centre table (between D and
  E), joins D just before the big east berm (first turn), then the lap goes back west on E.
v1 -> v2: E and F 28 ft further south to leave room for the start between D and E.
Every bump is a measured JGSX unit (lib/), no new shape. Local coords: x east, z south (image down), origin = west end of A."""
import numpy as np
from engine import Path
import layouts_sx as LS
from layouts_sx import L, sec, _start, SA, SD, SC, BB, TABLE_A, TABLE9, RB, RS, BIG, BIG2, SMALL, SMALL2

STT_ORIGIN = (160.0, 100.0)
ZA, ZB, ZC, ZD, ZE, ZF = 0.0, 43.0, 86.0, 129.0, 200.0, 243.0     # rows (E, F moved south in v2: start lane between D and E)
XW, XM, XE, XNS = 0.0, 150.0, 370.0, 445.0                         # west ends (A, B, E, F) / (C, D), east ends, east lane
FINISH_SEC = 'STT-D 2 singles + grosse table centrale (arrivee)'

def placed(name, tokens, lane_len, u0_v1):
    """v2 keeps every obstacle where it was in v1 while the riders now go the other way: tokens reversed, offset measured
    from the other end of the lane (each unit is still rendered forward, so take-off faces face the riders)."""
    n = len(L('tmp', list(reversed(tokens)))) * 0.1
    return sec(name, list(reversed(tokens)), lane_len - u0_v1 - n)

def stt():
    ox, oz = STT_ORIGIN
    p = Path(ox + XM, oz + ZD, 0.0, 'STT')                    # D, west end, eastbound
    p.straight(XE - XM, [placed(FINISH_SEC, [TABLE9, ('gap', 30.0), SD[0], SD[1]], XE - XM, 24.0)], tag='D 2 singles + big centre table 9 ft')
    p.turn(-90, RB, BIG, tag='T1 big east berm (1/2)')        # D -> E, the start joins just before
    p.straight(ZE - ZD - 2 * RB, [], tag='T1 short straight')
    p.turn(-90, RB, BIG2, tag='T1 big east berm (2/2)')
    p.straight(XE - XW, [], tag='E flat, westbound')
    p.turn(+180, RB, BIG, tag='T2')                            # E -> F
    p.straight(XNS - RS - XW, [sec('STT-F 12 whoops puis 3 petits singles', [('whoops', 'Custom_0', 12), ('gap', 40.0), 'Glendale_g40_2', SD[0], SD[1]], 20.0)], tag='F whoops along the stands')
    p.turn(+90, RS, SMALL, tag='T3')                           # F -> east lane, northbound
    p.straight((ZF - RS) - (ZA + RS), [placed('STT-NS triple + petite bosse', SA[3:6] + [('gap', 10.0), 'Glendale_g40_2'], (ZF - RS) - (ZA + RS), 18.0)], tag='east lane: triple + small bump')
    p.turn(+90, RS, SMALL2, tag='T4')                          # east lane -> A, westbound
    p.straight(XNS - RS - XW, [placed('STT-A longue rythmique (11 singles)', SA + SD + ['Glendale_g40_2'], XNS - RS - XW, 14.0)], tag='A long rhythm along the north fence')
    p.turn(+180, RB, BIG2, tag='T5')                           # A -> B, eastbound
    p.straight(XE - XW, [placed('STT-B rythmique, 2 gros singles', [SC[0], 'Arlington_g37_2', SC[1], SC[2], SA[2], 'Arlington_g1_2', SA[3]], XE - XW, 16.0)], tag='B rhythm + 2 big singles')
    p.turn(-180, RB, BIG, tag='T6')                            # B -> C, westbound
    p.straight(XE - XM, [placed('STT-C triple on table, off', SD[2:4] + [TABLE_A] + SA[:2], XE - XM, 14.0)], tag='C triple on table / off')
    p.turn(+180, RB, BIG2, tag='T7')                           # C -> D, eastbound (closes the lap)
    _start('STT', ox, oz, gate=(-100.0, 160.0), heading=0.0,
           route=[('S', 50.0), ('TO', (150.0, 166.0)), ('TO', (342.0, 166.0)), ('TO', (XE - 4.0, ZD))],
           narrow=[(0.0, None), (15.0, None), (55.0, 40.0), (150.0, 30.0)], end_w=30.0,
           finish=(FINISH_SEC, 2))
    return p
