"""Saint-Thibéry (USLAND), from the user's drone photos and drawings. SX arena, no sand. North = top, stands = south,
START = west end. Every bump is a measured JGSX unit (lib/) unless marked 'scaled' (height scaled, same shape/length),
'landing' (scaled, back side replaced by a gentle slope) or 'trapeze' (synthetic mound) - asked by the user in game tests.

Lap (v29, user drawing: straight bank slope behind the fence (fence terrace kept), poles at the bottom inside the
  fence on the dirt, paddle-shaped yellow markers (no logo), none on the freestyle kicker / landing, one continuous net per
  turn following the ground. Before, v28, night only: 6 light poles (3 facing 3, L1 side / whoops side) low in a steeper slope right behind the fences,
  each on a platform cut into the slope; yellow marker stakes on every bump crest (both ends); blue nets on the berms of 5
  turns; one big square-mesh start floor behind the 22 gates, cut at each gate. Track itself unchanged.
  Before, v27: 3D grass removed (too heavy in game), DVDB grass patches back with a row along the fence (clean edge).
  Before, v26: Scuttle normal grass (grass_5 / grass_30, dry tuft) all over the grass; night: strong side flood (day sun angle)
  for relief. Before, v25: night: track lit exactly like by day (day lightmap inside the fence), night around; dirt decals under the
  track ones; clean dirt/grass line at the fence (rounded distance field); start corners rounded (no cone); JGSX green 3D grass
  tufts instead of the DVDB patches. Before, v24: dirt (track decals) up to the fence, grass from the fence; start: one smooth slope from the platform up the bank,
  merged at the corners; fence closed loop; thicker ribbon on map.png; night lightmap with the day key light (relief). Before, v23: grass decal patches (DVDB grass) on the grass. Before, v22: flat terrace under the fences (no tilt), fences around rounded corners, steep bank right behind the start with a
  flat back to it; night: 10 poles on flat pads, light points (lamp_glow) on the lamps. Before, v21: track frozen. Arena bank 42 ft, gentler (inner 160 ft); fences 28 ft up the slope; start platform 10 ft;
  realistic grass tile; night version (export_stt_night.py, 20 light poles, lights baked in the lightmap). Before, v20: arena bank 36.7 ft with a gentle inner slope; wooden fence (fence_wood) at its foot all around; track centred
  on the terrain. Before, v19, 14th test: L2 1st bump less steep (lip 0.75) with a softer entry; L1 1st bump 6 ft after the turn (triple in,
  not quad); giant grassed earth bank around the arena (22 ft, the track in a pit); track moved 65 ft east on the terrain.
  Before, v18, 13th test: L2 1st bump lower (4.3 / 3.3 ft); L1 1st bump back to the v13 one (measured 4.0 ft, 16 ft after the
  turn); freestyle side ramp = the user's steel model ramp_50 (with collision), no dirt ramp; grass all around the arena.
  Before, v17, 12th test: L3 last 2 bumps 4 ft further apart (room before the U); L2 smoother entry on both halves (lead-in
  ball 15 ft, kick curve kept); L1 1st bump 5 ft after the turn, less round top, smoother entry. Before, v16, 11th test: bowl 18 ft earlier after the freestyle landing (L3 gaps 3 ft); L2 left take-off 4.7 ft, concave
  bottom and rolled-over top, right half a normal 3.6 ft bump; rhythm landings fuller (L1, L2, L3); L1 1st bump 8 ft after
  the turn, between measured and kick; fused double 1st hump 4.4 ft, straight climb to the 2nd. Before, v15, 10th test: start platform 8 ft with a straight descent; L3 turns 6 ft earlier (roller 1 ft after the bowl, 5 ft
  before the U); L2 take-off = concave kicker ("kick"), 3rd bump 5.2 ft; east lane -> L1 = the big 90 of the whoops (r 21.5,
  big berm x1.2); L1 1st bump concave 4.3 ft, 12 ft after the turn, gaps 7.2 ft. Before, v13, after the 8th in-game test: wheel tap 3rd roller = 1st, bowl berm x0.85, fused double 5.0 / 5.5 ft with a
  steeper climb to the 2nd hump, L2 inside half 3.6 ft and 2nd bump 4.6 ft, start platform, freestyle ramp, no arches):
  L7  along the stands, eastbound : small double right at the turn exit (landing turned around), 11 whoops, triple (approved)
  high berm turn (90, big radius) -> east lane northbound : bigger SX triple (Cleveland g29 x1.15), first take-off foot
      rounded (smoother), landing 8.8 ft with a 35 % longer back (gentler), crest at the same place
  tight turn -> L1 north, westbound : triple, triple, bump, table, bump, 2 bumps, feet rounded, first take-off smoother
  left turn -> west column southbound : finish double, round normal landing (Glendale g83 at 10 ft) (approved)
  one 90 curve (r 16) -> L4 eastbound : wheel tap (roller, medium bump, roller) (approved), freestyle jump: kicker cut clean
      at its first edge (lip 6.9 ft, same place) with a straight back; landing climb straight and steeper (22 ft, slope 1.0),
      same flat and descent, 9 ft wider on the right (start corridor moved 8 ft south)
  bowl (left 180, half berm) -> L3 westbound : low roller, bump (approved), fused double longer and deeper (crests 5.5 ft,
      bottom 2.2 ft, crest to crest 46 ft, faces 0.5), 3 bumps ending 8 ft before the U (user: 8 ft, never more)
  U (right 180) -> L2 eastbound : long triple right at the turn exit (split 1st bump, smoother take-off), triple, double,
      same gaps, feet rounded, ends 8 ft before the turn
  -> middle lane southbound : bump, table, bump (approved)
  -> L6 westbound : jumpable roller right at the turn exit, flat straight (approved)
  U (left 180, half berm) -> L7
Start: 22 gates at the west end (v12: 8 ft further south), eastbound behind the freestyle jump (between L4 and L6), left into the bowl.
Local coords: x east, z south (image down)."""
import numpy as np
from engine import Path
import layouts_sx as LS
from layouts_sx import L, sec, _start, SA, SD, SC, BB, TABLE_A, TABLE_B, TABLE9, BIG_TRIPLE, RB, RS, BIG, BIG2, SMALL, SMALL2

