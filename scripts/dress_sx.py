"""v9 'habillage': everything around the terrain that JGSX 2026 tracks have, placed with the JGSX rules measured on
Detroit / Glendale (see docs/11_habillage.md):
  - start gates (gate01.jm) on the 22 grid positions of timing_gates;
  - surrounding landscape ET.jm (JGSX 593 ft arena hole) re-cut for the 1187 ft compound terrain (hole x2, ring unchanged);
  - chain-link fence (13.11 ft panels) around each track, light poles at the fence corners, 2.jm markers at big-turn centres;
  - pit cluster (vans, semi, water truck + tank, Matrix + EZ-up, dozer, bobcat) on a gravel strip outside each fence;
  - decals: track.png on every riding surface (incl. start straight), sand.png in the Glendale sand, one obstacle decal per unit
    (single / whoops / table / tripleface / triplemiddle), 180 / 90 on berm turns, tear-offs, gravel under the pits;
  - flaggers: 30-second board at the gate row, finish flagger at the finish gate.
All three folders get the whole world (the three tracks share one terrain); gates and flaggers are per track.
Run after export_sx.py:  python3 scripts/dress_sx.py
"""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import os, sys, json, shutil, numpy as np
sys.path.insert(0, ROOT + '/scripts')
from scipy import ndimage as ndi
from scipy.signal import find_peaks
import layouts_sx as LS
from mxs import parse_gates

OUT = ROOT + '/tracks'; BUILD = ROOT + '/build'
DET = f'{REF}/JGSX2026TestTracks/JGSX2026Detroit'
from names import FOLDERS as F
A = f'{OUT}/{F["SX1"]}'; P = '@' + F['SX1']
H = np.load(f'{BUILD}/H.npy').astype(np.float64); S = 0.28975; N = H.shape[0]; SIZE = (N - 1) * S
rng = np.random.default_rng(2026)
UJ = json.load(open(ROOT + '/lib/sx_units.json'))

def ang_of(fx, fz):
    """MXS statue/decal angle whose local z axis points along (fx, fz) (same convention as the start gates)."""
    return float(np.arctan2(-fx, -fz))

# ------------------------------------------------------------------ assets
STATUES = ['gate01', 'chainlink', '2', 'lightpole', 'transit', 'watertruck', 'watertank', 'semi_1', 'matrixa2', 'ezup', 'dozer', 'bobcat']
DECALS = ['track', 'sand', 'gravel', 'single', 'whoops', 'tripleface', 'triplemiddle', 'table', '90', '180', 'Tearoff']
def copy_assets():
    for sub in ('statue', 'decal'): os.makedirs(f'{A}/{sub}', exist_ok=True)
    for f in os.listdir(f'{DET}/statue'):
        base = f.split('.')[0].split('_')[0]
        if f.endswith('.shp') or any(f.startswith(s + '.') or f.startswith(s + '_') for s in STATUES) or f.startswith('transit') or f.startswith('ws_semiskin'):
            if f != 'ET.jm': shutil.copy(f'{DET}/statue/{f}', f'{A}/statue/{f}')
    shutil.copy(f'{DET}/statue/ET.png', f'{A}/statue/ET.png'); shutil.copy(f'{DET}/statue/ET_spec.png', f'{A}/statue/ET_spec.png')
    for f in ('tuff-medium.jm', 'tuff_mechanic_autumn.png', 'tuff_mechanic_autumn_norm.png', 'tuff_mechanic_alpha.png'):   # v10 tuff blocks
        shutil.copy(f'{DET}/seq/{f}', f'{A}/statue/{f}')
    for d in DECALS:
        for suf in ('', '_tnorm', '_tspec'):
            src = f'{DET}/decal/{d}{suf}.png'
            if os.path.exists(src): shutil.copy(src, f'{A}/decal/{d}{suf}.png')

def make_environment():
    """JGSX ET.jm = landscape ring around a 593.4 ft hole. Hole stretched x2 (piecewise, ring geometry unchanged) -> 1186.8 ft."""
    L = open(f'{DET}/statue/ET.jm').read().split('\n'); nv = int(L[2].split()[0])
    hole = 593.4; k = SIZE / hole
    def m(v): return np.where(v < 0, v, np.where(v <= hole, v * k, v + (SIZE - hole)))
    out = L[:3]
    for l in L[3:3 + nv]:
        p = l.split(); x, y, z = float(p[0]), float(p[1]), float(p[2])
        out.append(' '.join([f'{float(m(x)):.6f}', p[1], f'{float(m(z)):.6f}'] + p[3:]))
    out += L[3 + nv:]
    open(f'{A}/statue/ET_compound.jm', 'w').write('\n'.join(out))

