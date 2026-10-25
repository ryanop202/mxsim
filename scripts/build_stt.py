"""Saint-Thibéry: its own terrain (same grid as the USLAND compound: 4097 px at 0.28975 ft), rendered exactly like
build_sx.py (measured lane units, JGSX berm stamps, max of the layers). Writes build/stt_H.npy, build/stt_tiles.npy,
build/stt_report.json. Track map only for now (not exported to a game folder).
Run: python3 scripts/build_stt.py"""
import os, sys, json
ROOT = os.environ.get('MXSIM_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
import numpy as np
from engine import Grid, render_split, render_lane_block, render_berm_stamp, turn_mid_angle, LIB, berm_ang_scale
import layouts_sx as LS
import layouts_stt as LT

OUT = ROOT + '/build'; os.makedirs(OUT, exist_ok=True)
G = Grid(11, 0.28975); N = G.N; S = G.s
TW = LIB['sx_lateral']['top_width']
T_MAIN, T_JUMP, T_WHOOP, T_BERM = range(4)

def build():
    jumps = np.zeros((N, N)); whoops = np.zeros((N, N)); berms = np.zeros((N, N))
    p = LT.stt(); secs, turns = [], []
    for g in p.segs:
        if g['kind'] == 'S':
            for prof, u0, name in g['sections']:
                render_lane_block(G, whoops if 'whoops' in name else jumps, g, prof, u0, TW)
                for sp in LS.SPLITS.get(name, []): render_split(G, jumps, g, sp, u0, TW)
                secs.append(dict(lane=g['tag'], name=name, s0=g['s0'] + u0, length=len(prof) * 0.1, hmax=float(prof.max()),
                                 items=LS.COMBOS[name]['items']))
        elif g['kind'] == 'T':
            if g.get('berm') and g.get('tag') in getattr(LT, 'HALF_BERM', ()):
                # v4: berm only on the second half of the turn (user's drawing): fade in between 45 % and 60 % of the turn
                tmp = np.zeros((N, N)); sl = render_berm_stamp(G, tmp, g['berm'], g['cx'], g['cz'], turn_mid_angle(g), ang_scale=berm_ang_scale(g['berm'], g['ang']))
                smp = p.samples(0.5); k0 = int(np.argmin(np.abs(smp['s'] - g['s0'])))
                phi0 = np.arctan2(smp['z'][k0] - g['cz'], smp['x'][k0] - g['cx']); sgn = -np.sign(g['ang'])     # left turn: heading (and angle) decreases
                jj, ii = np.meshgrid(np.arange(sl[1].start, sl[1].stop), np.arange(sl[0].start, sl[0].stop))
                phi = np.arctan2(ii * S - g['cz'], jj * S - g['cx']); rel = np.angle(np.exp(1j * (phi - phi0))) * sgn
                u = rel / np.radians(abs(g['ang'])); w = np.clip((u - 0.45) / 0.15, 0, 1); w = w * w * (3 - 2 * w)
                gain = getattr(LT, 'BERM90_GAIN', 1.0) if abs(abs(g['ang']) - 90) < 1 else 1.0
                berms[sl] = np.maximum(berms[sl], tmp[sl] * w * gain)
            elif g.get('berm') and abs(abs(g['ang']) - 90) < 1 and getattr(LT, 'BERM90_GAIN', 1.0) != 1.0:
                tmp = np.zeros((N, N)); sl = render_berm_stamp(G, tmp, g['berm'], g['cx'], g['cz'], turn_mid_angle(g), ang_scale=berm_ang_scale(g['berm'], g['ang']))
                berms[sl] = np.maximum(berms[sl], tmp[sl] * LT.BERM90_GAIN)          # v6: 90 deg berms higher (user)
            elif g.get('berm'): render_berm_stamp(G, berms, g['berm'], g['cx'], g['cz'], turn_mid_angle(g), ang_scale=berm_ang_scale(g['berm'], g['ang']))
            turns.append(dict(tag=g['tag'], angle=g['ang'], r=g['r'], berm=g.get('berm')))
    H = np.maximum.reduce([jumps, whoops, berms])
    TN = 2 ** 11; t = lambda a: a[:-1:2, :-1:2][:TN, :TN]
    tiles = np.full((TN, TN), T_MAIN, np.uint8)
    tiles[t(jumps) > 0.05] = T_JUMP; tiles[t(whoops) > 0.05] = T_WHOOP; tiles[t(berms) > 0.05] = T_BERM
    rep = dict(lap_ft=p.s, sections=secs, turns=turns, start=LS.STARTS['STT'])
    np.save(f'{OUT}/stt_H.npy', H.astype(np.float32)); np.save(f'{OUT}/stt_tiles.npy', tiles)
    json.dump(rep, open(f'{OUT}/stt_report.json', 'w'), indent=1, default=float)
    return H, p, rep

if __name__ == '__main__':
    H, p, rep = build()
    print('Saint-Thibery : tour %.0f ft, H max %.2f ft, %d sections, %d virages' % (p.s, H.max(), len(rep['sections']), len(rep['turns'])))