STT_ORIGIN = (390.0, 295.0)                                                # v21: re-centred for the bigger bank
FIN = ['Custom1_g30_2', ('gap', 12.0), ('scale', 'Glendale_g83_2', 10.0)]   # v9: round normal landing (Glendale g83 double landing, 7.9 -> 10 ft),
                                                                            # crest at the same distance as v8
R_CURVE = 16.0                                                              # one 90 deg curve west column -> L4 (v8: 21.5 -> 16, room for L1 lower)
R_HIGH = 21.5                                                               # the 90 after the whoops: big radius, big berm
R_TIGHT = 21.5                                                              # v15: east lane -> L1 = same turn as after the whoops (R_HIGH)
Z = dict(L1=-21.3, L2=43.0, L3=86.0, L4=129.0, L6=206.0, L7=249.0)        # v8: L1 10 ft lower (east lane turns earlier)
XWL, XBOWL, XU, XMID, XEL, XU67 = -35.0, 277.0, 40.0, 364.0, 445.0, -5.0   # v8: U L3 -> L2 20 ft west (L3 and L2 longer)
ARENA = (-110.0, 475.0, Z['L1'] - 24.0, 274.0)                            # fence box (x0, x1, z0, z1), local
ROWS = dict(L1=('L1', XU + 50), L2=('L2', XU + 50), L3=('L3', XU + 50), L4=('L4', 100.0), L6=('L6', 40.0), L7=('L7', 40.0))
FINISH_SEC = 'STT-ouest saut d arrivee (court)'
HALF_BERM = ('bowl (L4 -> L3)', 'U L6 -> L7')
BERM_FADE = {}   # v56 (user): back to the usual fade (45 % / 15 %) for the U L6 -> L7 (v54 54 % / 14 %, v55 54 % / 5 %)
BERM_SHIFT = {'U L6 -> L7': (94.0, 180.0)}   # v58 (user): not cut, a whole berm (own entry + exit, same shape both ends) moved into
# the 2nd half of the U: starts at 0 at turn progress 94 deg (= the red line z 524), peak in the corner, exit at the turn end
BERM_CLIP = {}   # was v57 {'U L6 -> L7': (524.0, 10.0)}   # v57 (user): progressive, not a cut: 0 at z 524 rising smoothly over 10 ft;   # v56 (user's red line: grid end -> pylon): the berm comes exactly to z 524, never past it
# (z < 524 = in front of the gate row); full height from z 525.5
# since the start moved 8 ft south -> it starts at 54 % (past the gate row end, z ~ 526); the others keep 45 % / 15 %                             # berm only on the second half of these turns
BERM90_GAIN = 1.4                                                           # berms of the 90 deg turns higher (v6)
BERM_GAIN = {'L7 -> east lane (real high berm)': 1.2, 'bowl (L4 -> L3)': 0.85, 'east lane -> L1 (high berm, as after the whoops)': 1.2}   # v13: bowl berm a bit lower                      # v7: that one a bit lower
ROLLER, SMALL_B = 'Custom1_g30_1', 'Glendale_g40_2'                        # 1.9 / 2.5 ft
# v12: freestyle landing wider ("beaucoup de place", mostly on the right): section -> (from_ft, to_ft, left_ft, right_ft)
# v13: start on a raised platform (gates and grates on it), a short descent right after the gate line (ft)
START_GATE, START_HEADING = (-100.0, 183.0), 0.0                         # gate row centre (local), heading (deg); v53 (user): 2 gates (8 ft) outwards, platform with it
START_PLATFORM = dict(h=10.0, back=40.0, front=5.0, down=55.0, side=6.0, side_ramp=30.0, lin=6.0)   # v24: smooth side ramps (30 ft), the bank takes over behind
# v13: freestyle ramp beside the wheel tap (right, off the lane), turned slightly to face the wide part of the landing (local)
FMX_RAMP = dict(lip=(98.0, 153.0), aim=(170.0, 150.0), H=7.5, width=8.0, side=0.5,
                model='ramp_50', model_len=18.47)   # v18: the user's steel FMX ramp (ramp_50.jm/.shp, lip 9 ft, 4 ft wide)
                                                    # replaces the dirt ramp; its lip is put where the dirt lip was