# ------------------------------------------------------------------ geometry of the three tracks
PATHS = {'SX1': LS.sx1(), 'SX2': LS.sx2(), 'SX3': LS.sx3()}
from starts import StartRoute
ROUTES = {k: StartRoute(LS.STARTS[k], LS.N_GATES, LS.GATE_PITCH) for k in PATHS}
def start_corridor(key):
    S0 = LS.STARTS[key]; h = np.radians(S0['heading']); f = np.array([np.cos(h), np.sin(h)]); n = np.array([-f[1], f[0]])
    g = np.array(S0['gate']); M = np.array(S0['merge'])
    return g, f, n, None, M, S0

def riding_mask():
    """Per track: riding surface (path +-17 ft, start straight + funnel), and footprint (riding surface + obstacles + berms)."""
    yy, xx = np.mgrid[0:N:4, 0:N:4] * S   # 1.16 ft cells
    from scipy.spatial import cKDTree
    masks = {}
    Hs = H[::4, ::4]
    for key, p in PATHS.items():
        smp = p.samples(1.0); tr = cKDTree(np.c_[smp['x'], smp['z']])
        d, _ = tr.query(np.c_[xx.ravel(), yy.ravel()]); d = d.reshape(xx.shape)
        ride = d < 17.0
        X_, Z_, S_, B_ = ROUTES[key].area_points(1.0, 1.0, margin=-2.0)      # start corridor (+2 ft)
        g, f, n, b, M, S0 = start_corridor(key)
        for u in np.arange(-12, 0, 1.0):                                       # behind the gate row
            for v in np.arange(-ROUTES[key].W0 / 2, ROUTES[key].W0 / 2, 1.0):
                X_ = np.append(X_, g[0] + f[0] * u + n[0] * v); Z_ = np.append(Z_, g[1] + f[1] * u + n[1] * v)
        ci = (Z_ / (4 * S)).astype(int).clip(0, xx.shape[0] - 1); cj = (X_ / (4 * S)).astype(int).clip(0, xx.shape[1] - 1)
        ride[ci, cj] = True; ride = ndi.binary_closing(ride, iterations=1)
        masks[key] = dict(ride=ride, dist=d)
    near = np.argmin(np.stack([masks[k]['dist'] for k in PATHS]), axis=0)   # every obstacle pixel belongs to its nearest track
    for i, key in enumerate(PATHS):
        foot = masks[key]['ride'] | ((Hs > 0.02) & (masks[key]['dist'] < 70) & (near == i))
        masks[key]['foot'] = ndi.binary_closing(foot, iterations=3)
    return masks, xx, yy

# ------------------------------------------------------------------ statues
def statue(x, z, a, model, tex, shape='null', y=0.0):
    return f'[{x:.6f} {y:.6f} {z:.6f}] {a:.6f} {P}/statue/{model}.jm {P}/statue/{tex}.png {shape if shape == "null" else P + "/statue/" + shape}'

def fence_rect(key, masks, xx, yy, margin=14.0):
    fm = masks[key]['foot']; zs, xs = np.nonzero(fm)
    return (xs.min() * 4 * S - margin, xs.max() * 4 * S + margin, zs.min() * 4 * S - margin, zs.max() * 4 * S + margin)

PANEL = 13.11   # chainlink.jm panel length (Detroit spacing)
def fence(rect):
    x0, x1, z0, z1 = rect; out = []
    for (ax, az, bx, bz) in ((x0, z0, x1, z0), (x1, z0, x1, z1), (x1, z1, x0, z1), (x0, z1, x0, z0)):
        L = np.hypot(bx - ax, bz - az); n = int(np.ceil(L / PANEL)); fx, fz = (bx - ax) / L, (bz - az) / L
        for i in range(n):
            t = (i + 0.5) * L / n; out.append((ax + fx * t, az + fz * t, ang_of(fx, fz)))
    return out

