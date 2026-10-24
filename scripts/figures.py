"""Deliverable figures, all drawn from the EXPORTED terrain (dist/RyanCompoundMX/terrain.png)."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, os, json, numpy as np
sys.path.insert(0, ROOT + '/scripts')
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.colors import LightSource, ListedColormap
from mxs import Track, parse_gates
from engine import LIB, section_profile
import layouts

OUT = ROOT + '/legacy_mx/deliver/figures'; os.makedirs(OUT, exist_ok=True)
T = Track(ROOT + '/legacy_mx/tracks/RyanCompoundMX', 'xz'); H = T.H; s = T.s
plt.rcParams.update({'font.size': 9})

def hill(ax, x0, x1, z0, z1, exag=2.5, contours=True):
    j0, j1, i0, i1 = [int(v / s) for v in (x0, x1, z0, z1)]
    st = max(1, (j1 - j0) // 2200); Hc = H[i0:i1:st, j0:j1:st]
    ax.imshow(LightSource(315, 35).hillshade(Hc, vert_exag=exag / (s * st)), cmap='gray', extent=[x0, x1, z1, z0])
    ax.imshow(Hc, cmap='terrain', alpha=0.33, extent=[x0, x1, z1, z0])
    if contours:
        ax.contour(np.linspace(x0, x1, Hc.shape[1]), np.linspace(z0, z1, Hc.shape[0]), Hc, levels=np.arange(-20, 50, 2.5), colors='k', linewidths=0.2)
    ax.set_xlim(x0, x1); ax.set_ylim(z1, z0); ax.set_xlabel('x (ft)'); ax.set_ylabel('z (ft)')

def draw_path(ax, p, folder, every=150):
    smp = p.samples(1.0); x, z = smp['x'], smp['z']
    ax.plot(x, z, 'r-', lw=0.8, alpha=0.8)
    for k in range(0, len(x) - 3, every):
        ax.annotate('', xy=(x[k + 3], z[k + 3]), xytext=(x[k], z[k]), arrowprops=dict(arrowstyle='-|>', color='r', lw=1.2))
    G = parse_gates(f'{ROOT}/legacy_mx/tracks/{folder}/timing_gates')
    for i, cp in enumerate(G['cps']):
        L_, cx, cy, cz, dx, dy, dz = cp[:7]; ax.plot([cx + dz, cx - dz], [cz - dx, cz + dx], color='#ff00ff', lw=0.8)
    st = np.array([g[:3] for g in G['start']]); ax.plot(st[:, 0], st[:, 2], 's', color='yellow', ms=2.5, mec='k', mew=0.3)
    for g in p.segs:
        if g['kind'] == 'S' and g['sections']:
            names = ', '.join(sec[0] for sec in g['sections'])
            xm = g['x0'] + g['L'] / 2 * np.cos(g['t']); zm = g['z0'] + g['L'] / 2 * np.sin(g['t'])
            ax.text(xm, zm, names, fontsize=6.5, color='navy', ha='center', va='center', bbox=dict(fc='white', alpha=0.65, lw=0, pad=0.5))
    ax.text(st[0, 0], st[0, 2] - 12, 'START', fontsize=8, color='k', weight='bold', bbox=dict(fc='yellow', alpha=0.8, lw=0))

# 1. compound overview
fig, ax = plt.subplots(figsize=(14, 14)); hill(ax, 0, T.size, 0, T.size, contours=True)
for nm, fn, col in (('MX', layouts.mx, 'r'), ('SX1', layouts.sx1, 'b'), ('SX2', layouts.sx2, 'm')):
    smp = fn().samples(2.0); ax.plot(smp['x'], smp['z'], '-', color=col, lw=1, label=nm)
ax.legend(loc='upper right'); ax.set_title('Ryan Compound - terrain partagé exporté (1638 x 1638 ft, grille 0.4 ft)')
plt.savefig(f'{OUT}/00_compound_overview.png', dpi=80, bbox_inches='tight'); plt.close()

# 2. per-circuit top views
for nm, fn, folder, box, size in (('MX', layouts.mx, 'RyanCompoundMX', (0, 1638, 0, 1290), (18, 15)),
                                  ('SX1', layouts.sx1, 'RyanCompoundSX1', (10, 600, 1280, 1638), (18, 11.5)),
                                  ('SX2', layouts.sx2, 'RyanCompoundSX2', (620, 1190, 1130, 1638), (16, 14.5))):
    p = fn(); fig, ax = plt.subplots(figsize=size); hill(ax, *box, contours=(nm == 'MX'))
    draw_path(ax, p, folder, every=150 if nm == 'MX' else 70)
    ax.set_title(f'{nm} - vue de dessus (terrain exporté), {p.s:.0f} ft / {p.s*0.3048:.0f} m, sens de circulation = flèches, portes = magenta')
    plt.savefig(f'{OUT}/01_topview_{nm}.png', dpi=80, bbox_inches='tight'); plt.close()

# 3. SX profiles: exported lane centreline vs measured reference profile
for nm, fn in (('SX1', layouts.sx1), ('SX2', layouts.sx2)):
    p = fn(); lanes = [g for g in p.segs if g['kind'] == 'S' and g['sections']]
    fig, axs = plt.subplots(len(lanes), 1, figsize=(18, 2.3 * len(lanes)))
    for ax, g in zip(axs, lanes):
        u = np.arange(0, g['L'], 0.1); x = g['x0'] + u * np.cos(g['t']); z = g['z0'] + u * np.sin(g['t'])
        ax.plot(u, T.h(x, z), 'k-', lw=1.2, label='terrain exporté (axe de la ligne)')
        for sec in g['sections']:
            pr = section_profile(sec[0], sec[2] if len(sec) > 2 else None)
            ax.plot(sec[1] + np.arange(len(pr)) * 0.1, pr, 'r--', lw=0.8, label=f"mesure réf. {sec[0]} ({LIB['sx_sections'][sec[0]]['ref'][8:]})")
        ax.set_aspect('equal'); ax.set_xlim(0, g['L']); ax.set_ylim(-0.5, 12); ax.grid(alpha=0.3); ax.legend(fontsize=6.5, loc='upper right')
        ax.set_title(f"{nm} - {g['tag']} (longueur {g['L']:.0f} ft, échelle 1:1)", fontsize=9)
    plt.tight_layout(); plt.savefig(f'{OUT}/02_profiles_{nm}.png', dpi=75); plt.close()

# 4. SX berm cross-section: exported vs reference stamp
B = json.load(open(ROOT + '/lib/berm_stamps.json'))
from engine import turn_mid_angle
fig, axs = plt.subplots(1, 2, figsize=(16, 3.5))
p = layouts.sx1(); done = set()
for g in p.segs:
    if g['kind'] == 'T' and g.get('berm') and g['berm'] not in done and len(done) < 2:
        done.add(g['berm']); ax = axs[len(done) - 1]; a = turn_mid_angle(g); r = np.arange(0, 60, 0.1)
        ax.plot(r, T.h(g['cx'] + r * np.cos(a), g['cz'] + r * np.sin(a)), 'k', label='exporté (bissectrice du virage)')
        ref = Track(REF + '/JGSX2026TestTracks/' + B[g['berm']]['ref'], 'xz'); bb = B[g['berm']]
        ax.plot(r, ref.h(bb['cx'] + r * np.cos(bb['mid_angle']), bb['cz'] + r * np.sin(bb['mid_angle'])) - np.median(ref.H), 'r--', label=f"réf. {bb['ref'][8:]} ({bb['cx']:.0f},{bb['cz']:.0f})")
        ax.axvline(g['r'], color='b', lw=0.6); ax.text(g['r'], 0.3, ' ligne de pilotage', color='b', fontsize=7)
        ax.set_aspect('equal'); ax.grid(alpha=.3); ax.legend(fontsize=7); ax.set_title(f"Berm {g['berm']} - profil radial depuis le centre du virage ({g['tag']})")
plt.tight_layout(); plt.savefig(f'{OUT}/03_berm_sections_SX.png', dpi=80); plt.close()

# 5. MX: full centreline profile + zooms on the measured sections (exported vs reference)
D = np.load(ROOT + '/legacy_mx/build/mx_line.npz'); R = json.load(open(ROOT + '/legacy_mx/build/build_report.json'))
x, z, ss = D['x'], D['z'], D['s']; hc = T.h(x, z)
fig, ax = plt.subplots(figsize=(22, 4)); ax.plot(ss, hc, 'k', lw=0.8)
for sec in R['mx']['sections']:
    ax.axvspan(sec['s0'], sec['s1'], color='orange', alpha=0.25); ax.text(sec['s0'], hc.max() + 1, sec['sid'], rotation=90, fontsize=6, va='bottom')
sand = D['sand']; ax.fill_between(ss, hc.min() - 2, hc.min() - 1, where=sand, color='gold', label='section sable')
ax.set_xlabel('distance le long du tour (ft)'); ax.set_ylabel('altitude (ft)'); ax.legend(); ax.grid(alpha=0.3); ax.set_ylim(hc.min() - 3, hc.max() + 14)
ax.set_title('MX - profil longitudinal complet de la ligne de pilotage (terrain exporté)')
plt.tight_layout(); plt.savefig(f'{OUT}/04_profile_MX_full.png', dpi=75); plt.close()
LIBS = {**LIB['mx_desert_sections'], **LIB['mx_drdew_sections'], **LIB['mx_sections']}
secs = R['mx']['sections']; n = len(secs); cols = 3; rows = int(np.ceil(n / cols))
fig, axs = plt.subplots(rows, cols, figsize=(22, 2.6 * rows))
for ax, sec in zip(axs.flat, secs):
    m = (ss >= sec['s0'] - 20) & (ss <= sec['s1'] + 20)
    ax.plot(ss[m] - sec['s0'], hc[m] - np.interp(sec['s0'], ss, hc), 'k', lw=1.2, label='exporté')
    P = LIBS[sec['sid']]; pr = np.asarray(P['prof']); ax.plot(np.arange(len(pr)) * P['step'], pr, 'r--', lw=0.9, label='mesure réf.')
    ax.set_aspect('equal'); ax.grid(alpha=0.3); ax.set_title(f"{sec['sid']} ({sec['edge']}) - {P.get('source', P.get('ref'))}", fontsize=7.5); ax.legend(fontsize=6)
for ax in list(axs.flat)[n:]: ax.axis('off')
plt.tight_layout(); plt.savefig(f'{OUT}/05_profiles_MX_sections.png', dpi=70); plt.close()
# MX cross-sections at a berm and at a jump
fig, axs = plt.subplots(1, 3, figsize=(20, 3.2))
mx = layouts.mx(); tseg = [g for g in mx.segs if g['kind'] == 'T' and g['r'] <= 35][3]
from engine import turn_mid_angle as tma
a = tma(tseg); r = np.arange(-10, 70, 0.25)
axs[0].plot(r, T.h(tseg['cx'] + r * np.cos(a), tseg['cz'] + r * np.sin(a)), 'k'); axs[0].axvline(tseg['r'], color='b', lw=0.6)
axs[0].set_title(f"MX virage {tseg['tag']} (R={tseg['r']:.0f} ft): coupe radiale", fontsize=8); axs[0].set_aspect('equal'); axs[0].grid(alpha=.3)
for ax, sid in zip(axs[1:], ('dd_g125', 'ds_s9173_table')):
    sec = [q for q in secs if q['sid'] == sid][0]; k = np.argmin(np.abs(ss - (sec['s0'] + (sec['s1'] - sec['s0']) * 0.45)))
    th = np.arctan2(np.gradient(z)[k], np.gradient(x)[k]); t = np.arange(-50, 50.1, 0.25)
    ax.plot(t, T.h(x[k] - np.sin(th) * t, z[k] + np.cos(th) * t), 'k'); ax.set_aspect('equal'); ax.grid(alpha=.3)
    ax.set_title(f'MX coupe transversale sur {sid} (pente latérale limitée à 25°)', fontsize=8)
plt.tight_layout(); plt.savefig(f'{OUT}/06_cross_sections_MX.png', dpi=80); plt.close()
print('figures in', OUT, sorted(os.listdir(OUT)))
