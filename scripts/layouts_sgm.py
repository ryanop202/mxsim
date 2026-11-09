"""Saint-Georges-de-Montaigu (SX Tour), from the user's drone photo (assets/sgm/vue_aerienne.jpg), their marks
(vue_aerienne_marques_user.png) and their spoken description (docs/13_saint_georges.md). Same art direction as Saint-Thibery.
v1 (2026-11-06): first top view to validate. Every bump is a measured JGSX unit (lib/) unless marked 'scale' / 'fuse'.

Lap (heading west on the start straight, as on the photo: north = top):
  start straight westbound (grid at the east end, 22 gates) -> left turn (flat) ->
  L2 southbound : roller + roller fused, into a table; a bump; a big SX triple -> left U in a berm ->
  L3 northbound : steep double; special finish jump (to work on with the user) -> right U (hairpin) in a berm ->
  L4 southbound : whoops; a triple after them (as Saint-Thibery) -> right 90 with a very small berm ->
  bottom westbound : very small double (as the one before the whoops at Saint-Thibery) -> right 90 in a berm ->
  L1 northbound (along the west crowd) : triple out of the turn, landing fused (bump, 2 fused bumps, the 3rd higher);
      another triple; double, table, bump -> right 90 in a berm ->
  top eastbound : big SX triple -> right U -> start straight.
Scale: 43 ft between lane axes (as Saint-Thibery) = 70 px on the photo (1.63 px / ft, L1 axis at x 212, top lane at y 428).
Local coords: x east, z south (image down)."""
import numpy as np
from engine import Path
import layouts_sx as LS
from layouts_sx import L, sec, _start, SA, SD, SC, TABLE_B, RB, RS, BIG, BIG2, SMALL, SMALL2
from layouts_stt import rounded, even, up, spread

KEY, PFX = 'SGM', 'sgm'
DAY = dict(folder='USLAND2026SaintGeorgesbyBazo_jour', desc='USLAND: 2026 Saint Georges (jour, travail)')
STT_ORIGIN = (380.0, 330.0)                    # local (0, 0) = L1 axis x, top lane axis z (world ft)
X = dict(L1=0.0, L2=43.0, L3=86.0, L4=129.0)  # lane axes (x)
ZT, ZS, ZH, ZB = 0.0, 47.0, 111.0, 502.0         # top lane, start straight, hairpin top, bottom lane (z): photo, 1.63 px / ft
Z_U23 = 416.5                                   # v17 (user): +31 ft for the extra roller before the big triple (same gaps)
# was 385.5
#                                  # L2 / L3 straights end here (left U below)
L3_SKEW, R_HP = 5.0, 27.0                       # v3 (user's plan): L3 askew (deg, to the right going up), open hairpin radius
TOP_A1 = 150.0                                  # v4: top U = 150 deg then a tight 30 deg exit (the cut)
L1_Q4 = 12.0                                    # v12 (user): entry triple -> 4th bump (was the L1 gap, 15): same height, closer, to do the quad
L1_OFF = 10.0                                   # v9 (user): table -> last bump (was L1_GAP 15)
U4 = 3.0                                        # v9 (user): whoops start right where the hairpin berm ends (was 2.0)
L2_FILL = 1.4   # v17 (user): the v13 version was the best (v14 plateau + dip removed)
# v14 was dict(hold=8.0, hold_h=3.1, down=7.0, low=2.3)   # v14 (user's drawing): after the bump crest stay up (~3.1 ft) for 8 ft, down a bit (to 2.3) over 7 ft, then the table face
# v13 was 1.4 (a flat fill)
#                                  # v13 (user): fill level between the L2 bump and the table (ft)
L1_GAP = 15.0                                   # v6: max gap between the L1 bumps
U3, G3 = 0.0, 4.0                               # v6 (user): the take-off 6 ft earlier, the jump 6 ft longer (see finish_jump drop)
#                             # v5b (user): L3 double right at the turn exit, 10 ft before the finish take-off
R_ST = RB                                       # v5 (user): the first turn after the start wider (11 -> 21.5 ft)
XU = 262.0                                      # v3 (user): the top U starts here (a bit further east), see top_u()
ROLLER, SMALL_B = 'Custom1_g30_1', 'Glendale_g40_2'
FIN = None   # v5: see finish_jump()
# v4 was [('cut', 'Detroit_g31_1', 5.6, 1.2), ('gap', 14.0), ('trapeze', 11.0, 28.0, 4.0, 32.0)]   # v4 (user): take-off = the Saint-Thibery freestyle kicker, shorter and less steep (6.9 -> 5.6 ft, back 0.9 -> 1.2); landing (user's drawing): a short flat, then a BIG mound (11 ft, much higher than the lip) rising over 28 ft, round top, long way down
FINISH_SEC = 'SGM-L3 double, saut d arrivee'
SIDE_CUT, PROPS, RAILS = {}, [], []   # v17: filled by track() (finish take-off cut on the left; barriers / cone along the finish jump)
BIG3 = [('scale', 'Custom1_g29_2', 8.5), ('gap', 0.5), ('scale', 'Custom1_g29_3', 5.6), ('gap', 0.2), ('stretch', 'Arlington_g29_2', 8.3, 1.3)]   # v12 (user): middle lower (6.5 -> 5.6), almost stuck to the 3rd (gap 1.6 -> 0.2)

# arena (fence box, local) + the start area east of it (kept as dirt)
# v11 (user): the dirt edge closer to the track on the east side, along the whoops lane (~12 ft beyond the whoops, same angle);
# north / west / south sides unchanged
ARENA_POLY = [(-32.0, ZT - 32.0), (343.3, ZT - 32.0), (328.9, 130.0), (190.1, 130.0),   # v36 (user): back where it was before v33 (x 333 at the gate row centre) but parallel to the gate row
               # v33 (user): the fence behind the start 8 ft further back
                # v28: the start area in the polygon (notch at x 200 = fence bug)
              (154.0, ZB + 32.0), (-32.0, ZB + 32.0)]   # v26 (user's grey lines): the east edge straight up to the start-area south edge, a square corner
ARENA = (-32.0, 200.0, ZT - 32.0, ZB + 32.0)          # v3: L4 further east (askew L3, open hairpin)
GRASS_OUTSIDE = dict(keep=[(200.0, 328.9, ZT - 32.0, 130.0)], dirt_to_fence=True)   # v33 (user): dirt right up to the fence everywhere (no bare strip), start 8 ft deeper   # v12 (user): dirt ends right behind the gate floor (x 332) and right south of the row (z 128): fence 2 m from them
START_GATE, START_HEADING = (314.0, 84.0), 185.0   # v3 (user's plan): right of the top U, higher, a few deg askew   # v2 (user): row a bit skewed, facing the berm of the hairpin after the finish jump
BERM90_GAIN = 1.4
BERM_GAIN = {'start -> L2 (wider, low berm)': 0.85,   # v21 (user): steeper, dug more (0.55 -> 0.85)
             'bottom -> L1 (small berm, a bit bigger)': 0.85, 'hairpin L3 -> L4 (berm)': 1.9,
             'L1 -> top (berm, a bit lower)': 0.95}   # v4 (user, 2nd test): 1st left gets a low berm, hairpin outside higher, L1 -> top lower again   # v3 (user, 1st test)
# v10 (user, in game): the v9 stretched exit left a low lump (1-2 ft) on the outer line right at the 1st whoop: the berm
# now stays full longer (exit half up to 200 deg) and is cut cleanly between 160 and 180 deg (BERM_END)
BERM_END = {'hairpin L3 -> L4 (berm)': (160.0, 180.0),
            'U L2 -> L3 (berm)': (143.0, 168.0),
            'L1 -> top (berm, a bit lower)': (50.0, 92.0)}   # v28 (user): the berm faded out smoothly before the triple take-off (no line)   # v19 (user): a bit more progressive (v17: 145-154, too sudden)   # v17 (user): the berm ran into the take-off of the double: stopped ~1 m after the last net post
BERM_OFFSET = {'hairpin L3 -> L4 (berm)': (2.75, 3.0)}   # v11: R_HP 30 -> 27 moves the whoops lane 5.7 ft in; the berm stays where it was
BERM_SHIFT = {'hairpin L3 -> L4 (berm)': (25.0, 90.0, 200.0, 1.15, 1.0),   # v12 (user): far too high at x1.5 (9 ft): a bit lower than the left U (7.4 ft) -> 6.9 ft   # v11 (user): higher, bigger (6 -> 9 ft)
                # v9 (user): the outer side ran out over the middle of the whoops: exit half stretched to the turn end, the whoops start right there
              'U L2 -> L3 (berm)': (0.0, 70.0, 155.0, 1.15, 1.0), 'top U (real half turn)': (0.0, 45.0, 90.0, 0.75, 1.0),
              'L4 -> bottom (small berm)': (-15.0, 45.0, 105.0, 0.85, 0.75)}   # v5 (user): L2 -> L3 berm ends earlier (it touched the double); L4 -> bottom steeper   # v4: L2 -> L3 a bit lower; L4 -> bottom a longer entry and exit
