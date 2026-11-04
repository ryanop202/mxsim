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
    prof = np.where(u < -P['back'] - (3.0 if LT.GRASS_OUTSIDE.get('west_wall') else 1.0), 0.0,   # v37: under the wall, no groove
                     np.where(u <= P['front'], 1.0, down))
    half = (LS.N_GATES - 1) / 2 * LS.GATE_PITCH + P['side']
    lat = 1 - ss_((np.abs(v) - half) / P['side_ramp'])
    return P['h'] * prof * lat

def dirt_region(GX, GZ):
    x0, x1, z0, z1 = LT.ARENA; m = (GX >= x0) & (GX <= x1) & (GZ >= z0) & (GZ <= z1)
    for a0_, a1_, b0_, b1_ in _keep_rects(): m |= (GX >= a0_) & (GX <= a1_) & (GZ >= b0_) & (GZ <= b1_)
    return m

def _keep_rects():
    """v36: start strip(s) of GRASS_OUTSIDE; with west_wall.z the strip runs along the whole west side of the arena."""
    GO = getattr(LT, 'GRASS_OUTSIDE', {}); K = list(GO.get('keep', []))
    if GO.get('west_wall', {}).get('z') and K:
        a0_, a1_, _, _ = K[0]; K[0] = (a0_, a1_, LT.ARENA[2], LT.ARENA[3])
    return K

def west_weight(d, iz, ix, step):
    """v36: 1 on the edge of the west (start) strip, fading along the arena edge over start_blend ft, 0 elsewhere."""
    from scipy.ndimage import distance_transform_edt, gaussian_filter
    ox, oz = LT.STT_ORIGIN; side = (N - 1) * S; g = np.arange(0, side + step / 2, step); GX, GZ = np.meshgrid(g - ox, g - oz)
    a0_, a1_, b0_, b1_ = _keep_rects()[0]; sb = (GX >= a0_) & (GX <= a1_ + 0.5) & (GZ >= b0_) & (GZ <= b1_)
    WW = LT.GRASS_OUTSIDE.get('west_wall', {})
    # v37: evaluated at the point itself (not at its nearest dirt point: that fans out at the corners -> streaks in the step)
    w = 1 - ss_(distance_transform_edt(~sb) * step / WW.get('blend', LT.ARENA_BANK['start_blend']))
    return gaussian_filter(w, WW.get('sigma', 40.0) / step)

