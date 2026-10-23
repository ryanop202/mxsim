"""Layout + rendering engine for the compound.

World convention (validated on the references): x -> heightmap column, z -> heightmap row,
units = MX Simulator world units (inferred: feet). Heading theta: direction (cos t, sin t) in (x, z);
seen from above with z pointing 'down' on the image, a LEFT turn decreases theta.
"""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import json, numpy as np
from scipy import ndimage as ndi

def _load(p):
    return json.load(open(p)) if _os.path.exists(p) else {}   # tolerant: first run of the analysis chain


LIB = _load(ROOT + '/lib/library.json')


class Path:
    def __init__(self, x, z, heading_deg, name=''):
        self.x, self.z, self.t = float(x), float(z), np.radians(heading_deg)
        self.segs = []; self.name = name; self.s = 0.0

    def straight(self, L, sections=(), tag='', grade=None):
        x0, z0 = self.x, self.z
        self.x += L * np.cos(self.t); self.z += L * np.sin(self.t)
        self.segs.append(dict(kind='S', s0=self.s, L=float(L), x0=x0, z0=z0, t=self.t, sections=list(sections), tag=tag, grade=grade))
        self.s += L; return self

    def turn(self, ang_deg, r, berm=None, tag=''):
        """ang_deg > 0 = LEFT turn, < 0 = RIGHT turn. r = riding-line radius."""
        a = np.radians(ang_deg); left = ang_deg > 0
        n = np.array([np.sin(self.t), -np.cos(self.t)]) if left else np.array([-np.sin(self.t), np.cos(self.t)])
        cx, cz = self.x + r * n[0], self.z + r * n[1]
        t0 = self.t; self.t = self.t - a  # left decreases heading
        # new position: rotate (pos-centre) by -a
        px, pz = self.x - cx, self.z - cz; ca, sa = np.cos(-a), np.sin(-a)
        self.x, self.z = cx + ca * px - sa * pz, cz + sa * px + ca * pz
        L = abs(a) * r
        self.segs.append(dict(kind='T', s0=self.s, L=float(L), cx=cx, cz=cz, r=float(r), ang=float(ang_deg), t0=t0, t1=self.t, berm=berm, tag=tag))
        self.s += L; return self

    def samples(self, ds=0.5):
        X, Z, TH, S, SEG = [], [], [], [], []
        for k, g in enumerate(self.segs):
            n = max(2, int(np.ceil(g['L'] / ds)))
            u = np.linspace(0, g['L'], n, endpoint=False)
            if g['kind'] == 'S':
                X.append(g['x0'] + u * np.cos(g['t'])); Z.append(g['z0'] + u * np.sin(g['t'])); TH.append(np.full(n, g['t']))
            else:
                a = np.radians(g['ang']) * u / g['L']; th = g['t0'] - a
                left = g['ang'] > 0
                # position on arc: centre + r * (-normal rotated)
                n0 = np.array([np.sin(g['t0']), -np.cos(g['t0'])]) if left else np.array([-np.sin(g['t0']), np.cos(g['t0'])])
                vx, vz = -n0[0] * g['r'], -n0[1] * g['r']  # centre -> start point
                ca, sa = np.cos(-a), np.sin(-a)
                X.append(g['cx'] + ca * vx - sa * vz); Z.append(g['cz'] + sa * vx + ca * vz); TH.append(th)
            S.append(g['s0'] + u); SEG.append(np.full(n, k))
        return dict(x=np.concatenate(X), z=np.concatenate(Z), th=np.concatenate(TH), s=np.concatenate(S), seg=np.concatenate(SEG))

    def closure(self):
        g0 = self.segs[0]; x0 = g0['x0'] if g0['kind'] == 'S' else None
        return self.x, self.z, np.degrees(self.t) % 360