INNER_RUTS = {}   # v5 (user): inside rut dropped (v4: bottom -> L1, h 1.3)   # v4 (user): inside rut in the middle of the track   # v3 (user): bigger, above all at the entry (peak earlier)
TARPS = False
# v12 (user): people on the mounds (Saint-Thibery crowd cut-outs, cropped sprites), only where the ground is raised
CROWD = dict(rows=tuple(np.arange(16.0, 126.0, 5.0)), step=5.0, jitter=2.5, skip=0.08,   # v26 (user): many more, up to the top of the mounds
             size=48.0, side_jit=3.0, hmin=2.0,
             own={'Crowd5': 'Crowd5_fr'}, imgs=('Crowd1', 'Crowd2', 'Crowd3', 'Crowd4', 'Crowd5', 'Crowd6', 'Crowd8', 'Crowd9'),
             src='@2022Miamibeachrace/billboard', mesh=True, game='C:/Program Files (x86)/MX Simulator', sprites=True,
             beast=True,
             extra=dict(rings=(2.6, 5.2), step=5.5, skip=0.45, sprinkle=dict(d=(9.0, 34.0), per=150.0, hmax=2.0),   # v33 (user): people all round the ground
                        zones=[(140.0, 184.0, 545.0, 700.0, 170.0), (190.0, 250.0, 180.0, 300.0, 50.0)], zone_per=70.0,   # v39 (user): many more in front of the hall   # v38: fewer under the arch, a few in front of the hall
                        avoid=[(-60.0, 350.0, -135.0, -40.0), (296.0, 470.0, -60.0, 150.0)], clear=5.0, no_back=True))   # v38 (user): nobody behind the start, nobody behind the mounds   # v31 (user): Mr Beast's face on every face of the crowd (3 photos in turn, fitted per person)
# v12 (user): grass patches on the grass / mounds (Saint-Thibery DVDB decal, recoloured dry), not over the fence line
GRASS_DECALS = dict(size=45.0, step=26.0, clear=44.0, ring=44.0, auto=((0.0, 3.5, 7.0, 3.4), (3.5, 9.0, 13.0, 6.5)), auto_max_df=70.0, max_slope=0.30,   # v38 (user: texture patches on the mounds): not on steep slopes
                      # v33: + patches from the tile map near every edge
                    near=dict(rows=((9.5, 5.5, 2.6), (13.5, 12.0, 6.0), (24.0, 21.0, 10.0), (36.0, 30.0, 14.0)),   # v33 (user: no bare ground): from right behind the fence, wherever it is grass
                              zones=((-1e9, 1e9, -1e9, 1e9),), not_paths=True))
PATHS_DIRT = False   # v33 (user): the paths in dark gravel again (v31-v32 'main' track dirt)   # v31 (user): track dirt texture   # v30 (user): the paths (north / start / east) in dirt, not gravel
#   # v28 (user: the grass hid the gravel paths): off the gravel ring (24 ft), roads, yard
DIRT_DECALS = dict(size=26.0, step=10.0, inside=True, yard=True)   # v31: + the yard   # v28 (user): the dirt texture everywhere between the lanes (up to the dirt edge)
LIGHT_DECALS = ('track', 'whoops', 'table', 'single', 'tripleface', 'triplemiddle', '90', '180')   # v28: the SX1 dirt decals lightened like the dirt
ROUGH = dict(shiny=dict(prefix=('boudin_', 'startb_'), grain=0.010, spec=1.5),   # v31 (user): the boudins are shiny vinyl: much less roughness
             grain=0.035, spec=0.5, prefix=('pylon_round', 'f50_cylinder', 'rider_gate', 'boudin_', 'startb_', 'bale_', 'hay_', 'clubhouse',
                                                 'arch_tube', 'cone_orange', 'rail_', 'fence_heras', 'pole_concrete'))   # v28 (user): a bit of roughness on the objects
# v6 (user): earth mounds for the crowd in the 3 zones the user circled on the drone photo (west along L1, east along the lower
# half of L4, south), dry grass on them and all around
SLOPE = dict(h=18.0, d0=43.0, inner=52.0,   # v41 (user): the foot beyond the road (it was cut into a steep step)
              top=10.0, outer=34.0, fade=12.0, lin=0.7)   # v12 (user): long inclined plane, much higher, down behind
# v18 (user): a 2.5-3 m path between the fence (6.5 ft from the dirt) and the mounds: the mound foot ~3 m (10 ft) beyond the fence everywhere
# v21b (user): the path fence -> mounds doubled (~10 -> ~20 ft), the passage between the two back mounds twice that (~40 ft)
MOUNDS = dict(h=9.0, d0=23.3, inner=24.0, top=30.0, outer=28.0, fade=30.0,
              zones=[(-260.0, -32.0, -80.0, 370.0),
                     (120.0, 282.0, 278.0, ZB + 140.0, SLOPE),   # v24 (user's brown): starts at z ~220 (the hall before it), to x ~276
                       # v21 (user): down to the SE corner, the passage below separates it from the south one   # v18 (user): the whoops mound ~9 m longer (north end z 150 -> 120)
                              # v12 (user): east, along the whole whoops lane down to the turn: a long inclined plane
                     (-260.0, 330.0, ZB + 14.0, ZB + 300.0, SLOPE)],   # v21: east to the SE corner
              # v21 (user): the whoops mound and the south mound brought together, a ~4 m (13 ft) passage between them at the
              # SE corner of the arena (diagonal, local point + direction), sides sloping over `soft` ft
              passages=[])   # v25 (user): the two mounds right of the road joined again (the road cuts them); v21: diagonal passage   # v12 (user): south, the same, from right at the turn exit (the two separated at the corner)   # v11 (user): east mound follows the closer edge; east and south mounds SEPARATED at the south-east corner (grass between)   # west, east, south
CLOSE_R = 3.0   # v26 (user): square corners at the start area (was 15)
# v18 was 15.0   # v18 (user: the whoops mound longer to the north): the inner corner arena / start area less rounded (45 -> 15 ft), fence and mound go further into it
GRASS_DRY = (128, 118, 68)   # mean colour of the grass tile (Saint-Thibery ~ (58, 92, 38)): dry yellowish grass   # v3 (user): no sponsor tarps on the fence, no START sign, no flames
# not yet for this track (Saint-Thibery features): bank, platform, pylons, flagger stand, night, crowd...
ARENA_BANK = START_PLATFORM = GRASS_TUFTS = None
# v20 (user: the flag marshal's hut was forgotten): the Saint-Thibery finish flagger stand, same settings: a dirt platform joined to
# the RIGHT side of the finish take-off (whoops side), flat top 1 ft under the crest, the animated photo flagger in the steel cage
FLAG_STAND = dict(box=True, item=2, side=1, v0=16.5,   # v21 (user): lower (drop 1 -> 2.5), straight walls all round (box, slope 6)
                    # item 2 of the L3 section = the finish take-off (0 = the double's)
                  w=8.0, back=4.5, fwd=8.0, drop=2.5, slope=2.5, rect=True, flip=1,   # v22 (user): cut straight at the cage (1 m less before it), clean square walls, a bit off the lane
                 
                  rf=dict(src='@2024Bh1Conway/flaggerfiles', size=10.5, flip=1))
START_FLOOR = dict(back=18.0, side=2.5)   # (the props it copies are still needed; the floor itself is replaced by START_GRIDS)
START_GRIDS = dict(length=9.5, frame_rgb=(170, 174, 177), beam_gap=0.0, beam_shp=True,   # v31 (user): a bit longer, beam right against the grids, with collision
                   clean=dict(bar=0.10, lwd=0.38, swd=0.19, strand=0.045,   # v37 (user): a bit smaller again
                               y_plate=0.06, y_top=0.12, mud=0.0))   # v33 (user: diamonds not readable in game): bigger diamonds, thicker strands   # v31b (user): back on the ground   # v31 (user): thin edges, clear diamonds, no mud, off the ground
#   # v30 (user): longer than a bike, no red frame (usual steel), beam 2.5 ft further back
GATE_FRAME = dict(rgb=(196, 26, 24), square=True, flat=dict(w=0.24, t=0.12))   # v31 (user): flat rectangular bars, sharp corners   # v30 (user): the falling gate = a red rectangle
#   # v29 (user's photo): short diamond-mesh plates in red frames, a beam behind (scripts/start_grids.py)
NET_SHP = dict(spring=62, damping=3)   # v30 (user): every net a bit softer (85 / 4)
# v34 (user's blue line): past the top, the wall steps down one layer every half block (45 deg) and stops
CONCRETE_WALL = dict(stair=dict(after=3.0, step=2.62), h_end=2.6, r=3.0, off=18.0, depth=2.62, cut=14.0, fill_from=13.0, shp=True)   # v30 (user): the wall IS the side of the landing face: dirt behind it filled level, the flank outside cut away (no dirt sticking out), the wooden barrier back on top, collision
WALLS = []   # filled by track()
WALL_EDGE = dict(w=3.4)
# v41 (user's in-game top view of v40, night): the minimap = the arena cut out of the shot, START on the grid, BAZOWURX at the
# top; the terrain cut down to a square around the arena (the game draws map.png over the whole terrain) - the arch and the
# yard kept, the far fields / trees lost
REFRAME = dict(x0=155.0, z0=228.0, side=762.0)
MAP_SHOT = dict(img='assets/map/sgm_topview_v40.png', rect=(0, 0, 1279, 727), r_px=40, soft=1.5, mask_df=3.0,
                title_img='assets/map/bazo_wurx.png', title_box=(412.0, 252.0, 658.0, 306.0),
                text='START', text_box=(648.0, 372.0, 686.0, 458.0), text_rot=85, M=1024, follow=dict(half=19.0, close=18, poly=[(332.0, 36.0), (246.0, 20.0), (60.0, 20.0), (60.0, 82.0), (155.9, 91.0), (187.8, 108.0), (274.4, 132.0), (332.0, 136.0)]),   # v41b (user's white rectangle): START in front of the grid, along it; map cut along the track
                pts=[((449.4, 406.4), (924.0, 203.8)), ((444.3, 751.3), (231.0, 236.0)), ((517.0, 470.5), (804.0, 348.0)),
                     ((489.9, 809.9), (119.0, 333.0)), ((401.7, 809.9), (103.5, 156.0)), ((402.3, 353.8), (1024.0, 102.5)),
                     ((633.6, 352.4), (1053.0, 568.0)), ((703.9, 349.0), (1070.0, 708.4))])
