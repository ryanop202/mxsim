"""usland race track - RF (MX Simulator SX 2026 Anaheim 1, Anaheim 2, Houston) measured units -> lib/rf_units.json.

Reads the .saf archives of refs/rf/ in memory (no extraction on disk): terrain.hf, terrain.png, timing_gates.
RF terrains: n = 9, 0.5795 ft/px (1025 px, 593.4 ft) = half the JGSX resolution. Resolution bias measured by re-sampling the
90 JGSX units on the RF grid: height +-0.01 ft, lengths +-0.1 ft, max face angle -0.2 deg (median) -> profiles usable as is.
RF tracks have no construction lines (edinfo empty), so lanes are measured along every checkpoint axis (the gate vector of
timing_gates points along the riding direction): sample the terrain on the axis from -220 to +220 ft (0.1 ft), and at +-8 ft
beside it; keep the run around the checkpoint where the three profiles agree (< 0.25 ft: a straight block lane, not a turn);
units = complete runs above 0.06 ft (ground). Floor gap = flat ground between two consecutive units of the same lane.
Lanes seen from several checkpoints are kept once (same set of unit centres).
Note: RF blocks are 35.3 ft wide on top (JGSX / USLAND 30.4 ft): only the profile along the lane is used; the usland race
track lays it on the measured USLAND cross profile (30.4 ft + 4 ft walls).
python3 scripts/rf_units.py"""
import os, sys, re, io, json
import numpy as np
from PIL import Image

