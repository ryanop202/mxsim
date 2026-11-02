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

ss_ = lambda t: (lambda t_: t_ * t_ * (3 - 2 * t_))(np.clip(t, 0, 1))

def plat_h(XL, ZL):
    """v24: start platform height at local coords: flat top (h) from `back` ft behind the gate to `front` ft after it, straight
    descent (`down` ft, rounded ends), sides: flat over the gate row + `side`, then a smooth ramp of `side_ramp` ft to the floor."""
    P = LT.START_PLATFORM; a = np.radians(LT.START_HEADING); c, s_ = np.cos(a), np.sin(a)
    u = (XL - LT.START_GATE[0]) * c + (ZL - LT.START_GATE[1]) * s_; v = -(XL - LT.START_GATE[0]) * s_ + (ZL - LT.START_GATE[1]) * c
    Ld, f = P['down'], P['lin']; x = np.clip(u - P['front'], 0, Ld); m = 1.0 / (Ld - f)
    down = 1 - np.where(x < f, m * x * x / (2 * f), np.where(x > Ld - f, 1 - m * (Ld - x) ** 2 / (2 * f), m * (x - f / 2)))
    prof = np.where(u < -P['back'] - 1.0, 0.0, np.where(u <= P['front'], 1.0, down))
    half = (LS.N_GATES - 1) / 2 * LS.GATE_PITCH + P['side']
    lat = 1 - ss_((np.abs(v) - half) / P['side_ramp'])
    return P['h'] * prof * lat

def dirt_region(GX, GZ):
    x0, x1, z0, z1 = LT.ARENA; m = (GX >= x0) & (GX <= x1) & (GZ >= z0) & (GZ <= z1)
    for a0_, a1_, b0_, b1_ in getattr(LT, 'GRASS_OUTSIDE', {}).get('keep', []): m |= (GX >= a0_) & (GX <= a1_) & (GZ >= b0_) & (GZ <= b1_)
    return m

def region_dist(step=1.0, close_r=45.0):
    """v25: distance (ft) to the dirt area on a `step` ft world grid, the area's inner corners rounded (binary closing, radius
    close_r) so the bank has no crease / cone where the start area meets the arena. Returns (d, iz, ix, GX, GZ); also saved to
    build/stt_dist.npy (1 ft grid, world origin) for export (tiles, fence line, decals, night light)."""
    from scipy.ndimage import distance_transform_edt, binary_closing
    ox, oz = LT.STT_ORIGIN; side = (N - 1) * S
    g = np.arange(0, side + step / 2, step); GX, GZ = np.meshgrid(g - ox, g - oz)
    from scipy.ndimage import binary_opening
    x0, x1, z0, z1 = LT.ARENA; m = (GX >= x0) & (GX <= x1) & (GZ >= z0) & (GZ <= z1)
    for a0_, a1_, b0_, b1_ in getattr(LT, 'GRASS_OUTSIDE', {}).get('keep', []):     # v25: start area with rounded outer corners
        sb = (GX >= a0_) & (GX <= a1_ + 40) & (GZ >= b0_) & (GZ <= b1_); ko = int(30.0 / step); yo, xo = np.mgrid[-ko:ko + 1, -ko:ko + 1]
        m |= binary_opening(sb, structure=(xo * xo + yo * yo) <= ko * ko) & (GX <= a1_)
    k = int(close_r / step); yy, xx = np.mgrid[-k:k + 1, -k:k + 1]
    m = binary_closing(m, structure=(xx * xx + yy * yy) <= k * k)
    d, (iz, ix) = distance_transform_edt(~m, return_indices=True); d = d * step
    if step == 1.0: np.save(f'{OUT}/stt_dist.npy', d.astype(np.float32))
    return d, iz, ix, GX, GZ

