# 06 — Le pipeline : comment le code marche et comment modifier les pistes

## Chaîne complète

```
refs/extracted/ (7 pistes de référence)
   │  ./make_all.sh analysis
   ▼
lib/  ← la « base » mesurée (JSON + stamps .npy)          analysis/ ← figures et intermédiaires
   │  ./make_all.sh build
   ▼
build_sx.py  → build/H.npy, tiles.npy, build_report.json   (terrain + tilemap en mémoire)
export_sx.py → tracks/USLAND2026SX1..3                    (fichiers MX Simulator)
validate_sx.py → build/validation.json                      (39 contrôles, relit les fichiers exportés)
laptime.py → build/laptime.json                             (estimation de chrono)
preview_sx.py sx1|sx2|sx3 → analysis/pv2_*.png              (chaque piste seule + contrôles géométriques)
figures_sx.py → viewer/figures/*.jpg, viewer/terrain_data.js
gen_docs.py → docs/09_donnees_mesurees.md, docs/data/*.csv, docs/img/atlas_*.jpg
```

Reproductibilité vérifiée : une copie vierge du repo + les archives → `./make_all.sh` redonne `lib/` et `tracks/` **identiques à l'octet**
(seuls changent des chemins absolus dans des champs texte et des `inf`).

Variables : `MXSIM_REF` (dossier des références extraites, défaut `refs/extracted`), `MXSIM_ROOT` (racine du repo, auto),
`FROM=<script.py>` (reprendre la chaîne à une étape), `PYTHON` (interpréteur).

## Les scripts

### Lecture / mesure
| Script | Fait | Sorties |
|---|---|---|
| `mxs.py` | lecture des pistes (`Track`, `parse_gates`, `parse_tileinfo`, `parse_edinfo`, `Track.h(x,z)`, `Track.line`) | — |
| `profiles.py` | analyse 1D des profils (pentes, faces, plateaux) | — |
| `validate_format.py` | teste les conventions d'axes sur les 7 références | console |
| `shading.py` | lightmap Lambert + calibration sur une référence | — |
| `catalog.py` | profils le long de toutes les lignes edinfo | `analysis/catalog_raw.json` |
| `sx_components.py` | découpe chaque obstacle SX isolé en stamp 2D | `lib/sx/*.npy`, `lib/sx_components.json` |
| `sx_classify.py`, `sx_classify_lib.py` | mesures des blocs (faces, lips, plateau) + galerie | `analysis/sx_gallery.png` |
| `sx_lateral.py` | profil en travers (dessus 30,4 ft, flanc 4 ft) | console (→ `build_library`) |
| `sx_lanes.py <ref>` | axes de couloir | `analysis/lanes_*.json/png` |
| `sx_berms.py`, `berm_stamps.py` | familles de berms + 6 stamps exacts | `lib/sx_berms.json`, `lib/berm_*.npy`, `lib/berm_stamps.json` |
| `build_library.py` | assemble `lib/library.json` | |
| `sx_units.py` | toutes les unités + écarts de sol, dédoublonnage | `lib/sx_units.json` |
| `sx_whoops.py` | sections de whoops | `lib/sx_whoops.json` |
| `sand_stamps.py` | sable Glendale GL/GR (hauteurs, tiles, ligne) | `lib/sand_*.npy`, `lib/sand_stamps.json` |
| `starts_ref.py`, `gle_sand_view.py` | analyse des départs / du sable | `analysis/starts_ref*.png`, `gle_*.png` |
| `mx_*.py`, `centerline.py`, `desert_sections.py`, `drdew_sections.py` | MX (v1) | `analysis/…`, `library.json → mx_*` |

### Construction
| Script | Rôle |
|---|---|
| `engine.py` | `Path` (chemin : `straight`, `turn`, `stamp`), `Grid`, rendu des couloirs (`render_lane_block`), berms (`render_berm_stamp`), stamps (`render_stamp`) |
| `compose.py` | `lane(tokens)` : enchaîne des unités mesurées avec les bons écarts de sol |
| `layouts_sx.py` | **les 3 pistes** (le fichier à modifier) + `STARTS` |
| `build_sx.py` | rend les 3 chemins sur un terrain commun + tilemap |
| `export_sx.py` | écrit les dossiers (terrain, tileinfo, lighting, timing_gates, shading, ressources) |
| `validate_sx.py` | 39 contrôles |
| `laptime.py` | estimation de chrono (point-masse : v max 20 m/s SX, accél. 7,5, frein 8, adhérence latérale 1,3 g ; sable ×0,85) |

## Conventions du moteur

