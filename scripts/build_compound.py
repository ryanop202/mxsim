"""Build the shared compound terrain (MX + SX1 + SX2) and export three MX Simulator track folders.

Reproducible: python3 build_compound.py  ->  <repo>/build/<folders>
All obstacle geometry comes from lib/library.json + lib/berm_*.npy (measured on the JGMX references).
"""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import os, sys, json, shutil, numpy as np
sys.path.insert(0, ROOT + '/scripts')
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from scipy.interpolate import PchipInterpolator
from PIL import Image
from engine import *
import layouts

OUT = ROOT + '/legacy_mx/build'
NAMES = {'MX': 'RyanCompoundMX', 'SX1': 'RyanCompoundSX1', 'SX2': 'RyanCompoundSX2'}
REF = REF
N_EXP, SPACING = 11, 0.4
MX_W = 34.0          # MX riding width (ft): measured 32-36 at Desert Sand turns / Dr.Dew jumps
MX_SIDE_DEG = 25.0   # side slope of MX obstacles beyond the riding width (median of measured side angles)
BLEND = 22.0         # ft over which the track surface blends into the surrounding relief
G = Grid(N_EXP, SPACING)
N = G.N; S = G.s
jj, ii = np.meshgrid(np.arange(N), np.arange(N))
X = jj * S; Z = ii * S
report = {}

# ------------------------------------------------------------------ 1. base relief
def bump(cx, cz, amp, sig):
    return amp * np.exp(-((X - cx) ** 2 + (Z - cz) ** 2) / (2 * sig ** 2))

B = np.zeros((N, N))
HILLS = [(330, 330, 24, 150), (1440, 880, 18, 120), (1470, 300, 16, 140), (900, 430, 9, 110),
         (1010, 870, -8, 100), (560, 960, -5, 90), (700, 160, 6, 120), (1450, 1400, 14, 110)]
for h in HILLS: B += bump(*h)
# SX stadium pads are flat (floor 0): fade relief out around them
pad = np.zeros((N, N), bool)
pad |= (X > 15) & (X < 605) & (Z > 1150); pad |= (X > 625) & (X < 1225) & (Z > 1120)
dist_pad = ndi.distance_transform_edt(~pad) * S
B *= np.clip(dist_pad / 120.0, 0, 1) ** 2

# ------------------------------------------------------------------ 2. MX track
mx = layouts.mx()
smp = mx.samples(0.5)
sx_, sz_, sth, ss = smp['x'], smp['z'], smp['th'], smp['s']
L = mx.s
# design grade = relief along the path, low-passed (120 ft)
gB = ndi.map_coordinates(B, [sz_ / S, sx_ / S], order=1)
k = int(120 / 0.5)
Gdes = ndi.uniform_filter1d(gB, k, mode='wrap')

# sections placed on straights (from the layout)
LIBS = {}
LIBS.update(LIB.get('mx_desert_sections', {})); LIBS.update(LIB.get('mx_drdew_sections', {})); LIBS.update(LIB.get('mx_sections', {}))
placed = []
for g in mx.segs:
    if g['kind'] != 'S': continue
    for sec in g['sections']:
        sid, u0 = sec[0], sec[1]; P = LIBS[sid]
        prof = np.asarray(P['prof']); step = P['step']
        placed.append(dict(sid=sid, s0=g['s0'] + u0, s1=g['s0'] + u0 + (len(prof) - 1) * step, prof=prof, step=step, edge=g['tag'],
                           net=float(prof[-1]), src=P.get('source', P.get('ref'))))
placed.sort(key=lambda p: p['s0'])
# Track elevation: sections keep their exact measured profile (absolute angles preserved: Gdes is frozen
# under each section); their net climb/drop persists and decays in the following gap (max 8 deg change),
# the surrounding relief is then re-shaped to follow the track (no trenches / walls).
E = np.empty_like(Gdes); O = np.zeros_like(Gdes)
MAXG = np.tan(np.radians(8.0))
order = placed
off = 0.0; cur_s = 0.0
def fill_gap(s_a, s_b, off_a, off_b):
    m = (ss >= s_a) & (ss < s_b)
    t = (ss[m] - s_a) / max(s_b - s_a, 1e-6); w = 3 * t ** 2 - 2 * t ** 3
    E[m] = Gdes[m] + off_a + (off_b - off_a) * w
