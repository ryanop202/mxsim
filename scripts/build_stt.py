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
import importlib
LT = importlib.import_module(os.environ.get('MX_LAYOUT', 'layouts_stt'))   # v66: any track layout (default Saint-Thibery)
KEY, PFX = getattr(LT, 'KEY', 'STT'), getattr(LT, 'PFX', 'stt')

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

def arena_mask(GX, GZ):
    """v69 (Saint-Georges v11): LT.ARENA_POLY (local (x, z) points) = dirt area outline closer to the track; else the ARENA rect."""
    PL = getattr(LT, 'ARENA_POLY', None)
    if PL:
        from matplotlib.path import Path as MPath
        return MPath(np.array(PL, float)).contains_points(np.c_[GX.ravel(), GZ.ravel()]).reshape(GX.shape)
    x0, x1, z0, z1 = LT.ARENA; return (GX >= x0) & (GX <= x1) & (GZ >= z0) & (GZ <= z1)

def dirt_region(GX, GZ):
    m = arena_mask(GX, GZ)
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

def region_dist(step=1.0, close_r=None):
    """v25: distance (ft) to the dirt area on a `step` ft world grid, the area's inner corners rounded (binary closing, radius
    close_r) so the bank has no crease / cone where the start area meets the arena. Returns (d, iz, ix, GX, GZ); also saved to
    build/stt_dist.npy (1 ft grid, world origin) for export (tiles, fence line, decals, night light)."""
    from scipy.ndimage import distance_transform_edt, binary_closing
    ox, oz = LT.STT_ORIGIN; side = (N - 1) * S
    g = np.arange(0, side + step / 2, step); GX, GZ = np.meshgrid(g - ox, g - oz)
    from scipy.ndimage import binary_opening
    m = arena_mask(GX, GZ)
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
    if close_r is None: close_r = getattr(LT, 'CLOSE_R', 45.0)   # v74 (Saint-Georges v18): per track
    k = int(close_r / step); yy, xx = np.mgrid[-k:k + 1, -k:k + 1]
    m = binary_closing(m, structure=(xx * xx + yy * yy) <= k * k)
    d, (iz, ix) = distance_transform_edt(~m, return_indices=True); d = d * step
    WW = getattr(LT, 'GRASS_OUTSIDE', {}).get('west_wall')
    if WW:                                       # v36 (user): on the west (start) side the fence step starts right at the dirt edge
        d = np.where(d > 0, d + WW['shift'] * west_weight(d, iz, ix, step), d)
    if step == 1.0: np.save(f'{OUT}/{PFX}_dist.npy', d.astype(np.float32))
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

def mounds_h(step=1.0):
    """v67 (user, Saint-Georges): grassed earth mounds for the crowd, only in the zones the user circled (LT.MOUNDS['zones'],
    local rects x0, x1, z0, z1, faded over `fade` ft at their ends). Across: from d0 ft beyond the dirt edge a smooth climb
    over `inner` ft up to h, a flat top `top` ft wide, then down over `outer` ft. Returns heights on a `step` ft world grid.
    v70 (Saint-Georges v12): a zone may carry its own dict (h, d0, inner, top, outer, fade, lin); lin = share of a straight
    climb (1 = a long inclined plane, rounded at both ends by the rest of the smoothstep)."""
    M = LT.MOUNDS; d, iz, ix, GX, GZ = region_dist(step); out = np.zeros_like(d)
    for zn in M['zones']:
        x0, x1, z0, z1 = zn[:4]; P = dict(M, **(zn[4] if len(zn) > 4 else {}))
        x_ = d - P['d0']; t_ = np.clip(x_ / P['inner'], 0, 1); lin = P.get('lin', 0.0)
        climb = lin * t_ + (1 - lin) * ss_(x_ / P['inner'])
        prof = np.where(x_ <= P['inner'] + P['top'], P['h'] * climb, P['h'] * (1 - ss_((x_ - P['inner'] - P['top']) / P['outer'])))
        fd = P['fade']; w = ss_((GX - x0) / fd) * ss_((x1 - GX) / fd) * ss_((GZ - z0) / fd) * ss_((z1 - GZ) / fd)
        out = np.maximum(out, prof * w * (d > 0))
    for PS in M.get('passages', []):              # v77 (Saint-Georges v21): a walkway between two mounds
        dv = np.array(PS['dir'], float); dv /= np.linalg.norm(dv); v_ = np.abs(-(GX - PS['p'][0]) * dv[1] + (GZ - PS['p'][1]) * dv[0])
        t_ = (GX - PS['p'][0]) * dv[0] + (GZ - PS['p'][1]) * dv[1]   # only from the point outwards (a half-line, not the whole map)
        out = out * np.maximum(ss_((v_ - PS['w'] / 2) / PS['soft']), ss_((-30.0 - t_) / 10.0))
    RD = getattr(LT, 'ROAD', None)                # v80 (Saint-Georges v24): the road cuts through the mounds
    if getattr(LT, 'ROADS', None):
        out = out * ss_((road_dist(GX, GZ) - 8.0 - getattr(LT, 'ALLEY_WIDEN', 0.0)) / RD['soft'])   # v81: every road cuts the mounds; v82: alley wider
    return out