# v18: grass all around the dirt arena (as on the drone photos); dirt kept under the start area (local box x0, x1, z0, z1)
# v21: night version (USLAND2026StThiberyNuit): light poles on the bank, `d` ft from the dirt area, lights baked in the lightmap
NIGHT = dict(folder='USLAND2026StThiberyNuit', desc='USLAND: Saint-Thibery (nuit)', d=45.0, n_long=5, n_short=3, keep_every=2, pad=(7.0, 15.0))
# v24: track-coloured decals over all the dirt up to the fence ("le contour marron clair")
DIRT_DECALS = dict(size=26.0, step=10.0)
# v23: grass decal patches over the grass (DVDBVisualsCompound grass.png, the user's choice): size ft, grid step ft, clear ft from the dirt
GRASS_DECALS = dict(size=45.0, step=26.0, clear=51.0)   # v27: DVDB grass patches back (3D tufts too heavy in game); centre >= fence + 23 ft: no fringe over the fence line
# v25: 3D grass tufts (JGSX2026Scuttle grass_5 / grass_15 models sent by the user, green tuft texture) on the grass, from just
# outside the fence to the top of the bank; jittered grid `step` ft, kept with probability p; 3rd-party files, local use only
GRASS_TUFTS = None   # v27: removed (the game lagged with them)
GRASS_OUTSIDE = dict(arena=True, keep=[(-140.0, -110.0, 97.0, 253.0)], dirt_to_fence=True,
                     west_wall=dict(z=True, shift=19.0, extra_h=4.0, top_h=4.0, blend=160.0, sigma=60.0, corner_r=45.0, smooth=4.0))
# v37 (user): bank a bit higher at the start (wall +4 ft, top +4 ft on the west side), corners rounder and the slope smoothed
# (sigma `smooth` ft beyond the fence terrace): no crease / staircase line at the corners
# v36 (user): behind the start grate the border is ONE straight wall (no shelf, no detour around the start area): the start
# strip (x -140..-110) runs along the whole west side, and on that side the fence step starts right at the dirt edge
# (distance shifted by `shift` ft) and is `extra_h` ft higher   # v24: start area = platform + ramps; dirt up to the fence
# v19: the track sits in a pit: a giant grassed earth bank all around the dirt arena (and around the start area), as on the
# drone photos. Height h ft, inner slope over `inner` ft (rounded toe and top), flat top `top` ft, outer slope `outer` ft.
ARENA_BANK = dict(h=42.0, inner=160.0, top=14.0, outer=70.0, terrace=(28.0, 6.0), start_inner=75.0, start_blend=90.0,
                  straight=dict(slope=0.4, terrace_h=6.0, rise=6.0, toe=2.0, crest=12.0))
# v35 (user): bank a bit less steep (0.5 -> 0.4) and the fence border 3x higher (step 2 -> 6 ft, over 6 ft instead of 3)
# v29 (user's drawing on the v28 cross-section): flat dirt floor up to `rise` ft before the fence terrace, a short step up to
# the terrace (terrace_h ft, fence on it, unchanged), then ONE straight slope (`slope`, rounded toe / crest) up to h - no more
# gentle slope + steep wall (v28 'steep', removed)
# v29 (user's drawing): 3 light poles on each long side facing each other (whoops side = south, L1 side = north), at the
# bottom, just inside the fence, on the flat dirt (no platform): d = ft from the dirt area (fence at 28)
POLES = dict(n=3, d=20.5, pad=(2.0, 4.0), floor=True)   # v37 (user): a bit forward, smaller dig (some fences fell in the hole)   # v36 (user): at the foot of the fence border, IN the step, the step dug
# around each pole down to the floor (pad level = lowest ground within pad[1]); v35: 31 (terrace), v29: 20
# v28: yellow marker stakes on the crest of every bump, at both ends (lane edges), like the drone photos; v ft from the lane axis
STAKES = dict(v=14.2, prom=0.6, table=6.0, tables=('Arlington_g49_2', 'Custom1_g71_1'), table_drop=1.2, sprite=1.8)
# v41 (user): stakes are billboards (sprite 1.8 ft, always upright: as statues the game tilted them with the slope, e.g. on the
# freestyle kicker and the finish take-off); tables (items in `tables`): a stake at BOTH ends of the top (the top within
# `table_drop` ft of the highest point: these tables rise a little to their end, so only the end was found before)
# v28: blue nets on the outside of 5 turns (user), on the berm crest (drone photos: blue posts + net)
NETS = dict(turns='all', skip=('curve west column -> L4',), step=8.0, flat_off=8.0, flat_gap=3.0)   # v34 (user): no net in the turn after the finish jump
#   # v32 (user): a net in every turn (v28: 5 turns); turns without a
# berm: net `flat_gap` ft outside the lane edge
# v28: one big start floor (square mesh) behind the whole gate row instead of one grate per gate
START_FLOOR = dict(back=18.0, side=2.5)   # v36 (user): grates cut shorter (22 -> 18 ft, user's line)
# v31 (user, 2026-11-03): black pylons (ATVMC shape, all black) inside the 9 turns. v32 (user): placed by one rule, always the
# same spot: on the turn bisector, `margin` ft inside the inner lane edge (lane half width `half`); soft collision.
PYLONS = dict(half=15.2, margin=1.5,
              # v34 (user, 2026-11-03): red squares on 8 in-game top views (scale from the 1.85 ft base, rotation from the base
              # edges + the net); turn 8 (after the finish) has no square -> v33 spot kept. Estimate +-1 ft.
              # v33: spots drawn on 9 in-game screenshots (turn 7 pushed out of the lane).
              # v35 (user, top views): turns 3, 5, 7 moved again (red squares); v34 spots kept for the others
              points=[(665.3, 400.2), (427.8, 359.6), (733.9, 356.9), (735.8, 481.7), (387.9, 523.9),
                      (811.1, 521.8), (812.2, 295.8), (375.5, 292.0), (376.6, 403.3)])
