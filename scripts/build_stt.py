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

def render_split_blend(grid, out, seg, split, u0, top_width, band=10.0):
    """v10: double line rendered as ONE block whose height goes smoothly from the left half to the right half over a band
    in the middle (engine.render_split leaves a step when the halves differ: "la premiere bosse pas tres smooth")."""
    from engine import sx_wall
    st, pl, pr = split; prof = np.maximum(pl, pr); L = len(prof) * 0.1; c, s_ = np.cos(seg['t']), np.sin(seg['t'])
    half = top_width / 2 + 8.0; u0 = u0 + st
    pts = np.array([(seg['x0'] + uu * c - vv * s_, seg['z0'] + uu * s_ + vv * c) for uu in (u0, u0 + L) for vv in (-half, half)])
    sl, X, Z = grid.window(pts[:, 0].min(), pts[:, 0].max(), pts[:, 1].min(), pts[:, 1].max())
    dx, dz = X - seg['x0'], Z - seg['z0']; u = dx * c + dz * s_ - u0; v = -dx * s_ + dz * c
    a = np.interp(u / 0.1, np.arange(len(pl)), pl, left=0, right=0); b = np.interp(u / 0.1, np.arange(len(pr)), pr, left=0, right=0)
    w = np.clip(v / band + 0.5, 0, 1); w = w * w * (3 - 2 * w)                       # v > 0 = right of the riding direction
    h = (a * (1 - w) + b * w) * sx_wall(np.abs(v) - top_width / 2)
    out[sl] = np.maximum(out[sl], h)

def extras():
    """v13: start platform (gates + grates on it, descent right after the gate line) and the freestyle ramp beside the
    wheel tap (steel-like: near-vertical sides). Shapes asked by the user in game tests, not measured units."""
    import compose
    E = np.zeros((N, N)); ox, oz = LT.STT_ORIGIN; st = LS.STARTS['STT']
    P = getattr(LT, 'START_PLATFORM', None)
    if P:
        gx, gz = LT.START_GATE[0] + ox, LT.START_GATE[1] + oz
        a = np.radians(LT.START_HEADING); c, s_ = np.cos(a), np.sin(a); half = (LS.N_GATES - 1) / 2 * LS.GATE_PITCH + P['side']
        r = P['back'] + P['edge'] + half + P['front'] + P['down'] + 5
        sl, X, Z = G.window(gx - r, gx + r, gz - r, gz + r); u = (X - gx) * c + (Z - gz) * s_; v = -(X - gx) * s_ + (Z - gz) * c
        uu = np.clip((u - P['front']) / P['down'], 0, 1)
        down = (1 + np.cos(np.pi * uu)) / 2
        if P.get('lin'):                                   # v15: straight descent with rounded ends (fillets lin ft)
            Ld, f = P['down'], P['lin']; x = np.clip(u - P['front'], 0, Ld); m = 1.0 / (Ld - f)
            down = 1 - np.where(x < f, m * x * x / (2 * f), np.where(x > Ld - f, 1 - m * (Ld - x) ** 2 / (2 * f), m * (x - f / 2)))
        prof = np.where(u <= P['front'], np.clip((u + P['back'] + P['edge']) / P['edge'], 0, 1), down)
        lat = np.clip((half + P['edge'] - np.abs(v)) / P['edge'], 0, 1)
        E[sl] = np.maximum(E[sl], P['h'] * prof * lat)
    R = getattr(LT, 'FMX_RAMP', None)
    if R:
        k = compose.lane([('cut', 'Detroit_g31_1', R['H'], 0.9)])[0]; il = int(np.argmax(k)) * 0.1
        lx, lz = R['lip'][0] + ox, R['lip'][1] + oz
        d = np.array([R['aim'][0] - R['lip'][0], R['aim'][1] - R['lip'][1]]); d /= np.linalg.norm(d)
        x0, z0 = lx - d[0] * il, lz - d[1] * il; L = len(k) * 0.1; w = R['width'] / 2 + R['side'] + 1
        sl, X, Z = G.window(min(x0, x0 + d[0] * L) - w, max(x0, x0 + d[0] * L) + w, min(z0, z0 + d[1] * L) - w, max(z0, z0 + d[1] * L) + w)
        u = (X - x0) * d[0] + (Z - z0) * d[1]; v = -(X - x0) * d[1] + (Z - z0) * d[0]
        h = np.interp(u / 0.1, np.arange(len(k)), k, left=0, right=0) * np.clip(1 - (np.abs(v) - R['width'] / 2) / R['side'], 0, 1)
        E[sl] = np.maximum(E[sl], h)
    return E

def build():
    jumps = np.zeros((N, N)); whoops = np.zeros((N, N)); berms = np.zeros((N, N))
    p = LT.stt(); secs, turns = [], []
    for g in p.segs:
        if g['kind'] == 'S':
            for prof, u0, name in g['sections']:
                render_lane_block(G, whoops if 'whoops' in name else jumps, g, prof, u0, TW)
                for sp in LS.SPLITS.get(name, []): render_split_blend(G, jumps, g, sp, u0, TW)
                if name in getattr(LT, 'WIDE', {}):          # v12: a wider block over part of the section (freestyle landing)
                    a0, a1, wl, wr = LT.WIDE[name]; i0, i1 = int(a0 / 0.1), int(a1 / 0.1)
                    render_lane_block(G, jumps, g, prof[i0:i1], u0 + a0, TW + wl + wr, v_off=(wr - wl) / 2)
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
                gain = getattr(LT, 'BERM_GAIN', {}).get(g.get('tag'), getattr(LT, 'BERM90_GAIN', 1.0) if abs(abs(g['ang']) - 90) < 1 else 1.0)   # v13: per-turn gain on 180s too
                berms[sl] = np.maximum(berms[sl], tmp[sl] * w * gain)
            elif g.get('berm') and abs(abs(g['ang']) - 90) < 1 and getattr(LT, 'BERM90_GAIN', 1.0) != 1.0:
                tmp = np.zeros((N, N)); sl = render_berm_stamp(G, tmp, g['berm'], g['cx'], g['cz'], turn_mid_angle(g), ang_scale=berm_ang_scale(g['berm'], g['ang']))
                berms[sl] = np.maximum(berms[sl], tmp[sl] * getattr(LT, 'BERM_GAIN', {}).get(g.get('tag'), LT.BERM90_GAIN))   # 90 deg berms higher (v6), per-turn override (v7)
            elif g.get('berm'): render_berm_stamp(G, berms, g['berm'], g['cx'], g['cz'], turn_mid_angle(g), ang_scale=berm_ang_scale(g['berm'], g['ang']))
            turns.append(dict(tag=g['tag'], angle=g['ang'], r=g['r'], berm=g.get('berm')))
    H = np.maximum.reduce([jumps, whoops, berms])
    H = np.maximum(H, extras())                                  # v13: start platform + freestyle ramp
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