# v39 (user): the 30 s board man as Saint-Thibery: in the middle of the start straight, running off to one side
BOARD30 = dict(stand=(110.0, 7.5),   # v41c (user): 2 m to the riders' left (the side he runs to), out well before the gate drops
               hide=(110.0, -1), hide_out=-16.0, speed=10, done='blank')
# v39 (user): timing gates at the turn pylons, fanned (as Saint-Thibery)
# v40 (user, edited in the game editor on v38): the 2 checkpoints of the start straight wider, in the middle of the corridor
CHECKPOINT_FIX = [((582.418814, 377.0), (601.320129, 395.110840), (-38.077026, 0.494507)),
                  ((513.459407, 377.0), (507.363861, 384.231689), (-28.186890, 0.494507))]
GATES_PROPOSAL = dict(lanes=dict(off=30.0, half=21.0, min_len=50.0, gap=70.0, spacing=115.0, turns=True), half_lane=15.2, inner=12.0, outer=12.0, start_pad=4.0)   # v43 proposal (user): fewer gates, straights only
TIMING_GATES_FILE = 'assets/sgm/user/timing_gates_v43.txt'   # v43 (user approved): the 33 gates frozen; the user retouches a few in game   # v41 (user): his gates (edited in the game editor on v40), kept as they are from now on
TURN_GATES = GATES_PROPOSAL   # v43 (user: "on garde ca"): 33 gates, ~35 m apart in the lanes + one wide gate per turn
_TURN_GATES_V39 = dict(half_lane=15.2, inner=2.0, outer=12.0, fr=(0.15, 0.85), fan=True, start_pad=4.0)
# v39 (user): an extra day track, the track only (no decor), to take the in-game top view for the minimap
MAP_TRACK = dict(folder='USLAND2026SaintGeorgesbyBazo_carte', desc='USLAND: 2026 Saint Georges (carte, jour)',
                 keep=('pylon_round', 'boudin_logo3', 'start_grids', 'cwall_'))   # v38 (user): a real mound edge (rounded lane side shape) where the blocks were removed, not a sheer cut
MOUND_FLANK = None   # v37 (user): no rounded sides - the mound as built, cut straight in the wall plane
_MOUND_FLANK_V36 = dict(e0=14.0, w_west=15.0, w_east=9.0, ext=14.0, end_fade=12.0)   # v33 (user: "IRL ca descend, c'est large sur les cotes"): the landing mound's sides widened (cosine slope) - east 9 ft (Bobcat boudins), west under / past the wall
WALL_TOP = []   # v31: u of the mound top (for the tarps / person)
WALL_STAIR = {}   # v34: filled by track(): u0, ltop, step
# v31 (user): sponsor tarps hung on the block wall (RBT, USLAND, BAZOWURX) and an RBT tarp laid on the other side of the mound
WALL_TARPS = dict(names=('rbt', 'bazowurx', 'usland'), du=(-9.0, 0.0, 9.0), y=7.3, scale=0.78)   # v34: a bit smaller, placed where the 4th row exists   # v31b (user): on the 4th row of blocks (3 x 2.62 ft up), BAZOWURX in the middle
MOUND_TARP = dict(name='rbt', du=(-7.5, 7.5), h=(5.5, 10.5), off=(14.0, 30.0))
#   # v29 (user's photo): concrete lego blocks along the left edge of the finish landing (scripts/concrete_blocks.py)   # one big square-mesh floor behind the gate row (as Saint-Thibery)
FENCE = dict(model='fence_heras', off=6.5, step=11.48)   # v12 (user): mobile mesh fence (3.5 m panels on concrete blocks, scripts/fence_heras.py) 2 m around the dirt   # v11 (user): no fence   # wooden fence around the dirt area (as Saint-Thibery), 6 ft from its edge
# night (same art direction as Saint-Thibery): light poles 3 on each long side facing the track, lights baked in the lightmap
NIGHT = dict(folder='USLAND2026SaintGeorgesbyBazo', desc='USLAND: 2026 Saint Georges by bazo', d=40.0, n_long=5, n_short=3, keep_every=2, pad=(7.0, 15.0), pole_models=True, pole_model='pole_concrete', glow=dict(lamps=[(-1.3, 43.7), (1.3, 44.3)], x=2.4, size=10.0), head=44.0)   # v28 (user): the real site's concrete poles   # v11 (user): no light poles (new ones to be modelled), light kept
# v30 (user: "allume plus les lampadaires ... regarde la nuit [de Peneman Moon] ... si tu peux le recreer, fais-le"): one big
# dark decal over the arena (clear pools under the poles, a shadow of every object per lamp = star shadows), warm light / blue
# ambient / black fog for the bikes, flare billboards on the lamps; the person on the landing top (last lap only)
NIGHT['fx'] = dict(overlay=dict(centre=(530.0, 580.0), size=880.0, px=2048, cone=(0.45, 0.95), r0=2500.0, tilt=0.42, ref_pct=88, shadow_k=0.55, shadow_w=0.7,   # v31 (user): one pool per pole where it aims, lighter / thinner shadows
                                a_max=0.42, a_min=0.03, k=0.42, gamma=1.0, shadow_max=32.0),
                   glow_bb=12.0, flare_k=0.72,   # v31 (user): the big light points a bit less bright (v30 16 ft, full)
                   lighting=['sun_vector [ -0.6528\t0.3590\t0.6671 ]', 'sun_color [ 1.05 1.00 0.82 ]', 'ambient [ 0.27 0.29 0.42 ]',
                             'fog [ 0.0 0.0 0.0 ] 0.0015'],   # v33 (user: dark where not lit): denser black fog (v31 0.0007)
                   extra=[dict(c=(375.5, 278.1), aim=(0.0, 1.0), head=45.2, gain=0.35, flare=8.0, lamps=((375.5 - 0.6, 278.1), (375.5 + 0.6, 278.1)))],   # v31 (user): the sign's spot, weaker
                   sky=(0.022, 0.022, 0.026),   # v31 (user): black sky, white stars
                   person=dict(img='assets/sgm/person.png', c=(92.9, 184.6), h=6.5))   # v31 (user's circle): west edge, by the wall (v30 (119, 186))
NIGHT['blend'] = 45.0   # v39 (user): the ground darkens like the trees (v36 110 ft kept it lit far away)   # v36 (user): the light fades out slowly away from the fence (v33 25 ft: green then black at once)
NIGHT['fx']['overlay']['blend'] = 45.0
NIGHT['bake_base'] = (4.0, 5.0)   # v33 (user): the unlit surroundings almost black (v22-v32 14 + 18 x moon)
NIGHT['bake_extra'] = [dict(c=(232.0, 222.0), aim=(0.0, 1.0), head=18.0, gain=0.35, tilt=0.9)]   # v33 (user): the hall a bit lit (local)
NIGHT['tint_bb'] = dict(lo=10.0, hi=210.0, min=0.08, min_crowd=1.0, skip_first=1)   # v41 (user): the crowd lit again (only the trees darken)   # v39 (user): the crowd behind the lights much darker   # crowd never darker than 55 % (faces still readable)
TEAROFFS = False   # v33 (user): no tear-off decals on the track   # v33: trees / crowd billboards as dark as the light where they stand
NIGHT['bake_gain'] = 0.75   # v39 (user): a lot less light round the poles outside the track (v29-v38 1.5)   # v30 (user): the lamps brighter outside the fence too
POLE_SPOTS = [((-39.6, z), (1.0, 0.0)) for z in (70.0, 255.0, 440.0)] + [((round(187.9, 1), z), (-1.0, 0.0)) for z in (240.0,)] \
             + [((178.0, 350.0), (-1.0, 0.0)), ((168.2, 460.0), (-1.0, 0.0)), ((344.6, 60.0), (-1.0, 0.0))] \
             + [((95.0, 541.6), (0.0, -1.0)), ((20.0, 541.6), (0.0, -1.0)), ((65.0, -39.6), (0.0, 1.0))]   # v29 (user): right behind the metal fence (one was in the hall)   # v28 (user): + the small double at the bottom, + the top triple
