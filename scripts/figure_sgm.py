"""Saint-Georges-de-Montaigu track map (proposal to validate): top view of build/sgm_H.npy (hillshade, bumps coloured by
height) with the riding line, lane names, start (22 gates), finish line; plus the same route drawn on the user's drone photo.
Run after: MX_LAYOUT=layouts_sgm python scripts/build_stt.py
Run: python scripts/figure_sgm.py <out dir>"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT + '/scripts')
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from shading import lambert_shadow
from starts import StartRoute
import layouts_sx as LS, layouts_sgm as LT

S = 0.28975; H = np.load(f'{ROOT}/build/sgm_H.npy').astype(float); ox, oz = LT.STT_ORIGIN
p = LT.track(); smp = p.samples(1.0)
X0, X1, Z0, Z1 = ox - 130, ox + 400, oz - 70, oz + 700
PX = 2.6
P = lambda x, z: ((x - X0) * PX, (z - Z0) * PX)
FONT = lambda n: ImageFont.truetype('arialbd.ttf', n)

def topview():
    sl = (slice(int(Z0 / S), int(Z1 / S)), slice(int(X0 / S), int(X1 / S))); h = H[sl]
    lam, _ = lambert_shadow(h, S, [-0.6528, 0.3590, 0.6671], shadow=False); sh = np.clip(0.35 + 0.85 * lam, 0, 1)
    dirt = np.array([0.62, 0.45, 0.30]); grass = np.array([0.55, 0.52, 0.30])          # dry grass
    xx = X0 + np.arange(h.shape[1]) * S - ox; zz = Z0 + np.arange(h.shape[0]) * S - oz
    a0, a1, b0, b1 = LT.ARENA; inside = (xx[None] >= a0) & (xx[None] <= a1) & (zz[:, None] >= b0) & (zz[:, None] <= b1)
    if getattr(LT, 'ARENA_POLY', None):          # v11: dirt outline closer to the track
        from matplotlib.path import Path as MPath; XX, ZZ = np.meshgrid(xx, zz)
        inside = MPath(np.array(LT.ARENA_POLY)).contains_points(np.c_[XX.ravel(), ZZ.ravel()]).reshape(XX.shape)
    for c0, c1, d0, d1 in LT.GRASS_OUTSIDE['keep']: inside |= (xx[None] >= c0) & (xx[None] <= c1) & (zz[:, None] >= d0) & (zz[:, None] <= d1)
    t = np.clip(h / 9.0, 0, 1)[..., None]                                                  # bumps warmer with height
    col = np.where(inside[..., None], dirt * (1 - 0.25 * t) + np.array([0.80, 0.55, 0.32]) * 0.25 * t, grass) * sh[..., None]
    im = Image.fromarray((col.clip(0, 1) * 255).astype(np.uint8)).resize((int((X1 - X0) * PX), int((Z1 - Z0) * PX)), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    pts = [P(x, z) for x, z in zip(smp['x'], smp['z'])]; d.line(pts + [pts[0]], fill=(255, 210, 0), width=3)
    for k in range(30, len(pts), 90):
        (xa, za), (xb, zb) = pts[k - 6], pts[k]; a = np.arctan2(zb - za, xb - xa)
        tip = np.array([xb, zb]); l, r = tip - 18 * np.array([np.cos(a - 0.45), np.sin(a - 0.45)]), tip - 18 * np.array([np.cos(a + 0.45), np.sin(a + 0.45)])
        d.polygon([tuple(tip), tuple(l), tuple(r)], fill=(255, 210, 0))
    R = StartRoute(LS.STARTS[LT.KEY], LS.N_GATES, LS.GATE_PITCH); s = R.samples(1.0)
    nx, nz = -np.sin(s['th']), np.cos(s['th'])
    for sg in (-1, 1): d.line([P(x + sg * a * w / 2, z + sg * b * w / 2) for x, z, a, b, w in zip(s['x'], s['z'], nx, nz, s['w'])], fill=(255, 255, 255), width=2)
    gx, gz = LS.STARTS[LT.KEY]['gate']
    hd = np.radians(LS.STARTS[LT.KEY]['heading']); rn = np.array([-np.sin(hd), np.cos(hd)])          # along the gate row
    for k in range(LS.N_GATES):
        o = -(LS.N_GATES - 1) * LS.GATE_PITCH / 2 + k * LS.GATE_PITCH; cx_, cz_ = P(gx + rn[0] * o, gz + rn[1] * o); d.ellipse((cx_ - 4, cz_ - 4, cx_ + 4, cz_ + 4), fill=(220, 30, 40))
    d.text(P(gx - 20, gz - 70), 'START', fill='white', font=FONT(30), stroke_width=3, stroke_fill='black')
    d.text(P(gx - 22, gz + 50), '22 grilles', fill='white', font=FONT(22), stroke_width=3, stroke_fill='black')
    g3 = [g for g in p.segs if g['kind'] == 'S' and any(nm == LT.FINISH_SEC for _, _, nm in g['sections'])][0]
    prof, u0, _ = g3['sections'][0]; it = LS.COMBOS[LT.FINISH_SEC]['items'][LS.STARTS[LT.KEY]['finish'][1]]
    k = int(it[1] / 0.1) + int(np.argmax(prof[int(it[1] / 0.1):int(it[2] / 0.1)])); uc = u0 + k * 0.1
    fx, fz = g3['x0'] + uc * np.cos(g3['t']), g3['z0'] + uc * np.sin(g3['t'])
    for j in range(8): d.rectangle([*P(fx - 18 + j * 4.5, fz - 1.5), *P(fx - 13.5 + j * 4.5, fz + 1.5)], fill=('white' if j % 2 else 'black'))
    d.text(P(fx - 30, fz + 6), 'ARRIVÉE', fill='white', font=FONT(20), stroke_width=3, stroke_fill='black')
    lab = [('1', LT.XU - 60, LT.ZS - 14), ('2', LT.X['L2'] - 5, 150), ('3', LT.X['L3'] - 5, 300), ('4', LT.X['L4'] + 21, 150),
           ('5', 60, LT.ZB + 20), ('6', LT.X['L1'] - 5, 300), ('7', 150, LT.ZT - 24)]
    for t_, x, z in lab:
        cx, cz = P(ox + x, oz + z); d.ellipse((cx - 17, cz - 17, cx + 17, cz + 17), fill=(255, 255, 255), outline=(220, 30, 40), width=3)
        tb = d.textbbox((0, 0), t_, font=FONT(22)); d.text((cx - (tb[2] - tb[0]) / 2 - tb[0], cz - (tb[3] - tb[1]) / 2 - tb[1]), t_, fill=(200, 0, 0), font=FONT(22))
    d.rectangle([0, 0, im.width, 46], fill=(15, 18, 40))
    d.text((14, 8), 'SAINT-GEORGES-DE-MONTAIGU  ·  tracé v26 (proposition)  ·  tour %.0f ft' % p.s, fill='white', font=FONT(24))
    return im

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else f'{ROOT}/viewer/figures'; os.makedirs(out, exist_ok=True)
    topview().save(f'{out}/sgm_trackmap.png'); print(f'{out}/sgm_trackmap.png')

def on_photo(path):
    """the same route on the user's drone photo (lane axes measured on the photo: 1.47 px / ft, L1 at x 233, top lane at y 427)."""
    im = Image.open(path).convert('RGB'); W0 = im.width; im = im.resize((W0 * 2, im.height * 2), Image.LANCZOS); d = ImageDraw.Draw(im)
    f = lambda x, z: (2 * (212 + 1.63 * (x - ox)), 2 * (428 + 1.63 * (z - oz)))
    pts = [f(x, z) for x, z in zip(smp['x'], smp['z'])]; d.line(pts + [pts[0]], fill=(255, 220, 0), width=5)
    gx, gz = LS.STARTS[LT.KEY]['gate']
    hd = np.radians(LS.STARTS[LT.KEY]['heading']); rn = np.array([-np.sin(hd), np.cos(hd)])
    for k in range(LS.N_GATES):
        o = -(LS.N_GATES - 1) * LS.GATE_PITCH / 2 + k * LS.GATE_PITCH; a, b = f(gx + rn[0] * o, gz + rn[1] * o); d.rectangle([a - 3, b - 3, a + 3, b + 3], fill=(220, 30, 40))
    d.rectangle([0, 0, im.width, 50], fill=(15, 18, 40)); d.text((14, 10), 'Ta photo + mon tracé (jaune)', fill='white', font=FONT(28))
    return im.crop((300, 0, 1480, 2300)) if im.width > 1480 else im

if len(sys.argv) > 2:
    on_photo(sys.argv[2]).save(f'{sys.argv[1]}/sgm_sur_photo.png'); print(f'{sys.argv[1]}/sgm_sur_photo.png')