for n_, p in enumerate(order):
    gap = p['s0'] - cur_s
    tgt = off * 0.3
    tgt = off - np.sign(off) * min(abs(off - tgt), MAXG * gap / 1.5)
    fill_gap(cur_s, p['s0'], off, tgt)
    m = (ss >= p['s0']) & (ss <= p['s1'])
    base = np.interp(p['s0'], ss, Gdes) + tgt
    q = np.interp(ss[m] - p['s0'], np.arange(len(p['prof'])) * p['step'], p['prof'])
    E[m] = base + q
    lin = base + p['net'] * (ss[m] - p['s0']) / (p['s1'] - p['s0'])
    O[m] = E[m] - lin
    off = base + p['net'] - np.interp(p['s1'], ss, Gdes)
    p['offset_in'] = float(tgt); p['offset_out'] = float(off); p['gap_before'] = float(gap)
    cur_s = p['s1'] + 1e-6
fill_gap(cur_s, L + 1, off, 0.0)   # close the loop on the design grade
report['closing_gap_ft'] = float(L - cur_s); report['closing_offset_ft'] = float(off)
# relief follows the track: kernel-smoothed offsets (sigma 45 ft), faded with distance to the track
dE = (E - O) - Gdes
acc = np.zeros((N, N)); wac = np.zeros((N, N))
ci_ = np.clip((sz_ / S).astype(int), 0, N - 1); cj_ = np.clip((sx_ / S).astype(int), 0, N - 1)
np.add.at(acc, (ci_, cj_), dE); np.add.at(wac, (ci_, cj_), 1.0)
sig = 45.0 / S
acc_b = ndi.gaussian_filter(acc, sig); wac_b = ndi.gaussian_filter(wac, sig)
env = np.clip(wac_b / (wac_b.max() * 0.25), 0, 1)
B = B + np.where(wac_b > 1e-9, acc_b / np.maximum(wac_b, 1e-12), 0) * env * np.clip(dist_pad / 60.0, 0, 1)
# turns: berm on the outside (measured Desert Sand template); taper 25 ft at both ends
berm_prof = np.asarray(LIB['mx_berm']['prof']); berm_step = LIB['mx_berm']['step']
turn_side = np.zeros_like(E); turn_w = np.zeros_like(E)
for g in mx.segs:
    if g['kind'] != 'T' or g.get('tag', '').endswith('flat'): continue
    TP = 45.0  # berm run-in / run-out along the track
    m = (ss >= g['s0'] - TP) & (ss <= g['s0'] + g['L'] + TP)
    u = ss[m] - g['s0']; w = np.clip(np.minimum(u + TP, g['L'] + TP - u) / TP, 0, 1); w = w * w * (3 - 2 * w)
    turn_w[m] = np.maximum(turn_w[m], w); turn_side[m] = np.sign(g['ang'])  # outside = right of travel (v>0) for a left turn
grade_deg = np.degrees(np.arctan(np.gradient(ndi.uniform_filter1d(E - O, int(30 / 0.5), mode='wrap'), 0.5)))
report['mx'] = dict(lap_ft=L, sections=[{k_: v for k_, v in p.items() if k_ != 'prof'} for p in placed],
                    grade_abs_p50_p90_max=[float(np.percentile(np.abs(grade_deg), 50)), float(np.percentile(np.abs(grade_deg), 90)), float(np.abs(grade_deg).max())])

