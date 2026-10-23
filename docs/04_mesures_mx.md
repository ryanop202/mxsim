# 04 — Mesures MX (Desert Sand, Dr. Dew) et la v1 MX abandonnée

> Ryan, après la v1 : « alors le MX ça va pas du tout, on laisse tomber, on fait que SX pour le moment ».
> Tout ce qui concerne le MX est donc **en pause**. Les mesures sont gardées (elles serviront si on y revient), le code v1 aussi.

## Ce qui a été mesuré

### Lignes de course (centrelines)
- `centerline.py` : chemin de moindre coût entre checkpoints consécutifs, sur la couverture des decals « sur piste »
  (Desert Sand : `decal/sand.png` ; Dr. Dew aurait `decal/ontrack.png`). Résultat : `analysis/centerline_Desert.json/png`.
- `mx_centerline_profile.py` : profil de hauteur + courbure le long de cette ligne → `analysis/cl_Desert.npz`, `clprof_Desert.png`.
- `mx_features.py` : sauts/rollers détectés sur la centreline, faces, lips, réceptions, coupes en travers, virages → `analysis/mxfeat_Desert.json`.

### Profils par checkpoint
- `mx_cp_lanes.py` : profil le long de la direction du couloir (normale du checkpoint) à travers **chaque** checkpoint,
  ±110 ft → `analysis/cplanes_{DrDew,Desert}.json/png`.
- `mx_faces.py` : segmentation en faces / plateaux / unités → `analysis/mx_units.json` puis `library.json → mx_units` :
  **247 unités** (Desert 151, Dr. Dew 96).

| Type | n | Hauteur (p10 / médiane / p90) ft | Longueur de face | Angle max face | Lip | Angle max dos | Plateau |
|---|---|---|---|---|---|---|---|
| jump | 33 | 2,1 / 3,8 / 7,4 | 18 ft | 20° | 17° | 26° | — |
| table | 23 | 1,6 / 3,9 / 5,9 | 14 ft | 23° | 19° | 25° | 26,5 ft |
| step-up | 136 | 3,6 / 7,3 / 22,3 | 28 ft | 25° | 17° | 19° | 3,8 ft |
| step-down (depuis un saut) | 17 | 1,7 / 3,0 / 5,5 | 11 ft | 23° | 21° | 26° | 15,5 ft |
| roller | 8 | 1,6 / 2,4 / 4,4 | 15 ft | 14° | 13° | 15° | 20 ft |
| bump | 30 | 1,7 / 2,2 / 2,8 | 11 ft | 17° | 14° | — | — |

Beaucoup de « step-up » = montées le long du relief naturel (les pistes MX suivent les collines), pas des sauts construits.

### Sections exactes (profils réels)
- `mx_sections.py` → `mx_sections` (Dr. Dew : tables cp27/30/12/35, sauts cp24/16, step-down cp48, rythmique cp17).
- `desert_sections.py` → `mx_desert_sections` (le long de la centreline Desert : `ds_s<abscisse>_<type>`).
- `drdew_sections.py` → `mx_drdew_sections` (le long des lignes edinfo de Dr. Dew : `dd_g8`, `dd_g43`, `dd_g125`, `dd_g132`, `dd_g18`).
- `mx_berm.py` → `mx_berm` : un seul virage relevé mesuré, Desert Sand (718, 398), **R = 22 ft, mur à 47°** (coupe vers l'extérieur).
- Largeur roulable MX mesurée : **32–36 ft** (virages Desert Sand, sauts Dr. Dew) ; pente latérale médiane des obstacles 25°.

Tous les chiffres : `docs/09_donnees_mesurees.md` § 8, `docs/data/mx_*.csv`.

## La v1 MX (pourquoi ça n'a pas marché)

Construction (`legacy`: `layouts.py → mx()`, `build_compound.py`, `export.py`, `validate.py`) :
- grand tracé de 25 coins arrondis (`fillet_path`) sur un terrain de 4097 px à 0,4 ft/px (1638 ft de côté), largeur 34 ft, raccord au relief sur 22 ft ;
- tour MX 7637 ft (estimation ~2:27), SX1 v1 2631 ft (~1:00), SX2 v1 2613 ft (~1:01) ; 20 grilles ;
- sections MX mesurées posées sur les lignes droites (rollers, sauts, tables, step-up de Desert Sand et Dr. Dew) ;
- 4 lignes droites en sable ; objectif de tour ~2:20.

Problèmes (constat après coup) :
1. Les obstacles MX **ne sont pas des blocs** : ils font partie du relief (pentes, contre-pentes). Les extraire le long d'une ligne
   et les recoller sur un sol plat donne des formes sans contexte (montées sans descente, step-up au milieu de rien).
2. Les virages MX de référence sont des **ornières et des pentes naturelles** ; un seul berm a été mesuré proprement.
3. Le terrain 0,4 ft/px est moins fin que JGSX, et le sol plat autour fait « piste posée sur un parking ».
4. Pas de decals ni d'objets → aucun repère visuel.

Si on reprend le MX un jour : partir d'**un morceau de relief réel** (stamp 2D d'une zone entière de Desert Sand ou Dr. Dew,
comme on a fait pour le sable de Glendale), plutôt que de profils 1D recollés.

## Fichiers v1

- `scripts/layouts.py` (MX + anciens SX1/SX2 v1), `build_compound.py`, `export.py`, `validate.py`, `figures.py`, `web_data.py`,
  `view_build.py`, `check_mx.py`, `mx_preview.py`, `mx_candidates.py`, `mx_grad_profiles.py`, `preview.py`.
- Sorties v1 non versionnées, **reconstructibles** : `./make_all.sh mx` (vérifié : 32/32 contrôles v1, sorties dans `legacy_mx/build` et `legacy_mx/tracks`).
- Catalogue v1 (101 lignes, toutes les sections avec largeur / longueur / hauteur / angles / confiance) : `docs/data/catalogue_obstacles_v1.csv`.