# v13 (user): nets in the turns as Saint-Thibery (on the berm crest; just outside the lane where there is no berm), wooden
# posts, grey mesh (galvanised colour). Not in the cut end of the top U: the start runs through it.
NETS = dict(turns='all', skip=('top U (cut end, tight, flat)',), end={'top U (real half turn)': 0.72},   # v22 (user): the top U net came back into the line: stopped earlier
             step=8.0, flat_off=8.0, flat_gap=3.0, tex='net_black_fine', fine=dict(cell=0.16, strand=3, knot=5), round_posts=True)   # v28 (user's photo): round wooden posts, small black mesh; v13-v27 tex='net_grey'
# v13 (user): black pylons inside the turns on a small raised dirt mound, exactly as Saint-Thibery (turn bisector rule, the
# Saint-Thibery v32 margin); no yellow stakes on the bumps (none on this track)
PYLONS = dict(half=15.2, margin=1.5, skip=('top U (cut end, tight, flat)',),
              # v15 (user's black circles on 8 in-game top views of v13, located from the known pylons / whoops; +-2 ft):
              # 1st turn, hairpin, L1 -> top, top U moved deeper inside the turn (divider nose); the 3 others unchanged (rule)
              points=[(449.4, 406.4), (444.3, 751.3), (517.0, 470.5), (489.9, 809.9), (401.7, 809.9), (402.3, 353.8), (633.6, 352.4)])   # v19 (user's circles on v17): L4 -> bottom, bottom -> L1, L1 -> top   # v17 (user's circles on v16): 1st turn, L1 -> top, top U moved again
# v15 (user's white rectangles): straw bales (Saint-Thibery model), world (x, z, long axis angle deg): 2 pairs at the start
# of the whoops and 2 in their middle, against the fence (east) and in the divider with L3 (west), long side across the
# lane; 1 along the divider nose of the U L2 -> L3, next to its pylon
# v17 (user): on the whoops the pairs spread more (16 ft) and zig-zag (one bale closer to the lane, the other further out),
# 3 groups: whoops start, middle, last whoop; + 1 at the nose of the U L2 -> L3
# v22 (user's rectangles on v21 top views): real-straw bales along the whoops (yellow), white Saint-Thibery bales in the
# turn after the whoops and in the turn after the small double (white); (x, z, long axis deg, texture)
# v24b (user): the fence-side straw bales against the fence (3 ft beyond the dirt edge), the divider ones off the whoops (23.5 ft
# from the lane axis), all along the lane
# v28 (user's review of v27): 2 whoops bales (fence one against the fence, the other off the whoops), real hay bales; SE turn
# bale off the track; the 2 bales of the turn L1 -> top removed
BALES = [(553.8, 624.4, 5, 'bale_hay'),
         (561.1, 604.5, 5, 'bale_hay'),
         (556.6, 558.2, 5, 'bale_hay'),
         (567.0, 531.7, 5, 'bale_hay'),
         (510.1, 579.5, 5, 'bale_hay'),
         (511.5, 551.8, 5, 'bale_hay'),
         (485.4, 849.1, 0, 'bale_straw'),
         (475.0, 849.1, 0, 'bale_straw'),
         (482.2, 813.8, 0, 'bale_straw'),
         (472.2, 815.2, 0, 'bale_straw'),
         (494.8, 804.6, 95, 'bale_straw'),
         (533.9, 810.6, 95, 'bale_straw'),   # v29 (user): 0.8 m back towards the track
         (517.2, 506.4, 5, 'bale_hay'),   # v30 (user): perpendicular to the whoops   # v29 (user): whoops entry, right side, against the whoops
         (361.3, 804.8, 90, 'bale_straw'),   # v29 (user): opposite the inside one (mirror across L1)
         (398.7, 804.8, 90, 'bale_straw'),
         (407.1, 815.0, 0, 'bale_straw'),
         (444.1, 743.7, 90, 'bale_straw')]   # v26 (user's marks on v25)
# v19 (user's lines): logo boudins as Saint-Thibery (no Moto Club logo): 50 Factory (yellow), SX Tour, Fly, RBT; local coords
# north side of the start straight (divider with the top lane, from the top U pylon to the 1st turn) and south side of the
# start corridor (from the south end of the gate row to the pylon of the 1st turn, bent to stay off the hairpin berm)
# v30 (user): inner side of the start: the 2 first 50 Factory straight out of the grid, then the Fly ones askew so the line
# runs at the FOOT of the hairpin berm (flat ground, >= 4 ft off its toe), no more 50 Factory in the berm, no hole dug in it
BOUDINS = dict(lines=[dict(p0=(136.3, 144.2), p1=(131.0, 204.0), tex=('boudin_bobcat3',)),   # v22 (user): 10 red Bobcat boudins from the hairpin pylon, divider whoops / finish
                     dict(p0=(246.0, 26.0), p1=(64.0, 26.0)),
                     dict(p0=(310.3, 131.4), p1=(274.44, 128.26), tex=('startb_50factory3',) * 2),
                     dict(p0=(274.44, 128.26), p1=(187.80, 104.01), tex=('boudin_fly3',) * 3 + ('boudin_sxtour3',) * 2),
                     dict(p0=(187.80, 104.01), p1=(155.90, 87.32), tex=('boudin_sxtour3', 'boudin_fly3')),
                     dict(p0=(155.90, 87.32), p1=(84.62, 77.17), tex=('boudin_fly3', 'boudin_fly3', 'boudin_sxtour3', 'boudin_sxtour3'))],
               grey_ends=True, flatten=0.0,   # v30 (user): flattening removed (it cut the hairpin berm and the Fly pylon mound)
                 # v29 (user: a Fly boudin sunk): the ground flattened under the lines   # v28 (user): grey inside every boudin, as the Bobcat ones
               model='boudin_logo3', seg=18.0,   # v28 (user's photo): 3 boudins in one, one long logo (scripts/boudin3.py)
               tex=('startb_50factory3',) * 3 + ('boudin_fly3',) * 3 + ('boudin_sxtour3',) * 3)   # v21 (user): no RBT, blocks of 10 as Saint-Thibery
# v17 (user): freestyle ramp as Saint-Thibery (the user's steel ramp_50, the texture WITHOUT logos), beside the finish take-off
# on the whoops side (in the divider, off the lane), turned ~8 deg towards L3 so it jumps into the finish landing (aim = the
# back side of the 16 ft landing, ~12 ft high, a bit east of the L3 axis); local coords
FMX_RAMP = dict(lip=(124.0, 257.0), aim=(119.0, 172.0),   # v22 (user): 5 m closer, a bit less turned
                  # v19 (user): 12 m further back, a bit less turned
                H=9.0, width=4.0, side=0.5, model='ramp_50', model_len=18.47)
# v17 (user): in the right turn after the small double (bottom -> L1), a small berm in the middle of the inside part of the
# turn ("un petit externe mais au milieu"), as high as the pylon mound (0.75 ft), to lean on in the inside line: an arc
# around the turn centre, crest at `r` ft, face towards the inside line over `w_in` ft, back over `w_out` ft, faded at both ends
MINI_BERMS = [dict(tag='bottom -> L1 (small berm, a bit bigger)', P=(12.1, 493.5), nrm=(0.76, -0.64), R=24.0, half_len=8.0, fade_len=4.0, h=0.5, w_in=2.5, w_out=2.5)]   # v22 (user's line on v21): moved, shorter
# v21 (user: it turned sharp on the spot, a weird quarter turn): a tiny copy of the real outer berm, SAME radius (R ~ the net's),
# its crest through the user's spot (r 9.5 ft from the turn centre, mid-turn), 28 ft long, faded over 7 ft at both ends   # v20b: placed from the v19 berm visible on the user's screenshot (line ~9.5 ft from the centre, ~150 deg)   # v20 (user): at least as long as the user's line (longer, shorter fades), a bit lower (0.75 -> 0.5)   # v19 (user's black line): crest 6.5 ft from the turn centre (was 14.5)
PYLON_SKINS = {0: 'pylon_round_motul', 1: 'pylon_round_f50', 4: 'pylon_round_motul', 5: 'pylon_round_f50'}   # v28b (user): U before the finish + L1 -> top yellow 50 Factory, bottom -> L1 Motul   # v28 (user): logos back (Fly on the black ones = pylon_round, Motul on the 1st)   # v26 (user): no logo on the pylons; v17 was pylon_motul   # v17 (user): the 1st pylon after the start red (Motul)
# v21 (user): a bump on the INSIDE of the turn after the whoops triple (L4 -> bottom), from the end of the landing, at the
# pylon's level, a bit skewed; local centre, travel direction `ang` deg (x east, z south), cosine along L, flat crest W wide
EXTRA_BUMPS = []   # v22 (user): the inside bump removed; v21 was [dict(c=(117.0, 488.0), h=2.4, L=12.0, W=11.0, ang=160.0, ends=3.0)]
# v23 (user: the decor of the real site from Google satellite views, registered on the drone photo - work/sgm_decor.py):
# trees where the satellite shows trees (cut-out billboards of other tracks), the pond (its exact satellite shape, east of our
# start area: a 2 m bank going down 1.5 m to the water), the gravel road between the east fence and the mounds down to the
# back passage, the club house at the head of the road
DECOR = dict(file='assets/sgm/decor.json', tree_tex=('@CahuillaMx/billbourd/freecutout_tree_14_oak.png', '@CahuillaMx/billbourd/freecutout_tree_20_Linden.png',
             '@CahuillaMx/billbourd/freecutout_tree_07_youngoak.png', '@CahuillaMx/billbourd/freecutout_tree_08.png',
             '@CahuillaMx/billbourd/freecutout_tree_02.png'), tree_size=(30.0, 46.0))   # v24b (user): no palm tree (the Miami one)
