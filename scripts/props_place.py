"""v12 où poser les objets USLAND (props_usland.py) : arche d'arrivée, grates de départ, paddock.
Ne lit que ce qui est dans tracks/ (terrain, timing_gates) + layouts_sx : marche sans les archives de référence.
Utilisé par dress_sx.py (build complet) et preview_props.py (aperçu)."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/scripts')
import numpy as np
from PIL import Image
from names import FOLDERS
from mxs import parse_gates
import props_usland as PU

def ang_of(fx, fz):
    """MXS statue angle whose local z axis points along (fx, fz) (same convention as the start gates)."""
    return float(np.arctan2(-fx, -fz))

def load_terrain(folder=None):
    d = f'{ROOT}/tracks/{folder or FOLDERS["SX1"]}'
    n, S, h0, h1 = open(f'{d}/terrain.hf').read().split()[:4]; S, h0, h1 = float(S), float(h0), float(h1)
    H = h0 + np.array(Image.open(f'{d}/terrain.png')).astype(np.float64) / 65535.0 * (h1 - h0)
    shade = np.array(Image.open(f'{d}/shading.ppm').convert('L')) if os.path.exists(f'{d}/shading.ppm') else np.full(H.shape, 180, np.uint8)
    tiles = np.fromfile(f'{d}/tilemap', np.uint8).reshape(2048, 2048)
    return dict(H=H, S=S, shade=shade, tiles=tiles)

def h_at(T, x, z):
    H, S = T['H'], T['S']
    return H[(np.asarray(z) / S).astype(int).clip(0, H.shape[0] - 1), (np.asarray(x) / S).astype(int).clip(0, H.shape[1] - 1)]

_LINES = None
def riding_lines():
    """riding-line samples of the 3 tracks (1 ft), for the distance checks."""
    global _LINES
    if _LINES is None:
        import layouts_sx as LS
        from scipy.spatial import cKDTree
        _LINES = {}
        for k, f in (('SX1', LS.sx1), ('SX2', LS.sx2), ('SX3', LS.sx3)):
            s = f().samples(1.0); _LINES[k] = cKDTree(np.c_[s['x'], s['z']])
    return _LINES

def finish_gate(key):
    G = parse_gates(f'{ROOT}/tracks/{FOLDERS[key]}/timing_gates'); g = G['cps'][G['normal'][-1]]
    c = np.array([g[1], g[3]]); f = np.array([g[4], g[6]]); f /= np.linalg.norm(f)
    return c, f, g[0]

def arch_pose(key, T):
    """finish arch centred on the finish gate, across the riding direction; base y = lowest ground under the pillar plates.
    Returns the pose and the checks (pillar distance to every riding line, slope under the plates, banner clearance)."""
    c, f, half = finish_gate(key); n = np.array([-f[1], f[0]])
    plates, dmin, slope = [], 1e9, 0.0
    for sg in (-1, 1):
        p = c + n * sg * PU.ARCH_X
        q = np.array([p + n * u + f * v for u in np.linspace(-1.5, 1.5, 4) for v in np.linspace(-1.5, 1.5, 4)])
        hh = h_at(T, q[:, 0], q[:, 1]); plates.append(hh); slope = max(slope, float(np.ptp(hh)))
        dmin = min(dmin, min(float(tr.query(q)[0].min()) for tr in riding_lines().values()))
    y = float(min(h.min() for h in plates))
    q = np.array([c + n * u + f * v for u in np.linspace(-15.2, 15.2, 31) for v in np.linspace(-12, 12, 25)])
    crest = float(h_at(T, q[:, 0], q[:, 1]).max())
    return dict(x=float(c[0]), z=float(c[1]), y=y, a=ang_of(f[0], f[1]), f=[float(f[0]), float(f[1])],
                crest=crest, clearance=y + PU.ARCH_CLEAR - crest, pillar_line_dist=dmin, plate_slope=slope,
                pillars=[(c + n * s * PU.ARCH_X).tolist() for s in (-1, 1)])

def start_gates(key):
    """[x, y, z, angle] of the 22 start gates."""
    return [g[:4] for g in parse_gates(f'{ROOT}/tracks/{FOLDERS[key]}/timing_gates')['start']]

def grate_poses(key, T):
    """one grate per gate, same angle (the grate model runs backwards from the gate), y = local ground."""
    out = []
    for x, y, z, a in start_gates(key):
        f = np.array([-np.sin(a), -np.cos(a)]); q = np.array([[x, z]]) - np.outer(np.linspace(0.4, 0.4 + sum(L for _, L in PU.GRATE['parts']), 9), f)
        out.append((x, float(h_at(T, q[:, 0], q[:, 1]).max()), z, a))
    return out

def gantry_pose(key, T):
    """start gantry centred on the gate row, same angle as the gates (truss above the gate line), y = ground."""
    G = start_gates(key); x = float(np.mean([g[0] for g in G])); z = float(np.mean([g[2] for g in G])); a = float(G[0][3])
    return dict(x=x, z=z, y=float(h_at(T, x, z)), a=a)

BED_FLOOR, BIKE_AXLE_Z = 2.55, -5.3     # pickup bed floor height, rear axle of the bike in pickup coordinates
def bike_in_pickup(x, y, z, a):
    """pose of the bike + trainer in the bed of a pickup placed at (x, y, z, a): reversed (front wheel to the tailgate)."""
    f = np.array([-np.sin(a), -np.cos(a)])                     # pickup forward (local +z) in the world
    p = np.array([x, z]) + f * BIKE_AXLE_Z
    return dict(x=float(p[0]), y=float(y + BED_FLOOR), z=float(p[1]), a=float(a + np.pi))

ARCH_MODEL = {'SX1': 'finish_arch', 'SX2': 'finish_arch', 'SX3': 'finish_arch'}   # always black

def finish_flagger(key):
    """finish flagger beside the arch: between the lanes (>= 20 ft from every riding line), >= 4 ft from the arch pillars."""
    c, f, half = finish_gate(key); n = np.array([-f[1], f[0]]); pil = [c + n * s * PU.ARCH_X for s in (-1, 1)]
    best = None
    for sg in (1, -1):
        for along in (6.0, -6.0, 8.0, -8.0, 0.0):
            for o in np.arange(18.0, 36.0, 0.25):
                q = c + n * sg * o + f * along
                d = min(float(tr.query(q)[0]) for tr in riding_lines().values()); dp = min(np.linalg.norm(q - p) for p in pil)
                if d >= 20 and dp >= 4 and (best is None or d > best[0] + 1e-6): best = (d, q)
    if best is None: raise ValueError(f'{key}: no room for the finish flagger')
    return best[1]