# Detroit pit cluster, relative to its fence top side (fence z = 99, centre x = 295): u along the side, w outward
DET_FENCE_Z, PIT_U0 = 99.0, 466.0
PITS = [('transit', 'transit-jgmx', 542.1, 87.1, 3.1286), ('transit', 'transit-donut', 554.6, 87.2, 3.1321),
        ('transit', 'transit-smidly', 567.4, 87.1, 3.1316), ('watertruck', 'watertruck', 394.0, 90.8, 1.5541),
        ('watertank', 'watertank', 354.7, 90.8, -3.1416), ('semi_1', 'ws_semiskin', 442.0, 94.0, -1.5838),
        ('matrixa2', 'matrixa2', 578.4, 89.5, -0.0004), ('ezup', 'ezup', 578.4, 89.6, -0.0004),
        ('dozer', 'dozer', 330.0, 80.0, -0.0159), ('bobcat', 'bobcat', 316.0, 80.0, -3.1416)]

def side_frame(rect, side):
    """origin = middle of the fence side, e = along the side, o = outward normal; returns (origin, e, o, length)."""
    x0, x1, z0, z1 = rect
    if side == 'top': return np.array([(x0 + x1) / 2, z0]), np.array([1.0, 0]), np.array([0, -1.0]), x1 - x0
    if side == 'bottom': return np.array([(x0 + x1) / 2, z1]), np.array([1.0, 0]), np.array([0, 1.0]), x1 - x0
    if side == 'right': return np.array([x1, (z0 + z1) / 2]), np.array([0, 1.0]), np.array([1.0, 0]), z1 - z0
    if side == 'left': return np.array([x0, (z0 + z1) / 2]), np.array([0, 1.0]), np.array([-1.0, 0]), z1 - z0

def pits(rect, side, shift=0.0):
    o0, e, o, L = side_frame(rect, side); st = []; grav = []
    rot = np.arctan2(e[1], e[0])   # Detroit side runs along +x: rotate model angles by the same amount (angle grows clockwise)
    for model, tex, x, z, a in PITS:
        u = x - PIT_U0 + shift; w = DET_FENCE_Z - z + 22.0
        p = o0 + e * u + o * w
        st.append((p[0], p[1], a - rot, model, tex))
    for u in np.arange(-L / 2 + 6, L / 2 - 6, 5.9):
        for w in np.arange(30, 74, 5.9):
            p = o0 + e * u + o * w; grav.append((p[0], p[1], rng.uniform(-np.pi, np.pi)))
    return st, grav

# ------------------------------------------------------------------ decals
def decal(x, z, a, size, tex):
    return f'[{x:.6f} {z:.6f}] {a:.6f} {size:.6f} 1.000000 {P}/decal/{tex}.png'

def unit_info(item_name):
    if item_name.startswith('whoops'): return 'whoops', None
    if item_name.startswith('split'): return 'single', None
    uid = UJ['alias'].get(item_name, item_name); u = UJ['units'][uid]; return u['kind'], u

def obstacle_decals(p):
    out = []
    for g in p.segs:
        if g['kind'] != 'S': continue
        c, s_ = np.cos(g['t']), np.sin(g['t']); a = ang_of(c, s_)
        for prof, u0, name in g['sections']:
            for it in LS.COMBOS[name]['items']:
                nm, st, en, hh = it; kind, u = unit_info(nm); L = en - st
                if kind == 'whoops':
                    seg = prof[int(st / 0.1):int(en / 0.1)]; pk, _ = find_peaks(seg, prominence=0.8, distance=60)
                    for k in pk:
                        uu = u0 + st + k * 0.1; out.append(decal(g['x0'] + uu * c, g['z0'] + uu * s_, a, 110.0, 'whoops'))
                    continue
                uu = u0 + (st + en) / 2; x, z = g['x0'] + uu * c, g['z0'] + uu * s_
                if hh >= 6.6 or kind == 'X':  tex, cl = 'tripleface', 79.1
                elif L >= 52 or kind in ('T', 'combo'): tex, cl = 'table', 63.4
                else: tex, cl = 'single', 47.5
                size = max(110.0, 110.0 * (L + 14) / cl)
                out.append(decal(x, z, a, size, tex))
                if tex == 'tripleface' and L > 70:     # long big jumps: middle decal as at Detroit
                    out.append(decal(x, z, a, 110.0, 'triplemiddle'))
    return out

def turn_decals(p):
    out = []
    for g in p.segs:
        if g['kind'] == 'T' and g.get('berm'):
            from engine import turn_mid_angle
            m = turn_mid_angle(g); fx, fz = np.cos(m), np.sin(m)
            if abs(g['ang']) > 120: out.append(decal(g['cx'] + fx * 9, g['cz'] + fz * 9, ang_of(fx, fz), 110.0, '180'))
            else: out.append(decal(g['cx'] + fx * 14, g['cz'] + fz * 14, ang_of(fx, fz), 110.0, '90'))
    return out

