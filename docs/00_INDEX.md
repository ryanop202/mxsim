# Documentation

Commencer par le [README](../README.md) à la racine : arborescence, liste des pistes, faire une nouvelle piste.

## guide/ — comment ça marche (valable pour toutes les pistes)

| # | Fichier | Pour quoi |
|---|---|---|
| 01 | [guide/01_formats_mxs.md](guide/01_formats_mxs.md) | formats des fichiers MX Simulator (heightmap, tilemap, timing_gates, shading, edinfo…), unités, axes |
| 02 | [guide/02_references.md](guide/02_references.md) | inventaire des 7 pistes de référence (3 archives) |
| 03 | [guide/03_mesures_sx.md](guide/03_mesures_sx.md) | **mesures SX** : méthode, bloc SX, unités, enchaînements, whoops, berms, sable Glendale, départs |
| 04 | [guide/04_mesures_mx.md](guide/04_mesures_mx.md) | mesures MX (Desert Sand, Dr. Dew) et pourquoi la v1 MX a été abandonnée |
| 06 | [guide/06_pipeline.md](guide/06_pipeline.md) | le code : chaîne complète, conventions, recettes (changer un couloir, ajouter une piste / un stamp) |
| 08 | [guide/08_installation_et_test.md](guide/08_installation_et_test.md) | installer dans le jeu + checklist de test |
| 09 | [guide/09_donnees_mesurees.md](guide/09_donnees_mesurees.md) | **toutes les données** (généré) : chaque unité, whoop, berm, bloc, section MX |
| 12 | [guide/12_objets_usland.md](guide/12_objets_usland.md) | **objets faits maison** : specs pour le jeu, **règles de design** |

## pistes/ — notes et historique de chaque piste

| # | Fichier | Piste |
|---|---|---|
| 00 | [pistes/00_cahier_des_charges_original.txt](pistes/00_cahier_des_charges_original.txt) | SX 1-3 : le cahier des charges de départ de Ryan |
| 05 | [pistes/05_compound_sx.md](pistes/05_compound_sx.md) | SX 1-3 couloir par couloir, départs, tiles, historique, contrôles |
| 07 | [pistes/07_journal_conversation.md](pistes/07_journal_conversation.md) | SX 1-3 : journal des demandes, réponses, retours et décisions |
| 10 | [pistes/10_suite_et_idees.md](pistes/10_suite_et_idees.md) | SX 1-3 : limites connues, idées, prochaines étapes |
| 11 | [pistes/11_habillage.md](pistes/11_habillage.md) | SX 1-3 : grilles de départ, grillages, paddock, paysage, decals, drapeaux |
| 13 | [pistes/13_saint_georges.md](pistes/13_saint_georges.md) | Saint-Georges : cahier des charges et notes |
| 14 | [pistes/14_suite_paris_autre_pc.md](pistes/14_suite_paris_autre_pc.md) | Paris 2026 : reprendre sur un autre PC |

Chaque piste a aussi sa fiche dans `pistes/<nom>/README.md` à la racine du dépôt.

## Dossiers

- `data/` : tableaux CSV (séparateur `;`) : `sx_units`, `sx_blocks`, `sx_whoops`, `sx_berm_stamps`, `sx_floor_gaps`,
  `sx_lanes_sequences`, `sx_sections`, `sand_stamps`, `mx_units`, `mx_*sections`, `catalogue_obstacles_v1`.
- `img/` : atlas des 7 références (`atlas_<dossier>.jpg` : relief, hauteurs, lignes `g#`, blocs, checkpoints, grille) et la photo
  de sable envoyée par Ryan.

Autres images : `../commun/viewer/figures/` (pistes), `../commun/analysis/` (analyses : départs, sable, berms, couloirs, MX).