# v33 (user: "ça coupe les intérieurs de virage"): 3 timing gates per turn (entry, pylon, exit).
# v34 (user): every turn gate starts AT the pylon (fan from the pylon through the riding line at entry / apex / exit, out to
# `outer` ft past the outer lane edge): a tight inside line next to the pylon counts, going inside the pylon misses the gate.
# start_pad: start straight gates (start-only + loop straight gates on the start merge straight) wider by this much per side
# v35 (user's white rectangles on 6 top views, cleaned up): straw bales (x, z, long axis angle deg in the x-z plane).
# Top lane (L1, z = 273.7): 2 facing pairs at each end, 19.5 ft each side of the lane axis; 2 at the inside corner of the turn
# L1 -> west column (along both lane edges), 1 in the middle of the U L3 -> L2 (east of the pylon), 1 next to the pylon of
# east lane -> L1 (as drawn, tilted).
BALES = [  # v37 (user's 4 top views: red dot = remove, white = add, 2 redrawn = moved closer to the track)
         (818.0, 317.1, 90), (818.0, 323.0, 90), (818.0, 328.9, 90),         # east lane, landing of the SX triple: 3 each side
         (853.5, 317.1, 90), (853.5, 323.0, 90), (853.5, 328.9, 90),         # v38 (user): closer together (pitch 7.15 -> 5.9), centred
                                                                             # between the turn (berm from z 303) and the landing foot
                                                                             # (z 341); west row 1.5 ft east
         (816.5, 500.0, 90), (816.5, 507.15, 90), (816.5, 514.3, 90),        # east lane, flat before the take-off (turn exit)
         (850.0, 500.0, 90), (850.0, 507.15, 90), (850.0, 514.3, 90),        # v38 (user's white lines): east row 3.5 ft closer to the track
         (804.4, 525.4, 152),                                                # inside of the turn entry before the triple
         (372.8, 299.2, 90), (382.9, 291.9, 0),                              # inside corner of L1 -> west column
         (340.6, 298.7, 90), (380.9, 259.2, 0),                              # outside of that turn (moved ~2 ft towards the track)
         (434.7, 359.3, 0)]                                                  # U L3 -> L2 (v37: 1 ft east, off the pylon bump)
# v37: removed the 4 at the east end of the top lane and the tilted one at the pylon of east lane -> L1 (red dots)
# v35: first layout (2 facing pairs at each end of the top lane, the west ones removed in v36)
# v35 (user's photo): black foam tubes, segments end to end along both edges of the lane (`off` ft from the lane axis to the tube
# axis): from `before` ft before the whoops to half of them (L7), and along both sides of the freestyle gap (lip -> landing)
BOUDINS = dict(whoops=dict(tag='L7 small double', x=(393.0, 513.0), side=-1, off=22.0, model='boudin_logo', tex=('boudin_sxtour', 'boudin_mcst')),   # v39: logo mesh (logo bigger, higher)   # v38 (user): 1 ft closer, still straight (whoops foot < 0.1 ft under its edge = the sink); SX Tour / Moto Club logos alternated   # v37: off 17.9 -> 23 (it sat half on the whoops' side slopes, which reach z 523)   # v36b (user): same plain tube as the freestyle one
               fmx=dict(p0=(497.1, 445.7), p1=(535.4, 448.7), model='boudin_logo', tex=('boudin_sxtour', 'boudin_mcst')))   # v39 (user): logos here too   # v37: user's line (top view), lip -> landing corner