def surface_decals(key, masks, xx, yy):
    """track.png (sand.png in the Glendale sand) every ~3.9 x 5.2 ft over the riding surface, random rotation (Detroit density)."""
    out = []; p = PATHS[key]; smp = p.samples(3.9)
    sand_seg = {k for k, g in enumerate(p.segs) if g['kind'] == 'P'}
    for x, z, th, sg in zip(smp['x'], smp['z'], smp['th'], smp['seg']):
        nx, nz = -np.sin(th), np.cos(th)
        if int(sg) in sand_seg: continue                 # sand: decals laid on the sand tiles themselves (sand_decals)
        tex = 'track'
        for v in (-10.4, -5.2, 0.0, 5.2, 10.4):
            j = rng.normal(0, 0.8, 2)
            out.append(decal(x + nx * v + j[0], z + nz * v + j[1], rng.uniform(-np.pi, np.pi), 26.0, tex))
    X_, Z_, S_, B_ = ROUTES[key].area_points(4.5, 5.5, margin=2.0)
    for x, z in zip(X_, Z_): out.append(decal(x + rng.normal(0, 0.6), z + rng.normal(0, 0.6), rng.uniform(-np.pi, np.pi), 26.0, 'track'))
    # tear-offs: ~50 per track, on the riding line
    idx = rng.choice(len(smp['x']), 50, replace=False)
    for i in idx:
        out.append(decal(smp['x'][i] + rng.normal(0, 5), smp['z'][i] + rng.normal(0, 5), rng.uniform(-np.pi, np.pi), 4.84, 'Tearoff'))
    return out

def sand_decals():
    """sand.png (26 ft, as Glendale) every 6 ft on the sand tiles (tilemap cells 4..7)."""
    T = np.load(f'{BUILD}/tiles.npy'); cs = SIZE / T.shape[0]; out = []
    sand = np.isin(T, (4, 5, 6, 7)); sand = ndi.binary_opening(sand, iterations=2)
    step = int(round(6.0 / cs))
    for i in range(0, T.shape[0], step):
        for j in range(0, T.shape[1], step):
            if sand[i, j]:
                out.append(decal(j * cs + rng.normal(0, 1), i * cs + rng.normal(0, 1), rng.uniform(-np.pi, np.pi), 26.0, 'sand'))
    return out

TUFF_LEN = 5.6   # tuff-medium.jm is 5.4 ft long
def tuff_rows():
    """v10 delimitations: tuff blocks wherever two parts of a lap (or a lap and a start corridor) run close to each other but far
    apart along the lap - i.e. where a rider could cut: on the median between adjacent lanes, between the sand J and its neighbours,
    and along both sides of every start corridor. Never on a riding surface, an obstacle, a crossing or a merge."""
    from scipy.spatial import cKDTree
    lines = []; cand = []
    for key, p in PATHS.items():
        smp = p.samples(2.0); P_ = np.c_[smp['x'], smp['z']]; tr = cKDTree(P_)
        pr = tr.query_pairs(70.0, output_type='ndarray'); far = np.abs(smp['s'][pr[:, 0]] - smp['s'][pr[:, 1]]); far = np.minimum(far, p.s - far)
        pr = pr[far > 110]
        for a, b in pr:
            A, B = P_[a], P_[b]; m = (A + B) / 2; u = (B - A) / max(np.linalg.norm(B - A), 1e-6)
            cand.append((m[0], m[1], -u[1], u[0], key))
        lines.append(P_)
        R = ROUTES[key]; rs = R.samples(TUFF_LEN)
        for x, z, th, sv, w in zip(rs['x'], rs['z'], rs['th'], rs['s'], rs['w']):
            if sv > R.L - 25: continue
            nx, nz = -np.sin(th), np.cos(th)
            for sg in (-1, 1): cand.append((x + sg * nx * (w / 2 + 3.5), z + sg * nz * (w / 2 + 3.5), np.cos(th), np.sin(th), key))
    allp = np.vstack(lines); trall = cKDTree(allp)
    corr = [ROUTES[k].area_points(2.0, 2.0, margin=-1.5) for k in PATHS]
    trc = cKDTree(np.vstack([np.c_[c[0], c[1]] for c in corr]))
    marks = np.array([(g['cx'], g['cz']) for p in PATHS.values() for g in p.segs if g['kind'] == 'T' and g.get('berm') and g['r'] > 20])
    out, kept = [], []
    cand = sorted(cand, key=lambda c: (round(c[0] / 50), round(c[1] / 50), c[0], c[1]))
    kd_kept = None
    for x, z, ex, ez, key in cand:
        if not (2 < x < SIZE - 2 and 2 < z < SIZE - 2): continue
        if trall.query([x, z])[0] < 20.2: continue                        # >= lane half width + wall + block half width
        if len(marks) and np.min(np.hypot(marks[:, 0] - x, marks[:, 1] - z)) < 4: continue
        fx = np.array([ex, ez]); q = np.array([[x, z]]) + np.outer(np.linspace(-2.8, 2.8, 5), fx)
        q = np.vstack([q + np.array([-fx[1], fx[0]]) * o for o in (-1.0, 0, 1.0)])
        hh = H[(q[:, 1] / S).astype(int).clip(0, N - 1), (q[:, 0] / S).astype(int).clip(0, N - 1)]
        if hh.max() > 0.65: continue                                       # flat median, or the very foot of two jump walls
        if trc.query(q)[0].min() < 1.0: continue                          # never inside a start corridor (+1.5 ft)
        if kept and np.min(np.hypot(np.array(kept)[:, 0] - x, np.array(kept)[:, 1] - z)) < TUFF_LEN: continue
        kept.append((x, z)); out.append((x, z, ang_of(ex, ez), float(hh.min())))
    return out