def region_dist(step=1.0, close_r=45.0):
    """v25: distance (ft) to the dirt area on a `step` ft world grid, the area's inner corners rounded (binary closing, radius
    close_r) so the bank has no crease / cone where the start area meets the arena. Returns (d, iz, ix, GX, GZ); also saved to
    build/stt_dist.npy (1 ft grid, world origin) for export (tiles, fence line, decals, night light)."""
    from scipy.ndimage import distance_transform_edt, binary_closing
    ox, oz = LT.STT_ORIGIN; side = (N - 1) * S
    g = np.arange(0, side + step / 2, step); GX, GZ = np.meshgrid(g - ox, g - oz)
    from scipy.ndimage import binary_opening
    x0, x1, z0, z1 = LT.ARENA; m = (GX >= x0) & (GX <= x1) & (GZ >= z0) & (GZ <= z1)
    WW0 = LT.GRASS_OUTSIDE.get('west_wall')
    for a0_, a1_, b0_, b1_ in _keep_rects():                                       # v25: start area with rounded outer corners
        if WW0:                                  # v37: plain strip; the corners are rounded on the whole region below
            m |= (GX >= a0_) & (GX <= a1_) & (GZ >= b0_) & (GZ <= b1_); continue
        sb = (GX >= a0_) & (GX <= a1_ + 40) & (GZ >= b0_) & (GZ <= b1_); ko = int(30.0 / step); yo, xo = np.mgrid[-ko:ko + 1, -ko:ko + 1]
        m |= binary_opening(sb, structure=(xo * xo + yo * yo) <= ko * ko) & (GX <= a1_)
    if WW0:                                      # v37 (user: round it all): west corners of the dirt area rounded (radius corner_r)
        ko = int(WW0['corner_r'] / step); yo, xo = np.mgrid[-ko:ko + 1, -ko:ko + 1]
        mo = binary_opening(m, structure=(xo * xo + yo * yo) <= ko * ko)
        m = np.where(GX <= _keep_rects()[0][1] + 1.5 * WW0['corner_r'], mo, m)
    k = int(close_r / step); yy, xx = np.mgrid[-k:k + 1, -k:k + 1]
    m = binary_closing(m, structure=(xx * xx + yy * yy) <= k * k)
    d, (iz, ix) = distance_transform_edt(~m, return_indices=True); d = d * step
    WW = getattr(LT, 'GRASS_OUTSIDE', {}).get('west_wall')
    if WW:                                       # v36 (user): on the west (start) side the fence step starts right at the dirt edge
        d = np.where(d > 0, d + WW['shift'] * west_weight(d, iz, ix, step), d)
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
    a0_, a1_, b0_, b1_ = _keep_rects()[0]; sb = (GX >= a0_) & (GX <= a1_) & (GZ >= b0_) & (GZ <= b1_)
    w = (1 - ss_(distance_transform_edt(~sb) * step / B_['start_blend']))[iz, ix]   # 1 on the start edge, fading along the edge
    from scipy.ndimage import gaussian_filter                                  # v24: no crease where the nearest edge switches
    w = gaussian_filter(w, 40.0 / step)                                         # v25: wide blends -> no crease / cone where the
    k_ = ss_(d / 30.0); base = gaussian_filter(base, 6.0 / step) * (1 - k_) + gaussian_filter(base, 25.0 / step) * k_   # nearest edge switches
    if getattr(LT, 'GRASS_OUTSIDE', {}).get('west_wall'):   # v36: the west wall starts AT the edge: no blur there (blur = small ditch)
        a0_, a1_, b0_, b1_ = _keep_rects()[0]                    # v37: platform height read straight across the wall (smooth in z;
        raw = gaussian_filter(plat_h(np.clip(GX, a0_, a1_), np.clip(GZ, b0_, b1_)), 2.0 / step)   # the nearest-point read was jagged)
        wr_ = west_weight(d, iz, ix, step); base = np.maximum(base * (1 - wr_) + raw * wr_, raw * ss_((wr_ - 0.5) / 0.3))   # no dip at the foot
    inner = B_['inner'] + (B_['start_inner'] - B_['inner']) * w
    SG = B_.get('straight')
    if SG and B_.get('terrace'):                  # v29 (user's drawing): floor, short step to the fence terrace, ONE straight slope
        ta, tw = B_['terrace']; ta_, tb_ = ta - tw / 2, ta + tw / 2
        smax = lambda a, b, c: 0.5 * (a + b + np.sqrt((a - b) ** 2 + c * c))      # smooth max / min (rounded corners)
        smin = lambda a, b, c: 0.5 * (a + b - np.sqrt((a - b) ** 2 + c * c))
        WW = getattr(LT, 'GRASS_OUTSIDE', {}).get('west_wall'); ww_ = west_weight(d, iz, ix, step) if WW else 0.0
        th_ = SG['terrace_h'] + (WW['extra_h'] * ww_ if WW else 0.0)                  # v36: higher wall west
        terr = base + th_ * ss_((d - (ta_ - SG['rise'])) / SG['rise'])
        hh_ = B_['h'] + (WW['top_h'] * ww_ if WW and WW.get('top_h') else 0.0)            # v37: higher bank on the west side
        top = np.maximum(hh_ - base - th_, 0.1)
        rise = smax(SG['slope'] * (d - tb_), 0.0, SG['toe'] * SG['slope'])         # straight slope from the terrace, rounded toe
        up = terr + smin(rise, top, SG['crest'] * SG['slope'])                      # ... up to h, rounded crest
        d_top = tb_ + top / SG['slope'] + SG['crest']
        hb = np.where(d <= d_top + B_['top'], up, hh_ * (1 - ss_((d - d_top - B_['top']) / B_['outer'])))
        if WW and WW.get('smooth'):              # v37: smooth the slope beyond the terrace (no crease at the corners)
            k2 = ss_((d - (tb_ + 4.0)) / 10.0); hb = hb * (1 - k2) + gaussian_filter(hb, WW['smooth'] / step) * k2
            k3 = np.clip(ww_ * 2 - 0.2, 0, 1) * (d > 0)                  # v37: mild smoothing of the west wall itself (no ripple)
            hb = hb * (1 - k3) + gaussian_filter(hb, 1.5 / step) * k3
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

