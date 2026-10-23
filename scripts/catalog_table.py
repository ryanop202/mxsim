"""Obstacle catalogue (CSV + JSON) from the library - every value traced to a reference file."""
import os as _os
ROOT = _os.environ.get('MXSIM_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # repo root
REF = _os.environ.get('MXSIM_REF') or _os.path.join(ROOT, 'refs', 'extracted')  # extracted JGMX/JGSX reference archives
import sys, json, csv, numpy as np
sys.path.insert(0, ROOT + '/scripts')
from profiles import analyze, face_metrics
from mx_faces import faces
L = json.load(open(ROOT + '/lib/library.json'))
B = json.load(open(ROOT + '/lib/berm_stamps.json'))
rows = []
TW = L['sx_lateral']['top_width']; w = np.array(L['sx_lateral']['wall']); wd = L['sx_lateral']['wall_d0'] + np.arange(len(w)) * 0.1
foot_extra = float(wd[np.argmax(w < 0.02)])
def kind_sx(e, sid):
    if 'whoops' in sid and e['H'] < 3.2: return 'whoop'
    if e['H'] >= 8.5: return 'gros saut (step-up / triple landing)'
    if e['H'] >= 7.0: return 'saut triple / gros double'
    if e['top'] and e['top'] > 10: return 'table'
    if e['H'] >= 5.0: return 'table / double'
    if e['H'] >= 2.5: return 'single (rythmique)'
    return 'transition / entrée'
for sid, S in L['sx_sections'].items():
    E = S['elements']
    for k, e in enumerate(E):
        gap = (E[k + 1]['crest'] - e['crest']) if k + 1 < len(E) else None
        rows.append(dict(ref=f"{S['ref']} terrain.png - ligne JGMX g{S['grad']} ({S['axis']})", section=sid, type=kind_sx(e, sid), discipline='SX',
                         largeur=f"{TW:.1f} ft plat + 2x{foot_extra:.1f} ft de flanc", longueur=f"{e['foot1']-e['foot0']:.1f} ft (pied à pied)", hauteur=f"{e['H']:.2f} ft",
                         angle=f"montée max {e['up_max'] or 0:.0f}°, descente max {e['dn_max'] or 0:.0f}°",
                         profil=f"face {e['up_L'] or 0:.1f} ft / dos {e['dn_L'] or 0:.1f} ft, plateau {e['top']:.1f} ft",
                         reception=(f"crête suivante à {gap:.1f} ft" if gap else '-'), confiance='mesure directe (heightmap 0.29 ft)'))
for fam in ('sx_berm_big', 'sx_berm_small'):
    F = L[fam]; p = np.array(F['prof']); r = F['r_rel0'] + np.arange(len(p)) * F['step']
    ci = int(np.argmax(p)); g = np.degrees(np.arctan(np.gradient(p, 0.1)))
    rows.append(dict(ref='; '.join(f'{m[0]} ({m[1]},{m[2]})' for m in F['members']), section=fam, type='berm croissant ' + ('180°' if 'big' in fam else '90°'), discipline='SX',
                     largeur=f"rayon de crête {F['R_crest']:.1f} ft, arc {F['span_deg']:.0f}°", longueur='-', hauteur=f"{F['H']:.2f} ft (médiane {F['n']} berms)",
                     angle=f"paroi intérieure max {g[:ci].max():.0f}°, extérieure max {-g[ci:].min():.0f}°",
                     profil=f"face intérieure {r[ci]-r[np.argmax(p > 0.05)]:.1f} ft", reception=f"ligne de pilotage à r ≈ {F['R_crest'] - (r[ci]-r[np.argmax(p > 0.05)]) - 1.5:.1f} ft", confiance='mesure directe'))
rows.append(dict(ref=f"{L['sx_lateral']['n_samples']} blocs SX isolés (5 pistes JGSX)", section='sx_lateral', type='flanc latéral des obstacles SX', discipline='SX',
                 largeur=f"plateau {TW:.1f} ft", longueur='-', hauteur='indépendant de la hauteur', angle='variable (course constante)',
                 profil=f"10-90 % de la hauteur sur ≈4 ft quel que soit l'obstacle (1.9 à 11.2 ft)", reception='-', confiance='mesure directe + modèle validé (RMSE 0.02 ft)'))
MX = {**L['mx_desert_sections'], **L['mx_drdew_sections'], **L['mx_sections']}
used = {'ds_s2796_roller', 'ds_s5459_jump', 'dd_g43', 'ds_s8552_jump', 'ds_s9173_table', 'ds_s7981_step', 'ds_s4671_step', 'dd_g8', 'ds_s6256_step',
        'dd_g125', 'ds_s6470_jump', 'ds_s7006_step', 'dd_g132', 'ds_s10356_step', 'ds_s8736_step', 'ds_s2649_step', 'ds_s9681_step', 'ds_s3795_step', 'dd_g18', 'ds_double31'}
for sid in sorted(used):
    P = MX[sid]; pr = np.array(P['prof']); F, _ = faces(pr if P['step'] == 0.25 else np.interp(np.arange(0, (len(pr) - 1) * P['step'], 0.25), np.arange(len(pr)) * P['step'], pr))
    up = [f for f in F if f['sign'] > 0]; dn = [f for f in F if f['sign'] < 0]
    mu = max(up, key=lambda f: f['H']) if up else None; md = max(dn, key=lambda f: f['H']) if dn else None
    src = P.get('source', P.get('ref'))
    typ = 'saut / kicker' if mu and mu['lip'] >= 25 else ('table' if 'table' in sid else ('step-down' if P['net'] < -8 else ('montée / step-up' if P['net'] > 8 else 'rouleau / bosse')))
    rows.append(dict(ref=f"{'JGMXDesertSand' if sid.startswith('ds') else 'JGMXDrDew'} terrain.png - {src}", section=sid, type=typ, discipline='MX',
                     largeur='piste 34 ft (estimation dans la plage mesurée 32-36 ft)', longueur=f"{P['length']:.0f} ft (section)", hauteur=f"max {P['hmax']:+.1f} ft / net {P['net']:+.1f} ft",
                     angle=(f"face max {mu['amax']:.0f}°, lèvre {mu['lip']:.0f}°" if mu else '-'),
                     profil=(f"face {mu['L']:.1f} ft / {mu['H']:.1f} ft, angles 25/50/75 % = {mu['a25']:.0f}/{mu['a50']:.0f}/{mu['a75']:.0f}°" if mu else '-'),
                     reception=(f"descente {md['L']:.1f} ft / {md['H']:.1f} ft, max {md['amax']:.0f}°" if md else '-'), confiance='mesure directe le long de l\'axe (profil exact) ; largeur estimée'))
bp = np.array(L['mx_berm']['prof'])
rows.append(dict(ref=L['mx_berm']['src'], section='mx_berm', type='berm MX (sable)', discipline='MX', largeur='crête à ≈19 ft de l\'axe', longueur='-', hauteur=f"{bp.max():.2f} ft",
                 angle='paroi max 47°', profil='plat jusqu\'à ≈14 ft puis paroi', reception='-', confiance='mesure directe sur 1 virage (axe reconstitué depuis les décals : ±2 ft)'))
with open(ROOT + '/legacy_mx/deliver/catalogue_obstacles.csv', 'w', newline='', encoding='utf-8') as f:
    wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter=';'); wr.writeheader(); wr.writerows(rows)
json.dump(rows, open(ROOT + '/legacy_mx/build/catalogue.json', 'w'), ensure_ascii=False, indent=0)
print(len(rows), 'rows')