POND = dict(bank=6.6, drop=4.9, deep=8.5, water_rgb=(42, 62, 58))
# v25 (user's drawing on v24): the south road down to a departmental road (asphalt) across the bottom, the site road continued
# east (north of the hall, south of the pond); every road cuts the mounds
ROADS = [dict(pts=[(204.0, 141.0), (148.0, 780.0)], w=16.0, kind='gravel'),
         dict(pts=[(205.0, 152.0), (575.0, 158.0)], w=16.0, kind='gravel'),
         ]   # v28 (user): no departmental road any more (v25-v27 asphalt + markings removed)   # v26 (user): the road goes on south past the departmental (crossroads)
WOOD_BARRIER = dict(off=4.8, chunk=100.0, skip=[(-1e9, 1e9, -1e9, -20.0), (195.0, 1e9, -1e9, 135.0)])   # v29 (user): none behind the start / on the north side (x0, x1, z0, z1)   # v28b (user's photo): round-post wooden barrier with one top rail, inside the metal fence
GRAVEL_STYLE = 'dark'   # v33 (user's photo): dark crushed stone on the paths (roads through the arch, site road)
GRAVEL_RING = None   # v33 (user): grass all round behind the fence (no path ring)
_GRAVEL_RING_V32 = dict(d=(6.5, 24.0), skip=[(-1e9, -32.0, -1e9, 1e9), (-1e9, 1e9, 534.0, 1e9)])   # v29 (user): grass again on the west / south sides   # v28 (user): from the fence line exactly   # v26 (user): dark grey gravel all round the arena, between the fence and the mounds
ALLEY_WIDEN = 14.0   # v28 (user): the mounds further apart so the arch feet show; v26 was 5.0   # v26 (user): the alley through the mounds twice as wide (1.5 m more each side)
LIGHT_DIRT = dict(x=(-60.0, 350.0), z=(-135.0, -40.0), tile='main')   # v31 (user): the yard with the track texture (main dirt tile + dirt decals)   # v26 (user): light dirt yard on the other side of the start straight (north)
LIGHT_TRACK = (1.36, 1.44, 1.40)   # v28 (user): lighter again and less red than Saint-Thibery (sandy); v26 was 1.16   # v26 (user): the track dirt a bit lighter
SKY_FLAT = True   # v26 (user): no mountains in the background, fields
GROUND_PHOTO = dict(file='assets/sgm/fields.png', x0=-380.0, z0=-330.0, res=0.5, chunk=128.0, cell=8.0, lift=0.25)   # v27 (user): a few real
# fields round the ground (IGN BD ORTHO, Etalab 2.0), the photo stretched so the real track fits ours (scripts/sgm_fields.py)
PYLON_MODEL = 'pylon_round'   # v26 (user): round base, no logo (plain black; the 1st one plain red)
ROAD = dict(soft=6.0, tile=8)   # v24: the gravel tile; ROADS above   # v24 (user's drawing): one straight road from the start-area corner south, cutting the mounds
BUILDINGS = [dict(model='clubhouse', c=(252.0, 236.0), ang=130.0, half=(36.0, 36.0)),   # v28 (user): the mound cut back (z0 214 -> 278), the hall in the room, 2 storeys   # v26 (user): turned like the user's grey rectangle, flat roof
             dict(model='arch_tube', c=(161.6, 625.0), ang=5.0, half=(0.0, 0.0), cables=True, cable_out=25.0, cable_along=10.0),   # v28 (user): plain arch, black guy cables to the mounds
             dict(model='rider_gate', c=(319.3, 28.6), ang=168.0, half=(0.0, 0.0)),   # v30 (user's yellow rectangle): forward (towards the track) and askew   # v28 (user's yellow rectangle): turned round, beside the north end of the grid
             dict(model='hay_block', c=(59.9, 528.1), ang=70.0, half=(0.0, 0.0)),   # v30 (user's yellow line): between the 2 bumps of the small double, a bit askew   # v29: (48, 530) ang 90; the block at (0, -36.3) by the sign removed (user)
             dict(model='hay_block', c=(-28.0, 111.0), ang=0.0, half=(0.0, 0.0)),   # v29 (user's yellow squares): perpendicular to the west fence
             dict(model='hay_block', c=(-27.0, 290.0), ang=0.0, half=(0.0, 0.0)),
             dict(model='start_tarp', c=(337.4, 84.7), ang=-85.0, half=(0.0, 0.0)),   # v36 (user): parallel to the gate row and to the fence (now aligned too), right in front of it   # v36 (user): parallel to the fence (it was skewed 5 deg like the gate row: one end went behind the fence)   # v33 (user): stuck in front of the fence (fence at x 347.5)   # v31 (user): further back, behind the fence (the camera went behind it at the start)   # v30 (user): further back from the grids (v29 322.0, 84.7)   # v29 (user's photo): black net behind the grids + START / SX Tour / Shop Moto banner
             dict(model='scaffold_sign', c=(-12.0, -52.0), ang=180.0, half=(0.0, 0.0)),   # v29 (user's photo): sign structure behind the turn L1 -> top (logo to come)   # v28 (user): hay wall at the end of L1 (outside the turn L1 -> top, by the fence)   # v26 (user's yellow square): the 50 Factory rider gate (scripts/rider_gate.py)
             dict(model='f50_cylinder', c=(323.9, 19.0), ang=0.0, half=(0.0, 0.0)),
             dict(model='tractor_tank', c=(200.0, -56.0), ang=0.0, half=(23.0, 8.0))]   # v32 (user): black, bigger, bigger tank; the fire van removed   # v31 (user's red circle): the watering tractor + water tank in the yard   # v30 (user's yellow circle): beside the rider gate (v26-v29 (303, 29))   # v26 (user): white inflatable arch over the alley through the south mound   # v24 (user's grey square): a bigger hall
SOFT_FEET = dict(sigma=1.2, h=1.5)   # v22 (user: lines at the start of every bump): the bump feet rounded (no slope kink)
PYLON_GROUND = dict(mound=dict(h=0.75, r_flat=1.6, r=3.6), curb=dict(turns=(), h=0.35, r=2.6, w=0.9, ext_in=2.8, ext_out=1.0))
WIDE = {}

def rollers_table(h1=2.0, up1=12.0, v=0.6, pause=6.0, h2=3.3, rise=8.0, valley=2.0, down2=6.0, ht=7.2, smooth=1.2):
    """v2 (user): roller, roller, then the table without going down into the hole. v3: 1st rounder, 2nd 3.3, table 7.2.
    v4 (user, 2nd test): 1st roller less steep (longer round climb up1), a short pause after it (flat at v), the 2nd roller,
    then NO flat: a smooth raised valley (bottom `valley` ft) straight into the face of the table (Arlington g49_2 scaled to
    ht, taken from where its face reaches the valley level); the whole profile smoothed (gaussian, `smooth` ft)."""
    import compose
    from scipy.ndimage import gaussian_filter1d
    c = lambda n: (1 - np.cos(np.linspace(0, np.pi, n))) / 2
    t = compose.unit(TABLE_B)[1]; t = t * (ht / t.max()); i0 = int(np.nonzero(t >= valley)[0][0])
    p = np.r_[h1 * c(int(up1 / 0.1)), h1 - (h1 - v) * c(int(6.0 / 0.1)), np.full(int(pause / 0.1), v), v + (h2 - v) * c(int(rise / 0.1)),
              h2 - (h2 - valley) * c(int(down2 / 0.1)), t[i0:]]
    p = np.maximum(gaussian_filter1d(p, smooth / 0.1, mode='nearest'), 0.0); p[0] = 0.0; p[-1] = 0.0
    return ('raw', f'roller {h1:.1f}, pause, roller {h2:.1f}, transition, table {ht:.1f}', p, 'T')

def finish_jump(lip=5.6, lead=((4.0, 0.50),), s2=1.05, valley=3.2, drop=30.0, H=16.0, up_=22.0, top=4.0, down=38.0,
                back=10.0, vlow=1.0, kup=1.5):
    """v5 (user): hole FILLED between the take-off and the landing, landing 14.5 ft. Two items (the finish line goes on the
    lip of the first). v13 (user: "un plat puis une bosse", more link between the floor and the jump): a gentle lead-in
    (slope 0 -> 0.10 over 4 ft, -> 0.30 at 10 ft, ~1.4 ft up), then the ramp keeps steepening to s2 at the lip (same lip
    height, same kick at the top). v12: a short round foot (2.5 ft) then a ramp that kicks (~46 deg at the lip). v11: landing
    summit 12 ft further (drop 30). v8: landing climb steeper (22 ft). v14 (user): take-off back near the steep v12 one (it
    cuts the speed), only a slightly smoother foot (slope 0 -> 0.5 over 4 ft instead of 2.5); landing higher (14.5 -> 16 ft),
    same curve."""
    xs = [0.0] + [k[0] for k in lead]; ss = [0.0] + [k[1] for k in lead]
    h0 = sum((ss[k] + ss[k + 1]) / 2 * (xs[k + 1] - xs[k]) for k in range(len(xs) - 1))
    xs.append(xs[-1] + (lip - h0) / ((ss[-1] + s2) / 2)); ss.append(s2)
    x = np.arange(int(xs[-1] / 0.1) + 1) * 0.1; sl = np.interp(x, xs, ss)
    kick = np.r_[0.0, np.cumsum((sl[1:] + sl[:-1]) / 2 * 0.1)]; kick *= lip / kick[-1]
    c = lambda n_: (1 - np.cos(np.linspace(0, np.pi, n_))) / 2
    # v17 (user): the back of the take-off was flat: it now curves down like a real take-off (cosine over `back` ft to `vlow`),
    # then climbs smoothly onto the landing (c^kup: gentle at the bottom, steep near the top); summit at the same place
    rest = np.r_[lip - (lip - vlow) * c(int(back / 0.1))[1:], vlow + (H - vlow) * c(int((drop - back + up_) / 0.1))[1:] ** kup,
                 np.full(int(top / 0.1), H), H * (1 - c(int(down / 0.1)))]
    return [('raw', f'appel {lip:.1f} ft qui kicke', kick, 'T'), ('gap', 0.0), ('raw', f'trou comble, reception {H:.1f} ft', rest, 'T')]