def bank_h(step=1.0):
    """v24: bank height on a `step` ft grid over the whole terrain. Starts at the height of the nearest ground of the dirt area
    (start platform 10 ft, floor 0) and rises in one smoothstep slope to h; flat terrace under the fence; shorter slope behind
    the start (start_inner), blended along the edge (start_blend) so the corners merge into the rest of the bank."""
    from scipy.ndimage import distance_transform_edt
    B_ = LT.ARENA_BANK; ox, oz = LT.STT_ORIGIN; side = (N - 1) * S
    d, iz, ix, GX, GZ = region_dist(step)
    base = plat_h(GX, GZ)[iz, ix]                                               # ground height at the nearest dirt point
    a0_, a1_, b0_, b1_ = LT.GRASS_OUTSIDE['keep'][0]; sb = (GX >= a0_) & (GX <= a1_) & (GZ >= b0_) & (GZ <= b1_)
    w = (1 - ss_(distance_transform_edt(~sb) * step / B_['start_blend']))[iz, ix]   # 1 on the start edge, fading along the edge
    from scipy.ndimage import gaussian_filter                                  # v24: no crease where the nearest edge switches
    w = gaussian_filter(w, 40.0 / step)                                         # v25: wide blends -> no crease / cone where the
    k_ = ss_(d / 30.0); base = gaussian_filter(base, 6.0 / step) * (1 - k_) + gaussian_filter(base, 25.0 / step) * k_   # nearest edge switches
    inner = B_['inner'] + (B_['start_inner'] - B_['inner']) * w
    SG = B_.get('straight')
    if SG and B_.get('terrace'):                  # v29 (user's drawing): floor, short step to the fence terrace, ONE straight slope
        ta, tw = B_['terrace']; ta_, tb_ = ta - tw / 2, ta + tw / 2
        smax = lambda a, b, c: 0.5 * (a + b + np.sqrt((a - b) ** 2 + c * c))      # smooth max / min (rounded corners)
        smin = lambda a, b, c: 0.5 * (a + b - np.sqrt((a - b) ** 2 + c * c))
        terr = base + SG['terrace_h'] * ss_((d - (ta_ - SG['rise'])) / SG['rise'])
        top = np.maximum(B_['h'] - base - SG['terrace_h'], 0.1)
        rise = smax(SG['slope'] * (d - tb_), 0.0, SG['toe'] * SG['slope'])         # straight slope from the terrace, rounded toe
        up = terr + smin(rise, top, SG['crest'] * SG['slope'])                      # ... up to h, rounded crest
        d_top = tb_ + top / SG['slope'] + SG['crest']
        hb = np.where(d <= d_top + B_['top'], up, B_['h'] * (1 - ss_((d - d_top - B_['top']) / B_['outer'])))
        return np.where(d > 0, hb, np.minimum(hb, plat_h(GX, GZ)))
    if B_.get('terrace'):
        ta, tw = B_['terrace']; ta_, tb_ = ta - tw / 2, ta + tw / 2
        d = np.where(d < ta_, d, np.where(d <= tb_, ta_, d - tw))
    up = base + (B_['h'] - base) * ss_(d / inner)
    if B_.get('steep') and B_.get('terrace'):           # v28: steeper slope right behind the fence terrace, same top height
        sh, sw = B_['steep']; dd = np.clip(d - ta_, 0, None)
        up = base + sh * ss_(dd / sw) + (B_['h'] - base - sh) * ss_(d / inner)
    hb = np.where(d <= inner + B_['top'], up, B_['h'] * (1 - ss_((d - inner - B_['top']) / B_['outer'])))
    return np.where(d > 0, hb, np.minimum(hb, plat_h(GX, GZ)))                  # v25: inside: never above the real ground (no trench at the edge)

def extras():
    """v13: start platform (gates + grates on it, descent right after the gate line) and the freestyle ramp beside the
    wheel tap (steel-like: near-vertical sides). Shapes asked by the user in game tests, not measured units."""
    import compose
    E = np.zeros((N, N)); ox, oz = LT.STT_ORIGIN; st = LS.STARTS['STT']
    P = getattr(LT, 'START_PLATFORM', None)
    if P:                                        # v24: platform with smooth side ramps (plat_h), full resolution
        gx, gz = LT.START_GATE[0] + ox, LT.START_GATE[1] + oz; r = P['back'] + (LS.N_GATES - 1) / 2 * LS.GATE_PITCH + P['side'] + P['side_ramp'] + P['front'] + P['down'] + 5
        sl, X, Z = G.window(gx - r, gx + r, gz - r, gz + r)
        from scipy.ndimage import map_coordinates
        dreg = region_dist(1.0)[0]                                             # v25: platform only inside the (rounded) dirt area
        inside = map_coordinates(dreg, [Z.ravel(), X.ravel()], order=1).reshape(X.shape) <= 0.5
        E[sl] = np.maximum(E[sl], plat_h(X - ox, Z - oz) * inside)
    R = getattr(LT, 'FMX_RAMP', None)
    if R and not R.get('model'):                 # v18: a steel model (statue with collision) replaces the dirt ramp
        k = compose.lane([('cut', 'Detroit_g31_1', R['H'], 0.9)])[0]; il = int(np.argmax(k)) * 0.1
        lx, lz = R['lip'][0] + ox, R['lip'][1] + oz
        d = np.array([R['aim'][0] - R['lip'][0], R['aim'][1] - R['lip'][1]]); d /= np.linalg.norm(d)
        x0, z0 = lx - d[0] * il, lz - d[1] * il; L = len(k) * 0.1; w = R['width'] / 2 + R['side'] + 1
        sl, X, Z = G.window(min(x0, x0 + d[0] * L) - w, max(x0, x0 + d[0] * L) + w, min(z0, z0 + d[1] * L) - w, max(z0, z0 + d[1] * L) + w)
        u = (X - x0) * d[0] + (Z - z0) * d[1]; v = -(X - x0) * d[1] + (Z - z0) * d[0]
        h = np.interp(u / 0.1, np.arange(len(k)), k, left=0, right=0) * np.clip(1 - (np.abs(v) - R['width'] / 2) / R['side'], 0, 1)
        E[sl] = np.maximum(E[sl], h)
    B_ = getattr(LT, 'ARENA_BANK', None)
    if B_:                                       # v19/v24: earth bank around the dirt area (1 ft grid)
        from scipy.ndimage import map_coordinates
        h = bank_h()
        jj = np.arange(N) * S; JX, JZ = np.meshgrid(jj, jj)
        E = np.maximum(E, map_coordinates(h, [JZ.ravel(), JX.ravel()], order=1).reshape(N, N))
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