def road_dist(GX, GZ, roads=None):
    """v80/v81: distance (ft, local) to the roads (LT.ROADS polylines, or the given subset)."""
    out = np.full(np.shape(GX), 1e9)
    for RD in (roads if roads is not None else getattr(LT, 'ROADS', [])):
        P = np.array(RD['pts'], float)
        for p0, p1 in zip(P[:-1], P[1:]):
            dv = p1 - p0; L2 = float(dv @ dv); t = np.clip(((GX - p0[0]) * dv[0] + (GZ - p0[1]) * dv[1]) / L2, 0, 1)
            out = np.minimum(out, np.hypot(GX - (p0[0] + t * dv[0]), GZ - (p0[1] + t * dv[1])) - (RD['w'] / 2 - 8.0))
    return out

def mini_berms(p):
    """v72 (Saint-Georges v17): LT.MINI_BERMS: a small berm arc inside a turn (tag), around the turn centre: crest at r ft, face
    towards the centre over w_in ft, back over w_out ft, between turn progress a[0]..a[1] deg, faded over `fade` deg."""
    out = np.zeros((N, N)); smp = p.samples(0.5)
    for MB in getattr(LT, 'MINI_BERMS', []) or []:
        g = [g for g in p.segs if g['kind'] == 'T' and g['tag'] == MB['tag']][0]
        R = 2 * MB.get('R', MB.get('r', 10.0)) + MB['w_out'] + 30; sl, X, Z = G.window(g['cx'] - R, g['cx'] + R, g['cz'] - R, g['cz'] + R)
        k0 = int(np.argmin(np.abs(smp['s'] - g['s0']))); phi0 = np.arctan2(smp['z'][k0] - g['cz'], smp['x'][k0] - g['cx'])
        sgn = -np.sign(g['ang']); rel = np.degrees(np.angle(np.exp(1j * (np.arctan2(Z - g['cz'], X - g['cx']) - phi0)))) * sgn
        if MB.get('P'):                            # v78 (Saint-Georges v22): crest through a given point, curvature centre along nrm
            Pm = np.array(MB['P']) + LT.STT_ORIGIN; C2 = Pm + np.array(MB['nrm']) / np.linalg.norm(MB['nrm']) * MB['R']; pm = np.arctan2(Pm[1] - C2[1], Pm[0] - C2[0])
        elif MB.get('R'):
            pm = phi0 + sgn * np.radians(MB['mid']); C2 = np.array([g['cx'], g['cz']]) + np.array([np.cos(pm), np.sin(pm)]) * (MB['r'] - MB['R'])
        if MB.get('R'):                            # v77 (Saint-Georges v21): a tiny copy of a real berm, its own big radius
            r = np.hypot(X - C2[0], Z - C2[1]); u = r - MB['R']
            sa = np.angle(np.exp(1j * (np.arctan2(Z - C2[1], X - C2[0]) - pm))) * MB['R']                     # arc length from the mid
            w = ss_((MB['half_len'] + MB['fade_len'] - np.abs(sa)) / MB['fade_len'])
        else:
            r = np.hypot(X - g['cx'], Z - g['cz']); u = r - MB['r']
            fd = MB['fade']; w = ss_((rel - MB['a'][0]) / fd) * ss_((MB['a'][1] - rel) / fd)
        prof = np.where(u < 0, ss_(1 + u / MB['w_in']), ss_(1 - u / MB['w_out']))
        out[sl] = np.maximum(out[sl], MB['h'] * prof * w)
        print('mini berm', g['tag'], 'h %.2f' % out[sl].max())
    return out

