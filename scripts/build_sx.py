"""v3: SX-only compound. One terrain (4097 px at 0.28975 ft = the JGSX reference grid), three track folders.
python3 build_sx.py && python3 export_sx.py && python3 validate_sx.py
"""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import os, sys, json, numpy as np
sys.path.insert(0, ROOT + '/scripts')
from engine import Grid, render_lane_block, render_berm_stamp, turn_mid_angle, LIB, render_stamp
import layouts_sx as LS

OUT = ROOT + '/build'; os.makedirs(OUT, exist_ok=True)
G = Grid(11, 0.28975); N = G.N; S = G.s
TW = LIB['sx_lateral']['top_width']
# tile indices: order must match export_sx.TILES
T_MAIN, T_JUMP, T_WHOOP, T_BERM, T_SANDSTRAIGHT, T_SANDBUMP, T_SANDEXIT, T_SANDSOLO = range(8)
TILE_NAMES = ['SX Main', 'Jumps Sx', 'WhoopsV2', 'Berm Exit Sx', 'Sand Straight', 'Sand Bump Straight', 'Sand Exit', 'Sand Bump Solo']
# Glendale tile ids inside the sand stamps -> ours (names checked in sand_stamps.json)
GLENDALE_TILES = {10: T_SANDEXIT, 12: T_SANDSOLO, 3: T_JUMP, 1: T_BERM}

jumps = np.zeros((N, N)); whoops = np.zeros((N, N)); berms = np.zeros((N, N)); sand = np.zeros((N, N))
full_tiles = np.full((N, N), 255, np.int16)   # tiles coming from the sand stamps (full resolution, 255 = none)
report = {}
paths = {'SX1': LS.sx1(), 'SX2': LS.sx2(), 'SX3': LS.sx3()}
for key, p in paths.items():
    secs = []; turns = []
    for g in p.segs:
        if g['kind'] == 'S':
            for prof, u0, name in g['sections']:
                render_lane_block(G, whoops if 'whoops' in name else jumps, g, prof, u0, TW)
                secs.append(dict(lane=g['tag'], name=name, s0=g['s0'] + u0, length=len(prof) * 0.1, hmax=float(prof.max())))
        elif g['kind'] == 'P':
            render_stamp(G, sand, full_tiles, g, GLENDALE_TILES)
            turns.append(dict(tag=g['tag'], kind='Glendale sand stamp', angle=float(np.degrees(g['t_out'] - g['t_in'])), berm=g['stamp']))
        else:
            if g.get('berm'): render_berm_stamp(G, berms, g['berm'], g['cx'], g['cz'], turn_mid_angle(g))
            turns.append(dict(tag=g['tag'], kind='turn', angle=g['ang'], r=g['r'], berm=g.get('berm')))
    report[key] = dict(lap_ft=p.s, sections=secs, turns=turns, start=LS.STARTS[key])
H = np.maximum.reduce([jumps, whoops, berms, sand])
TN = 2 ** 11
def t(a): return a[:-1:2, :-1:2][:TN, :TN]
tiles = np.full((TN, TN), T_MAIN, np.uint8)
tiles[t(jumps) > 0.05] = T_JUMP; tiles[t(whoops) > 0.05] = T_WHOOP; tiles[t(berms) > 0.05] = T_BERM
ft = t(full_tiles); tiles[ft != 255] = ft[ft != 255].astype(np.uint8)       # Glendale sand tiles (channel floor included)
report['tiles'] = {n: int((tiles == i).sum()) for i, n in enumerate(TILE_NAMES)}
report['combos'] = {k: dict(length=v['length'], items=v['items']) for k, v in LS.COMBOS.items()}
np.save(f'{OUT}/H.npy', H.astype(np.float32)); np.save(f'{OUT}/tiles.npy', tiles)
json.dump(report, open(f'{OUT}/build_report.json', 'w'), indent=1, default=float)
print('H range', round(H.min(), 3), round(H.max(), 3), {k: round(v['lap_ft']) for k, v in report.items() if isinstance(v, dict) and 'lap_ft' in v}, report['tiles'])
