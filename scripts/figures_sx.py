"""v2 figures + viewer data, all drawn from the EXPORTED terrain (dist_sx)."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, os, json, base64, numpy as np
sys.path.insert(0, ROOT + '/scripts')
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
from PIL import Image
from mxs import Track, parse_gates
from engine import turn_mid_angle
import layouts_sx as LS
OUT = ROOT + '/viewer/figures'; os.makedirs(OUT, exist_ok=True)
from names import FOLDERS
T = Track(ROOT + '/tracks/' + FOLDERS['SX1'], 'xz'); H = T.H; s = T.s
FOLD = FOLDERS
PATHS = {'SX1': LS.sx1(), 'SX2': LS.sx2(), 'SX3': LS.sx3()}
def hill(ax, x0, x1, z0, z1):
    j0, j1, i0, i1 = [int(np.clip(v, 0, T.size) / s) for v in (x0, x1, z0, z1)]
    st = max(1, (j1 - j0) // 2400); Hc = H[i0:i1:st, j0:j1:st]
    ax.imshow(LightSource(300, 40).hillshade(Hc, vert_exag=3 / (s * st)), cmap='gray', extent=[j0 * s, j1 * s, i1 * s, i0 * s])
    ax.imshow(np.ma.masked_less(Hc, 0.15), cmap='terrain', alpha=.35, vmin=0, vmax=12, extent=[j0 * s, j1 * s, i1 * s, i0 * s])
    ax.set_xlim(x0, x1); ax.set_ylim(z1, z0); ax.set_xlabel('x (ft)'); ax.set_ylabel('z (ft)')
def path_draw(ax, key, every=70):
    p = PATHS[key]; smp = p.samples(1.0); x, z = smp['x'], smp['z']
    ax.plot(x, z, 'r-', lw=0.8, alpha=0.85)
    for k in range(0, len(x) - 3, every): ax.annotate('', xy=(x[k + 3], z[k + 3]), xytext=(x[k], z[k]), arrowprops=dict(arrowstyle='-|>', color='r', lw=1.1))
    G = parse_gates(f'{ROOT}/tracks/{FOLD[key]}/timing_gates')
    for i, cp in enumerate(G['cps']):
        L_, cx, cy, cz, dx, dy, dz = cp[:7]; ax.plot([cx - dx, cx + dx], [cz - dz, cz + dz], color='#ff00ff' if i in G['normal'] else '#ffaa00', lw=0.8)
    st = np.array([g[:3] for g in G['start']]); ax.plot(st[:, 0], st[:, 2], 's', color='yellow', ms=2.5, mec='k', mew=0.3)
    S0 = LS.STARTS[key]; hd = np.radians(S0['heading']); f = np.array([np.cos(hd), np.sin(hd)]); gc = np.array(S0['gate'])
    from starts import StartRoute
    RT = StartRoute(S0, LS.N_GATES, LS.GATE_PITCH); rs = RT.samples(1.0)
    for sg in (-1, 1):
        ax.plot(rs['x'] - np.sin(rs['th']) * rs['w'] / 2 * sg, rs['z'] + np.cos(rs['th']) * rs['w'] / 2 * sg, '--', color='gold', lw=1.2)
    ax.plot(rs['x'], rs['z'], ':', color='gold', lw=0.8)
    tp = gc + f * 28; ax.text(tp[0], tp[1], 'DÉPART', fontsize=8, weight='bold', ha='center', va='center', bbox=dict(fc='yellow', alpha=.9, lw=0))
    for g in p.segs:
        if g['kind'] == 'S' and g['sections']:
            nm = g['sections'][0][2].split(' ', 1)[1]
            ax.text(g['x0'] + g['L'] / 2 * np.cos(g['t']), g['z0'] + g['L'] / 2 * np.sin(g['t']), nm, fontsize=6.5, color='navy', ha='center', va='center',
                    rotation=0 if abs(np.cos(g['t'])) > 0.5 else 90, bbox=dict(fc='white', alpha=.7, lw=0, pad=0.4))
        if g['kind'] == 'P':
            m = g['pts'][len(g['pts']) // 2]
            ax.text(m[0], m[1], 'SABLE ' + ('Glendale (J)' if g['stamp'] == 'GL' else 'Glendale (virage)'), fontsize=7, color='saddlebrown', weight='bold', ha='center', bbox=dict(fc='lightyellow', alpha=.8, lw=0, pad=0.4))
# overview
fig, ax = plt.subplots(figsize=(13, 13)); hill(ax, 0, T.size, 0, T.size)
for k, c in (('SX1', 'r'), ('SX2', 'b'), ('SX3', 'm')):
    smp = PATHS[k].samples(2.0); ax.plot(smp['x'], smp['z'], '-', color=c, lw=1, label=k)
ax.legend(); ax.set_title('USLAND 2026 SX Test Tracks : terrain partagé exporté (1187 × 1187 ft, grille 0.29 ft identique aux JGSX)')
plt.savefig(f'{OUT}/00_overview.png', dpi=80, bbox_inches='tight'); plt.close()
for key, box, fs in (('SX1', (0, 595, 0, 425), (17, 12.2)), ('SX2', (572, 1045, 0, 535), (14, 15.8)), ('SX3', (20, 1150, 620, 1065), (19, 7.6))):
    fig, ax = plt.subplots(figsize=fs); hill(ax, *box); path_draw(ax, key)
    ax.set_title(f'{key} : {PATHS[key].s:.0f} ft ({PATHS[key].s*0.3048:.0f} m). Flèches = sens ; jaune = 22 grilles + couloir de départ ; magenta = portes du tour ; orange = portes du 1er tour')
    plt.savefig(f'{OUT}/01_top_{key}.png', dpi=80, bbox_inches='tight'); plt.close()
# lane profiles: exported vs composed measured units (coloured by source unit)
for key in ('SX1', 'SX2', 'SX3'):
    p = PATHS[key]; lanes = [g for g in p.segs if g['kind'] == 'S' and g['sections']]
    fig, axs = plt.subplots(len(lanes), 1, figsize=(18, 2.15 * len(lanes)))
    for ax, g in zip(np.atleast_1d(axs), lanes):
        u = np.arange(0, g['L'], 0.1); ax.plot(u, T.h(g['x0'] + u * np.cos(g['t']), g['z0'] + u * np.sin(g['t'])), 'k-', lw=1.3)
        for prof, u0, name in g['sections']:
            for n, a, b, hh in LS.COMBOS[name]['items']:
                ax.axvspan(u0 + a, u0 + b, color='orange' if 'whoops' in n else ('gold' if 'g6' in n or 'g8' in n and 'Glendale' in n and hh < 2 else 'lightsteelblue'), alpha=0.35, lw=0)
                ax.text(u0 + (a + b) / 2, hh + 0.4, f'{hh:.1f}', fontsize=6, ha='center')
        ax.set_aspect('equal'); ax.set_xlim(0, g['L']); ax.set_ylim(-0.3, 12.5); ax.grid(alpha=.3)
        ax.set_title(f"{key} – {g['sections'][0][2].split(' ', 1)[1]} (couloir {g['L']:.0f} ft, échelle 1:1, chiffres = hauteur en ft)", fontsize=9)
    plt.tight_layout(); plt.savefig(f'{OUT}/02_lanes_{key}.png', dpi=72); plt.close()
# berm radial section exported vs JGSX reference stamp (entry lip check)
B = json.load(open(ROOT + '/lib/berm_stamps.json'))
fig, axs = plt.subplots(1, 2, figsize=(16, 3.4)); done = []
for g in PATHS['SX1'].segs:
    if g['kind'] == 'T' and g.get('berm') and g['berm'] not in done and len(done) < 2:
        done.append(g['berm']); ax = axs[len(done) - 1]; a = turn_mid_angle(g); r = np.arange(0, 62, 0.05)
        ax.plot(r, T.h(g['cx'] + r * np.cos(a), g['cz'] + r * np.sin(a)), 'k', label='exporté')
        bb = B[g['berm']]; ref = Track(REF + '/JGSX2026TestTracks/' + bb['ref'], 'xz')
        ax.plot(r, ref.h(bb['cx'] + r * np.cos(bb['mid_angle']), bb['cz'] + r * np.sin(bb['mid_angle'])) - np.median(ref.H), 'r--', label=f"JGSX {bb['ref'][8:]}")
        ax.set_aspect('equal'); ax.grid(alpha=.3); ax.legend(fontsize=7); ax.set_title(f"Berm {g['berm']} : coupe radiale (pied du berm sans marche)")
plt.tight_layout(); plt.savefig(f'{OUT}/03_berms.png', dpi=80); plt.close()
for f in os.listdir(OUT):
    if f.endswith('.png'):
        im = Image.open(f'{OUT}/{f}').convert('RGB'); w, h = im.size
        if w > 1700: im = im.resize((1700, int(h * 1700 / w)), Image.LANCZOS)
        im.save(f'{OUT}/{f[:-4]}.jpg', quality=82, optimize=True); os.remove(f'{OUT}/{f}')
# viewer data (exported terrain, 0.58 ft display grid)
out = {}
for key, (x0, x1, z0, z1) in (('SX1', (0, 595, 0, 425)), ('SX2', (572, 1045, 0, 535)), ('SX3', (20, 1150, 620, 1065))):
    st = 2 if key != 'SX3' else 3
    j0, j1, i0, i1 = [int(round(min(v, T.size) / s)) for v in (x0, x1, z0, z1)]
    Hs = H[i0:i1 + 1:st, j0:j1 + 1:st]; hmin, hmax = float(Hs.min()), float(Hs.max())
    q = np.round((Hs - hmin) / max(hmax - hmin, 1e-6) * 65535).astype('<u2')
    tl = T.tiles[(np.arange(i0, i1 + 1, st) // 2).clip(0, 2047)][:, (np.arange(j0, j1 + 1, st) // 2).clip(0, 2047)].astype(np.uint8)
    smp = PATHS[key].samples(3.0); G = parse_gates(f'{ROOT}/tracks/{FOLD[key]}/timing_gates')
    out[key] = dict(w=int(Hs.shape[1]), h=int(Hs.shape[0]), x0=j0 * s, z0=i0 * s, step=st * s, hmin=hmin, hmax=hmax,
                    hb64=base64.b64encode(q.tobytes()).decode(), tb64=base64.b64encode(tl.tobytes()).decode(),
                    path=np.round(np.c_[smp['x'], smp['z']], 1).ravel().tolist(), lap_ft=round(PATHS[key].s), gates=[[round(g[0], 1), round(g[2], 1)] for g in G['start']])
open(ROOT + '/viewer/terrain_data.js', 'w').write('const TERRAIN=' + json.dumps(out, separators=(',', ':')) + ';')
print(sorted(os.listdir(OUT)), os.path.getsize(ROOT + '/viewer/terrain_data.js') / 1e6)
# sand: exported SX3 sand vs the Glendale original (same hillshade settings)
from mxs import Track as _Tr
GLD = _Tr(REF + '/JGSX2026TestTracks/JGSX2026Glendale', 'xz')
fig, axs = plt.subplots(2, 2, figsize=(18, 16))
p3 = PATHS['SX3']
for row, key in enumerate(('GL', 'GR')):
    seg = [g for g in p3.segs if g['kind'] == 'P' and g['stamp'] == key][0]; W = seg['pts']
    x0, x1, z0, z1 = W[:, 0].min() - 70, W[:, 0].max() + 70, W[:, 1].min() - 60, W[:, 1].max() + 60
    hill(axs[row, 0], x0, x1, z0, z1); axs[row, 0].plot(W[:, 0], W[:, 1], 'r-', lw=1)
    axs[row, 0].set_title(f"SX3 exporté : {seg['tag']}" + (' (version miroir)' if seg.get('mirror') else ''))
    St = json.load(open(ROOT + '/lib/sand_stamps.json'))[key]; Lr = np.array(St['line'])
    rx0, rx1, rz0, rz1 = Lr[:, 0].min() - 70, Lr[:, 0].max() + 70, Lr[:, 1].min() - 60, Lr[:, 1].max() + 60
    j0, j1, i0, i1 = [int(np.clip(v, 0, GLD.size) / GLD.s) for v in (rx0, rx1, rz0, rz1)]
    Hc = GLD.H[i0:i1, j0:j1] - np.median(GLD.H)
    axs[row, 1].imshow(LightSource(300, 40).hillshade(Hc, vert_exag=3 / GLD.s), cmap='gray', extent=[j0 * GLD.s, j1 * GLD.s, i1 * GLD.s, i0 * GLD.s])
    axs[row, 1].imshow(np.ma.masked_less(Hc, 0.15), cmap='terrain', alpha=.35, vmin=0, vmax=12, extent=[j0 * GLD.s, j1 * GLD.s, i1 * GLD.s, i0 * GLD.s])
    axs[row, 1].plot(Lr[:, 0], Lr[:, 1], 'r-', lw=1); axs[row, 1].set_title(f'Original JGSX 2026 Glendale (avec les pistes voisines)')
plt.tight_layout(); plt.savefig(f'{OUT}/04_sand_vs_glendale.png', dpi=60); plt.close()
im = Image.open(f'{OUT}/04_sand_vs_glendale.png').convert('RGB'); w, h = im.size
if w > 1700: im = im.resize((1700, int(h * 1700 / w)), Image.LANCZOS)
im.save(f'{OUT}/04_sand_vs_glendale.jpg', quality=82, optimize=True); os.remove(f'{OUT}/04_sand_vs_glendale.png')
print('sand figure done')