- `Path(x, z, cap_deg)` : cap 0° = +x, 90° = +z (bas de l'image), −90° = −z (haut).
- `p.straight(L, sections, tag)` : ligne droite de L ft ; `sections` = liste de `(profil, u0, nom)` posés à u0 ft du début.
- `p.turn(angle, r, berm, tag)` : **angle > 0 = gauche**, < 0 = droite (sur l'image, z vers le bas). `r` = rayon de la ligne de course
  (21,5 ft gros berm 180°, 11 ft petit berm 90°). `berm` = clé de stamp (`big_det_a`, `big_cle`, `big_cus`, `small_cus_a`, `small_cus_b`,
  `small_arl`) ou `None` = virage plat.
- `p.stamp('GL'|'GR', tag, snap=True, mirror=False)` : pose un stamp avec sa ligne de course ; le chemin continue à la sortie du stamp.
  `snap` aligne le cap de sortie sur la grille (±4°). `mirror` = version gauche/droite.
- Le rendu prend le **max** de toutes les couches (sauts, whoops, berms, sable) → les obstacles ne se creusent jamais l'un l'autre.

### Tokens de `compose.lane`

```python
['Arlington_g37_0', 'Arlington_g37_1']          # unités mesurées (uid de lib/sx_units.json, alias acceptés)
('gap', 14.0)                                    # sol plat imposé, en ft (remplace l'écart mesuré suivant)
('whoops', 'Custom_0', 12)                       # n premières whoops d'une section (Detroit_0, Custom_0, Custom1_0)
('split', 'Detroit_g36_1', 'Custom1_g30_1')     # double ligne : unité à gauche / à droite (sens de course), chacune sur la moitié de la largeur
```
Entre deux unités sans `gap` : écart mesuré de la paire si elle existe dans une référence (`PAIR`), sinon médiane par types (`GAP`).

## Recettes

### Changer un couloir
Dans `layouts_sx.py`, remplacer la liste de tokens d'un `sec(...)`. Exemple : passer les whoops du SX1 de 12 à 10 :
```python
p.straight(xe - xw, [sec('SX1-B whoops (entry+9)', [('whoops', 'Custom_0', 10), BB[0]], 22.0)], tag='B 10 whoops + single')
```
Puis `./make_all.sh build`. Vérifier : la section tient dans la ligne droite (l'aperçu `analysis/pv2_sx1.png` et le contrôle
« profils exportés » le signalent), et la piste reste à ≥ 75 ft des autres.

Trouver une unité : `docs/09_donnees_mesurees.md` § 1 (type, longueur, hauteur) ou `docs/data/sx_units.csv` ; la localiser sur
la piste d'origine : `docs/img/atlas_<ref>.jpg` (ligne `g<N>` = le `g` dans l'uid).

### Ajouter une piste (SX4)
1. `layouts_sx.py` : `SX4_ORIGIN`, `def sx4()`, et `_start('SX4', …)` (grille, cap, longueur de ligne droite, point de jonction sur le tour).
   Il reste de la place en bas à droite du terrain (x > 600, z > 450) et en bas à gauche (z > 1050).
2. `build_sx.py` : ajouter `'SX4': LS.sx4()` dans `paths`.
3. `export_sx.py` : `F`, `PATHS`, `DESC` ; `validate_sx.py` : `paths` ; `figures_sx.py` : zone de crop.
4. `./make_all.sh build`.

### Ajouter un nouveau stamp (ex. un autre morceau de sable, un virage spécial)
Sur le modèle de `sand_stamps.py` : découper la zone (hauteurs + tiles), calculer la ligne de course (squelette du chenal ou
ligne tracée à la main), écrire `lib/sand_<KEY>.npy`, `lib/sand_<KEY>_tiles.npy` et une entrée dans `lib/sand_stamps.json`
(`x0, z0, s, shape, line, hmax, edge_cut, tile_names`). Ensuite `p.stamp('<KEY>')` dans un layout, et ajouter la correspondance
des tiles dans `build_sx.GLENDALE_TILES` si nouveaux tiles.

### Mesurer une nouvelle piste de référence
Ajouter son dossier dans `refs/extracted/…`, l'ajouter aux listes `refs` de `sx_components.py`, `sx_units.py`, `sx_whoops.py`,
`sx_berms.py`, `catalog.py`, `gen_docs.py` (chacun a sa liste en tête), puis `./make_all.sh`.
Si la grille est différente de 0,28975 ft, les stamps 2D devront être rééchantillonnés (le moteur interpole déjà, mais le contrôle
« profils exportés » suppose la même grille).

## Fichiers de `lib/` (la base)

| Fichier | Contenu |
|---|---|
| `library.json` | `sx_lateral` (profil en travers), `sx_sections` (couloirs entiers v1), `sx_berm_big/small` (modèles moyens), `mx_units`, `mx_sections`, `mx_desert_sections`, `mx_drdew_sections`, `mx_berm` |
| `sx_units.json` | `units` (90 unités : profil 0,1 ft, L, H, crêtes, type, axe), `seqs` (70 lignes de référence : unités + écarts), `alias` |
| `sx_whoops.json` | 3 sections de whoops (profil, hauteurs, pas) |
| `sx_components.json` + `sx/*.npy` | 132 blocs SX isolés (stamp 2D, centre, orientation, dimensions, faces) |
| `sx_berms.json` | les 29 croissants trouvés |
| `berm_stamps.json` + `berm_*.npy` | 6 berms exacts (centre, R crête, angle milieu, rayon de trajectoire) |
| `sand_stamps.json` + `sand_*.npy` | sable Glendale GL / GR (hauteurs, ligne de course, chenal, tiles) |

Les `.npy` se lisent avec `numpy.load` ; grille = `s` (0,28975 ft), origine `x0, z0` dans les coordonnées de la piste de référence.