def pylon_ground(p):
    """v37 (user): a small dirt bump IN the terrain under each pylon (flat top, smooth sides), or, for the turns in curb, a very
    small berm arc around the pylon on the riding-line side. Added on top of the ground. Pylons from LT.PYLONS['points']."""
    PG = getattr(LT, 'PYLON_GROUND', None); out = np.zeros((N, N))
    if not PG or not getattr(LT, 'PYLONS', {}).get('points'): return out
    smp = p.samples(1.0)
    for k, (px, pz) in enumerate(LT.PYLONS['points']):
        R = max(PG['mound']['r'], PG['curb']['r'] + PG['curb'].get('ext_in', 0) + 2 * PG['curb']['w']) + 1
        sl, X, Z = G.window(px - R, px + R, pz - R, pz + R); r = np.hypot(X - px, Z - pz)
        if k in PG['curb']['turns']:
            C = PG['curb']; j = int(np.argmin(np.hypot(smp['x'] - px, smp['z'] - pz))); kk = 14
            Pc = np.array([px, pz]); pt = lambda i: np.array([smp['x'][i], smp['z'][i]])
            def side(i):                                   # unit tangent and the normal pointing from the pylon to the line
                t = pt(i + 1) - pt(i - 1); t /= np.linalg.norm(t); n = np.array([-t[1], t[0]])
                return t, (n if np.dot(n, pt(i) - Pc) > 0 else -n)
            # v38: entry / exit directions = those of the turn itself (the pylon can sit ~19 ft off the lane centre, before the
            # turn: the nearest centre-line point is then still on the straight)
            gT = min((g for g in p.segs if g['kind'] == 'T'), key=lambda g: abs(g['s0'] + abs(np.radians(g['ang'])) * g['r'] / 2 - smp['s'][j]))
            s_in, s_out = gT['s0'] - 5.0, gT['s0'] + abs(np.radians(gT['ang'])) * gT['r'] + 5.0
            t_in, n_in = side(int(np.argmin(np.abs(smp['s'] - s_in)))); t_out, n_out = side(int(np.argmin(np.abs(smp['s'] - s_out))))
            a_in, a_out = np.arctan2(n_in[1], n_in[0]), np.arctan2(n_out[1], n_out[0]); da_ = np.angle(np.exp(1j * (a_out - a_in)))
            arc = [Pc + C['r'] * np.array([np.cos(a_in + da_ * u), np.sin(a_in + da_ * u)]) for u in np.linspace(0, 1, 40)]
            tail_in = [arc[0] - t_in * C['ext_in'] * u for u in np.linspace(1, 0, 20, endpoint=False)]
            tail_out = [arc[-1] + t_out * C['ext_out'] * u for u in np.linspace(0, 1, 10)[1:]]
            poly = np.array(tail_in + arc + tail_out); sv = np.r_[0, np.cumsum(np.linalg.norm(np.diff(poly, axis=0), axis=1))]
            Q = np.stack([X.ravel(), Z.ravel()], 1); dd = np.linalg.norm(Q[:, None, :] - poly[None], axis=2); ii = dd.argmin(1)
            dmin = dd[np.arange(len(Q)), ii].reshape(X.shape); s_ = sv[ii].reshape(X.shape)
            fa = ss_(np.minimum(s_, sv[-1] - s_) / 0.6)                                       # soft ends
            out[sl] = np.maximum(out[sl], C['h'] * np.clip(1 - (dmin / C['w']) ** 2, 0, 1) ** 1.5 * fa)
            print('curb pylon', k, 'arc %.0f deg' % abs(np.degrees(da_)))
        else:
            M = PG['mound']; out[sl] = np.maximum(out[sl], M['h'] * (1 - ss_((r - M['r_flat']) / (M['r'] - M['r_flat']))))
    return out

def flag_stand_geom(p):
    """v40: (crest world xz, lane unit vectors d / n, crest height, stand centre xz) of the finish take-off, LT.FLAG_STAND."""
    FS = LT.FLAG_STAND
    for g in p.segs:
        if g['kind'] != 'S': continue
        for prof, u0, name in g['sections']:
            if name != LT.FINISH_SEC: continue
            it = LS.COMBOS[name]['items'][0]; k = int(np.argmax(prof[:int(it[2] / 0.1)])); uc = u0 + k * 0.1
            d = np.array([np.cos(g['t']), np.sin(g['t'])]); n = np.array([-np.sin(g['t']), np.cos(g['t'])]) * FS['side']
            c = np.array([g['x0'], g['z0']]) + d * uc
            hp = lambda ur: np.interp((k * 0.1 + ur) / 0.1, np.arange(len(prof)), prof, left=0, right=0)   # bump profile, ur from the crest
            us = np.arange(-FS['back'], FS['fwd'], 0.1); fl_ = us[hp(us) >= prof[k] - FS['drop'] - 1e-6]          # flat top (cut)
            ctr = c + d * float(fl_.mean()) + n * (FS['v0'] + FS['w'] / 2)
            return c, d, n, float(prof[k]), ctr, hp
    raise KeyError(LT.FINISH_SEC)

