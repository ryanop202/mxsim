"""Saint-Thibéry track map (proposal to validate): top view of build/stt_H.npy with the riding line, rows, turns, start,
finish, plus the user's drone photo with the same route drawn on it. Run after build_stt.py.
Run: python3 scripts/figure_stt.py <drone top photo> <out dir>"""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT + '/scripts')
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from shading import lambert_shadow
from starts import StartRoute
import layouts_sx as LS, layouts_stt as LT

S = 0.28975; H = np.load(f'{ROOT}/build/stt_H.npy').astype(float); ox, oz = LT.STT_ORIGIN
p = LT.stt(); smp = p.samples(1.0); X0, X1, Z0, Z1 = ox - 135, ox + 495, oz - 70, oz + 285
PX = 3.0                                                         # image px per ft
def P(x, z): return ((x - X0) * PX, (z - Z0) * PX)
FONT = lambda n: ImageFont.truetype('arialbd.ttf', n)

def topview():
    sl = (slice(int(Z0 / S), int(Z1 / S)), slice(int(X0 / S), int(X1 / S))); h = H[sl]
    lam, _ = lambert_shadow(h, S, [-0.6528, 0.3590, 0.6671], shadow=False); sh = np.clip(0.35 + 0.85 * lam, 0, 1)
    dirt = np.array([0.60, 0.43, 0.29]); grass = np.array([0.30, 0.52, 0.24])
    xx = X0 + np.arange(h.shape[1]) * S; zz = Z0 + np.arange(h.shape[0]) * S
    inside = ((xx[None, :] > ox - 120) & (xx[None, :] < ox + 475) & (zz[:, None] > oz - 50) & (zz[:, None] < oz + 262))
    col = np.where(inside[..., None], dirt, grass) * sh[..., None]
    im = Image.fromarray((col.clip(0, 1) * 255).astype(np.uint8)).resize((int((X1 - X0) * PX), int((Z1 - Z0) * PX)), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    d.rectangle([*P(ox - 120, oz - 50), *P(ox + 475, oz + 262)], outline=(245, 245, 245), width=5)          # arena fence
    d.rectangle([*P(ox + 60, oz + 268), *P(ox + 470, oz + 283)], fill=(120, 120, 125)); d.text(P(ox + 230, oz + 268), 'TRIBUNES', fill='white', font=FONT(30))
    # riding line + arrows
    pts = [P(x, z) for x, z in zip(smp['x'], smp['z'])]; d.line(pts + [pts[0]], fill=(255, 210, 0), width=4)
    for k in range(40, len(pts), 120):
        (xa, za), (xb, zb) = pts[k - 6], pts[k]; a = np.arctan2(zb - za, xb - xa)
        tip = np.array([xb, zb]); l, r = tip - 22 * np.array([np.cos(a - 0.45), np.sin(a - 0.45)]), tip - 22 * np.array([np.cos(a + 0.45), np.sin(a + 0.45)])
        d.polygon([tuple(tip), tuple(l), tuple(r)], fill=(255, 210, 0))
    # start: gates, corridor
    R = StartRoute(LS.STARTS['STT'], LS.N_GATES, LS.GATE_PITCH); s = R.samples(1.0)
    nx, nz = -np.sin(s['th']), np.cos(s['th'])
    for sg in (-1, 1): d.line([P(x + sg * a * w / 2, z + sg * b * w / 2) for x, z, a, b, w in zip(s['x'], s['z'], nx, nz, s['w'])], fill=(255, 255, 255), width=3)
    gx, gz = LS.STARTS['STT']['gate']
    for k in range(LS.N_GATES):
        zg = gz - (LS.N_GATES - 1) * LS.GATE_PITCH / 2 + k * LS.GATE_PITCH; d.rectangle([*P(gx - 1, zg - 1.6), *P(gx + 1, zg + 1.6)], fill=(220, 30, 40))
    d.text(P(gx - 32, gz - 60), 'START', fill='white', font=FONT(34)); d.text(P(gx - 30, gz + 52), '22 grilles', fill='white', font=FONT(24))
    # finish line: crest of the big table (D)
    sec = [g for g in p.segs if g['kind'] == 'S' and any('STT-D' in nm for _, _, nm in g['sections'])][0]
    m = (smp['s'] >= sec['s0']) & (smp['s'] <= sec['s0'] + 120)
    hh = H[(smp['z'][m] / S).astype(int), (smp['x'][m] / S).astype(int)]; k = np.argmax(hh); fx, fz = smp['x'][m][k], smp['z'][m][k]
    for j in range(8): d.rectangle([*P(fx - 1.5, fz - 18 + j * 4.5), *P(fx + 1.5, fz - 13.5 + j * 4.5)], fill=('white' if j % 2 else 'black'))
    d.text(P(fx - 30, fz - 40), 'ARRIVÉE', fill='white', font=FONT(26))
    # labels
    lab = {'A': (ox + 200, oz - 30, 'A  longue rythmique (11 singles 2,5-4 ft)'), 'B': (ox + 180, oz + 43 - 27, 'B  rythmique + 2 gros singles (5,8-5,9 ft)'),
           'C': (ox + 230, oz + 86 - 27, 'C  triple sur table, off'), 'D': (ox + 230, oz + 129 - 27, 'D  grosse table centrale 9 ft + 2 singles'),
           'E': (ox + 150, oz + 172 - 27, 'E  ligne droite départ / arrivée (plate)'), 'F': (ox + 150, oz + 215 + 20, 'F  3 singles + 12 whoops'),
           'NS': (ox + 452, oz + 60, 'triple')}
    for k_, (x, z, t) in lab.items(): d.text(P(x, z), t, fill='white', font=FONT(24), stroke_width=3, stroke_fill='black')
    for g in p.segs:
        if g['kind'] == 'T': d.text(P(g['cx'] - 8 + (25 if g['cx'] > ox + 200 else -25), g['cz'] - 8), g['tag'][:2], fill=(255, 255, 255), font=FONT(30), stroke_width=3, stroke_fill='black')
    d.rectangle([0, 0, im.width, 60], fill=(15, 18, 40)); d.text((20, 10), 'SAINT-THIBÉRY - track map (proposition)  ·  tour %.0f ft  ·  pas de sable' % p.s, fill='white', font=FONT(34))
    return im

def on_photo(path):
    """my route drawn on the drone top view (photo rows A..F at y 140..590, west end x 200, east end x 920)."""
    im = Image.open(path).convert('RGB'); d = ImageDraw.Draw(im)
    fx = lambda x: 200 + (x - ox) * (720 / 370.0); fz = lambda z: 140 + (z - oz) * (450 / 215.0)
    pts = [(fx(x), fz(z)) for x, z in zip(smp['x'], smp['z'])]; d.line(pts + [pts[0]], fill=(255, 220, 0), width=4)
    gx, gz = LS.STARTS['STT']['gate']; d.text((fx(gx) - 10, fz(gz) - 50), 'START', fill='white', font=FONT(22), stroke_width=3, stroke_fill='black')
    for t, z in zip('ABCDEF', (0, 43, 86, 129, 172, 215)): d.text((fx(ox + 175), fz(oz + z) - 30), t, fill=(255, 255, 0), font=FONT(30), stroke_width=3, stroke_fill='black')
    d.rectangle([0, 0, im.width, 44], fill=(15, 18, 40)); d.text((10, 8), 'Ta photo + mon tracé (jaune) : à corriger si besoin', fill='white', font=FONT(24))
    return im

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else f'{ROOT}/viewer/figures'; os.makedirs(out, exist_ok=True)
    topview().save(f'{out}/stt_trackmap.png'); print(f'{out}/stt_trackmap.png')
    if len(sys.argv) > 1: on_photo(sys.argv[1]).save(f'{out}/stt_sur_photo.png'); print(f'{out}/stt_sur_photo.png')