def bump_table(h=3.3, up_=11.0, down_=6.0, valley=2.0, ht=6.6, smooth=1.2):
    """v12 (user): the 2nd bump of L2 FUSED into the table: cosine bump h, down to a slight dip (`valley` ft, not to the floor),
    straight into the face of the table (Arlington g49_2 scaled to ht, taken from where its face reaches the dip level), the
    whole profile smoothed: one smooth transition, the table a bit closer."""
    import compose
    from scipy.ndimage import gaussian_filter1d
    c = lambda n_: (1 - np.cos(np.linspace(0, np.pi, n_))) / 2
    t = compose.unit(TABLE_B)[1]; t = t * (ht / t.max()); i0 = int(np.nonzero(t >= valley)[0][0])
    p = np.r_[np.zeros(10), h * c(int(up_ / 0.1)), h - (h - valley) * c(int(down_ / 0.1)), t[i0:]]
    p = np.maximum(gaussian_filter1d(p, smooth / 0.1, mode='nearest'), 0.0); p[0] = 0.0; p[-1] = 0.0
    return ('raw', f'bosse {h:.1f} fusionnee, table {ht:.1f}', p, 'T')

def fill_between(toks, k, lev, e=0.5):
    """v14: lev may be a dict (hold, hold_h, down, low): the fill floor follows the user's drawing (plateau, small dip)."""
    """v13 (user): replace the block-k bump, the gap after it and the next block by ONE raw profile with the same shapes at the
    same places, the hole between the bump crest and the next crest filled up to `lev` ft (soft max, rounded corners)."""
    i = [j for j, t in enumerate(toks) if t[0] != 'gap'][k - 1]; assert toks[i + 1][0] == 'gap'
    p = np.asarray(L('tmp', toks[i:i + 3]), float); n2 = len(L('tmp', [toks[i]]))
    a, b_ = int(np.argmax(p[:n2])), n2 + int(np.argmax(p[n2:]))
    if isinstance(lev, dict):
        u = np.arange(b_ - a + 1) * 0.1; c_ = lambda t: (1 - np.cos(np.pi * np.clip(t, 0, 1))) / 2
        F = np.where(u < lev['hold'], p[a] + (lev['hold_h'] - p[a]) * u / lev['hold'], lev['hold_h'] - (lev['hold_h'] - lev['low']) * c_((u - lev['hold']) / lev['down']))
    else: F = lev
    q = p.copy(); seg = p[a:b_ + 1]; q[a:b_ + 1] = (seg + F + np.sqrt((seg - F) ** 2 + e * e)) / 2
    q[a:b_ + 1] -= np.linspace(q[a] - p[a], q[b_] - p[b_], b_ - a + 1)          # no step at the two crests
    if not isinstance(lev, dict):                # v19 (user): the flat -> table transition more progressive (was abrupt)
        from scipy.ndimage import gaussian_filter1d
        kf = a + int(np.nonzero(p[a:b_ + 1] <= lev)[0][-1]); u_ = (np.arange(len(q)) - kf) * 0.1
        w_ = np.where(np.abs(u_) < 12.0, (1 + np.cos(np.pi * u_ / 12.0)) / 2, 0.0); q = q * (1 - w_) + gaussian_filter1d(q, 4.5 / 0.1) * w_
    print('L2 fill: bump crest -> table crest %.1f ft' % ((b_ - a) * 0.1))
    return toks[:i] + [('raw', 'bosse, plateau, petit creux, table', q, 'T')] + toks[i + 3:]

L2_TRIPLE = dict(mid=5.8, shift=12.0, low=3.0)   # v30 (user): dug more between the 2nd and 3rd (valley 4.2 -> 3.0)   # v29 (user): L2 big SX triple, middle 6.5 -> 5.8 ft, 12 ft closer to the 3rd, fused (valley 4.2)

def big3_top(shift=10.0, low=3.6, tm=0.45, toks=None, name='triple haut'):
    """v15 (user's drawing on the top-lane triple): 1st and 3rd bumps unchanged; the middle bump keeps its shape (same slope)
    but comes `shift` ft later, flat ground before it. v17 (user): the last two bumps 10 ft further apart (shift 20 -> 10, crests
    ~40 ft apart) and the hole filled smoothly, round then round: from the middle crest a cosine down to `low` ft (at `tm` of the
    way) and a cosine up to the 3rd crest, zero slope at both crests and at the bottom (no flat). Same length as BIG3."""
    toks = toks or BIG3
    p = np.asarray(L('tmp', toks), float); n1 = len(L('tmp', toks[:1])); n2 = len(L('tmp', toks[:3]))
    v1 = n1 - 5 + int(np.argmin(p[n1 - 5:n1 + 5])); v2 = n2 - 5 + int(np.argmin(p[n2 - 5:n2 + 5]))
    m = p[v1:v2 + 1].copy(); q = p.copy(); q[v1:v2 + 1] = np.minimum(q[v1:v2 + 1], np.linspace(p[v1], p[v2], v2 - v1 + 1))
    k = int(round(shift / 0.1)); ms = np.zeros_like(p); ms[v1 + k:v2 + k + 1] = m[:max(0, len(p) - v1 - k)][:v2 - v1 + 1]
    q = np.maximum(q, ms); ic = v1 + k + int(np.argmax(m)); i3 = v2 + int(np.argmax(p[v2:]))
    t = np.arange(i3 - ic + 1) / (i3 - ic)
    F = np.where(t < tm, low + (q[ic] - low) * (1 + np.cos(np.pi * t / tm)) / 2,
                 low + (q[i3] - low) * (1 - np.cos(np.pi * (t - tm) / (1 - tm))) / 2)
    q[ic:i3 + 1] = F
    print('%s: middle crest moved %.0f ft, crests %.1f ft apart, valley %.1f ft' % (name, shift, (i3 - ic) * 0.1, low))
    return ('raw', f'{name}: bosse du milieu fusionnee, creux arrondi {low:.1f}', q, 'T')

FUSE_L1 = dict(shift=12.0, low=2.2)   # v28 (user, photo 12): L1 central triple, middle bump 12 ft closer to the 3rd, valley 2.2 ft

def fuse_pair(a, g, b, shift=12.0, low=2.2, tm=0.45):
    """v28 (user: "rapproche la bosse du milieu et smooth les deux, comme le triple du haut"): bump a then gap g then bump b; a
    keeps its shape but comes `shift` ft later (flat ground before it), then round-round as big3_top: a cosine from a's crest
    down to `low` (at `tm` of the way) and up to b's crest, zero slope at both crests. Same length as [a, gap g, b]."""
    pa = np.asarray(L('tmp', [a]), float); p = np.asarray(L('tmp', [a, ('gap', g), b]), float); na = len(pa); ng = int(round(g / 0.1))
    k = int(round(shift / 0.1)); q = p.copy(); q[:na] = 0.0; sh = np.zeros_like(p); sh[k:k + na] = pa[:max(0, len(p) - k)][:na]
    q = np.maximum(q, sh); ic = k + int(np.argmax(pa)); ib = na + ng + int(np.argmax(p[na + ng:]))
    t = np.arange(ib - ic + 1) / (ib - ic)
    q[ic:ib + 1] = np.where(t < tm, low + (q[ic] - low) * (1 + np.cos(np.pi * t / tm)) / 2, low + (q[ib] - low) * (1 - np.cos(np.pi * (t - tm) / (1 - tm))) / 2)
    print('L1 central triple: middle crest moved %.0f ft, crests %.1f ft apart, valley %.1f ft' % (shift, (ib - ic) * 0.1, low))
    return ('raw', f'triple central L1: bosse du milieu fusionnee, creux {low:.1f}', q, 'T')

def round_crest(tok, sm=1.3, half=6.0):
    """v16 (user): the crest of a bump a bit rounder: gaussian (`sm` ft) blended in over +-`half` ft around the crest, the
    crest height kept, the rest of the profile unchanged."""
    from scipy.ndimage import gaussian_filter1d
    p = np.asarray(L('tmp', [tok]), float); k = int(np.argmax(p)); g = gaussian_filter1d(p, sm / 0.1, mode='nearest')
    u = (np.arange(len(p)) - k) * 0.1; w = np.where(np.abs(u) < half, (1 + np.cos(np.pi * u / half)) / 2, 0.0)
    q = p * (1 - w) + g * w; q += (p[k] - q.max()) * w
    return ('raw', 'recep fusionnee, sommet arrondi', q, 'T')

