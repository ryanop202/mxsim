"""Saint-Thibéry (v1, track map proposal): SX arena from the user's drone photos (Saint-Thibéry SX, France), no sand.
Read from the top-down photo (north = top, stands = south, START platform = west end, blue arch north-west):
  6 rows east-west, ~370 ft like the photo (rows 450 px apart over 6 rows -> 0.48 ft/px -> rows ~360 ft), JGSX spacing 43 ft
    A  north fence     eastbound   long rhythm (~12 singles)
    B                  westbound   rhythm with two big singles
    C  (shorter west)  eastbound   triple on table, off
    D  (shorter west)  westbound   the big centre table (9 ft) then two singles  -> finish line on the table
    E  start/finish    eastbound   flat start straight (as on the photos)
    F  along stands    westbound   three singles, then 12 whoops (nothing bigger after them)
  + one lane north -> south along the east fence (A -> F) with a triple.
  turns: T1 E->D east (left 180, big berm), T2 D->C west (right 180), T3 C->B east (left 180), T4 B->A west (right 180),
         T5 A -> east lane (right 90), T6 east lane -> F (right 90), T7 F->E west (right 180).
  start: 22 gates at the west end between the T4 and T7 berms, heading east, tapers and joins E after T7 (merge).
Every bump is a measured JGSX unit (lib/), no new shape. Local coords: x east, z south (image down), origin = west end of A."""
import numpy as np
from engine import Path
import layouts_sx as LS
from layouts_sx import L, sec, _start, SA, SD, SC, BB, TABLE_A, TABLE9, RB, RS, BIG, BIG2, SMALL, SMALL2

STT_ORIGIN = (160.0, 100.0)
ZA, ZB, ZC, ZD, ZE, ZF = 0.0, 43.0, 86.0, 129.0, 172.0, 215.0     # rows, JGSX lane spacing
XW, XM, XE, XNS = 0.0, 150.0, 370.0, 445.0                         # west ends (A, B, E, F) / (C, D), east ends, east lane

def stt():
    ox, oz = STT_ORIGIN
    p = Path(ox + 94.0, oz + ZE, 0.0, 'STT')                  # merge point on E (start joins here), heading east
    p.straight(XE - 94.0, [], tag='E start/finish straight (flat, as on the photos)')
    p.turn(+180, RB, BIG, tag='T1')                            # E -> D (north), westbound
    p.straight(XE - XM, [sec('STT-D grosse table centrale (arrivee) + 2 singles', [TABLE9, ('gap', 30.0), SD[0], SD[1]], 14.0)], tag='D big centre table 9 ft + 2 singles')
    p.turn(-180, RB, BIG2, tag='T2')                           # D -> C, eastbound
    p.straight(XE - XM, [sec('STT-C triple on table, off', SD[2:4] + [TABLE_A] + SA[:2], 14.0)], tag='C triple on table / off')
    p.turn(+180, RB, BIG, tag='T3')                            # C -> B, westbound
    p.straight(XE - XW, [sec('STT-B rythmique, 2 gros singles', [SC[0], 'Arlington_g37_2', SC[1], SC[2], SA[2], 'Arlington_g1_2', SA[3]], 16.0)], tag='B rhythm + 2 big singles')
    p.turn(-180, RB, BIG2, tag='T4')                           # B -> A, eastbound
    p.straight(XNS - RS - XW, [sec('STT-A longue rythmique (11 singles)', SA + SD + ['Glendale_g40_2'], 14.0)], tag='A long rhythm along the north fence')
    p.turn(-90, RS, SMALL, tag='T5')                           # A -> east lane, southbound
    p.straight((ZF - RS) - (ZA + RS), [sec('STT-NS triple + petite bosse', SA[3:6] + [('gap', 10.0), 'Glendale_g40_2'], 18.0)], tag='east lane: triple + small bump')
    p.turn(-90, RS, SMALL2, tag='T6')                          # east lane -> F, westbound
    p.straight(XNS - RS - XW, [sec('STT-F 3 singles + 12 whoops (rien apres)', SC[:3] + [('gap', 25.0), ('whoops', 'Custom_0', 12)], 20.0)], tag='F singles + whoops along the stands')
    p.turn(-180, RB, BIG, tag='T7')                            # F -> E, eastbound
    p.straight(94.0 - XW, [], tag='E before the merge (closes the lap)')
    _start('STT', ox, oz, gate=(-100.0, 106.0), heading=0.0,
           route=[('S', 95.0), ('T', -45, 40.0, None), ('S', 60.3), ('T', +45, 40.0, None)],
           narrow=[(0.0, None), (30.0, 70.0), (95.0, 50.0)], end_w=30.0,
           finish=('STT-D grosse table centrale (arrivee) + 2 singles', 0))
    return p
