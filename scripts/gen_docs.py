"""Generate the measured-data tables (docs/data/*.csv + docs/09_donnees_mesurees.md) and the reference atlas
(docs/img/atlas_*.jpg) from lib/*.json. Re-run after any change of the measurements:  python3 scripts/gen_docs.py
Atlas images need the extracted references (refs/extracted); tables only need lib/."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, json, csv, numpy as np
from collections import Counter, defaultdict
sys.path.insert(0, ROOT + '/scripts')

D = f'{ROOT}/docs/data'; IMG = f'{ROOT}/docs/img'
_os.makedirs(D, exist_ok=True); _os.makedirs(IMG, exist_ok=True)
L = json.load(open(f'{ROOT}/lib/library.json'))
UN = json.load(open(f'{ROOT}/lib/sx_units.json'))
W = json.load(open(f'{ROOT}/lib/sx_whoops.json'))
B = json.load(open(f'{ROOT}/lib/berm_stamps.json'))
S = json.load(open(f'{ROOT}/lib/sand_stamps.json'))
C = json.load(open(f'{ROOT}/lib/sx_components.json'))
r1 = lambda v, n=1: '' if v is None else round(float(v), n)
md = ['# 09 — Données mesurées (généré automatiquement)', '',
      '> Fichier produit par `scripts/gen_docs.py` à partir de `lib/*.json`. Ne pas éditer à la main.',
      '> Unités : pieds (ft) = unités monde MX Simulator. 1 ft = 0,3048 m.', '']

def write_csv(name, header, rows):
    with open(f'{D}/{name}', 'w', newline='') as f:
        w = csv.writer(f, delimiter=';', lineterminator='\n'); w.writerow(header); w.writerows(rows)

def md_table(header, rows):
    out = ['| ' + ' | '.join(header) + ' |', '|' + '---|' * len(header)]
    out += ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in rows]
    return out

# ------------------------------------------------------------------ SX units (rhythm library)
KIND = {'S': 'single (3-4.3 ft)', 'B': 'gros single / table courte (4.3-6.6 ft, < 62 ft)', 'T': 'table longue (4.3-6.6 ft, >= 62 ft)',
        'X': 'gros saut (>= 6.6 ft)', 'low': 'petite bosse (< 2.5 ft)', 'combo': 'bloc multi-crêtes (on-off, step, table+...)', 'whoops': 'whoops'}
U = UN['units']
rows = []
for uid, u in sorted(U.items(), key=lambda kv: (kv[1]['kind'], kv[1]['H'])):
    cr = [round(c, 2) for c in u['crests']]
    rows.append([uid, u['ref'], u['grad'], u['kind'], r1(u['L']), r1(u['H'], 2), u['npk'], ' / '.join(map(str, cr)), r1(u['start']), u['axis'], u['lane_dir']])
write_csv('sx_units.csv', ['uid', 'ref', 'ligne_edinfo', 'type', 'longueur_ft', 'hauteur_ft', 'nb_cretes', 'cretes_ft', 'debut_sur_ligne_ft', 'axe', 'sens'], rows)
aliases = defaultdict(list)
for a, k in UN['alias'].items():
    if a != k: aliases[k].append(a)
md += ['## 1. Unités SX (bibliothèque des rythmiques)', '',
       f'{len(U)} unités uniques (après dédoublonnage de {len(UN["alias"])} unités trouvées sur {len(UN["seqs"])} lignes JGSX).',
       'Une **unité** = un obstacle séparé par du sol plat avant et après (single, double, table, on-off...).',
       'Profil exact échantillonné à 0,1 ft dans `lib/sx_units.json` (`units[uid].prof`). Fichier complet : `docs/data/sx_units.csv`.', '',
       'Types :', ''] + [f'- `{k}` : {v} — {n} unités' for k, v in KIND.items() for n in [Counter(u['kind'] for u in U.values())[k]] if n] + ['']
md += md_table(['uid', 'type', 'L ft', 'H ft', 'crêtes', 'aussi présente sur'],
               [[r[0], r[3], r[4], r[5], r[7], ', '.join(aliases.get(r[0], [])) or '—'] for r in rows]) + ['']

# floor gaps
pairs = defaultdict(list)
for sq in UN['seqs']:
    us = sq['units']
    for k in range(len(us) - 1):
        a, b = us[k], us[k + 1]
        if a and b and k < len(sq['gaps']):
            pairs[(U[a]['kind'], U[b]['kind'])].append(sq['gaps'][k])
grow = [[f'{a} → {b}', len(v), r1(np.median(v), 2), r1(np.min(v), 2), r1(np.max(v), 2)] for (a, b), v in sorted(pairs.items(), key=lambda kv: -len(kv[1]))]
write_csv('sx_floor_gaps.csv', ['paire', 'n', 'mediane_ft', 'min_ft', 'max_ft'], grow)
md += ['### Sol plat entre deux unités consécutives (mesuré)', '',
       'Écart pied à pied entre deux unités qui se suivent sur une ligne de référence. Ce tableau compte **toutes** les lignes, y compris les doublons (les pistes test JGSX partagent beaucoup de couloirs) : les médianes diffèrent donc un peu des constantes `GAP` de `compose.py`, fixées en v2 sur les couloirs rythmiques sans doublons (S→S = 5,3 ft).', ''] + md_table(['paire', 'n', 'médiane ft', 'min', 'max'], grow) + ['']
srows = []
for sq in UN['seqs']:
    seq = [x or '·' for x in sq['units']]
    srows.append([sq['ref'].replace('JGSX2026', ''), f"g{sq['grad']}", ' → '.join(seq), ' / '.join(f'{g:.1f}' for g in sq['gaps'])])
write_csv('sx_lanes_sequences.csv', ['ref', 'ligne', 'unites', 'ecarts_ft'], srows)
md += ['### Séquences complètes des lignes de référence', '', '`·` = morceau non classé (bord, virage, bosse coupée). Écarts en ft dans le même ordre.', ''] + md_table(['ref', 'ligne', 'unités', 'écarts ft'], srows) + ['']

# ------------------------------------------------------------------ whoops
wr = []
for k, w in W.items():
    h = np.array(w['heights']); p = np.array(w['pitch'])
    wr.append([k, w['ref'], w['n'], r1(w['length']), ' / '.join(f'{x:.2f}' for x in h), r1(np.median(p), 2), r1(p.min(), 2), r1(p.max(), 2)])
write_csv('sx_whoops.csv', ['cle', 'ref', 'nb', 'longueur_ft', 'hauteurs_ft', 'pas_median_ft', 'pas_min', 'pas_max'], wr)
md += ['## 2. Whoops', '', 'Les 3 sections de whoops JGSX ont la même forme : 1re bosse d’entrée ~1,9 ft puis ~2,9 ft, pas de 20 ft, séparées par 1-2 ft de sol.',
       '`compose.whoops(key, n)` coupe les n premières (bosse d’entrée comprise) sur le sol après la n-ième crête.', ''] + md_table(['clé', 'ref', 'nb', 'L ft', 'hauteurs ft', 'pas médian', 'min', 'max'], wr) + ['']

# ------------------------------------------------------------------ berms
br = []
for k, b in B.items():
    br.append([k, b['ref'], r1(b['cx']), r1(b['cz']), r1(b['R_crest']), r1(b['H'], 2), r1(b['ride_r']), r1(np.degrees(b['mid_angle'])), f"{b['shape'][1]}×{b['shape'][0]}"])
write_csv('sx_berm_stamps.csv', ['cle', 'ref', 'centre_x', 'centre_z', 'R_crete_ft', 'H_ft', 'rayon_trajectoire_ft', 'angle_milieu_deg', 'taille_px'], br)
md += ['## 3. Berms SX (virages en croissant)', '',
       'Modèle moyen (`library.json`) :', '',
       f"- **gros berm** : R crête {L['sx_berm_big']['R_crest']:.1f} ft, ouverture {L['sx_berm_big']['span_deg']:.0f}°, H {L['sx_berm_big']['H']:.2f} ft, {L['sx_berm_big']['n']} exemplaires mesurés ; trajectoire à r ≈ 21,5 ft (virage 180°).",
       f"- **petit berm** : R crête {L['sx_berm_small']['R_crest']:.1f} ft, ouverture {L['sx_berm_small']['span_deg']:.0f}°, H {L['sx_berm_small']['H']:.2f} ft, {L['sx_berm_small']['n']} exemplaires ; trajectoire r ≈ 11 ft (virage 90°).",
       '', 'Le compound utilise les **stamps exacts** (copie 2D tel que construit, `lib/berm_*.npy`) :', ''] + md_table(['clé', 'ref', 'cx', 'cz', 'R crête', 'H', 'r trajectoire', 'angle milieu °', 'px'], br) + ['']
md += ['Membres mesurés : gros = ' + ', '.join(f'{m[0][8:]} ({m[1]},{m[2]})' for m in L['sx_berm_big']['members']) +
       ' ; petits = ' + ', '.join(f'{m[0][8:]} ({m[1]},{m[2]})' for m in L['sx_berm_small']['members']), '']

# ------------------------------------------------------------------ lateral model
lat = L['sx_lateral']; wall = np.array(lat['wall'])
d = lat['wall_d0'] + np.arange(len(wall)) * lat['wall_step']
i10 = d[np.argmin(np.abs(wall - 0.9))]; i90 = d[np.argmin(np.abs(wall - 0.1))]
md += ['## 4. Profil en travers des obstacles SX', '',
       f"h(u, v) = p(u) × wall(|v| − {lat['top_width']:.1f}/2) : dessus plat de **{lat['top_width']:.1f} ft**, flanc qui passe de 90 % à 10 % de la hauteur entre {i10:+.1f} et {i90:+.1f} ft du bord (≈ {i90 - i10:.1f} ft).",
       f"Médiane sur {lat['n_samples']} blocs isolés (RMSE ≈ 0,02 ft). Courbe `wall` dans `library.json → sx_lateral`.", '']

# ------------------------------------------------------------------ sand
md += ['## 5. Sable Glendale (stamps)', '']
sr = []
for k, s in S.items():
    ln = np.array(s['line']); seg = np.hypot(*np.diff(ln, axis=0).T).sum()
    sr.append([k, f"{s['shape'][1]}×{s['shape'][0]}", r1(s['shape'][1] * s['s']), r1(s['shape'][0] * s['s']), r1(s['hmax'], 2), r1(s['edge_cut'], 3), len(ln), r1(seg), ', '.join(f'{a}={b}' for a, b in s['tile_names'].items())])
write_csv('sand_stamps.csv', ['cle', 'px', 'largeur_ft', 'hauteur_ft', 'hmax_ft', 'coupe_bord_ft', 'pts_ligne', 'longueur_ligne_ft', 'tiles'], sr)
md += md_table(['clé', 'px', 'largeur ft', 'profondeur ft', 'H max', 'coupe au bord', 'pts ligne', 'longueur ligne ft', 'tiles Glendale'], sr) + [
    '', '- `GL` : le J de sable à gauche de Glendale (≈ 230°), sortie décalée de 187 ft.',
    '- `GR` : le virage de sable en S (≈ 165°), sortie décalée de 114 ft (posé en miroir dans SX3).', '']

# ------------------------------------------------------------------ components (all isolated SX blocks)
cr = []
for c in C:
    up = c.get('up') or {}; dn = c.get('down') or {}
    cr.append([c['id'], c['ref'], r1(c['cx']), r1(c['cz']), r1(c['hmax'], 2), r1(c.get('length_lane')), r1(c.get('width_lane')), c.get('npeaks', ''),
               r1(up.get('L')), r1(up.get('amax')), r1(up.get('lip')), r1(dn.get('L')), r1(dn.get('amax')), r1(c.get('top_len')), c.get('cls', '')])
write_csv('sx_blocks.csv', ['id', 'ref', 'cx', 'cz', 'hmax_ft', 'longueur_ft', 'largeur_ft', 'nb_cretes', 'montee_L_ft', 'montee_angle_max', 'lip_deg',
                            'descente_L_ft', 'descente_angle_max', 'plateau_ft', 'classe'], cr)
md += ['## 6. Blocs SX isolés (tous les obstacles détachés des 5 pistes JGSX)', '',
       f'{len(C)} blocs ; stamps 2D dans `lib/sx/<id>.npy` (régénérés par `sx_components.py`). Tableau complet : `docs/data/sx_blocks.csv`.', '']
cnt = Counter(c['ref'] for c in C)
md += md_table(['ref', 'blocs'], [[k, v] for k, v in cnt.items()]) + ['']

# ------------------------------------------------------------------ SX sections (v1 whole lanes)
xr = [[k, v['ref'].replace('JGSX2026', ''), f"g{v['grad']}", r1(v['length']), v.get('elements', ''), v['axis']] for k, v in L['sx_sections'].items()]
write_csv('sx_sections.csv', ['cle', 'ref', 'ligne', 'longueur_ft', 'elements', 'axe'], xr)
md += ['## 7. Sections SX complètes (v1, lignes entières)', ''] + md_table(['clé', 'ref', 'ligne', 'L ft', 'éléments', 'axe'], xr) + ['']

# ------------------------------------------------------------------ MX
mu = L['mx_units']
mr = []
for u in mu:
    up = u.get('up') or {}; dn = u.get('down') or {}
    mr.append([u['ref'], u['cp'], r1(u['x']), r1(u['z']), u['kind'], r1(up.get('L')), r1(up.get('H'), 2), r1(up.get('amax')), r1(up.get('lip')),
               r1(dn.get('L')), r1(dn.get('H'), 2), r1(dn.get('amax')), r1(u['top']) if u.get('top') is not None else ''])
write_csv('mx_units.csv', ['ref', 'checkpoint', 'x', 'z', 'type', 'face_L_ft', 'face_H_ft', 'face_angle_max', 'lip_deg', 'dos_L_ft', 'dos_H_ft', 'dos_angle_max', 'plateau_ft'], mr)
md += ['## 8. MX (Desert Sand, Dr. Dew) — v1 abandonnée, gardé pour référence', '',
       f'{len(mu)} faces/unités mesurées le long des lignes de checkpoint (`docs/data/mx_units.csv`).', '']
md += md_table(['ref / type', 'n'], [[f'{a} / {b}', n] for (a, b), n in sorted(Counter((u['ref'], u['kind']) for u in mu).items())]) + ['']
for key in ('mx_sections', 'mx_desert_sections', 'mx_drdew_sections'):
    rr = [[k, v.get('ref', ''), v.get('cp', v.get('g', '')), r1(v.get('length')), r1(v.get('hmax'), 2), r1(v.get('net'), 2), r1(v.get('flat_width_median'))] for k, v in L[key].items()]
    write_csv(f'{key}.csv', ['cle', 'ref', 'cp', 'longueur_ft', 'hmax_ft', 'denivele_net_ft', 'largeur_plate_ft'], rr)
    md += [f'### {key}', ''] + md_table(['clé', 'ref', 'cp', 'L ft', 'H max', 'dénivelé net', 'largeur plate'], rr) + ['']
md += [f"Berm MX : {L['mx_berm']['src']} — {L['mx_berm']['note']}.", '']
open(f'{ROOT}/docs/09_donnees_mesurees.md', 'w').write('\n'.join(md) + '\n')
print('tables written')

# ------------------------------------------------------------------ atlas (needs refs)
if 'tables' in sys.argv[1:] or not _os.path.isdir(REF):
    sys.exit(0)
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from mxs import Track, parse_gates
REFS = {'JGSX2026Detroit': 'JGSX2026TestTracks/JGSX2026Detroit', 'JGSX2026Arlington': 'JGSX2026TestTracks/JGSX2026Arlington',
        'JGSX2026Glendale': 'JGSX2026TestTracks/JGSX2026Glendale', 'JGSX2026Custom': 'JGSX2026TestTracks/JGSX2026Custom',
        'JGSX2026Custom1': 'JGSX2026TestTracks/JGSX2026Custom1', 'JGMXDesertSand': 'JGMXDesertSand/JGMXDesertSand', 'JGMXDrDew': 'JGMXDrDew/JGMXDrDew'}
def hill(H, s):
    gz, gx = np.gradient(H, s); n = np.dstack([-gx, -gz, np.ones_like(H)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
    return np.clip(n @ np.array([-0.5, -0.6, 0.62]) / 1.0, 0, 1)
for name, rel in REFS.items():
    T = Track(f'{REF}/{rel}', 'xz'); step = max(1, T.N // 2049); H = T.H[::step, ::step]; s = T.s * step
    H0 = H - np.median(H); ext = [0, T.size, T.size, 0]
    sx = name.startswith('JGSX')
    fig, ax = plt.subplots(figsize=(16, 16))
    ax.imshow(hill(H, s), cmap='gray', extent=ext, alpha=1.0)
    ax.imshow(np.ma.masked_less(H0, 0.3), cmap='turbo', extent=ext, alpha=0.45, vmin=0, vmax=12 if sx else np.percentile(H0, 99))
    for gi, g in enumerate(T.gradients):
        (ax_, az_), (bx_, bz_) = g['a'], g['b']
        ax.plot([ax_, bx_], [az_, bz_], color='w', lw=0.6, alpha=0.6, clip_on=True); ax.text((ax_ + bx_) / 2, (az_ + bz_) / 2, f'g{gi}', color='yellow', fontsize=8, clip_on=True)
    if sx:
        for c in C:
            if c['ref'] == name: ax.text(c['cx'], c['cz'], c['id'].split('_')[1], color='cyan', fontsize=7, ha='center', clip_on=True)
    G = parse_gates(f'{REF}/{rel}/timing_gates')
    for k, i in enumerate(G['normal']):
        cp = G['cps'][i]; ax.plot(cp[1], cp[3], 'o', color='lime', ms=3); ax.text(cp[1] + 3, cp[3] + 3, f'cp{i}', color='lime', fontsize=7, clip_on=True)
    st = np.array([g[:3] for g in G['start']])
    if len(st): ax.plot(st[:, 0], st[:, 2], 's', color='red', ms=3)
    ax.set_xlim(0, T.size); ax.set_ylim(T.size, 0)
    ax.set_title(f'{name} — relief ombré, hauteur (couleur), lignes edinfo g#, blocs (cyan), checkpoints cp#, grilles (rouge). x→, z↓ en ft', fontsize=10)
    ax.grid(alpha=0.25)
    fig.subplots_adjust(left=0.04, right=0.99, bottom=0.03, top=0.97)
    plt.savefig(f'{IMG}/atlas_{name}.jpg', dpi=90, pil_kwargs=dict(quality=82)); plt.close()
    print('atlas', name)