def sx_wall(d):
    """Measured normalized lateral wall: d = distance outward from the lane top edge."""
    W = LIB['sx_lateral']; w = np.asarray(W['wall'])
    i = (np.asarray(d) - W['wall_d0']) / W['wall_step']
    return np.interp(i, np.arange(len(w)), w, left=1.0, right=0.0)


def section_profile(sid, elems=None):
    """Return 1D as-built profile (0.1 ft step) of a measured SX section, optionally restricted to element indices [i0, i1]."""
    S = LIB['sx_sections'][sid]; p = np.asarray(S['prof'])
    if elems is None: return p
    E = S['elements']; i0, i1 = elems
    a = E[i0]['foot0'] - 1.0; b = E[i1]['foot1'] + 1.0
    ia, ib = max(0, int(a / 0.1)), min(len(p), int(b / 0.1) + 1)
    q = p[ia:ib].copy()
    # make the cut ends clean: taper the first/last 1 ft to 0 only if they are on the floor already
    return q


class Grid:
    def __init__(self, n_exp=11, s=0.4):
        self.n_exp = n_exp; self.s = s; self.N = 2 ** (n_exp + 1) + 1; self.size = (self.N - 1) * s
        self.H = np.zeros((self.N, self.N), np.float64)

    def window(self, x0, x1, z0, z1):
        j0 = max(0, int(np.floor(x0 / self.s))); j1 = min(self.N, int(np.ceil(x1 / self.s)) + 1)
        i0 = max(0, int(np.floor(z0 / self.s))); i1 = min(self.N, int(np.ceil(z1 / self.s)) + 1)
        jj, ii = np.meshgrid(np.arange(j0, j1), np.arange(i0, i1))
        return (slice(i0, i1), slice(j0, j1)), jj * self.s, ii * self.s


def render_lane_block(grid, out, seg, profile, u0, top_width, base=0.0, mode='max'):
    """Extrude a 1D profile along a straight segment, starting at distance u0 from the segment start."""
    L = len(profile) * 0.1; c, s_ = np.cos(seg['t']), np.sin(seg['t'])
    half = top_width / 2 + 8.0
    pts = []
    for uu in (u0, u0 + L):
        for vv in (-half, half):
            pts.append((seg['x0'] + uu * c - vv * s_, seg['z0'] + uu * s_ + vv * c))
    pts = np.array(pts)
    sl, X, Z = grid.window(pts[:, 0].min(), pts[:, 0].max(), pts[:, 1].min(), pts[:, 1].max())
    dx, dz = X - seg['x0'], Z - seg['z0']
    u = dx * c + dz * s_ - u0; v = -dx * s_ + dz * c
    pu = np.interp(u / 0.1, np.arange(len(profile)), profile, left=0, right=0)
    h = pu * sx_wall(np.abs(v) - top_width / 2) + base
    if mode == 'max': out[sl] = np.maximum(out[sl], h)
    return sl


def render_crescent(grid, out, cx, cz, mid_angle, fam, base=0.0):
    """SX crescent berm from the measured radial profile and measured angular taper."""
    F = LIB[fam]; prof = np.asarray(F['prof']); R = F['R_crest']
    rr_rel = F['r_rel0'] + np.arange(len(prof)) * F['step']
    rmax = R + rr_rel[-1]
    sl, X, Z = grid.window(cx - rmax, cx + rmax, cz - rmax, cz + rmax)
    dx, dz = X - cx, Z - cz; r = np.hypot(dx, dz)
    ang = np.degrees(np.arctan2(dz, dx)) - np.degrees(mid_angle); ang = (ang + 180) % 360 - 180
    radial = np.interp(r - R, rr_rel, prof, left=0, right=0)
    if 'taper' in F:
        td = np.asarray(F['taper_deg']); tp = np.asarray(F['taper'])
        span_ref = td.max() - td.min(); span = F['span_deg_use'] if 'span_deg_use' in F else span_ref
        tap = np.interp(ang * span_ref / span, td, tp, left=0, right=0)
    else:
        half = F['span_deg'] / 2
        tap = np.clip((half - np.abs(ang)) / 20.0, 0, 1); tap = np.sin(tap * np.pi / 2) ** 2
    h = radial * tap + base
    out[sl] = np.maximum(out[sl], h)
    return sl


