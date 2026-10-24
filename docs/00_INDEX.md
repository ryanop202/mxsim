# Documentation mxsimtrack

| # | Fichier | Pour quoi |
|---|---|---|
| 00 | `00_cahier_des_charges_original.txt` | le cahier des charges de départ de Ryan (texte intégral) |
| 01 | `01_formats_mxs.md` | formats des fichiers MX Simulator (heightmap, tilemap, timing_gates, shading, edinfo…), unités, axes |
| 02 | `02_references.md` | inventaire des 7 pistes de référence (3 archives) |
| 03 | `03_mesures_sx.md` | **mesures SX** : méthode, bloc SX, unités, enchaînements, whoops, berms, sable Glendale, départs |
| 04 | `04_mesures_mx.md` | mesures MX (Desert Sand, Dr. Dew) et pourquoi la v1 MX a été abandonnée |
| 05 | `05_compound_sx.md` | **les 3 pistes v3** couloir par couloir, départs, tiles, historique v1→v3, contrôles |
| 06 | `06_pipeline.md` | le code : chaîne complète, conventions, recettes (changer un couloir, ajouter une piste / un stamp) |
| 07 | `07_journal_conversation.md` | journal de la conversation : demandes, réponses, retours, décisions |
| 08 | `08_installation_et_test.md` | installer dans le jeu + checklist du 1er test |
| 09 | `09_donnees_mesurees.md` | **toutes les données** (généré) : chaque unité, whoop, berm, bloc, section MX |
| 10 | `10_suite_et_idees.md` | limites connues, idées, prochaines étapes |
| 11 | `11_habillage.md` | grilles de départ, grillages, paddock, paysage, decals, drapeaux (v9) |
| 12 | `12_objets_usland.md` | **objets faits maison (v12)** : specs pour le jeu, remplacement de l'habillage JGSX, **règles de design** |

Dossiers :
- `data/` — tableaux CSV (séparateur `;`) : `sx_units`, `sx_blocks`, `sx_whoops`, `sx_berm_stamps`, `sx_floor_gaps`,
  `sx_lanes_sequences`, `sx_sections`, `sand_stamps`, `mx_units`, `mx_*sections`, `catalogue_obstacles_v1`.
- `img/` — atlas des 7 références (`atlas_<dossier>.jpg` : relief, hauteurs, lignes `g#`, blocs, checkpoints, grille) et la photo
  de sable envoyée par Ryan.

Autres images : `../viewer/figures/` (pistes du compound), `../analysis/` (analyses : départs, sable, berms, couloirs, MX).