def smooth_takeoff(H, up_, n, back, sm, pad=None):
    """v11 (user): a normal, smooth take-off: concave face H (x / up_)^n, lip slightly rounded (gaussian sm ft), cosine back."""
    from scipy.ndimage import gaussian_filter1d
    x = np.arange(int(up_ / 0.1) + 1) * 0.1; face = H * (x / up_) ** n
    bk = H * (1 + np.cos(np.linspace(0, np.pi, int(back / 0.1)))) / 2
    pad = np.zeros(int((2 * sm if pad is None else pad) / 0.1) + 1); p = np.r_[pad, face, bk[1:], pad]
    p = gaussian_filter1d(p, sm / 0.1, mode='nearest'); p = np.maximum(p - p[0], 0) * (H / (p.max() - p[0])); p[0] = p[-1] = 0.0
    return ('raw', f'appel normal {H:.1f} ft', p, 'T')

def whoops_up(n, k):
    """v4 (user): the same whoops, every crest a bit higher (x k): a bit harder to pass."""
    import compose
    return ('raw', f'whoops Custom_0 x{n} (x{k:.2f})', compose.whoops('Custom_0', n) * k, 'W')

def evenly(blocks, lane, u0, end):
    """v2 (user): the SAME gap between every bump of the lane (no "triple, flat, triple"). blocks: list of token lists kept
    as they are inside (fused bumps, the big SX triple with its own gaps); one equal gap between consecutive blocks."""
    ln = [len(L('tmp', b)) * 0.1 for b in blocks]; g = (lane - u0 - end - sum(ln)) / max(1, len(blocks) - 1)
    toks = []
    for k, b in enumerate(blocks):
        toks += list(b)
        if k < len(blocks) - 1: toks.append(('gap', round(g, 1)))
    return toks, g

def top_u():
    """v3 (user): the top U a bit further east, a REAL half turn, its end cut. v4 (user, 2nd test): a TIGHT half turn, only
    the very exit cut: right arc A1 (radius R1) then a tight right arc of 180 - A1 (R2), with
    R1 (1 - cos A1) + R2 (1 + cos A1) = ZS - ZT. Returns (R1, R2, x where the start straight begins)."""
    A1, R2 = np.radians(TOP_A1), 6.0; R1 = ((ZS - ZT) - R2 * (1 + np.cos(A1))) / (1 - np.cos(A1))
    return R1, R2, XU + np.sin(A1) * (R1 - R2)