def extra_bumps():
    """v77 (Saint-Georges v21): LT.EXTRA_BUMPS: free bumps (inside of a turn): cosine along the travel direction (L ft),
    flat crest W ft wide with rounded ends (`ends` ft)."""
    out = np.zeros((N, N)); ox, oz = LT.STT_ORIGIN
    for EB in getattr(LT, 'EXTRA_BUMPS', []) or []:
        cx, cz = EB['c'][0] + ox, EB['c'][1] + oz; t = np.radians(EB['ang']); d = np.array([np.cos(t), np.sin(t)]); n = np.array([-d[1], d[0]])
        Rw = EB['L'] + EB['W'] + 2; sl, X, Z = G.window(cx - Rw, cx + Rw, cz - Rw, cz + Rw)
        u = (X - cx) * d[0] + (Z - cz) * d[1]; v = (X - cx) * n[0] + (Z - cz) * n[1]
        along = np.where(np.abs(u) < EB['L'] / 2, (1 + np.cos(2 * np.pi * u / EB['L'])) / 2, 0.0)
        across = ss_((EB['W'] / 2 + EB['ends'] - np.abs(v)) / EB['ends'])
        out[sl] = np.maximum(out[sl], EB['h'] * along * across)
        print('extra bump at local (%.1f, %.1f), h %.1f' % (EB['c'][0], EB['c'][1], EB['h']))
    return out

def pond_dig():
    """v79 (Saint-Georges v23): the pond (LT.POND, outline in LT.DECOR file): a bank `bank` ft wide going down `drop` ft to the
    water level, then deeper (`deep`) under the water plane (a statue)."""
    PD = getattr(LT, 'POND', None); out = np.zeros((N, N))
    if not PD: return out
    import json
    from matplotlib.path import Path as MPath
    from scipy.ndimage import distance_transform_edt
    poly = np.array(json.load(open(f"{ROOT}/{LT.DECOR['file']}"))['pond']) + np.array(LT.STT_ORIGIN)
    x0, z0 = poly.min(0) - 5; x1, z1 = poly.max(0) + 5
    sl, X, Z = G.window(x0, x1, z0, z1)
    ins = MPath(poly).contains_points(np.c_[X.ravel(), Z.ravel()]).reshape(X.shape)
    din = distance_transform_edt(ins) * S
    dep = np.where(din < PD['bank'], PD['drop'] * ss_(din / PD['bank']), PD['drop'] + (PD['deep'] - PD['drop']) * ss_((din - PD['bank']) / 6.0))
    out[sl] = np.where(ins, dep, 0.0)
    print('pond: max depth %.1f ft' % out.max())
    return out