# v36 (user's marks): whoops: ONE side only (north, the infield side), along the small double and the first whoops, from x 393
# to 513 (where the user's line stops); freestyle gap: one single line in the middle, plain black (no logo), segments touching
# v36 (user): no stakes on the steel freestyle ramp (v35); they go on the dirt take-off of the freestyle jump (L4) instead
# v37 (user): the pylon stands on a small dirt bump made IN the terrain (same look as the bumps): flat top r_flat, down to 0 at r
# (v35-v36: a dirt pad in the model: shiny). Turns in `curb` (L2 -> middle lane, middle lane -> L6): no bump, a very small
# berm arc around the pylon on the track side instead.
PYLON_GROUND = dict(mound=dict(h=0.75, r_flat=1.6, r=3.6), curb=dict(turns=(2, 3), h=0.35, r=2.6, w=0.9, ext_in=2.8, ext_out=1.0))
# v38 (user): mound higher (0.45 -> 0.75 ft), same width. Curb: a 90 deg arc around the pylon only (v37: 220 deg, a half turn),
# from the entry lane side to the exit lane side, + a short straight tail back along the entry lane and a short one at the exit
# (the user's 'P' drawing: it marks the inside of the turn)
VIPS = [dict(img='vip_mrbeast', h=6.4, sink=0.1, at=(452.0, 596.0)),          # v45 (user): cut-outs (rembg), all in ONE place: front row right behind the south
        dict(img='vip_netanyahu', h=5.5, sink=0.5, at=(468.0, 596.0)),        # fence facing the start of the whoops, one fence
        dict(img='vip_branson_epstein', h=6.0, sink=0.1, at=(484.0, 596.0)),  # section each, no tarp on those sections
        dict(img='vip_xddl', h=2.3, sink=-3.0, at=(500.0, 596.0), keep_tarp=True)]   # v49 (user): a head-and-shoulders portrait:
# standing behind the tarp of the next section (bust from 3.0 to 5.3 ft). v49: VIPs are billboards too (turn to the view)
PYLON_SKINS = {0: 'pylon_f50', 2: 'pylon_f50', 4: 'pylon_f50', 5: 'pylon_motul', 8: 'pylon_motul'}
# v50 (user's circles on the in-game top view): yellow = all 50 Factory yellow with its logo, red = red Motul column, black base
START_BOUDINS = dict(lines=[[(704.6, 409.8), (658.3, 522.0)],                       # v52 (user): 4 ft further out (more room in the
                            [(350.0, 426.0), (384.0, 449.0), (468.0, 453.0), (534.0, 453.0)],
                            [(302.0, 528.0), (338.0, 528.0)]],   # v56: ends where the berm (now up to z 524) takes over. v55 (user): no boudin on the flat; all 7 on the descent
                     # (x 302-344, from the top edge down to where the descent stops), on the pad edge (flat ends z ~527), straight;   # v54 (user's red line): from the
                     # gates to the U L6 -> L7 berm; v54b (user): one straight on the flat (pad top, x < 296), the others wholly
                     # on the straight descent (x 302-338) so the game tilts them parallel to the slope, none across the edge; turn); v52: one diagonal from the
                     # first slant straight to the line beside the FMX ramp, then straight, stopped at the landing (user's lines)
                     hide_after=15.0, pattern=(('50factory', 10), ('mcst', 10), ('sxtour', 10)))
# v51 (user): flat ground only (not up the L4 bump shoulders, z up to 447, nor the landing, z up to 456), on the start side of
# the steel FMX ramp (z 447-451) so the start cannot use it, along the landing and back to L4 right behind it; pattern: 10 x
# 50 Factory (yellow), 10 x Moto Club Saint Thibery, 10 x SX Tour, again and again (no other sponsor)
# start-only boudins: v51b soft collision (startb.shp; v50: none - unknown whether a statue moved by the script takes its
# collision along: to check in game), shown until 15 s
# after the gate drop, then sunk under the ground by nofrills.js; black ones with the sponsors and 50 Factory yellow ones,
# one in two
START_BANNER = dict(board=True, foot_h=0.4, back=1.4, model='start_sign')   # v41: sign on posts   # v40 (user): a BIG board on the platform at the foot of the start wall
# (v39: a 31.5 ft banner on top of the wall, in front of the fence: too small). Origin `back` ft in front of the wall foot
# (first point east of the wall within foot_h of the platform level).
BOARD30 = dict(stand=(201.0, -2.0), hide=(201.0, -1), hide_out=-20.0, speed=60, done='blank')   # v58 (user): 3x faster (20 -> 60)   # v57 (user: still running when the riders get there): starts 12 ft closer (z 476, 20 ft run), speed 12 -> 20
# v56 (user): he looked like running backwards going right -> runs left (the way the game's sprite faces) to z 456, just inside
# the start boudins; his last picture (standing there) = an empty picture: he disappears once tucked away (the game has no
# script call for flaggers, so not exactly at drop + 15 s)
# v55 (user's red line on a top view): not at the gates but ~200 ft ahead (x 491), across the start straight between the start
# boudins (z 453) and the fixed boudin line (z 522): stands in its middle (z 487.5), runs off behind the fixed line (z 526)
# v54 (user): the 30 s board man stands in the middle of the start line, 9 ft in front of the gates (first flaggers point);
# at the 5 s board he runs (second point = where the game makes him run to) off the north side of the start pad
# (16 ft past the last gate, down the pad shoulder). Speed 12 like the Bud / Miami tracks. Before: behind the gates.
FLAG_STAND = dict(side=1, v0=15.2, w=8.0, back=12.0, fwd=12.0, drop=1.0, slope=1.0, flip=1,
                  rf=dict(src='@2024Bh1Conway/flaggerfiles', size=10.5, flip=1))   # v48 (user, in game): -1 showed the flag on the wrong side -> 1   # v46 (user): animated photo flagger (RF), person about 6 ft   # v41 (user): flagger turned round (flag towards the track; v40 -1)   # v40b: the bump's own profile widened 8 ft, cut flat 1 ft under the crest (flat top ~6 ft long)