def write_tuff_shape():
    """collision shape for the tuff block, same format as JGSX cone.shp (count, then x y z + 4 parameters per sphere)."""
    lines = ['4'] + [f'0 0.6 {z:.6f}  1 1 300 20' for z in (-2.0, -0.7, 0.7, 2.0)]
    open(f'{A}/statue/tuff.shp', 'w').write('\n'.join(lines) + '\n')

def roads(masks, rects):
    """v10 concrete service roads (tile 'Road' = 8): an 18 ft ring 3 ft outside every fence + an east-west avenue between the
    top tracks and SX3; never on a fenced area, a riding surface or an obstacle."""
    cs = SIZE / 2048; jj, ii = np.meshgrid(np.arange(2048), np.arange(2048)); X = (jj + 0.5) * cs; Z = (ii + 0.5) * cs
    road = np.zeros((2048, 2048), bool); inside = np.zeros_like(road)
    for x0, x1, z0, z1 in rects.values():
        o = np.maximum.reduce([x0 - X, X - x1, z0 - Z, Z - z1])     # >0 outside the rectangle (Chebyshev distance)
        road |= (o > 3) & (o < 21); inside |= o < 3
    zr = (rects['SX1'][3] + rects['SX3'][2]) / 2
    road |= (np.abs(Z - zr) < 9) & (X > 8) & (X < SIZE - 8)
    Hc = H[1::2, 1::2][:2048, :2048]
    busy = inside | (Hc > 0.02)
    for k in masks:
        rm = ndi.zoom(masks[k]['ride'].astype(np.uint8), 2048 / masks[k]['ride'].shape[0], order=0)[:2048, :2048].astype(bool)
        busy |= ndi.binary_dilation(rm, iterations=8)
    return road & ~busy

# ------------------------------------------------------------------ flaggers
def flaggers(key):
    g, f, n, b, M, S0 = start_corridor(key); half = (LS.N_GATES - 1) / 2 * LS.GATE_PITCH
    b1 = g - f * 25 + n * (half - 15); b2 = g - f * 25 - n * (half - 15)   # behind the gate row, like a 30 s board
    G = parse_gates(f'{OUT}/{F[key]}/timing_gates'); fin = G['cps'][G['normal'][-1]]
    cx, cz, dx, dz = fin[1], fin[3], fin[4], fin[6]; L = np.hypot(dx, dz)
    cands = [(cx + sg * dx / L * o, cz + sg * dz / L * o) for sg in (1, -1) for o in (L + 14, 21.5, 25.0)]   # 21.5 = median between lanes
    fl = max(cands, key=lambda q: MASKS[key]['dist'][int(q[1] / (4 * S)), int(q[0] / (4 * S))] - 100 * MASKS[key]['ride'][int(q[1] / (4 * S)), int(q[0] / (4 * S))])
    return '\n'.join([f'[{b1[0]:.6f} 0.000 {b1[1]:.6f}]', f'[{b2[0]:.6f} 0.000 {b2[1]:.6f}]', '8.4 1', '9',
                      '@30sec_30.png', '@30sec_turn.seq', '@30sec_5.png', '@30sec_run.seq', '@30sec_done.png', '',
                      f'[{fl[0]:.6f} 0.000 {fl[1]:.6f}]', '8 -1', '@finish_green.png', '@finish_crossed.png', '@finish_white.png',
                      '@checkerwave.seq', '', '', '', '[0.00000000 0.000 0.00000000]', '9.6 1', '3 4 5 -1',
                      '@flagger_resting.png', '@flagger_waving.seq', '']), fl, (b1, b2)

