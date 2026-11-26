"""MX Simulator track I/O + measurement helpers (reverse-engineered, validated in validate_format.py)."""
import numpy as np, re, os
from PIL import Image
from scipy.ndimage import map_coordinates

class Track:
    def __init__(self, folder, flip=None):
        self.folder = folder
        hf = open(os.path.join(folder, 'terrain.hf')).read().split()
        self.n = int(hf[0]); self.s = float(hf[1]); self.hmin = float(hf[2]); self.hmax = float(hf[3])
        im = Image.open(os.path.join(folder, 'terrain.png'))
        self.raw = np.array(im, dtype=np.uint16)
        self.N = self.raw.shape[0]
        self.H = self.hmin + self.raw.astype(np.float64) / 65535.0 * (self.hmax - self.hmin)
        self.size = (self.N - 1) * self.s
        self.flip = flip  # mapping mode, set after validation
        tm = os.path.join(folder, 'tilemap')
        if os.path.exists(tm):
            t = np.fromfile(tm, np.uint8); k = int(round(np.sqrt(t.size)))
            self.tiles = t.reshape(k, k)
        self.gradients = parse_edinfo(os.path.join(folder, 'edinfo')) if os.path.exists(os.path.join(folder, 'edinfo')) else []

    def w2p(self, x, z, mode=None):
        mode = self.flip if mode is None else mode
        c = np.asarray(x) / self.s; r = np.asarray(z) / self.s
        if mode == 'xz':   return r, c          # row=z, col=x
        if mode == 'xz_fz': return (self.N - 1) - r, c
        if mode == 'zx':   return c, r
        if mode == 'xz_fx': return r, (self.N - 1) - c
        raise ValueError(mode)

    def h(self, x, z, mode=None):
        r, c = self.w2p(x, z, mode)
        return map_coordinates(self.H, [np.atleast_1d(r), np.atleast_1d(c)], order=1, mode='nearest')

    def line(self, x1, z1, x2, z2, step=None, mode=None):
        L = np.hypot(x2 - x1, z2 - z1); step = step or self.s / 2
        d = np.arange(0, L + 1e-9, step); t = d / max(L, 1e-9)
        x = x1 + (x2 - x1) * t; z = z1 + (z2 - z1) * t
        return d, self.h(x, z, mode)

def parse_edinfo(path):
    grads = []; cur = None
    for ln in open(path):
        p = ln.split()
        if not p: continue
        if p[0] == 'add_gradient':
            cur = {'a': (float(p[1]), float(p[2])), 'b': (float(p[3]), float(p[4])), 'pts': []}; grads.append(cur)
        elif p[0] == 'add_point' and cur is not None and len(p) >= 4:
            cur['pts'].append((int(p[1]), float(p[2]), float(p[3])))
    for g in grads:
        g['len'] = float(np.hypot(g['b'][0] - g['a'][0], g['b'][1] - g['a'][1]))
        g['pts'] = np.array(g['pts']) if g['pts'] else np.zeros((0, 3))
    return grads

def parse_gates(path):
    txt = open(path).read()
    out = {'start': [], 'cps': [], 'first': [], 'normal': []}
    sec = None
    for ln in txt.splitlines():
        s = ln.strip()
        if s.endswith(':'): sec = s[:-1]; continue
        if not s: continue
        nums = [float(v) for v in re.findall(r'-?\d+\.?\d*(?:e-?\d+)?', s.split('@')[0])]
        if sec == 'startinggate': out['start'].append(nums)
        elif sec == 'checkpoints': out['cps'].append(nums)
        elif sec == 'firstlap': out['first'] = [int(v) for v in s.split()]
        elif sec == 'normallap': out['normal'] = [int(v) for v in s.split()]
    return out

def parse_tileinfo(path):
    tiles = []; cur = {'lines': []}
    for ln in open(path, errors='replace'):
        s = ln.strip()
        if s == 'addtile': tiles.append(cur); cur = {'lines': []}; continue
        if s.startswith('name '): cur['name'] = s[5:]
        cur['lines'].append(s)
    if cur['lines'] and any(l for l in cur['lines']): tiles.append(cur)
    return tiles