# v40 (user): at the finish take-off, a dirt platform joined to the side of the bump (west side, outside the lane), its flat
# top `drop` ft under the crest, from `back` ft before the crest to `fwd` ft after it, `w` ft wide, sides 1:1; the finish
# flagger stands on it inside a small steel cage (stt_ads.flag_cage).
STAKE_PADS = None   # v41 (user): no pad any more (it bent the side of the kicker); v40: dict(items=('(cut',), half_u=0.7, half_v=0.8, skirt=0.6)
# v40 (user: the yellow stakes on the freestyle kicker lean): a small flat pad under each stake of the dirt kicker, at the
# highest ground under the stake, so they stand straight.
CROWD = dict(rows=tuple(np.arange(6.0, 112.0, 9.0)), step=5.5, jitter=3.0, skip=0.12, size=48.0, side_jit=3.0,   # v41 (user): the whole bank, up to the top; v43: twice as dense (step 11 -> 5.5)
             own={'Crowd5': 'Crowd5_fr'},   # v43 (user): the US-flag skirt recoloured as a French flag (work/flag_fr.py), shipped in the track
             imgs=('Crowd1', 'Crowd2', 'Crowd3', 'Crowd4', 'Crowd5', 'Crowd6', 'Crowd8', 'Crowd9'), src='@2022Miamibeachrace/billboard',
             mesh=True, game='C:/Program Files (x86)/MX Simulator', sprites=True)   # v49 (user): billboards again (they turn to the view;
# the v42 fixed quads were invisible edge-on, e.g. from the start), but each picture CROPPED to its people (own copies in
# billboard/, 256 px, stretched back by the aspect value): no more huge transparent squares   # v42 (user: less lag): 8 meshes of cropped quads, not billboards
# v40 (user): public on the grass bank: billboards (people cut-outs) from the 2022 Miami Beach Race track (installed in the
# user's game, referenced, not copied), 2 rows behind the fence (`rows` ft beyond it), about every `step` ft, some gaps.
# Size 48 -> people about 6 ft (Miami uses 61: 7.6 ft).
TURN_GATES = dict(half_lane=15.2, inner=2.0, outer=12.0, fr=(0.15, 0.85), fan=True, start_pad=4.0)

# v24: the bank starts at the height of the ground it touches (the start platform: 10 ft) and rises in ONE smooth slope
# (75 ft behind the start, blended into the 160 ft of the rest over ~90 ft along the edge, corners included).
# v22: terrace = flat strip (at d ft, w ft wide) cut in the bank under the fence (objects tilt with the ground);
# (v22 steep zone replaced in v24 by start_inner / start_blend)   # v21: a bit higher, much gentler (inner max slope ~0.4)   # v20: 2/3 higher (22 -> 36.7 ft), much gentler inner slope (max ~0.58)
# v20: wooden post-and-rail fence (scripts/fence_wood.py) in the grass at the foot of the bank, `off` ft outside the dirt area
FENCE = dict(model='fence_wood', off=28.0, step=8.0)   # v21: up in the slope (~3 ft up), not on the flat
WIDE = {'STT-L4 roller, bosse, roller, saut freestyle': (147.6, 212.6, 0.0, 9.0)}   # right only (L3 too close on the left); start corridor 8 ft south

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

def even(units, lane, u0, end, last_extra=0.0):
    """v8: same gap between every bump of the lane (the user: not 3, 3, 2). v17: last_extra ft more before the last unit."""
    unit_len = lambda u: len(L('tmp', [u])) * 0.1
    g = (lane - u0 - end - last_extra - sum(unit_len(u) for u in units)) / max(1, len(units) - 1)
    toks = []
    for j, u in enumerate(units):
        toks.append(u)
        if j < len(units) - 1: toks.append(('gap', round(g + (last_extra if j == len(units) - 2 else 0.0), 1)))
    return toks

