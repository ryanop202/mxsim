"""Saint-Thibéry track map as a light inline SVG (to show in the conversation): route, bumps (rects shaded by height),
berms, start gates, finish line, rows. Run: python3 scripts/svg_stt.py > out.svg"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT + '/scripts')
import numpy as np
import layouts_sx as LS, layouts_stt as LT
from starts import StartRoute

ox, oz = LT.STT_ORIGIN; p = LT.stt(); smp = p.samples(6.0)
X0, Z0, K = ox - 130, oz - 62, 1.06                    # ft -> px
P = lambda x, z: ((x - X0) * K, (z - Z0) * K)
f = lambda v: f'{v:.0f}'
out = []
ZF_ = LT.ZF; FEN = ZF_ + 47.0                          # south fence
W, Hh = 680, int((oz + FEN + 38 - Z0) * K)
out.append(f'<svg width="100%" viewBox="0 0 {W} {Hh}" role="img"><title>Saint-Thibéry track map</title><desc>Proposed Saint-Thibéry SX layout: six east-west rows, an east lane, start at the west end, finish on the big centre table.</desc>')
out.append(f'<rect x="0" y="0" width="{W}" height="{Hh}" fill="#3f6b32" rx="8"/>')
a0, b0 = P(ox - 120, oz - 50); a1, b1 = P(ox + 475, oz + FEN)
out.append(f'<rect x="{f(a0)}" y="{f(b0)}" width="{f(a1 - a0)}" height="{f(b1 - b0)}" fill="#8a6342" stroke="#f2f2f2" stroke-width="2"/>')
ta, tb = P(ox + 60, oz + FEN + 6); tc, td = P(ox + 470, oz + FEN + 20)
out.append(f'<rect x="{f(ta)}" y="{f(tb)}" width="{f(tc - ta)}" height="{f(td - tb)}" fill="#8c8c90" rx="3"/>')
out.append(f'<text class="ts" x="{f((ta + tc) / 2)}" y="{f((tb + td) / 2 + 4)}" text-anchor="middle" style="fill:#ffffff">Tribunes</text>')
# berms (outer arc of each bermed turn)
for g in p.segs:
    if g['kind'] == 'T' and g.get('berm'):
        u = np.linspace(0, g['L'], 12); a = np.radians(g['ang']) * u / g['L']; th = g['t0'] - a
        left = g['ang'] > 0; n0 = np.array([np.sin(g['t0']), -np.cos(g['t0'])]) if left else np.array([-np.sin(g['t0']), np.cos(g['t0'])])
        rr = g['r'] + 17.0; vx, vz = -n0[0] * rr, -n0[1] * rr
        pts = [P(g['cx'] + np.cos(-ai) * vx - np.sin(-ai) * vz, g['cz'] + np.sin(-ai) * vx + np.cos(-ai) * vz) for ai in a]
        out.append('<polyline fill="none" stroke="#5a3d24" stroke-width="7" stroke-linecap="round" points="' + ' '.join(f'{f(x)},{f(y)}' for x, y in pts) + '"/>')
# bumps
for g in p.segs:
    if g['kind'] != 'S': continue
    d = np.array([np.cos(g['t']), np.sin(g['t'])]); n = np.array([-d[1], d[0]]); s0 = np.array([g['x0'], g['z0']])
    for prof, u0, name in g['sections']:
        for it in LS.COMBOS[name]['items']:
            a, b, hgt = it[1], it[2], it[3]
            col = '#c99a6a' if hgt < 3.5 else ('#a87447' if hgt < 5.0 else '#6e4527')
            if 'whoops' in it[0]:
                for k in range(12):
                    c = s0 + d * (u0 + a + (k + 0.5) * (b - a) / 12)
                    q = [c + d * 4 + n * 15, c + d * 4 - n * 15, c - d * 4 - n * 15, c - d * 4 + n * 15]
                    out.append('<polygon fill="#c99a6a" points="' + ' '.join(f'{f(P(*v)[0])},{f(P(*v)[1])}' for v in q) + '"/>')
                continue
            c0, c1 = s0 + d * (u0 + a + 2), s0 + d * (u0 + b - 2)
            q = [c0 + n * 15, c0 - n * 15, c1 - n * 15, c1 + n * 15]
            out.append(f'<polygon fill="{col}" points="' + ' '.join(f'{f(P(*v)[0])},{f(P(*v)[1])}' for v in q) + '"/>')
# route
pts = [P(x, z) for x, z in zip(smp['x'], smp['z'])]
out.append('<polyline fill="none" stroke="#ffd21f" stroke-width="2" stroke-dasharray="6 4" points="' + ' '.join(f'{f(x)},{f(y)}' for x, y in pts + pts[:1]) + '"/>')
for k in range(10, len(pts), 24):
    (xa, ya), (xb, yb) = pts[k - 1], pts[k]; a = np.arctan2(yb - ya, xb - xa)
    tip = np.array([xb, yb]); l = tip - 9 * np.array([np.cos(a - 0.5), np.sin(a - 0.5)]); r = tip - 9 * np.array([np.cos(a + 0.5), np.sin(a + 0.5)])
    out.append(f'<polygon fill="#ffd21f" points="{f(tip[0])},{f(tip[1])} {f(l[0])},{f(l[1])} {f(r[0])},{f(r[1])}"/>')
# start corridor + gates
R = StartRoute(LS.STARTS['STT'], LS.N_GATES, LS.GATE_PITCH); s = R.samples(8.0); nx, nz = -np.sin(s['th']), np.cos(s['th'])
for sg in (-1, 1):
    out.append('<polyline fill="none" stroke="#ffffff" stroke-width="1.5" points="' + ' '.join(f'{f(P(x + sg * a * w / 2, z + sg * b * w / 2)[0])},{f(P(x + sg * a * w / 2, z + sg * b * w / 2)[1])}' for x, z, a, b, w in zip(s['x'], s['z'], nx, nz, s['w'])) + '"/>')
gx, gz = LS.STARTS['STT']['gate']; ga, gb = P(gx, gz - 44); gc, gd = P(gx, gz + 44)
out.append(f'<line x1="{f(ga)}" y1="{f(gb)}" x2="{f(gc)}" y2="{f(gd)}" stroke="#e0242c" stroke-width="4"/>')
sx, sy = P(gx, gz - 50); out.append(f'<text class="ts" x="{f(sx)}" y="{f(sy)}" text-anchor="middle" style="fill:#ffffff">Start</text>')
# finish on the D table crest
sec = [g for g in p.segs if g['kind'] == 'S' and any(nm == LT.FINISH_SEC for _, _, nm in g['sections'])][0]
it = LS.COMBOS[LT.FINISH_SEC]['items'][2]; u0f = [u for _, u, nm in sec['sections'] if nm == LT.FINISH_SEC][0]
c = np.array([sec['x0'], sec['z0']]) + np.array([np.cos(sec['t']), np.sin(sec['t'])]) * (u0f + (it[1] + it[2]) / 2)
fa, fb = P(c[0], c[1] - 17); fc, fd = P(c[0], c[1] + 17)
out.append(f'<line x1="{f(fa)}" y1="{f(fb)}" x2="{f(fc)}" y2="{f(fd)}" stroke="#ffffff" stroke-width="5" stroke-dasharray="4 4"/>')
out.append(f'<line x1="{f(fa)}" y1="{f(fb + 4)}" x2="{f(fc)}" y2="{f(fd)}" stroke="#111111" stroke-width="5" stroke-dasharray="4 4"/>')
fx, fy = P(c[0], c[1] - 22); out.append(f'<text class="ts" x="{f(fx)}" y="{f(fy)}" text-anchor="middle" style="fill:#ffffff">Arrivée</text>')
# row letters (west margin of each row)
for t, z, x in zip('ABCDEF', (LT.ZA, LT.ZB, LT.ZC, LT.ZD, LT.ZE, LT.ZF), (-8, -8, LT.XM - 8, LT.XM - 8, 130, -8)):
    lx, ly = P(ox + x + 40, oz + z - 22); out.append(f'<text class="th" x="{f(lx)}" y="{f(ly)}" style="fill:#ffffff">{t}</text>')
out.append('</svg>')
print('\n'.join(out))
