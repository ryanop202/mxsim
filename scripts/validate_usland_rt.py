"""usland race track - automatic checks on the EXPORTED files of tracks/USLANDRaceTrack (re-read from disk), same spirit as
validate_sx.py; + top view and lane profiles (viewer/figures/URT_*.png). Writes build/usland_rt_validation.json.
These are file / geometry checks only: NOT a test in MX Simulator.   python3 scripts/validate_usland_rt.py"""
import os, sys, json, re, subprocess
ROOT = os.environ.get('MXSIM_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree
from engine import sx_wall, turn_mid_angle
import layout_usland_rt as LU
import compose, rf_units
from laptime import estimate

D = f'{ROOT}/tracks/{LU.FOLDER}'; P = '@' + LU.FOLDER
B = json.load(open(f'{ROOT}/build/usland_rt_build.json'))
CH = []
def check(name, ok, detail):
    CH.append(dict(name=name, ok=bool(ok), detail=detail)); print(('OK  ' if ok else 'XX  ') + name + ' : ' + str(detail))

# ------------------------------------------------------------------ files
need = ['terrain.hf', 'terrain.png', 'tilemap', 'tileinfo', 'timing_gates', 'lighting', 'shading.ppm', 'shadingx2.ppm', 'desc',
        'statues', 'decals', 'billboards', 'flaggers', 'map.png', 'frills.js']
miss = [f for f in need if not os.path.exists(f'{D}/{f}')]
check('Fichiers de piste presents', not miss, miss or f'{len(need)} fichiers')
check('Nom en jeu', open(f'{D}/desc').read().strip() == LU.DESC, repr(open(f'{D}/desc').read().strip()))
n, s, h0, h1 = open(f'{D}/terrain.hf').read().split()[:4]; n, s, h0, h1 = int(n), float(s), float(h0), float(h1)
im = np.array(Image.open(f'{D}/terrain.png')); H = h0 + im.astype(np.float64) / 65535 * (h1 - h0); N = H.shape[0]
check('Heightmap 2049 px a 0,28975 ft (593,4 ft)', n == 10 and abs(s - 0.28975) < 1e-9 and im.shape == (2049, 2049) and im.dtype == np.uint16,
      f'n={n}, {s} ft/px, {im.shape}, {im.dtype}, cote {(N - 1) * s:.2f} ft')
Hb = np.load(f'{ROOT}/build/usland_rt_H.npy').astype(np.float64)
err = float(np.abs(H - Hb).max())
check('Heightmap relue = terrain construit', err < 2e-4, f'ecart max {err:.6f} ft (pas de quantification {(h1 - h0) / 65535:.6f} ft)')
tm = np.fromfile(f'{D}/tilemap', np.uint8); nt = sum(1 for l in open(f'{D}/tileinfo') if l.strip() == 'addtile')
check('Tilemap 1024 x 1024, tiles definis', tm.size == 1024 ** 2 and int(tm.max()) < nt, f'{tm.size} octets, max {tm.max()} < {nt} blocs')
txt = {f: open(f'{D}/{f}', encoding='utf-8', errors='replace').read() for f in ('tileinfo', 'lighting', 'timing_gates', 'statues', 'decals', 'billboards', 'frills.js')}
for r_, _, fs in os.walk(f'{D}/js'):
    for f in fs:
        if f.endswith('.seq'): txt[os.path.relpath(f'{r_}/{f}', D)] = open(f'{r_}/{f}', errors='replace').read()
refs = set(re.findall(r'@[A-Za-z0-9_.\-]+(?:/[A-Za-z0-9_.\-]+)+', ' '.join(txt.values())))
lower = {os.path.relpath(os.path.join(r_, f), D).replace('\\', '/').lower() for r_, _, fs in os.walk(D) for f in fs}
own = [r for r in refs if r.startswith(P + '/')]; bad = sorted(r for r in own if r[len(P) + 1:].lower() not in lower)
seqs = [r for r in own if r.endswith('.seq')]
for sq in seqs:                                                         # frames listed inside the .seq files
    for l in open(f'{D}/{sq[len(P) + 1:]}').read().split('\n')[1:]:
        if l.strip().startswith('@') and l.strip()[len(P) + 1:].lower() not in lower: bad.append(l.strip())
other = sorted(r for r in refs if not r.startswith(P + '/'))
check('Toutes les references @USLANDRaceTrack/ existent', not bad, bad[:5] or f'{len(own)} references, toutes presentes')
check('Aucune dependance vers un autre dossier de piste', not other, other[:5] or 'dossier autonome (seulement @ressources internes du jeu)')
check('frills.js en ASCII pur', all(ord(c) < 128 for c in txt['frills.js']), 'les accents faisaient planter le jeu (v13b)')

# ------------------------------------------------------------------ geometry
path = LU.track(); R = LU.start_route(); S = s
def h(x, z): return H[np.clip((np.asarray(z) / S).astype(int), 0, N - 1), np.clip((np.asarray(x) / S).astype(int), 0, N - 1)]
lap = path.samples(1.0); LAP = cKDTree(np.c_[lap['x'], lap['z']])
check('Tour ferme', np.hypot(path.x - LU.XF, path.z - (LU.ZTOP + LU.RS)) < 1e-6, f'tour {path.s:.1f} ft ({path.s * 0.3048:.0f} m)')
errs = {}
for g in path.segs:
    if g['kind'] != 'S': continue
    for prof, u0, name in g['sections']:
        u = np.arange(len(prof)) * 0.1; c, s_ = np.cos(g['t']), np.sin(g['t'])
        x = g['x0'] + (u0 + u) * c; z = g['z0'] + (u0 + u) * s_
        # bilinear read of the exported terrain on the lane axis
        fx, fz = x / S, z / S; j0, i0 = np.floor(fx).astype(int), np.floor(fz).astype(int); ax, az = fx - j0, fz - i0
        hv = H[i0, j0] * (1 - ax) * (1 - az) + H[i0, j0 + 1] * ax * (1 - az) + H[i0 + 1, j0] * (1 - ax) * az + H[i0 + 1, j0 + 1] * ax * az
        errs[name] = float(np.abs(hv - prof).max())          # lane axis = full height (as validate_sx.py)
fit = [(g['tag'], round(g['L'] - u0 - len(pr) * 0.1, 1)) for g in path.segs if g['kind'] == 'S' for pr, u0, _ in g['sections']]
check('Chaque section tient dans son couloir (>= 8 ft avant le virage)', min(f_ for _, f_ in fit) >= 8, ', '.join(f'{k.split()[0]} {f_:.0f}' for k, f_ in fit) + ' ft libres')
check('Profils exportes = profils mesures (RF + JGSX)', max(errs.values()) < 0.06, f'{len(errs)} sections, ecart max {max(errs.values()):.3f} ft')
bad = []
for name, c in LU.COMBOS.items():
    for (nm, st, en, hh), src in zip(c['items'], c['sources']):
        if nm.startswith('whoops'): continue
        k = LU.kind_of(('rf', nm) if src == 'RF' else nm)
        p = np.asarray(LU.RF[nm]['prof'] if src == 'RF' else compose.unit(nm)[1])
        if k in ('S', 'B') and p.max() / ((p > p.max() / 2).sum() * 0.1) > 0.31: bad.append(nm)
check('Pas de pains de sucre dans les enchainements', not bad, bad or 'toutes les S / B ont H / largeur a mi-hauteur <= 0,31')
smp = lap; worst = None
for i, j in LAP.query_pairs(41.0):
    d_s = abs(smp['s'][i] - smp['s'][j]); d_s = min(d_s, path.s - d_s)
    if d_s > 140: worst = (i, j); break
check('Couloirs separes (>= 41 ft hors parties voisines)', worst is None, 'aucune paire < 41 ft' if worst is None else str(worst))
# JGSX berm stamps must not reach another lane (|v| <= 19.2 ft of any straight that is not next to that turn)
from engine import Grid, render_berm_stamp, berm_ang_scale
Gb = Grid(LU.N_EXP, LU.S); over = []; skirts = []
for k, g in enumerate(path.segs):
    if g['kind'] != 'T' or not g['berm']: continue
    bm = np.zeros((N, N)); render_berm_stamp(Gb, bm, g['berm'], g['cx'], g['cz'], turn_mid_angle(g), ang_scale=berm_ang_scale(g['berm'], g['ang']))
    for j, s2 in enumerate(path.segs):
        if s2['kind'] != 'S' or min(abs(j - k), len(path.segs) - abs(j - k)) <= 1: continue
        e = np.array([np.cos(s2['t']), np.sin(s2['t'])]); nn = np.array([-e[1], e[0]])
        U_, V_ = np.meshgrid(np.arange(0, s2['L'], 1.0), np.arange(-19.2, 19.21, 1.0))
        ri = np.clip(((s2['z0'] + U_ * e[1] + V_ * nn[1]) / S).astype(int), 0, N - 1); ci = np.clip(((s2['x0'] + U_ * e[0] + V_ * nn[0]) / S).astype(int), 0, N - 1)
        lane_only = np.zeros_like(U_)
        for prof, u0, _ in s2['sections']:
            lane_only = np.maximum(lane_only, np.interp((U_ - u0) / 0.1, np.arange(len(prof)), prof, left=0, right=0) * sx_wall(np.abs(V_) - 15.2))
        top = np.abs(V_) <= 15.2; add = bm[ri, ci] - lane_only
        if (add[top] > 0.05).any(): over.append((g['tag'], s2['tag'], 'dessus roulable', round(float(add[top].max()), 2)))
        elif bm[ri, ci].max() > 0.05: skirts.append(f"{g['tag']}->{s2['tag']} {float(bm[ri, ci].max()):.2f} ft hors dessus")
check('Berms JGSX : stamps exacts, rien sur le dessus roulable (30,4 ft) d un autre couloir', not over,
      over or f"{sum(1 for g in path.segs if g.get('berm'))} berms ; jupes au bord : {', '.join(skirts) or 'aucune'}")
bowl = [g for g in path.segs if g['kind'] == 'T' and g['berm'] is None][0]
th = np.linspace(0, np.pi, 200); rr = np.arange(bowl['r'] - 20, bowl['r'] + 20.1, 1.0)
X = bowl['cx'] + np.outer(rr, np.cos(th)); Z = bowl['cz'] + np.outer(rr, np.sin(th))
check('Virage 1 : cuvette plate, aucun berm', float(h(X, Z).max()) < 0.01, f'hauteur max sur 40 ft de large : {float(h(X, Z).max()):.3f} ft (R {bowl["r"]:.0f})')
a = H[:-1, :-1]; b_ = H[1:, :-1]; c_ = H[:-1, 1:]
step = max(np.where(np.minimum(a, b_) < 0.02, np.abs(a - b_), 0).max(), np.where(np.minimum(a, c_) < 0.02, np.abs(a - c_), 0).max())
check('Pas de rebord au pied des obstacles', step <= 0.133 + 0.02, f'marche max sol -> obstacle {step:.3f} ft (reference JGSX Detroit 0,133 ft)')
check('Terrain sans trou ni pic', H.min() >= -1e-3 and H.max() <= 11.3, f'hauteurs {H.min():.3f} .. {H.max():.2f} ft')
nz = np.argwhere(H > 0.05) * S; fx0, fx1, fz0, fz1 = LU.STADIUM_FLOOR
check('Obstacles dans la boite des murs du stade RF (marge 8 ft)', nz[:, 1].min() >= fx0 + 8 and nz[:, 1].max() <= fx1 - 8 and nz[:, 0].min() >= fz0 + 8 and nz[:, 0].max() <= fz1 - 8,
      f'emprise x {nz[:, 1].min():.0f}-{nz[:, 1].max():.0f}, z {nz[:, 0].min():.0f}-{nz[:, 0].max():.0f} ft (forme reelle : controle du stade plus bas)')

# ------------------------------------------------------------------ start + gates
tg = open(f'{D}/timing_gates').read().split('\n'); secs = {}; cur = None
for l in tg:
    if l.endswith(':'): cur = l[:-1]; secs[cur] = []
    elif l.strip() and cur: secs[cur].append(l)
gates = [tuple(map(float, re.findall(r'-?\d+\.\d+', l)[:4])) for l in secs['startinggate']]
pitch = [np.hypot(gates[k + 1][0] - gates[k][0], gates[k + 1][2] - gates[k][2]) for k in range(len(gates) - 1)]
gx = np.array([[g[0], g[2]] for g in gates]); f = np.array([-np.sin(gates[0][3]), -np.cos(gates[0][3])])
under = max(float(h(*(q - f * d))) for q in gx for d in np.linspace(-3, 8, 12))
check('22 grilles au pas de 4 ft, sol plat (grilles + grates)', len(gates) == 22 and np.allclose(pitch, 4.0, atol=1e-4) and under < 0.01,
      f'{len(gates)} grilles, pas {min(pitch):.3f}-{max(pitch):.3f} ft, face {np.degrees(np.arctan2(f[1], f[0])):.0f} deg (sud), hauteur max {under:.3f} ft')
cxs, czs, _, _ = R.area_points(1.0, 1.0)
check('Couloir de depart degage jusqu a la jonction', float(h(cxs, czs).max()) < 0.01, f'{R.L:.0f} ft, hauteur max {float(h(cxs, czs).max()):.3f} ft, largeur 92 -> 40 -> 30 ft')
cps = [list(map(float, re.findall(r'-?\d+\.?\d*', l))) for l in secs['checkpoints']]   # half cx cy cz dx dy dz
first = [int(v) for v in secs['firstlap'][0].split()]; normal = [int(v) for v in secs['normallap'][0].split()]
def crossings(xs, zs):
    """indices of the checkpoints crossed (in the riding direction, within the gate) along a polyline, in order."""
    out = []
    for k in range(len(xs) - 1):
        p0, p1 = np.array([xs[k], zs[k]]), np.array([xs[k + 1], zs[k + 1]])
        for ci, c in enumerate(cps):
            cc = np.array([c[1], c[3]]); dv = np.array([c[4], c[6]]); hl = c[0]; e = dv / np.linalg.norm(dv); nn = np.array([-e[1], e[0]])
            a0, a1 = (p0 - cc) @ e, (p1 - cc) @ e
            if a0 < 0 <= a1:
                t_ = -a0 / (a1 - a0); q = p0 + (p1 - p0) * t_
                if abs((q - cc) @ nn) <= hl: out.append(ci)
    return out
rs = R.samples(0.5); L2 = path.samples(0.5); i0 = int(np.argmin(np.hypot(L2['x'] - R.merge[0], L2['z'] - R.merge[1])))
xs = np.r_[rs['x'], np.roll(L2['x'], -i0), L2['x'][i0:], L2['x'][:i0], L2['x'][i0:i0 + 1]]
zs = np.r_[rs['z'], np.roll(L2['z'], -i0), L2['z'][i0:], L2['z'][:i0], L2['z'][i0:i0 + 1]]
seq = crossings(xs, zs)
def follow(seq, order, k=0):
    for o in order:
        while k < len(seq) and seq[k] != o: k += 1
        if k == len(seq): return None
        k += 1
    return k
k1 = follow(seq, first); k2 = follow(seq, normal, k1) if k1 is not None else None
check('Comptage des tours simule (depart -> 1er tour -> tour complet)', k1 is not None and k2 is not None,
      f'{len(cps)} portes ; 1er tour {len(first)} portes, tour normal {len(normal)} portes, toutes franchies dans l ordre')
dl = [float(LAP.query([c[1], c[3]])[0]) for k, c in enumerate(cps) if k in normal]
check('Portes du tour sur la ligne de course, dans le sens de la course', max(dl) < 1.0, f'distance max porte -> ligne {max(dl):.2f} ft')
fin = cps[normal[-1]]
check('Arrivee sur la crete de l appel du step-up RF (couloir F)', abs(float(h(fin[1], fin[3])) - 8.75) < 0.1, f'porte d arrivee en ({fin[1]:.1f}, {fin[3]:.1f}), sol {float(h(fin[1], fin[3])):.2f} ft')

# ------------------------------------------------------------------ objects
st = [l for l in open(f'{D}/statues').read().split('\n') if l.strip()]
corr = cKDTree(np.c_[cxs, czs])
def rd(x, z): return min(float(LAP.query([x, z])[0]), float(corr.query([x, z])[0]))
far = []
for l in st:
    v = list(map(float, re.findall(r'-?\d+\.\d+', l)[:4])); m = l.split()[4].split('/')[-1]
    if m in ('2.jm',) and rd(v[0], v[2]) < 17: far.append((m, round(rd(v[0], v[2]), 1)))
A = B['arch']
check('Cones a >= 17 ft des lignes de course', not far, far or f'{sum(1 for l in st if "/2.jm" in l)} cones (1 par virage)')
check('Arche FINISH : poteaux hors piste, socles plats, hauteur libre', A['pillar_ride_dist'] >= 19 and A['plate_slope'] <= 1.2 and A['beam_clearance'] >= 20,
      f"poteaux a {A['pillar_ride_dist']} ft des lignes, pente sous socles {A['plate_slope']} ft, {A['beam_clearance']} ft au-dessus de la crete")
check('Grates et portique sur les 22 grilles', sum('start_grate' in l for l in st) == 22 and sum('start_gantry' in l for l in st) == 1, 'oui')
# RF stadium: ground-level structures (< 12 ft, rocks included) clear of every riding line
pts = []
for l in st:
    if '/stadiums/' not in l: continue
    v = list(map(float, re.findall(r'-?\d+\.\d+', l)[:4])); fn_ = l.split()[4].split('/')[-1]
    src = [os.path.join(r_, q) for r_, _, fs in os.walk(f'{D}/stadiums') for q in fs if q.lower() == fn_.lower()][0]
    t_ = open(src, errors='replace').read().split('\n'); nv = int(t_[2].split()[0])
    V = np.array([[float(x) for x in t_[3 + i].split()[:3]] for i in range(nv)])
    wx = v[0] + V[:, 0] * np.cos(v[3]) + V[:, 2] * np.sin(v[3]); wz = v[2] - V[:, 0] * np.sin(v[3]) + V[:, 2] * np.cos(v[3]); wy = v[1] + V[:, 1]
    # standing structures near the floor: walls, stands, signs (0.5-14 ft above the floor) + the rocks (any height);
    # the outfield grass planes (y -0.2) lie under the dirt and are not obstacles
    k = (wx > -5) & (wx < 600) & (wz > -5) & (wz < 600) & (('rocks' in fn_.lower()) | ((wy >= 0.5) & (wy <= 14)))
    pts.append(np.c_[wx[k], wz[k]])
pts = np.vstack(pts); dmin = min(float(LAP.query(pts)[0].min()), float(corr.query(pts)[0].min()))
foot = np.argwhere(H > 0.05)[:, ::-1] * S; dfoot = float(cKDTree(foot).query(pts)[0].min())
check('Stade RF Anaheim (murs, tribunes, rochers) : >= 25 ft des lignes, >= 8 ft des obstacles', dmin >= 25 and dfoot >= 8,
      f"{B['objects']['stadium RF Anaheim']} modeles ; ligne la plus proche {dmin:.0f} ft, obstacle le plus proche {dfoot:.0f} ft")
bb = [l for l in open(f'{D}/billboards').read().split('\n') if l.strip()]
check('Flammes d arrivee (2 billboards) + frills.js', len(bb) == 2 and 'color_billboard(0' in txt['frills.js'], f'{len(bb)} billboards')

# ------------------------------------------------------------------ lap time + SX1-3 untouched
ts = [estimate(path, 20.0, alat=a_)[0] for a_ in (1.6, 1.3, 1.0)]
check('Chrono ESTIME (modele point-masse laptime.py, pas une mesure)', True, f'{ts[1]:.1f} s (fourchette {ts[0]:.1f} - {ts[2]:.1f} s)')
try:
    dif = subprocess.run(['git', 'status', '--porcelain', '--', 'tracks/USLAND2026SX1', 'tracks/USLAND2026SX2', 'tracks/USLAND2026SX3'],
                         cwd=ROOT, capture_output=True, text=True).stdout.strip()
    check('SX1, SX2, SX3 inchangees (git)', dif == '', dif[:200] or 'aucune modification dans tracks/USLAND2026SX1-3')
except Exception as e:
    check('SX1, SX2, SX3 inchangees (git)', False, f'git indisponible : {e}')

ok = sum(c['ok'] for c in CH)
json.dump(dict(checks=CH, passed=ok, total=len(CH), lap_s=dict(est=ts[1], range=[ts[0], ts[2]]), profile_errors=errs),
          open(f'{ROOT}/build/usland_rt_validation.json', 'w'), indent=1)
print(f'\n{ok} / {len(CH)} controles reussis  (controles de fichiers et de geometrie : NON teste en jeu)')

# ------------------------------------------------------------------ figures
os.makedirs(f'{ROOT}/viewer/figures', exist_ok=True)
try: FT = ImageFont.truetype('arialbd.ttf', 16); FS = ImageFont.truetype('arial.ttf', 13)
except OSError: FT = FS = ImageFont.load_default()
PX = 2.4; M_ = 30; W = int((593.4 + 2 * M_) * PX)
hs = H[::2, ::2]; gx_, gz_ = np.gradient(hs); shade = np.clip(1.0 + 1.6 * (-gx_ * 0.7 - gz_ * 0.7), 0.45, 1.35); t = np.clip(hs / 11, 0, 1)[..., None]
col = np.array([150, 118, 86.])[None, None] * (1 - 0.35 * t) + np.array([90, 60, 40.]) * 0.35 * t
img = Image.new('RGB', (W, W), (34, 38, 46)); img.paste(Image.fromarray(np.clip(col * shade[..., None], 0, 255).astype(np.uint8)).resize((int(593.4 * PX),) * 2), (int(M_ * PX),) * 2)
d = ImageDraw.Draw(img); Q = lambda x, z: ((x + M_) * PX, (z + M_) * PX)
for x, z in pts[::2]: d.rectangle([Q(x - 0.8, z - 0.8), Q(x + 0.8, z + 0.8)], fill=(90, 200, 110))   # RF stadium: walls, stands, rocks (< 14 ft)
d.line([Q(x, z) for x, z in zip(lap['x'], lap['z'])], fill=(0, 200, 255), width=2)
d.line([Q(x, z) for x, z in zip(rs['x'], rs['z'])], fill=(255, 220, 0), width=2)
for g in gates: d.rectangle([Q(g[0] - 1.6, g[2] - 1), Q(g[0] + 1.6, g[2] + 1)], fill=(230, 40, 40))
for c in cps: e = np.array([c[4], c[6]]) / c[0]; nn = np.array([-e[1], e[0]]) * c[0]; d.line([Q(c[1] - nn[0], c[3] - nn[1]), Q(c[1] + nn[0], c[3] + nn[1])], fill=(255, 255, 255), width=1)
d.text(Q(fin[1] - 95, fin[3] - 6), 'ARRIVEE', fill=(255, 255, 255), font=FT)
lab = {'F': (LU.XF - 70, 300), 'A': (LU.XA + 20, 220), 'B': (LU.XB + 20, 330), 'C': (LU.XC + 20, 330), 'D': (LU.XD + 20, 330), 'E': (LU.XE + 22, 330), 'R': (330, LU.ZTOP - 30)}
for k, (x, z) in lab.items(): d.text(Q(x, z), k, fill=(255, 255, 255), font=FT)
d.text((10, 6), f"usland race track - terrain exporte (relu) - tour {path.s:.0f} ft - chrono ESTIME {ts[1]:.1f} s - {ok}/{len(CH)} controles - non teste en jeu", fill=(230, 230, 230), font=FS)
img.save(f'{ROOT}/viewer/figures/URT_top.png')
lanes = [(k, g) for k in ('F', 'A', 'B', 'C', 'D', 'E', 'R') for g in path.segs if g['kind'] == 'S' and g['tag'].startswith(k + ' ') or (g['kind'] == 'S' and g['tag'] == k and False)]
lanes = [(g['tag'].split()[0], g) for g in path.segs if g['kind'] == 'S' and g['sections']]
pim = Image.new('RGB', (1800, 150 * len(lanes) + 20), (250, 250, 248)); dp = ImageDraw.Draw(pim)
for i, (k, g) in enumerate(lanes):
    prof, u0, name = g['sections'][0]; y0 = 10 + i * 150; by = y0 + 116; sx = 1640 / 470.0
    u = np.arange(0, g['L'], 0.5); x = g['x0'] + u * np.cos(g['t']); z = g['z0'] + u * np.sin(g['t']); hv = h(x, z)
    dp.text((10, y0), f"{k} - {name} ({g['L']:.0f} ft)", fill=(20, 20, 20), font=FS)
    dp.line([(120, by), (120 + g['L'] * sx, by)], fill=(130, 130, 130))
    for (nm, st_, en, hh), src in zip(LU.COMBOS[name]['items'], LU.COMBOS[name]['sources']):
        c = (230, 120, 20) if src == 'RF' else (40, 90, 200); m = (u >= u0 + st_) & (u <= u0 + en)
        poly = [(120 + uu * sx, by - vv * 7.5) for uu, vv in zip(u[m], hv[m])]
        if len(poly) > 2: dp.polygon(poly + [(poly[-1][0], by), (poly[0][0], by)], fill=c)
        dp.text((120 + (u0 + (st_ + en) / 2) * sx, by - hh * 7.5 - 14), f'{hh:.1f}', fill=(30, 30, 30), font=FS, anchor='mm')
dp.text((1340, 4), 'orange = RF, bleu = JGSX (lu dans terrain.png)', fill=(60, 60, 60), font=FS)
pim.save(f'{ROOT}/viewer/figures/URT_lanes.png')