def pylon_spots(p):
    """v71 (Saint-Georges v13): the pylon spots: LT.PYLONS['points'] (user's spots) or the export rule (turn bisector,
    `margin` ft inside the inner lane edge; 90 deg turns: corner of the inner edges), turns in PYLONS['skip'] left out."""
    PY = getattr(LT, 'PYLONS', None) or {}
    if PY.get('points'): return list(PY['points'])
    if 'half' not in PY: return []
    smp = p.samples(1.0); out = []
    for g in p.segs:
        if g['kind'] != 'T' or g['tag'] in PY.get('skip', ()): continue
        sel = (smp['s'] >= g['s0']) & (smp['s'] <= g['s0'] + g['L']); X_, Z_ = smp['x'][sel], smp['z'][sel]
        c_ = np.array([g['cx'], g['cz']]); m_ = np.array([X_[len(X_) // 2], Z_[len(Z_) // 2]]); u_ = (m_ - c_) / np.linalg.norm(m_ - c_)
        k_ = 1.0 if abs(g['ang']) > 135 else np.sqrt(2)
        out.append(tuple(c_ + u_ * (g['r'] - PY['half'] - PY['margin']) * k_))
    return out

def pylon_ground(p):
    """v37 (user): a small dirt bump IN the terrain under each pylon (flat top, smooth sides), or, for the turns in curb, a very
    small berm arc around the pylon on the riding-line side. Added on top of the ground. Pylons from LT.PYLONS['points']."""
    PG = getattr(LT, 'PYLON_GROUND', None); out = np.zeros((N, N))
    SP = pylon_spots(p)
    if not PG or not SP: return out
    smp = p.samples(1.0)
    for k, (px, pz) in enumerate(SP):
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
            it = LS.COMBOS[name]['items'][FS.get('item', 0)]; i0_ = int(it[1] / 0.1)   # v76 (Saint-Georges v20): which item = the finish take-off
            k = i0_ + int(np.argmax(prof[i0_:int(it[2] / 0.1)])); uc = u0 + k * 0.1
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
    if FS.get('box'): hb = np.full_like(u, top)   # v77 (Saint-Georges v21): a flat box with straight walls, not the bump's shape
    if FS.get('rect'):                           # v78 (Saint-Georges v22): a clean square block, straight walls on all 4 sides
        dvi = np.maximum(FS['v0'] - v, 0); out[sl] = np.clip(top - np.maximum(np.maximum(du, dv), dvi) * FS['slope'], 0, None)
    else: out[sl] = np.clip(hb - np.hypot(du, dv) * FS['slope'], 0, None) * (v >= FS['v0'])   # joined to the bump at the lane edge, nothing in the lane
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
    E = np.zeros((N, N)); ox, oz = LT.STT_ORIGIN; st = LS.STARTS[KEY]
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
    if getattr(LT, 'MOUNDS', None):              # v67: crowd mounds in the user's zones (Saint-Georges)
        from scipy.ndimage import map_coordinates
        h = mounds_h(); jj = np.arange(N) * S; JX, JZ = np.meshgrid(jj, jj)
        E = np.maximum(E, map_coordinates(h, [JZ.ravel(), JX.ravel()], order=1).reshape(N, N))
        print('mounds: max %.1f ft' % h.max())
    B_ = getattr(LT, 'ARENA_BANK', None)
    if B_:                                       # v19/v24: earth bank around the dirt area (1 ft grid)
        from scipy.ndimage import map_coordinates
        h = bank_h()
        jj = np.arange(N) * S; JX, JZ = np.meshgrid(jj, jj)
        E = np.maximum(E, map_coordinates(h, [JZ.ravel(), JX.ravel()], order=1).reshape(N, N))
    return E

def inner_rut(out, g, IR):
    """v67 (user, Saint-Georges): an inside rut = a small berm ridge in the middle of the track along a turn (a 2nd line on the
    inside). Ridge on radius r + dr: inner face w_in ft long up to h, back w_out ft down to 0; faded in / out over ext deg
    before / after the turn."""
    r0 = g['r'] + IR.get('dr', 0.0); R = r0 + IR['w_out'] + 2
    sl, X, Z = G.window(g['cx'] - R, g['cx'] + R, g['cz'] - R, g['cz'] + R)
    dx, dz = X - g['cx'], Z - g['cz']; rr = np.hypot(dx, dz); d = rr - r0
    a0 = turn_mid_angle(g) + np.radians(g['ang']) / 2                           # centre -> turn start
    deg = np.degrees(np.angle(np.exp(1j * (np.arctan2(dz, dx) - a0)))) * -np.sign(g['ang'])
    A, e = abs(g['ang']), IR.get('ext', 10.0)
    wa = ss_((deg + e) / e) * ss_((A + e - deg) / e)
    prof = np.where(d < 0, ss_(1 + d / IR['w_in']), 1 - ss_(d / IR['w_out'])) * IR['h']
    out[sl] = np.maximum(out[sl], prof * wa)

def render_cut_block(out, g, prof, u0, C):
    """v73 (Saint-Georges v17): a lane block whose width is cut by C['w'] ft on one side (side -1 = left of the riding
    direction) between section distances C['a'] (cut back to 0 over C['fade'] ft at the end): the take-off narrower than
    the landing. Same skirt as render_lane_block."""
    from engine import sx_wall
    L = len(prof) * 0.1; c, s_ = np.cos(g['t']), np.sin(g['t']); half = TW / 2 + 8.0
    pts = np.array([(g['x0'] + uu * c - vv * s_, g['z0'] + uu * s_ + vv * c) for uu in (u0, u0 + L) for vv in (-half, half)])
    sl, X, Z = G.window(pts[:, 0].min(), pts[:, 0].max(), pts[:, 1].min(), pts[:, 1].max())
    dx, dz = X - g['x0'], Z - g['z0']; u = dx * c + dz * s_ - u0; v = -dx * s_ + dz * c
    pu = np.interp(u / 0.1, np.arange(len(prof)), prof, left=0, right=0)
    a0, a1 = C['a']; wc = C['w'] * (u >= a0) * ss_((a1 - u) / C['fade'])
    h = pu * sx_wall(np.abs(v + C['side'] * wc / 2) - (TW - wc) / 2)
    out[sl] = np.maximum(out[sl], h)


def wall_stair_top(U, WS):
    """v86 (Saint-Georges v34): top of the block wall allowed at section distance U (inf before the stair)."""
    U = np.asarray(U, float)
    if not WS: return np.full(U.shape, np.inf)
    n = WS['ltop'] - np.ceil(np.maximum(U - WS['u0'], 0) / WS['step'])
    return np.where(U <= WS['u0'], np.inf, np.maximum(n, 0) * 2.62)

def build():
    jumps = np.zeros((N, N)); whoops = np.zeros((N, N)); berms = np.zeros((N, N))
    p = LT.stt(); secs, turns = [], []
    for g in p.segs:
        if g['kind'] == 'S':
            for prof, u0, name in g['sections']:
                if name in getattr(LT, 'SIDE_CUT', {}): render_cut_block(jumps, g, prof, u0, LT.SIDE_CUT[name])   # v73
                else: render_lane_block(G, whoops if 'whoops' in name else jumps, g, prof, u0, TW)
                for sp in LS.SPLITS.get(name, []): render_split_blend(G, jumps, g, sp, u0, TW)
                if name in getattr(LT, 'WIDE', {}):          # v12: a wider block over part of the section (freestyle landing)
                    a0, a1, wl, wr = LT.WIDE[name]; i0, i1 = int(a0 / 0.1), int(a1 / 0.1)
                    render_lane_block(G, jumps, g, prof[i0:i1], u0 + a0, TW + wl + wr, v_off=(wr - wl) / 2)
                secs.append(dict(lane=g['tag'], name=name, s0=g['s0'] + u0, length=len(prof) * 0.1, hmax=float(prof.max()),
                                 items=LS.COMBOS[name]['items']))
        elif g['kind'] == 'T':
            if g.get('berm') and g.get('tag') in getattr(LT, 'BERM_SHIFT', {}):
                # v58: a whole crescent (130 deg) compressed between turn progress t0 and t1 (its own entry and exit tapers)
                # v59: (t0, t_peak, t1, gain, power): entry half squeezed into t0..t_peak, exit half into t_peak..t1 (peak anywhere)
                t0_, tp_, t1_, gain, pw_ = LT.BERM_SHIFT[g['tag']]
                bo_ = getattr(LT, 'BERM_OFFSET', {}).get(g['tag'], (0.0, 0.0)); g = dict(g, cx=g['cx'] + bo_[0], cz=g['cz'] + bo_[1])   # v69
                mid_ = turn_mid_angle(g) - np.sign(g['ang']) * np.radians(tp_ - abs(g['ang']) / 2)
                tA = np.zeros((N, N)); sl = render_berm_stamp(G, tA, g['berm'], g['cx'], g['cz'], mid_, ang_scale=65.0 / (tp_ - t0_))
                tB = np.zeros((N, N)); render_berm_stamp(G, tB, g['berm'], g['cx'], g['cz'], mid_, ang_scale=65.0 / (t1_ - tp_))
                jj, ii = np.meshgrid(np.arange(sl[1].start, sl[1].stop), np.arange(sl[0].start, sl[0].stop))
                d_ = np.angle(np.exp(1j * (np.arctan2(ii * S - g['cz'], jj * S - g['cx']) - mid_))) * -np.sign(g['ang'])   # > 0: past the peak
                h_ = np.where(d_ < 0, tA[sl], tB[sl]); hm_ = max(float(h_.max()), 1e-6)
                BE_ = getattr(LT, 'BERM_END', {}).get(g['tag'])   # v68 (Saint-Georges v10): clean berm end, no low tail into the exit lane
                if BE_:
                    pr_ = tp_ + np.degrees(d_); h_ = h_ * (1 - ss_((pr_ - BE_[0]) / (BE_[1] - BE_[0])))
                berms[sl] = np.maximum(berms[sl], gain * hm_ * (h_ / hm_) ** pw_)
            elif g.get('berm') and g.get('tag') in getattr(LT, 'HALF_BERM', ()):
                # v4: berm only on the second half of the turn (user's drawing): fade in between 45 % and 60 % of the turn
                tmp = np.zeros((N, N)); sl = render_berm_stamp(G, tmp, g['berm'], g['cx'], g['cz'], turn_mid_angle(g), ang_scale=berm_ang_scale(g['berm'], g['ang']))
                smp = p.samples(0.5); k0 = int(np.argmin(np.abs(smp['s'] - g['s0'])))
                phi0 = np.arctan2(smp['z'][k0] - g['cz'], smp['x'][k0] - g['cx']); sgn = -np.sign(g['ang'])     # left turn: heading (and angle) decreases
                jj, ii = np.meshgrid(np.arange(sl[1].start, sl[1].stop), np.arange(sl[0].start, sl[0].stop))
                phi = np.arctan2(ii * S - g['cz'], jj * S - g['cx']); rel = np.angle(np.exp(1j * (phi - phi0))) * sgn
                u = rel / np.radians(abs(g['ang'])); f0_, f1_ = getattr(LT, 'BERM_FADE', {}).get(g.get('tag'), (0.45, 0.15))   # v54: per turn
                w = np.clip((u - f0_) / f1_, 0, 1); w = w * w * (3 - 2 * w)
                if g.get('tag') in getattr(LT, 'BERM_CLIP', {}):          # v56: berm cut along a z line (user's red line)
                    zc_, tw_ = LT.BERM_CLIP[g['tag']]; c_ = np.clip((ii * S - zc_) / tw_, 0, 1); w = w * c_ * c_ * (3 - 2 * c_)
                gain = getattr(LT, 'BERM_GAIN', {}).get(g.get('tag'), getattr(LT, 'BERM90_GAIN', 1.0) if abs(abs(g['ang']) - 90) < 1 else 1.0)   # v13: per-turn gain on 180s too
                berms[sl] = np.maximum(berms[sl], tmp[sl] * w * gain)
            elif g.get('berm') and abs(abs(g['ang']) - 90) < 1 and getattr(LT, 'BERM90_GAIN', 1.0) != 1.0:
                tmp = np.zeros((N, N)); sl = render_berm_stamp(G, tmp, g['berm'], g['cx'], g['cz'], turn_mid_angle(g), ang_scale=berm_ang_scale(g['berm'], g['ang']))
                berms[sl] = np.maximum(berms[sl], tmp[sl] * getattr(LT, 'BERM_GAIN', {}).get(g.get('tag'), LT.BERM90_GAIN))   # 90 deg berms higher (v6), per-turn override (v7)
            elif g.get('berm'): render_berm_stamp(G, berms, g['berm'], g['cx'], g['cz'], turn_mid_angle(g), ang_scale=berm_ang_scale(g['berm'], g['ang']))
            IR_ = getattr(LT, 'INNER_RUTS', {}).get(g.get('tag'))
            if IR_: inner_rut(berms, g, IR_)                         # v67: inside rut (Saint-Georges)
            turns.append(dict(tag=g['tag'], angle=g['ang'], r=g['r'], berm=g.get('berm')))
    SF_ = getattr(LT, 'SOFT_FEET', None)          # v78 (Saint-Georges v22): bump feet rounded (the slope kink drew a line in game)
    if SF_:
        from scipy.ndimage import gaussian_filter
        for A_ in (jumps, whoops):
            w_ = ss_(A_ / SF_['h']); A_[:] = A_ * w_ + gaussian_filter(A_, SF_['sigma'] / S) * (1 - w_)
    H = np.maximum.reduce([jumps, whoops, berms])
    H = np.maximum(H, extras())                                  # v13: start platform + freestyle ramp
    H = H + pylon_ground(p)                                      # v37: dirt bump under each pylon / small curb (user)
    H = H + mini_berms(p)                                        # v72: small inside berms (Saint-Georges v17)
    H = np.maximum(H, extra_bumps())                             # v77: free bumps (Saint-Georges v21)
    H = np.maximum(H, flag_stand(p))                             # v40: flagger platform at the finish take-off (user)
    H = stake_pads(H, p)                                         # v40: flat pads under the freestyle kicker stakes (user)
    H = H - pond_dig()                                           # v79: the pond (Saint-Georges v23)
    BDf = getattr(LT, 'BOUDINS', None) or {}
    if BDf.get('flatten'):                                       # v84 (Saint-Georges v29): flat strip under the long boudins
        for ln_ in [l_ for l_ in BDf.get('lines', []) if l_.get('flatten', True)]:   # v30 (user): per line (Bobcat line / berm: no)
            p0_, p1_ = np.array(ln_['p0']), np.array(ln_['p1']); d_ = p1_ - p0_; Ld_ = np.linalg.norm(d_)
            lo_ = np.minimum(p0_, p1_) - 8; hi_ = np.maximum(p0_, p1_) + 8
            sl, X, Z = G.window(lo_[0] + LT.STT_ORIGIN[0], hi_[0] + LT.STT_ORIGIN[0], lo_[1] + LT.STT_ORIGIN[1], hi_[1] + LT.STT_ORIGIN[1])
            X = X - LT.STT_ORIGIN[0]; Z = Z - LT.STT_ORIGIN[1]; t_ = np.clip(((X - p0_[0]) * d_[0] + (Z - p0_[1]) * d_[1]) / Ld_ ** 2, 0, 1)
            dd_ = np.hypot(X - p0_[0] - t_ * d_[0], Z - p0_[1] - t_ * d_[1]); w_ = np.clip(1 - (dd_ - BDf['flatten']) / 3.0, 0, 1)
            hs_ = H[sl]; H[sl] = np.where(hs_ < 1.5, hs_ * (1 - w_), hs_)
    CWb = getattr(LT, 'CONCRETE_WALL', None); MFb = getattr(LT, 'MOUND_FLANK', None)
    for WLb in ((getattr(LT, 'WALLS', []) or []) if MFb else []):  # v86 (Saint-Georges v33): wide gentle sides on the landing mound
        o_ = np.array(WLb['o']); dl_ = np.array(WLb['dl']); rg_ = np.array(WLb['rgt']); ua_, ub_ = WLb['u']; e0_ = MFb['e0']
        ua2, ub2 = ua_ - MFb['ext'], ub_ + MFb['ext']; wmax = max(MFb['w_west'], MFb['w_east']) + e0_ + 2
        cs_ = [o_ + dl_ * u_ + rg_ * f_ for u_ in (ua2, ub2) for f_ in (-wmax, wmax)]
        sl, X, Z = G.window(min(c[0] for c in cs_), max(c[0] for c in cs_), min(c[1] for c in cs_), max(c[1] for c in cs_))
        U = (X - o_[0]) * dl_[0] + (Z - o_[1]) * dl_[1]; V = (X - o_[0]) * rg_[0] + (Z - o_[1]) * rg_[1]   # V > 0 east
        hs = H[sl].copy(); Uc = np.clip(U, ua2, ub2)
        for sg_, wf_ in ((-1, MFb['w_west']), (1, MFb['w_east'])):
            qx = o_[0] + dl_[0] * Uc + rg_[0] * sg_ * e0_; qz = o_[1] + dl_[1] * Uc + rg_[1] * sg_ * e0_
            he = H[np.clip((qz / G.s).astype(int), 0, H.shape[0] - 1), np.clip((qx / G.s).astype(int), 0, H.shape[1] - 1)]   # mound edge height
            t_ = np.clip((sg_ * V - e0_) / wf_, 0, 1); f_ = 0.5 * (1 + np.cos(np.pi * t_))
            on_ = (sg_ * V > e0_) & (U >= ua2) & (U <= ub2)
            hs = np.where(on_, np.maximum(hs, he * f_), hs)
        H[sl] = hs
        print('landing mound flanks widened (west %.0f ft, east %.0f ft)' % (MFb['w_west'], MFb['w_east']))
    for WLb in (getattr(LT, 'WALLS', []) or []):                 # v85 (Saint-Georges v30): the block wall is the side of the landing
        o_ = np.array(WLb['o']); dl_ = np.array(WLb['dl']); rg_ = np.array(WLb['rgt'])
        ua_, ub_ = WLb['u']; ow_, cut_, ff_ = CWb['off'], CWb['cut'], CWb['fill_from']
        cs_ = [o_ + dl_ * u_ - rg_ * f_ for u_ in (ua_ - 8, ub_ + 8) for f_ in (ff_ - 1, ow_ + cut_ + 1)]
        xs_ = [c[0] for c in cs_]; zs_ = [c[1] for c in cs_]
        sl, X, Z = G.window(min(xs_), max(xs_), min(zs_), max(zs_))
        U = (X - o_[0]) * dl_[0] + (Z - o_[1]) * dl_[1]; OF = -((X - o_[0]) * rg_[0] + (Z - o_[1]) * rg_[1])   # OF > 0 on the wall side
        Uc = np.clip(U, ua_, ub_); qx = o_[0] + dl_[0] * Uc - rg_[0] * ff_; qz = o_[1] + dl_[1] * Uc - rg_[1] * ff_
        hr = H[np.clip((qz / G.s).astype(int), 0, H.shape[0] - 1), np.clip((qx / G.s).astype(int), 0, H.shape[1] - 1)]   # dirt level at fill_from
        hs = H[sl].copy()
        inu = (U >= ua_) & (U <= ub_)
        wend = np.clip(1 - np.maximum(ua_ - U, U - ub_) / (MFb['end_fade'] if MFb else 6.0), 0, 1)   # 1 along the wall, fading out past its ends
        Tst = wall_stair_top(U, getattr(LT, 'WALL_STAIR', {}))          # v86 (v34): stair end - cut / fill only where the blocks are
        qfx = o_[0] + dl_[0] * Uc - rg_[0] * (ow_ - 1.0); qfz = o_[1] + dl_[1] * Uc - rg_[1] * (ow_ - 1.0)
        hface = np.maximum(hr, H[np.clip((qfz / G.s).astype(int), 0, H.shape[0] - 1), np.clip((qfx / G.s).astype(int), 0, H.shape[1] - 1)])
        blk = Tst >= hface - 1.0                                          # the blocks reach (about) the dirt there
        fill = inu & (OF >= ff_) & (OF <= ow_ - 0.6)   # the cut edge 0.6 ft behind the block face (grid staircase hidden)
        hs = np.where(fill, np.maximum(hs, hr), hs)
        cut = (OF > ow_ - 0.6) & (OF <= ow_ + cut_) & (wend > 0)
        hs = np.where(cut, hs * (1 - wend) + np.minimum(hs, 0.0) * wend, hs)
        # v86 (v35, user): where the blocks were removed (stair end), smooth dirt in place of the blocks: never above the
        # blocks' plane - from the top of the remaining blocks it goes back into the mound at a steep smooth slope
        WSb = getattr(LT, 'WALL_STAIR', {})
        WE_ = getattr(LT, 'WALL_EDGE', None)
        if WSb and WE_:                            # v87 (v38, user: "pas au secateur"): past the stair start the dirt ends with the
            from engine import sx_wall as sxw_     # usual lane edge shape (squeezed into the room left before the wall plane)
            e_ = WE_['w']; prof_ = hr * sxw_((OF - (ow_ - e_)) / (e_ / 7.0))
            zE_ = (U >= WSb['u0'] - 0.5) & (U <= ub_ + 3.0) & (OF >= ow_ - e_)
            hs = np.where(zE_, np.minimum(np.maximum(hs, 0.0), prof_), hs)
            wp_ = np.clip((U - (ua_ - 10.0)) / 4.0, 0, 1)                    # v88 (v39, user): before the wall start too (no cliff)
            zP_ = (U >= ua_ - 10.0) & (U < ua_) & (OF >= ow_ - e_) & (OF < ow_ + cut_)
            hs = np.where(zP_, hs * (1 - wp_) + np.minimum(hs, np.maximum(prof_, 0.0)) * wp_, hs)
        if WSb and getattr(LT, 'WALL_DIRT_RAMP', False):   # v36 ramp (v37: off - the dirt is cut straight in the wall plane like the blocks)
            Tlin = np.clip(WSb['ltop'] * 2.62 - (U - WSb['u0']) * 2.62 / WSb['step'], 0, None)   # the line through the stair corners
            rem = (U >= WSb['u0']) & (OF > ow_ - 30.0)
            cap = Tlin + np.maximum(ow_ - 0.6 - OF, 0) * 0.75                                     # a smooth ramp back into the mound
            hs = np.where(rem, np.minimum(hs, cap), hs)
            Tst2 = wall_stair_top(np.clip(U, ua_, ub_ + 12.0), WSb)
            hs = np.where(rem & (OF > ow_ - 0.6), np.minimum(hs, np.where(np.isfinite(Tst2), Tst2, 0.0)), hs)
        H[sl] = hs
        if MFb:                                    # v36 (user): clean smooth flanks - blur everything outside the lane top
            from scipy.ndimage import gaussian_filter as gfb_
            e0_ = MFb['e0']; Vb = (X - o_[0]) * rg_[0] + (Z - o_[1]) * rg_[1]
            hb_ = gfb_(H[sl], 3.0 / G.s)
            wl_ = np.clip((np.abs(Vb) - (e0_ - 2.0)) / 3.0, 0, 1)                         # 0 on the lane top
            u0b_ = WSb.get('u0', ub_) if WSb else ub_
            west_ = Vb < 0                                                               # wall side: only past the stair start
            zone_ = np.where(west_, np.clip((U - (u0b_ - 2.0)) / 4.0, 0, 1), 1.0)       # east flank: all along
            wl_ = wl_ * zone_ * (np.abs(Vb) < e0_ + MFb['w_west'] + 10.0) * (U > ua_ - MFb['ext'] - 10.0) * (U < ub_ + MFb['ext'] + 25.0)
            hs = H[sl] * (1 - wl_) + hb_ * wl_
            if WSb:                                # the blocks still stand clear of the dirt
                Tst3 = wall_stair_top(np.clip(U, ua_, ub_ + 12.0), WSb)
                hs = np.where((U >= WSb['u0']) & (OF > ow_ - 0.6) & (OF <= ow_ + 0.2), np.minimum(hs, np.where(np.isfinite(Tst3), Tst3, 0.0)), hs)
            fr_ = (OF > ow_ + 0.2) & (OF < ow_ + cut_) & (U >= ua_ - 1.0) & (U <= ub_ + 4.0)   # in front of the wall: flat ground
            hs = np.where(fr_, np.minimum(hs, 0.0), hs)
            H[sl] = hs
        print('concrete wall: dirt filled behind, flank cut outside, u %.0f..%.0f' % (ua_, ub_))
    TN = 2 ** 11; t = lambda a: a[:-1:2, :-1:2][:TN, :TN]
    tiles = np.full((TN, TN), T_MAIN, np.uint8)
    tiles[t(jumps) > 0.05] = T_JUMP; tiles[t(whoops) > 0.05] = T_WHOOP; tiles[t(berms) > 0.05] = T_BERM
    if not getattr(LT, 'ARENA_BANK', None): region_dist(1.0)            # v66: the export needs build/<pfx>_dist.npy even without a bank
    rep = dict(lap_ft=p.s, sections=secs, turns=turns, start=LS.STARTS[KEY])
    np.save(f'{OUT}/{PFX}_H.npy', H.astype(np.float32)); np.save(f'{OUT}/{PFX}_tiles.npy', tiles)
    json.dump(rep, open(f'{OUT}/{PFX}_report.json', 'w'), indent=1, default=float)
    return H, p, rep

if __name__ == '__main__':
    H, p, rep = build()
    print('Saint-Thibery : tour %.0f ft, H max %.2f ft, %d sections, %d virages' % (p.s, H.max(), len(rep['sections']), len(rep['turns'])))
