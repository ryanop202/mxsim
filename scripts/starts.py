"""Start corridors (v10): gate row -> route (straights, turns, 'TO' a point) -> merge point on the lap.

layouts_sx.STARTS[key] = dict(gate=(x, z) world, heading=deg, route=[ops], narrow=(s_a, s_b), finish=(section, item_index))
  ops: ('S', L) straight | ('T', ang_deg, r, berm_key or None) turn (ang > 0 = left) | ('TO', (x, z)) straight to a world point
  narrow: corridor full width (22 gates + margin) until s_a, then linear down to LANE_W at s_b.
  finish: lap finish line (last gate of normallap) on the crest of that unit of that section; None = just before the merge.
"""
import numpy as np
from engine import Path

LANE_W = 30.0

def full_width(n_gates, pitch):
    return (n_gates - 1) * pitch + 8.0

class StartRoute:
    def __init__(self, S0, n_gates=22, pitch=4.0):
        self.S0 = S0; self.W0 = full_width(n_gates, pitch)
        p = Path(S0['gate'][0], S0['gate'][1], S0['heading'], 'start')
        self.berm_turns = []
        for op in S0['route']:
            if op[0] == 'S': p.straight(op[1])
            elif op[0] == 'TO':
                dx, dz = op[1][0] - p.x, op[1][1] - p.z; p.t = float(np.arctan2(dz, dx)); p.straight(float(np.hypot(dx, dz)))
            elif op[0] == 'T':
                p.turn(op[1], op[2], op[3] if len(op) > 3 else None)
                if len(op) > 3 and op[3]: self.berm_turns.append(p.segs[-1])
        self.path = p; self.L = p.s
        self.merge = np.array([p.x, p.z]); self.merge_heading = p.t
        self.s_straight = S0['route'][0][1] if S0['route'][0][0] == 'S' else 0.0

    def width(self, s):
        a, b = self.S0['narrow']
        return np.interp(s, [0, a, b, 1e9], [self.W0, self.W0, LANE_W, LANE_W])

    def samples(self, ds=1.0):
        smp = self.path.samples(ds); smp['w'] = self.width(smp['s'])
        smp['berm'] = np.array([self.path.segs[int(k)].get('berm') is not None and self.path.segs[int(k)]['kind'] == 'T' for k in smp['seg']])
        return smp

    def area_points(self, ds=1.0, dv=1.0, margin=0.0):
        """points covering the corridor (|v| <= w/2 - margin); returns x, z, s, on_berm_turn"""
        smp = self.samples(ds); X, Z, S, B = [], [], [], []
        for x, z, th, s, w, b in zip(smp['x'], smp['z'], smp['th'], smp['s'], smp['w'], smp['berm']):
            nx, nz = -np.sin(th), np.cos(th); v = np.arange(-w / 2 + margin, w / 2 - margin + 1e-6, dv)
            X.append(x + nx * v); Z.append(z + nz * v); S.append(np.full(len(v), s)); B.append(np.full(len(v), b))
        return np.concatenate(X), np.concatenate(Z), np.concatenate(S), np.concatenate(B)

def finish_s(path, start, COMBOS):
    """arc length (on the lap path) of the finish line: crest of the given unit, or 8 ft before the merge."""
    smp = path.samples(0.5)
    sM = float(smp['s'][np.argmin(np.hypot(smp['x'] - start['merge'][0], smp['z'] - start['merge'][1]))])
    fin = start.get('finish')
    if not fin: return (sM - 8.0) % path.s, sM
    name, k = fin
    for g in path.segs:
        if g['kind'] != 'S': continue
        for prof, u0, nm in g['sections']:
            if nm == name:
                it = COMBOS[nm]['items'][k]; i0, i1 = int(it[1] / 0.1), int(it[2] / 0.1)
                crest = it[1] + float(np.argmax(prof[i0:i1])) * 0.1
                return float(g['s0'] + u0 + crest), sM
    raise KeyError(name)