def _close(P, R, interior=True, keep_in=False, R_in=40.0):
    """Grey closing with a ball (radius R ft) on a zero-padded copy: fills the concave corners at the foot of the bumps,
    crests and faces above are unchanged. interior: between the first and the last crest only (v10: no curb at the ends).
    keep_in (v12, "plus smooth le premier appel"): also rounds the foot of the first bump with a ball of R_in ft; the
    fillet is kept in front of the section. Returns (profile, lead_ft) - lead_ft = length added in front."""
    from scipy.ndimage import grey_closing
    from scipy.signal import find_peaks
    def cl(Q, r):
        n = int(r / 0.1); y = np.arange(-n, n + 1) * 0.1
        return grey_closing(Q, structure=np.sqrt(r * r - y * y) - r)
    npad = int(max(R, R_in) / 0.1) + 2; Q = np.r_[np.zeros(npad), P, np.zeros(npad)]; out = Q.copy()
    pk, _ = find_peaks(np.r_[0, Q, 0], prominence=0.3); pk = pk - 1
    if len(pk) == 0: return P.copy(), 0.0
    if interior: out[pk[0]:pk[-1]] = cl(Q, R)[pk[0]:pk[-1]]
    if keep_in: out[:pk[0]] = cl(Q, R_in)[:pk[0]]
    out = np.maximum(out, Q)
    nz = np.nonzero(out[:npad] > 1e-4)[0]; lead = (npad - nz[0]) if (keep_in and len(nz)) else 0
    return out[npad - lead:npad + len(P)], lead * 0.1

def _full(q, k):
    """back side (crest -> foot) of one bump made fuller: p + k p (pc - p) / pc. Same length and height; the slope is k x
    gentler just below the crest (where you land) and k x steeper near the foot (filled by the rounding)."""
    q = q.copy(); c = int(np.argmax(q)); pc = q[c]
    if pc > 0: q[c:] = q[c:] + k * q[c:] * (pc - q[c:]) / pc
    return q

def rounded(s, R=30.0, interior=True, lead_in=False, full=0.0, R_in=40.0):
    """v9: round the foot of the bumps (the user: "plat, bosse, plat, bosse" -> transitions). Split halves (double lines)
    too (v10). lead_in (v12): smoother first take-off - on the split halves when the section starts with a split."""
    P, u0, name = s; sp = LS.SPLITS.get(name, [])
    first_split = bool(sp) and sp[0][0] < 1.0
    if full:                                   # v16: "plus de terre au niveau des receptions" (rhythm bumps >= 2.5 ft, not the fused one)
        P = P.copy()
        for n_, a_, b_, h_ in LS.COMBOS[name]['items']:
            if h_ < 2.5 or 'fuse' in n_ or 'split' in n_ or 'whoops' in n_: continue
            ia, ib = int(round(a_ / 0.1)), min(int(round(b_ / 0.1)), len(P))
            P[ia:ib] = _full(P[ia:ib], full)
        if sp: sp = [(st, _full(pl, full), _full(pr, full)) for st, pl, pr in sp]; LS.SPLITS[name] = sp
    if sp:
        new = []
        for k, (st, pl, pr) in enumerate(sp):
            li = lead_in and k == 0 and first_split
            (a, la), (b, lb) = _close(pl, R, True, li, R_in), _close(pr, R, True, li, R_in); ld = max(la, lb)
            a = np.r_[np.zeros(int(round((ld - la) / 0.1))), a]; b = np.r_[np.zeros(int(round((ld - lb) / 0.1))), b]
            n = max(len(a), len(b)); new.append((st - ld, np.pad(a, (0, n - len(a))), np.pad(b, (0, n - len(b)))))
        LS.SPLITS[name] = new
    C, lead = _close(P, R, interior, lead_in and not first_split, R_in)
    if lead:                                   # profile starts lead ft earlier: shift the items and the splits
        c = LS.COMBOS[name]; c['items'] = [(n_, a_ + lead, b_ + lead, h_) for n_, a_, b_, h_ in c['items']]
        if name in LS.SPLITS: LS.SPLITS[name] = [(st + lead, pl, pr) for st, pl, pr in LS.SPLITS[name]]
    return (C, u0 - lead, name)