BERMS = _load(ROOT + '/lib/berm_stamps.json')


def render_berm_stamp(grid, out, key, cx, cz, mid_angle, base=0.0, mirror=False, ang_scale=1.0):
    """Paste a measured crescent (2D as-built stamp), rotated so its mid-angle matches the turn's outer bisector.
    ang_scale > 1 compresses the crescent around its bisector (radial profile unchanged): used to put a 180-degree
    big berm on a 90-degree turn without its ends sticking out over the approach and exit lanes (v4, SX2 T1 'rebord')."""
    B = BERMS[key]; P = np.load(f'{ROOT}/lib/berm_{key}.npy').astype(np.float64)
    rad = max(P.shape) * B['s'] * 0.75
    sl, X, Z = grid.window(cx - rad, cx + rad, cz - rad, cz + rad)
    dx, dz = X - cx, Z - cz
    keep = np.ones(dx.shape, bool)
    if ang_scale != 1.0:
        r = np.hypot(dx, dz); a = (np.arctan2(dz, dx) - mid_angle + np.pi) % (2 * np.pi) - np.pi
        a2 = a * ang_scale; keep = np.abs(a2) < np.pi
        dx, dz = r * np.cos(mid_angle + a2), r * np.sin(mid_angle + a2)
    rot = B['mid_angle'] - mid_angle
    if mirror:  # reflect across the mid-angle axis
        a = np.arctan2(dz, dx); r = np.hypot(dx, dz); a = 2 * mid_angle - a; dx, dz = r * np.cos(a), r * np.sin(a)
    c, s_ = np.cos(rot), np.sin(rot)
    sx = B['cx'] + c * dx - s_ * dz; sz = B['cz'] + s_ * dx + c * dz
    col = (sx - B['x0']) / B['s']; row = (sz - B['z0']) / B['s']
    h = np.where(keep, ndi.map_coordinates(P, [row, col], order=1, cval=0.0), 0.0) + base
    out[sl] = np.maximum(out[sl], h)
    return sl


def berm_ang_scale(key, ang_deg):
    """Big crescents measure 130 deg for 180-deg turns (ends 25 deg inside the turn). On a shorter turn, compress them
    so their ends stay at the turn tangents. Small crescents (105 deg, built for 90-deg turns) are never changed."""
    if key and key.startswith('big') and abs(ang_deg) < 170:
        return 130.0 / abs(ang_deg)
    return 1.0


def turn_mid_angle(seg):
    """Direction from turn centre to the arc midpoint (outer bisector)."""
    left = seg['ang'] > 0
    n0 = np.array([np.sin(seg['t0']), -np.cos(seg['t0'])]) if left else np.array([-np.sin(seg['t0']), np.cos(seg['t0'])])
    a0 = np.arctan2(-n0[1], -n0[0])  # centre -> start point
    return a0 - np.radians(seg['ang']) / 2


def render_sx(grid, out, path, base=0.0, top_width=None, log=None):
    tw = top_width or LIB['sx_lateral']['top_width']
    for g in path.segs:
        if g['kind'] == 'S':
            for sec in g['sections']:
                sid, u0 = sec[0], sec[1]; elems = sec[2] if len(sec) > 2 else None
                p = section_profile(sid, elems)
                render_lane_block(grid, out, g, p, u0, tw, base)
                if log is not None: log.append(dict(path=path.name, s=g['s0'] + u0, sid=sid, elems=elems, L=len(p) * 0.1, Hmax=float(p.max())))
        elif g.get('berm'):
            render_berm_stamp(grid, out, g['berm'], g['cx'], g['cz'], turn_mid_angle(g), base)