# rasterise the MX corridor
tree = cKDTree(np.c_[sx_, sz_])
near = ndi.distance_transform_edt(~pad) * S > 0  # everywhere
sel = np.ones((N, N), bool)
# restrict to pixels within 70 ft of the path
coarse = np.zeros((N // 8 + 1, N // 8 + 1), bool)
ci = (sz_ / S / 8).astype(int); cj = (sx_ / S / 8).astype(int); coarse[ci, cj] = True
REACH = 115.0
coarse = ndi.binary_dilation(coarse, iterations=int(REACH / (8 * S)) + 1)
cand = np.repeat(np.repeat(coarse, 8, 0), 8, 1)[:N, :N]
pi, pj = np.nonzero(cand)
px, pz = pj * S, pi * S
d, idx = tree.query(np.c_[px, pz], distance_upper_bound=REACH)
ok = np.isfinite(d); pi, pj, px, pz, d, idx = pi[ok], pj[ok], px[ok], pz[ok], d[ok], idx[ok]
th = sth[idx]; vx, vz = px - sx_[idx], pz - sz_[idx]
v = -vx * np.sin(th) + vz * np.cos(th)       # + = right of travel
av = np.abs(v)
# riding surface (+ berm on the outside of turns), then an 'embankment' at the measured side slope
# down/up to the surrounding relief: no cliffs, obstacles keep their measured longitudinal profile.
vout = v * turn_side[idx]; tw = turn_w[idx]
bh = np.interp(np.clip(vout, 0, None) / berm_step, np.arange(len(berm_prof)), berm_prof, right=berm_prof[-1])
top = E[idx] + bh * tw * (vout > 0)
flat_half = MX_W / 2 + (vout > 0) * tw * (len(berm_prof) - 1) * berm_step * 0.6
dist_out = np.maximum(av - flat_half, 0)
Bp = B[pi, pj]; diff = top - Bp
# Surroundings: the relief B is clipped between cone envelopes of slope tan(MX_SIDE_DEG) erected on the riding
# surface (incl. berms) and the start pad -> obstacle sides, cuts/fills and the ground between neighbouring
# lanes never exceed the measured side slope (no cliffs at lane seams).
KS = np.tan(np.radians(MX_SIDE_DEG))
fixed = np.zeros((N, N), bool); topv = np.zeros((N, N))
fm = dist_out <= 0
fixed[pi[fm], pj[fm]] = True; topv[pi[fm], pj[fm]] = top[fm]
h0 = float(np.interp(L - 155.0 + 1.0, ss, E))
padm = (X > 25) & (X < 96) & (Z > 1010) & (Z < 1110)
fixed |= padm; topv[padm] = h0
f2 = fixed[::2, ::2]; t2 = topv[::2, ::2]; s2 = 2 * S
low = np.full(f2.shape, -1e9, np.float32); upp = np.full(f2.shape, 1e9, np.float32)
lv = np.arange(np.floor(t2[f2].min()), np.ceil(t2[f2].max()) + 0.5, 0.5)
for Lv in lv:
    m = f2 & (t2 >= Lv - 1e-6)
    if m.any(): low = np.maximum(low, Lv - KS * ndi.distance_transform_edt(~m) * s2)
    m = f2 & (t2 <= Lv + 1e-6)
    if m.any(): upp = np.minimum(upp, Lv + KS * ndi.distance_transform_edt(~m) * s2)
low = ndi.zoom(low, N / low.shape[0], order=1)[:N, :N]; upp = ndi.zoom(upp, N / upp.shape[0], order=1)[:N, :N]
conflict = low > upp
Hmx = np.where(conflict, 0.5 * (low + upp), np.clip(B, low, upp))
Hmx[fixed] = topv[fixed]
Hmx = np.where(pad & ~fixed, B, Hmx)
report['mx']['cone_conflict_px'] = int(conflict.sum())
on_mx = np.zeros((N, N), np.uint8)
on_mx[pi[av <= MX_W / 2 + 4], pj[av <= MX_W / 2 + 4]] = 1
Olat = np.where(av <= MX_W / 2, np.abs(O[idx]), 0)
report['mx']['embankment_max_ft'] = float(np.abs(diff[av <= MX_W / 2]).max())

report['mx']['start_pad_height'] = h0

# ------------------------------------------------------------------ 3. SX tracks on their pads
H = Hmx.copy()
sx_logs = {}
for key, fn in (('SX1', layouts.sx1), ('SX2', layouts.sx2)):
    p = fn(); lg = []
    tmp = np.zeros((N, N))
    render_sx(G, tmp, p, 0.0, log=lg)
    H = np.where(tmp > 0, np.maximum(H, tmp), H)
    sx_logs[key] = (p, lg)
    report[key] = dict(lap_ft=p.s, sections=lg)

# ------------------------------------------------------------------ 4. sand section (MX): measured Desert tile physics
sand_s = []
for k_, g in enumerate(mx.segs):
    if g['kind'] == 'S' and 'sand' in g['tag']: sand_s.append((g['s0'] - 40, g['s0'] + g['L'] + 40))
sand_mask_s = np.zeros_like(E, bool)
for a, b in sand_s: sand_mask_s |= (ss >= a) & (ss <= b)
report['mx']['sand_length_ft'] = float(sand_mask_s.sum() * 0.5)

# ------------------------------------------------------------------ 5. tilemap
TN = 2 ** N_EXP; tile_s = G.size / TN
tH = H[:-1:2, :-1:2] if N - 1 == 2 * TN else ndi.zoom(H, TN / N)
tiles = np.full((TN, TN), 0, np.uint8)  # 0 grass / off-track
# SX: floor (Main), jumps, whoops, berms - from rendered SX masks
sxm = np.zeros((N, N), np.uint8)
for key in ('SX1', 'SX2'):
    p, lg = sx_logs[key]
    b1 = np.zeros((N, N)); b2 = np.zeros((N, N))
    for g in p.segs:
        if g['kind'] == 'S':
            for sec in g['sections']:
                prof = section_profile(sec[0], sec[2] if len(sec) > 2 else None)
                tgt = b2 if 'whoops' in sec[0] else b1
                render_lane_block(G, tgt, g, prof, sec[1], LIB['sx_lateral']['top_width'])
        elif g.get('berm'):
            bb = np.zeros((N, N)); render_berm_stamp(G, bb, g['berm'], g['cx'], g['cz'], turn_mid_angle(g)); sxm[bb > 0.05] = 4
    sxm[(b1 > 0.05)] = 2; sxm[(b2 > 0.05)] = 3
sx_floor = pad
T_GRASS, T_DIRT, T_JUMP, T_SAND, T_SXMAIN, T_SXJUMP, T_SXWHOOP, T_SXBERM = range(8)
tiles[:] = T_GRASS
on_t = on_mx[::2, ::2][:TN, :TN]
tiles[on_t == 1] = T_DIRT
# obstacle faces on MX: where |O| > 0.8 ft on the riding surface
Ofull = np.zeros((N, N)); Ofull[pi, pj] = np.abs(Olat)
tiles[(on_t == 1) & (Ofull[::2, ::2][:TN, :TN] > 0.8)] = T_JUMP
# sand: riding surface + 10 ft within the sand range
sand_px = np.zeros((N, N), bool); sm = sand_mask_s[idx] & (av <= MX_W / 2 + 14); sand_px[pi[sm], pj[sm]] = True
tiles[sand_px[::2, ::2][:TN, :TN]] = T_SAND
padt = pad[::2, ::2][:TN, :TN]; sxt = sxm[::2, ::2][:TN, :TN]
tiles[padt] = T_SXMAIN
tiles[padt & (sxt == 2)] = T_SXJUMP; tiles[padt & (sxt == 3)] = T_SXWHOOP; tiles[padt & (sxt == 4)] = T_SXBERM
report['tiles'] = {n_: int((tiles == i).sum()) for i, n_ in enumerate(['grass', 'mx dirt', 'mx jump faces', 'sand', 'sx floor', 'sx jumps', 'sx whoops', 'sx berms'])}

# ------------------------------------------------------------------ 6. save arrays for checks / viewer
os.makedirs(OUT, exist_ok=True)
np.save(f'{OUT}/H.npy', H.astype(np.float32)); np.save(f'{OUT}/tiles.npy', tiles); np.save(f'{OUT}/B.npy', B.astype(np.float32))
np.savez(f'{OUT}/mx_line.npz', x=sx_, z=sz_, s=ss, E=E, O=O, G=Gdes, sand=sand_mask_s, turn_w=turn_w)
json.dump(report, open(f'{OUT}/build_report.json', 'w'), indent=1, default=float)
print('built: H range', H.min(), H.max())
print(json.dumps({k_: (v_['lap_ft'] if isinstance(v_, dict) and 'lap_ft' in v_ else v_) for k_, v_ in report.items() if k_ != 'mx'}, default=float, indent=0)[:800])
print('MX lap', L, 'grade', report['mx']['grade_abs_p50_p90_max'], 'sand', report['mx']['sand_length_ft'])