ROOT = os.environ.get('MXSIM_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RF_DIR = ROOT + '/refs/rf'
TRACKS = {'A1': 'sx2026r01anaheim1', 'A2': 'sx2026r03anaheim2', 'HOU': 'sx2026r04houston'}
ST = 0.1


def saf_index(path):
    """{relative path: (offset, size)} of a .saf archive (header lines '<size> <path>', a '-' line, then the raw data)."""
    idx = {}; f = open(path, 'rb'); entries = []
    while True:
        line = f.readline()
        m = re.match(rb'^(\d+) (\S.*?)\r?\n$', line)
        if not m:
            if line.strip() != b'-': raise ValueError(f'{path}: unexpected header {line[:60]!r}')
            break
        entries.append((int(m.group(1)), m.group(2).decode('utf-8', 'replace')))
    off = f.tell(); f.close()
    for size, rel in entries:
        idx[rel] = (off, size); off += size
    if off != os.path.getsize(path): raise ValueError(f'{path}: size mismatch ({off} != {os.path.getsize(path)})')
    return idx


def saf_read(path, rel, idx=None):
    idx = idx or saf_index(path); off, size = idx[rel]
    with open(path, 'rb') as f:
        f.seek(off); data = f.read(size)
    if len(data) != size: raise ValueError(f'{path}: truncated {rel}')
    return data


class RFTrack:
    def __init__(self, key):
        self.key = key; name = TRACKS[key]; self.saf = f'{RF_DIR}/{name}.medium.saf'; ix = saf_index(self.saf)
        n, s, lo, hi = saf_read(self.saf, f'{name}/terrain.hf', ix).decode().split()[:4]
        self.s, lo, hi = float(s), float(lo), float(hi)
        im = np.array(Image.open(io.BytesIO(saf_read(self.saf, f'{name}/terrain.png', ix)))).astype(np.float64)
        self.H = lo + im / 65535.0 * (hi - lo); self.N = self.H.shape[0]; self.side = (self.N - 1) * self.s
        self.cps = parse_cps(saf_read(self.saf, f'{name}/timing_gates', ix).decode('utf-8', 'replace'))

    def h(self, x, z):
        x = np.asarray(x, float) / self.s; z = np.asarray(z, float) / self.s
        x0 = np.clip(np.floor(x).astype(int), 0, self.N - 2); z0 = np.clip(np.floor(z).astype(int), 0, self.N - 2)
        fx = np.clip(x - x0, 0, 1); fz = np.clip(z - z0, 0, 1); H = self.H
        return (H[z0, x0] * (1 - fx) * (1 - fz) + H[z0, x0 + 1] * fx * (1 - fz) + H[z0 + 1, x0] * (1 - fx) * fz + H[z0 + 1, x0 + 1] * fx * fz)


def parse_cps(txt):
    sec = None; cps = []; num = r'(-?[\d.eE+-]+)'
    for line in txt.replace('\r', '').split('\n'):
        t = line.strip()
        if t.endswith(':'): sec = t[:-1]; continue
        if sec == 'checkpoints':
            m = re.match(num + r' \[' + num + ' ' + num + ' ' + num + r'\] \[' + num + ' ' + num + ' ' + num + r'\]', t)
            if m:
                v = [float(m.group(i)) for i in range(1, 8)]; cps.append(dict(half=v[0], c=(v[1], v[3]), d=(v[4], v[6])))
    return cps


def faces(p, s=ST):
    """face metrics of one unit profile (ground to ground): H, L, 10-90 % face lengths, max angles, lip (mean slope over the
    2 ft before the plateau), plateau (>= 95 % H), width at half height, ratio H / width at half height, crests."""
    H = p.max(); i_top = np.where(p >= 0.9 * H)[0]; i_lo = np.where(p >= 0.1 * H)[0]
    g = np.degrees(np.arctan(np.gradient(p, s))); ic = int(np.argmax(p))
    pl = np.where(p >= 0.95 * H)[0]; k0 = max(0, pl[0] - int(2.0 / s))
    half = np.where(p >= 0.5 * H)[0]; w50 = (half[-1] - half[0]) * s
    crests = []
    for i in range(1, len(p) - 1):
        if p[i] >= p[i - 1] and p[i] > p[i + 1] and p[i] > 0.6:
            if not crests or (p[crests[-1][0]:i + 1].min() < min(p[crests[-1][0]], p[i]) - 0.4): crests.append((i, float(p[i])))
            elif p[i] > crests[-1][1]: crests[-1] = (i, float(p[i]))
    return dict(H=float(H), L=len(p) * s, up=(i_top[0] - i_lo[0]) * s, down=(i_lo[-1] - i_top[-1]) * s,
                max_up=float(g[:ic + 1].max()) if ic > 0 else 0.0, max_down=float(-g[ic:].min()) if ic < len(p) - 1 else 0.0,
                lip=float(np.degrees(np.arctan((p[pl[0]] - p[k0]) / max((pl[0] - k0) * s, 1e-6)))),
                plateau=(pl[-1] - pl[0]) * s, w50=w50, ratio=float(H / max(w50, 1e-6)), crests=[(round(i * s, 1), round(h, 2)) for i, h in crests])


def kind_of(p):
    """same height classes as sx_units.kind() (low < 2.5, S < 4.3, B / T < 6.6, X), combo = 2 crests >= half height."""
    H = p.max(); L = len(p) * ST
    pk = sum(1 for i in range(1, len(p) - 1) if p[i] >= p[i - 1] and p[i] > p[i + 1] and p[i] > 0.6 and p[i] > 0.5 * H)
    if pk >= 2: return 'combo'
    if H < 2.5: return 'low'
    if H < 4.3: return 'S'
    if H < 6.6: return 'B' if L < 62 else 'T'
    return 'X'


def lanes(T):
    seen = set(); out = []
    for ci, cp in enumerate(T.cps):
        c = np.array(cp['c']); d = np.array(cp['d']); L = np.linalg.norm(d)
        if L < 1e-6: continue
        e = d / L; n = np.array([-e[1], e[0]]); u = np.arange(-220, 220.01, ST)
        P = {o: T.h(c[0] + u * e[0] + o * n[0], c[1] + u * e[1] + o * n[1]) for o in (-8, 0, 8)}
        inside = (c[0] + u * e[0] > 2) & (c[0] + u * e[0] < T.side - 2) & (c[1] + u * e[1] > 2) & (c[1] + u * e[1] < T.side - 2)
        ok = (np.abs(P[-8] - P[0]) < 0.25) & (np.abs(P[8] - P[0]) < 0.25) & inside
        i0 = int(np.argmin(np.abs(u)))
        if not ok[i0]: continue
        a = i0
        while a > 0 and ok[a - 1]: a -= 1
        b = i0
        while b < len(u) - 1 and ok[b + 1]: b += 1
        p = np.median(np.stack([P[-8], P[0], P[8]]), 0)[a:b + 1]; uu = u[a:b + 1]
        units = []; i = 0
        while i < len(p):
            if p[i] > 0.06:
                j = i
                while j < len(p) and p[j] > 0.06: j += 1
                if p[i:j].max() > 0.5 and (j - i) * ST > 4 and i > 0 and j < len(p):
                    f = faces(p[i:j]); f['u0'] = float(uu[i]); f['u1'] = float(uu[j - 1]); w = c + (f['u0'] + f['u1']) / 2 * e
                    f['centre'] = (round(float(w[0]), 1), round(float(w[1]), 1)); f['prof'] = [round(float(v), 3) for v in p[i:j]]
                    f['kind'] = kind_of(p[i:j]); units.append(f)
                i = j
            else: i += 1
        if not units: continue
        for k in range(1, len(units)): units[k]['gap_before'] = round(units[k]['u0'] - units[k - 1]['u1'], 2)
        key = tuple(sorted((round(x['centre'][0] / 6), round(x['centre'][1] / 6)) for x in units))
        if key in seen: continue
        seen.add(key)
        out.append(dict(cp=ci, c=[round(float(x), 1) for x in c], heading_deg=round(float(np.degrees(np.arctan2(e[1], e[0]))), 1), units=units))
    return out


def main():
    lib = dict(note=__doc__.split('\n')[0], grid_ft=0.5795, units={}, lanes={})
    for key in TRACKS:
        T = RFTrack(key); L = lanes(T); lib['lanes'][key] = []
        for ln in L:
            ids = []
            for i, x in enumerate(ln['units']):
                uid = f"RF_{key}_cp{ln['cp']}_{i}"; ids.append(uid)
                lib['units'][uid] = dict(track=TRACKS[key], cp=ln['cp'], index=i, kind=x['kind'], H=round(x['H'], 3), L=round(x['L'], 1),
                                         ratio=round(x['ratio'], 3), up=round(x['up'], 1), max_up=round(x['max_up'], 1), lip=round(x['lip'], 1),
                                         down=round(x['down'], 1), max_down=round(x['max_down'], 1), plateau=round(x['plateau'], 1),
                                         crests=x['crests'], gap_before=x.get('gap_before'), centre=x['centre'], prof=x['prof'])
            lib['lanes'][key].append(dict(cp=ln['cp'], c=ln['c'], heading_deg=ln['heading_deg'], units=ids))
        print(key, len(L), 'lanes', sum(len(l['units']) for l in L), 'units')
    json.dump(lib, open(ROOT + '/lib/rf_units.json', 'w'), separators=(',', ':'))
    print('lib/rf_units.json:', len(lib['units']), 'units')


if __name__ == '__main__':
    main()