def fillet_path(corners, start_xz, name='', sections=None, berms=None, tags=None):
    """Closed polyline with filleted corners. corners: list of (x, z, r) in travel order; the path starts at
    start_xz (a point on the edge from the last corner to the first one) and ends there.
    sections: dict edge_index -> list of section tuples; edge i goes from corner i-1 to corner i (edge 0 = start edge).
    berms: dict corner_index -> berm key/flag."""
    sections = sections or {}; berms = berms or {}; tags = tags or {}
    C = np.array([(c[0], c[1]) for c in corners], float); R = [c[2] for c in corners]; n = len(C)
    # tangent points
    T_in, T_out, ANG = [], [], []
    for i in range(n):
        p_prev, p, p_next = C[i - 1], C[i], C[(i + 1) % n]
        a = (p - p_prev) / np.linalg.norm(p - p_prev); b = (p_next - p) / np.linalg.norm(p_next - p)
        th = np.arctan2(a[0] * b[1] - a[1] * b[0], a @ b)  # signed turn angle (+ = clockwise on image = RIGHT)
        d = R[i] * np.tan(abs(th) / 2)
        T_in.append(p - a * d); T_out.append(p + b * d); ANG.append(np.degrees(th))
    sx, sz = start_xz
    a = (C[0] - C[-1]); h0 = np.degrees(np.arctan2(a[1], a[0]))
    P = Path(sx, sz, h0, name)
    P.corner_info = []
    for i in range(n):
        L = np.linalg.norm(T_in[i] - np.array([P.x, P.z]))
        P.straight(L, sections.get(i, []), tag=tags.get(('e', i), f'edge{i}'))
        # ANG > 0 means right turn in image coords (z down) -> Path.turn uses +left
        P.turn(-ANG[i], R[i], berms.get(i), tag=tags.get(('c', i), f'corner{i}'))
        P.corner_info.append(dict(i=i, ang=-ANG[i], r=R[i]))
    L = np.linalg.norm(np.array([sx, sz]) - np.array([P.x, P.z]))
    P.straight(L, sections.get(n, []), tag=tags.get(('e', n), 'start edge (end)'))
    return P


# ---------------------------------------------------------------- measured 2D stamps with their own riding line (Glendale sand)
STAMPS = _load(ROOT + '/lib/sand_stamps.json')


def _stamp_frame(key, pose_xz, heading, mirror=False):
    """Rigid transform ref -> world mapping the stamp's first line point/heading onto the given pose.
    mirror=True reflects the stamp across its entry line first (left-hand version of a right-hand turn)."""
    L = np.asarray(STAMPS[key]['line'], float)
    h_ref = np.arctan2(L[5, 1] - L[0, 1], L[5, 0] - L[0, 0])
    th = heading - h_ref; c, s_ = np.cos(th), np.sin(th)
    Rm = np.array([[c, -s_], [s_, c]]); p0 = L[0]; W0 = np.asarray(pose_xz, float)
    if mirror:
        ch, sh = np.cos(2 * h_ref), np.sin(2 * h_ref); M = np.array([[ch, sh], [sh, -ch]])
    else:
        M = np.eye(2)
    A = Rm @ M
    fwd = lambda P: (np.asarray(P, float) - p0) @ A.T + W0
    inv = lambda Q: (np.asarray(Q, float) - W0) @ np.linalg.inv(A).T + p0
    return fwd, inv, th