def stt():
    ox, oz = STT_ORIGIN
    a_col = Z['L4'] - R_CURVE - RS - Z['L1']                               # west column straight
    x_l4 = XWL + R_CURVE
    p = Path(ox + x_l4, oz + Z['L4'], 0.0, 'STT')                          # L4, after the curve, eastbound (straight)
    # v12: kicker cut clean at its first edge (lip kept at 6.9 ft and at the same place) with a straight back; landing climb
    # straighter and steeper (22 ft, slope 1.0), same flat (same place) and same descent
    fmx = [('gap', 5.0), ('cut', 'Detroit_g31_1', 6.9, 0.9), ('gap', 24.2), ('trapeze', 18.0, 22.0, 8.0, 35.0, 'lin', 4.0)]
    l4 = [ROLLER, SA[1], ('gap', 6.0), ROLLER] + fmx                         # wheel tap (v13: 3rd = same roller as the 1st) + freestyle
    p.straight(XBOWL - x_l4, [sec('STT-L4 roller, bosse, roller, saut freestyle', l4, 14.0)], tag='L4 roller, bump, roller, freestyle jump')
    p.turn(+180, RB, BIG, tag='bowl (L4 -> L3)')
    l3 = [('scale', SA[0], 1.6), SA[1], ('fuse', TABLE_B, 4.4, 5.5, 2.2, 46.0, 0.58, 4.0), SA[2], SA[1], SA[0]]   # v11: roller, bump, fused double; v58 (user): 1st roller a bit lower (2.0 -> 1.6 ft)
                                                                            # (2nd hump = mirror of the 1st), 3 bumps
    p.straight(XBOWL - XU, [rounded(sec('STT-L3 roller, long creux, 3 bosses', even(l3, XBOWL - XU, 0.5, 1.0, 4.0), 0.5), full=0.3)], tag='L3 roller, bump, long raised dip, 3 bumps')
    p.turn(-180, RB, BIG2, tag='U L3 -> L2 (rays)')
    L2 = (XMID - RS) - XU
    first = ('split', ('kick', SA[1], 4.3, 0.75, 0.7), ('scale', SA[1], 3.3))   # v19: less steep (0.9 -> 0.75)   # v16: left lower, rolls over at the top; right normal         # v14: outside half more of a kicker (4.8 -> 5.3); inside 3.6
    l2 = even([first] + up([SA[2]], 1.25) + [('scale', SA[0], 5.2)] +            # v13: 2nd bump a bit lower (5.0 -> 4.6)
               up([SA[1], SA[2], SA[0]], 1.35) + up([SA[1], SA[2]], 1.35), L2, -4.0, 8.0)   # v12: 8 ft before the turn (user: 8 ft, never more); v14: 1st bump 4 ft closer to the U
    p.straight(L2, [rounded(sec('STT-L2 long triple, triple, double (ecarts egaux)', l2, -4.0), full=0.3, lead_in=True, R_in=22.0)], tag='L2 long triple, triple, double, same gaps')
    p.turn(-90, RS, SMALL, tag='L2 -> middle lane')
    Lmid = (Z['L6'] - RS) - (Z['L2'] + RS); mid = [SC[2], TABLE_B, SC[3]]
    p.straight(Lmid, [sec('STT-mid bosse, table, bosse', mid, (Lmid - len(L('tmp', mid)) * 0.1) / 2)], tag='middle lane: bump, table, bump')
    p.turn(-90, RS, SMALL2, tag='middle lane -> L6')
    p.straight((XMID - RS) - XU67, [sec('STT-L6 roller a sauter (sortie de virage)', [SMALL_B], 3.0)], tag='L6 straight, jumpable roller at the turn exit')
    p.turn(+180, RB, BIG, tag='U L6 -> L7')
    L7 = (XEL - R_HIGH) - XU67
    l7 = [('scale', ROLLER, 2.6), ('gap', 4.0), ('scale', 'Custom_g32_1', 2.6, 'flip'), ('gap', 10.0), ('whoops', 'Custom_0', 11), ('gap', 20.0)] + SA[3:6]
    p.straight(L7, [sec('STT-L7 petit double, 11 whoops, triple', l7, 1.5)], tag='L7 small double at the turn exit, 11 whoops, triple')
    p.turn(+90, R_HIGH, BIG, tag='L7 -> east lane (real high berm)')
    Lns = (Z['L7'] - R_HIGH) - (Z['L1'] + R_TIGHT)
    big3 = [('scale', 'Custom1_g29_2', 9.1), ('gap', 0.5), ('scale', 'Custom1_g29_3', 6.9), ('gap', 1.6), ('stretch', 'Arlington_g29_2', 8.8, 1.35)]  # v8: x1.15
    # v12: landing a bit higher (8.45 -> 8.8 ft), its back 35 % longer (gentler), crest at the same place
    p.straight(Lns, [rounded(sec('STT-east gros triple SX (plus gros)', big3, 30.0), interior=False, lead_in=True)], tag='east lane, bigger SX triple, less run-up')
    p.turn(+90, R_TIGHT, BIG, tag='east lane -> L1 (high berm, as after the whoops)')
    L1 = (XEL - R_TIGHT) - (XWL + RS)
    # v18: 1st bump back to the v13 one (measured, 4.0 ft, 16 ft after the turn, rounded foot) - the user: 'celle qui etait bien'
    l1 = even(up(SA[:3], 1.2) + up(SD[:3], 1.2) + up([SA[3]], 1.2) + [TABLE_B] + up([SA[0]], 1.2) + up([SA[0], SA[0]], 1.2), L1, 6.0, 22.0)
    p.straight(L1, [rounded(sec('STT-L1 triple, triple, bosse, table, bosse, 2 bosses', l1, 6.0), full=0.3, lead_in=True, R_in=15.0)], tag='L1 along the north fence, wider gaps')
    p.turn(+90, RS, SMALL, tag='L1 -> west column')
    nf = len(L('tmp', FIN)) * 0.1
    p.straight(a_col, [rounded(sec(FINISH_SEC, FIN, a_col - nf - 3.0))], tag='west column: room after the turn, short finish double, curve right after')
    p.turn(+90, R_CURVE, None, tag='curve west column -> L4')
    _start('STT', ox, oz, gate=START_GATE, heading=START_HEADING,
           route=[('S', 360.0), ('T', +90, 30.0, None), ('TO', (XBOWL + RB, Z['L4'] - RB))],
           narrow=[(0.0, None), (8.0, None), (42.0, 30.0)], end_w=30.0,
           finish=(FINISH_SEC, 0))
    return p