def track():
    ox, oz = STT_ORIGIN; R1, R2, XS = top_u()
    p = Path(ox + XS, oz + ZS, 180.0, 'SGM')                                  # start straight, westbound
    p.straight(XS - (X['L2'] + R_ST), [], tag='start straight')
    p.turn(+90, R_ST, BIG, tag='start -> L2 (wider, low berm)')   # v5 (user): the first turn wider
    l2_len = Z_U23 - (ZS + R_ST)
    big3_l2 = [('scale', 'Custom1_g29_2', 8.5), ('gap', 0.5), ('scale', 'Custom1_g29_3', L2_TRIPLE['mid']), ('gap', 1.6), ('scale', 'Arlington_g29_2', 8.3)]
    big3_l2 = [big3_top(shift=L2_TRIPLE['shift'], low=L2_TRIPLE['low'], toks=big3_l2, name='triple L2')]   # v29 (user): middle closer to the 3rd, fused, a bit lower
    # v5 (user): just a small roller, further on a bump, further on a table, then the big triple (same gap)
    # v6 (user, 4th test): a bump was missing after the table, before the big triple
    # v9 (user): table a bit lower (7.2 -> 6.6); more run-up between the bump and the big triple (+8 ft, the U 8 ft further)
    L2_RUN = 8.0
    l2, g2 = evenly([[('scale', ROLLER, 1.8)], [('scale', SA[1], 3.3)], [('scale', TABLE_B, 6.6)], [SA[2]], [('scale', ROLLER, 1.8)], big3_l2], l2_len - L2_RUN, 4.0, 8.0)   # v17 (user): one more roller after the bump, before the big triple   # v13 (user): v11 spacing back
    l2 = fill_between(l2, 2, L2_FILL)
    # v19 (user): the bump after the table and the roller closer (gaps 4 -> 1.5 ft), the roller smaller and rounder (1.8 -> 1.3 ft);
    # the room saved goes before the big triple (it does not move)
    assert l2[3][0] == 'gap' and l2[5][0] == 'gap' and l2[6][0] == 'scale' and l2[7][0] == 'gap'
    sv = (l2[3][1] - 1.5) + (l2[5][1] - 1.5); l2[3] = ('gap', 1.5); l2[5] = ('gap', 1.5)
    l2[6] = round_crest(('scale', ROLLER, 1.3), sm=2.5, half=9.0)   # v13 (user): same gaps and same table face as v11, the hole between the bump and the table partly filled   # v12 (user): the bump fused into the table (slight dip, smooth)
    k_ = len(l2) - len(big3_l2) - 1; assert l2[k_][0] == 'gap'; l2[k_] = ('gap', round(g2 + L2_RUN + sv, 1))   # v7 (user): 2nd bump a bit lower (3.7 -> 3.3)   # v2: same gap everywhere
    p.straight(l2_len, [rounded(sec('SGM-L2 roller, bosse, table, gros triple', l2, 4.0), interior=False)],
               tag='L2 rollers + table, bump, big triple')
    p.turn(+(180 - L3_SKEW), RB, BIG, tag='U L2 -> L3 (berm)')   # v12: the U turns straight onto the L3 heading (no flat bend): the double right at its exit
    # v3 (user's plan): L3 runs slightly askew (a few deg to the right going up), not parallel to L4; the hairpin is a real
    # half turn but more open (R_HP) so L3 and L4 do not touch. L3 straight ends where the hairpin top lands on ZH.
    a3 = np.radians(L3_SKEW)   # v7: R 60 -> 20, the double even closer to the U exit   # v6: tighter (R 200 -> 60): the double closer to the U exit
    # v3 (user): a normal double right at the turn exit; finish: steep low take-off, a flat, a big but short landing mound
    # v4 (user): the double right at the turn exit, a bit bigger and above all longer; less room before the finish jump
    # v5 (user, 3rd test): the double even more at the turn exit, less room before the finish jump, and the hairpin turns
    # shorter (earlier): the L3 straight is now as long as its content (+ 8 ft before the hairpin), the hairpin follows
    FIN = finish_jump()
    dbl = [smooth_takeoff(4.0, 10.0, 1.8, 9.0, 0.8, pad=0.4), ('gap', 24.5),   # v14 (user): landing peak at 57 ft (was 48.5)   # v13 (user): landing a bit further (13.5 -> 16)   # v12 (user): even more at the exit, kicks a bit more (lip ~36 deg)
           ('stretch', SA[2], 5.4, 1.5)]   # v11 (user): a normal take-off (the kick was a flat + a round top)   # v9 (user): a bit bigger, above all the landing higher (4.5 -> 5.4)   # v8 (user): smoother take-off out of the turn (concave foot, no wall)   # v6 (user): 1st bump lower and less steep (it threw riders straight into the finish)   # v5 (user): more dirt on the landing of the double
    # v7 (user's plan): L3 goes up to the black line again (hairpin top at ZH, its berm ends at the start corridor edge):
    # much more room between the double and the finish jump, finish jump longer
    z3 = ZH + R_HP * (1 - np.sin(a3)); l3_len = (p.z - oz - z3) / np.cos(a3)
    g3 = l3_len - U3 - 8.0 - (len(L('tmp', dbl)) + len(L('tmp', FIN))) * 0.1
    l3 = dbl + [('gap', round(g3, 1))] + FIN                                   # finish jump ends 8 ft before the hairpin
    # v17 (user): the take-off 1 m narrower on the LEFT (the landing wider than the take-off), back to full width by the
    # bottom of its back side; wooden barriers climbing along the left edge of the landing face, up to its top; a cone at the
    # left of the take-off foot (on-board photos)
    uf = (len(L('tmp', dbl)) * 0.1 + round(g3, 1)); kl = len(FIN[0][2]) * 0.1; rest = FIN[2][2]
    SIDE_CUT[FINISH_SEC] = dict(a=(uf, uf + kl + 10.0 + 16.0), w=6.6, fade=16.0, side=-1)   # v26 (user: a ledge where the cut ended): faded over 16 ft   # v20 (user): one more metre off the left (3.3 -> 6.6 ft)
    dl = np.array([np.cos(np.radians(-90 + L3_SKEW)), np.sin(np.radians(-90 + L3_SKEW))]); rgt = np.array([-dl[1], dl[0]])
    o3 = np.array([p.x, p.z]); i_low = int(np.argmin(rest[:int(30.0 / 0.1)])); i_top = int(np.argmax(rest))
    ua = uf + kl + (i_low + int(np.argmax(rest[i_low:] >= 1.5))) * 0.1; ub = uf + kl + i_top * 0.1
    nb = max(1, int(np.ceil((ub - ua) / 8.0))); stp = (ub - ua) / nb
    del PROPS[:]; del RAILS[:]
    # v19 (user: they did not touch the ground, the last post was missing): ONE barrier mesh following the ground, posts at both ends
    RAILS.append(dict(line=[tuple(map(float, o3 + dl * u_ - rgt * 15.0)) for u_ in np.arange(ua, ub + 0.01, 1.0)],
                      origin=tuple(map(float, o3 + dl * (ua + ub) / 2 - rgt * 26.0))))
    del WALLS[:]; ow_ = CONCRETE_WALL['off']; hb_ = CONCRETE_WALL.get('h_end', 2.6)   # v31 (user): both faces of the mound, stopped before it ends
    i0_ = i_low + int(np.argmax(rest[i_low:] >= hb_)); i1_ = i_top + int(np.argmax(rest[i_top:] < hb_)) - 1
    ua_w = uf + kl + i0_ * 0.1; ub_w = uf + kl + i1_ * 0.1; WALL_TOP[:] = [float(uf + kl + i_top * 0.1)]
    ST_ = CONCRETE_WALL.get('stair')
    if ST_:                                        # v34: the stair end (layers at the top -> one less every step past u0)
        lt_ = int(np.ceil((float(rest.max()) - 1.0) / 2.62)); u0s_ = WALL_TOP[0] + ST_['after']
        WALL_STAIR.update(u0=float(u0s_), ltop=lt_, step=ST_['step']); ub_w = min(ub_w, u0s_ + lt_ * ST_['step'])
    WALLS.append(dict(line=[tuple(map(float, o3 + dl * u_ - rgt * ow_)) for u_ in np.arange(ua_w, ub_w + 0.01, 1.0)],
                      origin=tuple(map(float, o3 + dl * (ua_w + ub_w) / 2 - rgt * (ow_ + 9.0))), o=tuple(map(float, o3)), dl=tuple(map(float, dl)),
                      rgt=tuple(map(float, rgt)), u=(float(ua_w), float(ub_w))))
    c_ = o3 + dl * (uf - 13.0) - rgt * (15.2 - SIDE_CUT[FINISH_SEC]['w'] + 1.8)   # v22 (user): the cone 4 m before the take-off
    PROPS.append(dict(model='cone_orange', x=float(c_[0]), z=float(c_[1]), f=(float(dl[0]), float(dl[1]))))
    p.straight(l3_len, [rounded(sec(FINISH_SEC, l3, U3), interior=False)], tag='L3 double, finish jump')
    # v8 (user): the whoops lane askew too, PARALLEL to L3 (a full 180: heading 95 deg, it drifts west going down)
    p.turn(-180, R_HP, BIG2, tag='hairpin L3 -> L4 (berm)')
    a4 = np.radians(L3_SKEW); l4_len = ((ZB - RS * (1 - np.sin(a4))) - (p.z - oz)) / np.cos(a4)
    # v4 (user): same whoops a bit higher; same room before the triple; triple smaller (less take-off), 2nd bump tiny,
    # landing flat and round (back side stretched x1.8)
    W_ = [whoops_up(10, 1.15)]                                               # v8 (user): one more (9 + the first, smaller one)                                                # v7 (user): 9 whoops                                              # v6 (user): 10 whoops                                                # v5 (user): 9 whoops
    T_ = [('scale', SA[3], 3.9), ('gap', 2.5), ('scale', SA[4], 2.3), ('gap', 3.5), ('stretch', SA[5], 4.0, 1.3)]   # v10 (user): shorter (1st -> 2nd 4.5 -> 2.5, 2nd -> 3rd 4.5 -> 3.5)   # v9 (user): shorter (gaps 5.3 -> 4.5, landing x1.5 -> 1.3)   # v6: a bit shorter (gaps 6.5 -> 5.3, landing x1.8 -> 1.5)   # v5 (user): triple bumps higher
    g4 = 27.0                                                                   # v3: whoops start 10 ft after the turn
    p.straight(l4_len, [sec('SGM-L4 whoops, triple', W_ + [('gap', round(g4, 1))] + T_, U4)], tag='L4 whoops, triple')   # v9 (user): whoops earlier, more run-up to the triple (gap 16 -> 24)   # v5b (user): whoops right at the hairpin exit
    p.turn(-(90 - L3_SKEW), RS, SMALL, tag='L4 -> bottom (small berm)')
    b_len = (p.x - ox) - (X['L1'] + RS)
    bot = [smooth_takeoff(2.4, 12.0, 1.6, 9.0, 1.2), ('gap', 20.0), ('scale', SA[1], 3.2)]   # v11 (user): take-off smoother (was too abrupt)   # v10 (user): both bumps turned around too   # v9 (user): the two bumps swapped: take-off lower, landing higher   # v8 (user): take-off less steep, more dirt, a bit bigger   # v7 (user): take-off a bit steeper; same gap   # v6b (user): a bit lower, right at the turn exit, the 2nd bump moved back (gap 9 -> 24 ft)
    p.straight(b_len, [sec('SGM-bas petit double', bot, b_len - 10.0 - len(L('tmp', bot)) * 0.1)], tag='bottom very small double')   # v14 (user): the whole double 4 ft back (6 -> 10 ft before the turn)   # v8: as late as possible = more run-up   # v7 (user): moved towards the next turn, landing 8 ft before it
    p.turn(-90, RS, SMALL, tag='bottom -> L1 (small berm, a bit bigger)')
    l1_len = (ZB - RS) - (ZT + RB)
    # v3 (user): 1st bump a bit higher, 2nd moved back, 3rd much higher (fused 2nd/3rd); then bigger bumps (Saint-Thibery L2
    # size, a bit smaller): triple, triple on a table, off - same gap between every bump
    # v4 (user): 1st take-off lower on the right than on the left (inside rut line), 7 ft out of the berm (was 4);
    # rhythm bumps bigger again, above all the 1st and 2nd after the 1st triple
    tri1 = [('split', ('scale', SA[0], 4.3), ('scale', SA[0], 3.4)), ('fuse', TABLE_B, 3.6, 6.4, 2.0, 37.0, 0.55)]   # v11 (user): entry triple, 3rd higher (5.5 -> 6.4), 2nd further from it, still fused (span 32 -> 37)   # v5 (user): 3rd bump a bit lower (6.2 -> 5.5)
    tri1[1] = round_crest(tri1[1], sm=3.0, half=9.0)   # v16 (user): the 6.4 ft crest of the fused landing a bit rounder
    blocks = [[tri1[0]], [tri1[1], ('gap', L1_Q4)] + up([SA[0]], 1.4)] + [[u] for u in up([SA[1]], 1.35) + up([SA[2]], 1.2) + up([SA[3]], 1.25) + [('scale', SA[4], 4.2)]] + [[TABLE_B, ('gap', L1_OFF), ('scale', SA[0], 3.5)]]
    # v29 (user): L1 back as before (v28 fused its central triple by mistake: the user meant the L2 big SX triple)   # v9 (user): last bump closer to the table (jump on / jump off)   # v6b (user): last bump a bit lower (4.0 -> 3.5)
    # v6: the same gap everywhere but at most L1_GAP ft (the lane got longer for the 10 whoops): the rest goes before the
    # first take-off (more room out of the turn), the last bump still ends 8 ft before the turn
    body = sum(len(L('tmp', b_)) * 0.1 for b_ in blocks); g1 = min(L1_GAP, (l1_len - 7.0 - 8.0 - body) / (len(blocks) - 1))
    u1 = l1_len - 8.0 - body - g1 * (len(blocks) - 1); l1, g1 = evenly(blocks, l1_len, u1, 8.0)
    p.straight(l1_len, [rounded(sec('SGM-L1 triple recep fusionnee, triple, triple sur table, off', l1, u1), full=0.3, lead_in=True, R_in=15.0)],
               tag='L1 triple (fused landing), triple, triple on table, off')
    p.turn(-90, RB, BIG, tag='L1 -> top (berm, a bit lower)')
    t_len = XU - (X['L1'] + RB)
    # v3 (user): big triple right at the turn exit, room, then a roller just before the U
    RL = ('scale', ROLLER, 2.6)                                                 # v4 (user): a small roller jumped into the turn
    Lt = len(L('tmp', BIG3)) * 0.1; Lr = len(L('tmp', [RL])) * 0.1
    top = [big3_top()] + [('gap', round(t_len - 12.0 - 3.0 - Lt - Lr, 1)), RL]   # v15 (user's drawing): middle bump later, fused into the 3rd
    p.straight(t_len, [rounded(sec('SGM-haut gros triple SX, roller', top, 12.0), interior=False, lead_in=True)], tag='top big SX triple, roller')
    p.turn(-TOP_A1, R1, BIG, tag='top U (real half turn)')   # its berm only on the first part (BERM_SHIFT): the start runs past the rest
    p.turn(-(180 - TOP_A1), R2, None, tag='top U (cut end, tight, flat)')
    _start(KEY, ox, oz, gate=START_GATE, heading=START_HEADING,
           route=[('S', 30.0), ('TO', (X['L2'] + R_ST + 12.0, ZS))],   # v7 (user's black line): the start corridor stays wide down to the first turn
           narrow=[(0.0, None), (30.0, None), (240.0, 44.0)], end_w=44.0,
           finish=(FINISH_SEC, 2))
    return p

stt = track