def _path_stamp(self, key, tag='', snap=True, mirror=False):
    fwd, inv, th = _stamp_frame(key, (self.x, self.z), self.t, mirror)
    L = np.asarray(STAMPS[key]['line'], float); W = fwd(L)
    seglen = np.r_[0, np.cumsum(np.hypot(*np.diff(W, axis=0).T))]
    h_out = np.arctan2(W[-1, 1] - W[-6, 1], W[-1, 0] - W[-6, 0])
    if snap:   # snap the exit heading to the lane grid if within 4 deg (the kink happens on the sand floor)
        q = np.round(h_out / (np.pi / 2)) * (np.pi / 2)
        if abs(q - h_out) < np.radians(4): h_out = q
    self.segs.append(dict(kind='P', s0=self.s, L=float(seglen[-1]), pts=W, cum=seglen, stamp=key, th=float(th), tag=tag, mirror=mirror,
                          t_in=self.t, t_out=float(h_out)))
    self.x, self.z = float(W[-1, 0]), float(W[-1, 1]); self.t = float(h_out); self.s += float(seglen[-1])
    return self


Path.stamp = _path_stamp
_old_samples = Path.samples


def _samples(self, ds=0.5):
    X, Z, TH, S, SEG = [], [], [], [], []
    for k, g in enumerate(self.segs):
        n = max(2, int(np.ceil(g['L'] / ds))); u = np.linspace(0, g['L'], n, endpoint=False)
        if g['kind'] == 'P':
            x = np.interp(u, g['cum'], g['pts'][:, 0]); z = np.interp(u, g['cum'], g['pts'][:, 1])
            th = np.arctan2(np.gradient(z), np.gradient(x))
        elif g['kind'] == 'S':
            x = g['x0'] + u * np.cos(g['t']); z = g['z0'] + u * np.sin(g['t']); th = np.full(n, g['t'])
        else:
            a = np.radians(g['ang']) * u / g['L']; th = g['t0'] - a
            left = g['ang'] > 0
            n0 = np.array([np.sin(g['t0']), -np.cos(g['t0'])]) if left else np.array([-np.sin(g['t0']), np.cos(g['t0'])])
            vx, vz = -n0[0] * g['r'], -n0[1] * g['r']; ca, sa = np.cos(-a), np.sin(-a)
            x = g['cx'] + ca * vx - sa * vz; z = g['cz'] + sa * vx + ca * vz
        X.append(x); Z.append(z); TH.append(th); S.append(g['s0'] + u); SEG.append(np.full(n, k))
    return dict(x=np.concatenate(X), z=np.concatenate(Z), th=np.concatenate(TH), s=np.concatenate(S), seg=np.concatenate(SEG))


Path.samples = _samples


def render_stamp(grid, out_h, out_t, seg, tile_map):
    """Paste a stamp (heights + reference tiles remapped through tile_map) with the segment's rigid transform."""
    key = seg['stamp']; St = STAMPS[key]
    P = np.load(f'{ROOT}/lib/sand_{key}.npy').astype(np.float64); Tt = np.load(f'{ROOT}/lib/sand_{key}_tiles.npy')
    fwd, inv, th = _stamp_frame(key, seg['pts'][0], seg['t_in'], seg.get('mirror', False))
    h_, w_ = P.shape; corners = np.array([[St['x0'], St['z0']], [St['x0'] + w_ * St['s'], St['z0']], [St['x0'], St['z0'] + h_ * St['s']], [St['x0'] + w_ * St['s'], St['z0'] + h_ * St['s']]])
    Wc = fwd(corners)
    sl, X, Z = grid.window(Wc[:, 0].min(), Wc[:, 0].max(), Wc[:, 1].min(), Wc[:, 1].max())
    R = inv(np.c_[X.ravel(), Z.ravel()])
    col = (R[:, 0] - St['x0']) / St['s']; row = (R[:, 1] - St['z0']) / St['s']
    hv = ndi.map_coordinates(P, [row, col], order=1, cval=0.0).reshape(X.shape)
    tv = ndi.map_coordinates(Tt.astype(np.float64), [np.round(row), np.round(col)], order=0, cval=255).reshape(X.shape).astype(int)
    out_h[sl] = np.maximum(out_h[sl], hv)
    if out_t is not None:
        tt = out_t[sl]
        for src, dst in tile_map.items(): tt[tv == src] = dst
        out_t[sl] = tt
    return sl
