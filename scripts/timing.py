"""Timing gates (startinggate / checkpoints / firstlap / normallap) of a track, from its path and start only (no terrain):
used by export_sx.py and by regen_timing.py (rewrites one timing_gates file in place, e.g. after moving the finish line)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import layouts_sx as LS

def gate_marks(path, turn_fr=None):
    """v11 (Ryan): fewer gates, only where needed - one in the middle of every turn (and of every Glendale sand stamp),
    2 per rhythm lane (3 if longer than 330 ft), at 1/(n+1) .. n/(n+1) of the straight."""
    out = []
    for g in path.segs:
        if g['kind'] in ('T', 'P'):
            if g['kind'] == 'T' and abs(g['ang']) < 45: continue          # flat drifts / sand exit bend: not a turn
            if turn_fr and g['kind'] == 'T': out += [g['s0'] + g['L'] * k for k in turn_fr]; continue   # v33 STT: middle one = pylon
            out.append(g['s0'] + g['L'] / 2)
        elif g['kind'] == 'S' and g['L'] > 60:
            n = 3 if g['L'] > 330 else 2
            out += [g['s0'] + g['L'] * k / (n + 1) for k in range(1, n + 1)]
    return out

def gates(path, start, half=18.0, turn_gates=None):
    """JGSX-style timing (v11).
    - startinggate: 22 gates at 4 ft, facing the start heading.
    - checkpoint line = 'half [centre] [vector]': the vector points ALONG the riding direction and its length is half (measured on
      all 7 reference tracks: cos(travel, vector) median 0.97-1.0, |vector| = half). v10 had it across the track (wrong).
    - loop gates = gate_marks (turns + 2-3 per lane), finish gate last (normallap ends on it): crest of a jump or 8 ft before the merge.
    - first lap: 1-2 start-only gates on the start route, then the loop from the merge to the finish. If the finish comes soon
      after the merge (less than half a lap), a separate gate F' (12 ft before the finish, first lap only) is crossed first."""
    from starts import StartRoute, finish_s
    smp = path.samples(0.5); L = path.s
    R = StartRoute(start, LS.N_GATES, LS.GATE_PITCH)
    gx, gz = start['gate']; h = np.radians(start['heading']); f = np.array([np.cos(h), np.sin(h)]); n = np.array([-f[1], f[0]])
    ang = float(np.arctan2(-f[0], -f[1]))                     # MXS gate angle: riders face (-sin a, -cos a)
    lines = ['startinggate:']
    for k in range(LS.N_GATES):
        o = (k - (LS.N_GATES - 1) / 2) * LS.GATE_PITCH; x, z = gx + o * n[0], gz + o * n[1]
        lines.append(f'[{x:.6f} 0.000000 {z:.6f}] {ang:.6f}')
    lines.append('checkpoints:'); cps = []
    sF, sM = finish_s(path, start, LS.COMBOS)
    def gate_at(x, z, th, hl): return (hl, x, z, np.cos(th) * hl, np.sin(th) * hl)      # vector along the travel direction
    TG = turn_gates
    def turn_gate(i, g, inner_d):
        # v33 (Saint-Thibery): asymmetric gate across a turn - stops `inner_d` ft inside the riding line (no cutting the inside),
        # reaches TG['outer'] ft past the outer lane edge (berm); line still perpendicular to the travel direction
        pnt = np.array([smp['x'][i], smp['z'][i]]); c = np.array([g['cx'], g['cz']]); n_in = (c - pnt) / np.linalg.norm(c - pnt)
        a = pnt + n_in * inner_d; b = pnt - n_in * (TG['half_lane'] + TG['outer']); m = (a + b) / 2; hl = float(np.linalg.norm(a - b) / 2)
        return gate_at(m[0], m[1], smp['th'][i], hl)
    def lap_gate(sv, hl0=half):
        i = int(np.argmin(np.abs(smp['s'] - sv % L)))
        g = path.segs[int(smp['seg'][i])]
        if TG and g['kind'] == 'T' and abs(g['ang']) >= 45:
            return turn_gate(i, g, TG['half_lane'] + TG['inner'])
        hl = hl0 + (6.0 if path.segs[int(smp['seg'][i])]['kind'] == 'P' else 0.0)     # wider in the Glendale sand channel
        return gate_at(smp['x'][i], smp['z'][i], smp['th'][i], hl)
    marks = gate_marks(path, TG['fr'] if TG else None)
    pyl_gate = {}
    if TG and TG.get('pylons'):          # v33: one gate per turn through the pylon (sample of the turn closest to it)
        tsegs = [k for k, g in enumerate(path.segs) if g['kind'] == 'T']
        for k, (px, pz) in zip(tsegs, TG['pylons']):
            idx = np.where(smp['seg'] == k)[0]; j = idx[int(np.argmin(np.hypot(smp['x'][idx] - px, smp['z'][idx] - pz)))]
            pnt = np.array([smp['x'][j], smp['z'][j]]); c = np.array([path.segs[k]['cx'], path.segs[k]['cz']])
            n_in = (c - pnt) / np.linalg.norm(c - pnt)
            pyl_gate[round(float(smp['s'][j]), 1)] = (j, k, float(np.dot(np.array([px, pz]) - pnt, n_in)))
            marks.append(float(smp['s'][j]))
    rel = sorted({round((m - sF) % L, 1) for m in marks})
    rel = [r for r in rel if 15.0 < r < L - 15.0 and abs(r - (sM - sF) % L) > 10.0]
    for r in rel:
        hit = [v for q, v in pyl_gate.items() if abs((q - (sF + r)) % L) < 0.3 or abs((q - (sF + r)) % L - L) < 0.3]
        if hit: j, k, d = hit[0]; cps.append(turn_gate(j, path.segs[k], d))
        else: cps.append(lap_gate(sF + r))
    cps.append(lap_gate(sF)); fin = len(cps) - 1
    loop_idx = list(range(len(cps)))
    loop_rel = [((sF + r) - sM) % L for r in rel] + [(sF - sM) % L]           # position of every loop gate after the merge
    # start-only gates: middle of the first straight, and of the last long straight of the route if any
    rs = R.samples(1.0); start_only = []
    marks = [R.s_straight / 2 if R.s_straight > 60 else 30.0] + [float(g['s0'] + g['L'] / 2) for g in R.path.segs[1:] if g['kind'] == 'S' and g['L'] > 60][-1:]
    for sv in sorted(set(round(m) for m in marks if 20 < m < R.L - 25)):
        i = int(np.argmin(np.abs(rs['s'] - sv))); hl = rs['w'][i] / 2 + 4.0
        cps.append(gate_at(rs['x'][i], rs['z'][i], rs['th'][i], hl)); start_only.append(len(cps) - 1)
    delta = (sF - sM) % L
    if delta < L / 2:      # finish just after the merge: lap 1 goes round once more
        i = int(np.argmin(np.abs(smp['s'] - (sF - 12.0) % L)))
        cps.append(gate_at(smp['x'][i], smp['z'][i], smp['th'][i], half)); fprime = len(cps) - 1
        after = [k for k in sorted(loop_idx, key=lambda k: loop_rel[k]) if loop_rel[k] > delta]
        before = [k for k in sorted(loop_idx, key=lambda k: loop_rel[k]) if loop_rel[k] < delta]
        first = start_only + [fprime] + after + before + [fin]
    else:
        # v12: only the loop gates between the merge and the finish (a finish in the middle of the lap gives a shorter first
        # lap, as JGSX); before, the finish was always just before the merge so every loop gate was in that interval
        first = start_only + [k for k in sorted(loop_idx, key=lambda k: loop_rel[k]) if k != fin and loop_rel[k] < delta] + [fin]
    for c in cps: lines.append(f'{c[0]:.6f} [{c[1]:.6f} 0.000000 {c[2]:.6f}] [{c[3]:.6f} 0.000000 {c[4]:.6f}]')
    lines += ['firstlap:', ' '.join(map(str, first)) + ' ', 'normallap:', ' '.join(map(str, loop_idx)) + ' ', '']
    return '\n'.join(lines), cps, first, loop_idx, sM, sF