def flag_stand(p):
    """v40 (user): dirt platform joined to the side of the finish take-off, flat top, 1:1 sides."""
    out = np.zeros((N, N)); FS = getattr(LT, 'FLAG_STAND', None)
    if not FS: return out
    c, d, n, hc, ctr, hp = flag_stand_geom(p); top = hc - FS['drop']; R = FS['back'] + FS['w'] + top / FS['slope'] + FS['v0'] + 2
    sl, X, Z = G.window(ctr[0] - R, ctr[0] + R, ctr[1] - R, ctr[1] + R)
    u = (X - c[0]) * d[0] + (Z - c[1]) * d[1]; v = (X - c[0]) * n[0] + (Z - c[1]) * n[1]
    du = np.maximum(np.maximum(-FS['back'] - u, u - FS['fwd']), 0); dv = np.maximum(v - FS['v0'] - FS['w'], 0)
    # v40b: the bump widened sideways (same take-off face and back as the bump itself), cut flat at `top`, sides 1:1 outside
    hb = np.minimum(hp(np.clip(u, -FS['back'], FS['fwd'])), top)
    out[sl] = np.clip(hb - np.hypot(du, dv) * FS['slope'], 0, None) * (v >= FS['v0'])   # joined to the bump at the lane edge, nothing in the lane
    print('flag stand: crest %.1f ft, top %.1f ft, centre (%.1f, %.1f)' % (hc, top, ctr[0], ctr[1]))
    return out

def stake_pads(H, p):
    """v40 (user): flat pads under the yellow stakes of the dirt freestyle kicker (same stake positions as export_stt)."""
    SP_ = getattr(LT, 'STAKE_PADS', None); SK = getattr(LT, 'STAKES', None)
    if not SP_ or not SK: return H
    from scipy.signal import find_peaks
    H = H.copy(); npad = 0
    for g in p.segs:
        if g['kind'] != 'S': continue
        c_, s_ = np.cos(g['t']), np.sin(g['t'])
        for prof, u0, name in g['sections']:
            its = [(a_, b_) for n_, a_, b_, h_ in LS.COMBOS[name]['items'] if any(k_ in n_ for k_ in SP_['items'])]
            if not its: continue
            pk, _ = find_peaks(np.r_[0, prof, 0], prominence=SK['prom']); pk = pk - 1
            for k in pk:
                if not any(a_ <= k * 0.1 <= b_ for a_, b_ in its): continue
                top = prof >= prof[k] - 0.15; a_ = k; b_ = k
                while a_ > 0 and top[a_ - 1]: a_ -= 1
                while b_ < len(prof) - 1 and top[b_ + 1]: b_ += 1
                us = [a_ * 0.1 + 0.5, b_ * 0.1 - 0.5] if (b_ - a_) * 0.1 > SK['table'] else [k * 0.1]
                for uu in us:
                    for sg in (-1, 1):
                        x_ = g['x0'] + (u0 + uu) * c_ - sg * SK['v'] * s_; z_ = g['z0'] + (u0 + uu) * s_ + sg * SK['v'] * c_
                        R = SP_['half_u'] + SP_['half_v'] + SP_['skirt'] + 1
                        sl, X, Z = G.window(x_ - R, x_ + R, z_ - R, z_ + R)
                        u = (X - x_) * c_ + (Z - z_) * s_; v = -(X - x_) * s_ + (Z - z_) * c_
                        inside = (np.abs(u) <= SP_['half_u']) & (np.abs(v) <= SP_['half_v'])
                        h0 = float(H[sl][inside].max())
                        dd = np.hypot(np.maximum(np.abs(u) - SP_['half_u'], 0), np.maximum(np.abs(v) - SP_['half_v'], 0))
                        w = np.clip(1 - dd / SP_['skirt'], 0, 1); w = w * w * (3 - 2 * w)
                        H[sl] = np.where(inside, h0, np.maximum(H[sl], H[sl] * (1 - w) + h0 * w)); npad += 1
    print('stake pads', npad)
    return H

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
    H = H + pylon_ground(p)                                      # v37: dirt bump under each pylon / small curb (user)
    H = np.maximum(H, flag_stand(p))                             # v40: flagger platform at the finish take-off (user)
    H = stake_pads(H, p)                                         # v40: flat pads under the freestyle kicker stakes (user)
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