# ------------------------------------------------------------------ main
PIT_SIDES = {'SX1': ('bottom', 0.0), 'SX2': ('right', 0.0), 'SX3': ('top', -250.0)}
if __name__ == '__main__':
    copy_assets(); make_environment()
    masks, xx, yy = riding_mask(); MASKS = masks
    world_st, world_dec, report = [], [], {}
    world_st.append(f'[0.000000 -0.100000 0.000000] 0.000000 {P}/statue/ET_compound.jm {P}/statue/ET.png null')
    for key, p in PATHS.items():
        rect = fence_rect(key, masks, xx, yy); fz = fence(rect)
        for x, z, a in fz: world_st.append(statue(x, z, a, 'chainlink', 'chainlink'))
        x0, x1, z0, z1 = rect; cxm, czm = (x0 + x1) / 2, (z0 + z1) / 2
        poles = [(x0 - 8, z0 - 8), (x1 + 8, z0 - 8), (x1 + 8, z1 + 8), (x0 - 8, z1 + 8), (cxm, z0 - 8), (cxm, z1 + 8)]
        for x, z in poles: world_st.append(statue(x, z, ang_of(x - cxm, z - czm), 'lightpole', 'lightpole'))
        marks = [(g['cx'], g['cz']) for g in p.segs if g['kind'] == 'T' and g.get('berm') and g['r'] > 20]
        for x, z in marks: world_st.append(statue(x, z, -1.6, '2', '2', shape='cone.shp'))
        side, shift = PIT_SIDES[key]; pst, grav = pits(rect, side, shift)
        for x, z, a, model, tex in pst: world_st.append(statue(x, z, a, model, tex))
        world_dec += [decal(x, z, a, 18.84, 'gravel') for x, z, a in grav]
        world_dec += surface_decals(key, masks, xx, yy) + obstacle_decals(p) + turn_decals(p)
        report[key] = dict(fence=rect, n_fence=len(fz), poles=poles, markers=marks, pits=[(x, z, model) for x, z, a, model, tex in pst],
                           gravel=[(x, z) for x, z, a in grav], pit_side=side)
    rects = {k: v['fence'] for k, v in report.items()}
    world_dec += sand_decals()
    write_tuff_shape(); tf = tuff_rows()
    for x, z, a, y in tf: world_st.append(f'[{x:.6f} {y:.6f} {z:.6f}] {a:.6f} {P}/statue/tuff-medium.jm {P}/statue/tuff_mechanic_autumn.png {P}/statue/tuff.shp')
    rd = roads(masks, rects)
    for key, folder in F.items():
        t = np.fromfile(f'{OUT}/{folder}/tilemap', np.uint8).reshape(2048, 2048)
        t[rd & (t == 0)] = 8; t.tofile(f'{OUT}/{folder}/tilemap')
    report['tuffs'] = len(tf); report['road_cells'] = int(rd.sum())
    for key, folder in F.items():
        d = f'{OUT}/{folder}'
        # start gates: add the gate model to every startinggate line
        tg = open(f'{d}/timing_gates').read().split('\n'); out = []; sec = None
        for l in tg:
            if l.endswith(':'): sec = l
            elif sec == 'startinggate:' and l.startswith('[') and '@' not in l:
                l = f'{l} {P}/statue/gate01.jm {P}/statue/gate01.png @startgate.shp'
            out.append(l)
        open(f'{d}/timing_gates', 'w').write('\n'.join(out))
        open(f'{d}/statues', 'w').write('\n'.join(world_st) + '\n')
        open(f'{d}/decals', 'w').write('\n'.join(world_dec) + '\n')
        fl, fpos, boards = flaggers(key); open(f'{d}/flaggers', 'w').write(fl)
        report[key]['finish_flagger'] = fpos; report[key]['boards'] = [tuple(b) for b in boards]
    json.dump(report, open(f'{BUILD}/dress_report.json', 'w'), indent=1, default=float)
    print('statues', len(world_st), 'decals', len(world_dec), 'tuffs', report['tuffs'], 'road cells', report['road_cells'], {k: (v['pit_side'], [round(x) for x in v['fence']]) for k, v in report.items() if isinstance(v, dict)})
