# 02 — Inventaire des références analysées

3 archives fournies par Ryan (empreintes et extraction : `refs/README.md`). 7 pistes au total.

| Dossier | Nom en jeu | Grille | Côté | Hauteurs (ft) | Lignes edinfo | Checkpoints (1er tour / tours) | Grilles | Tiles déclarés / utilisés | Statues | Decals |
|---|---|---|---|---|---|---|---|---|---|---|
| JGMXDesertSand | JGMX: Desert Sand | n=11, 0,22 ft, 4097 px | 901 ft | −15,0 … 31,5 | 127 | 77 (13 / 62) | 20 | 1 / 1 | 1435 | 7248 |
| JGMXDrDew | JGMX: Dr. Dew Racing Compound | n=10, 0,8 ft, 2049 px | 1638 ft | −63,4 … 132,3 | 136 | 67 (10 / 66) | 40 | 5 / 3 | 167 | 22950 |
| JGSX2026Detroit | JGSX: 2026 Detroit | n=10, 0,28975 ft, 2049 px | 593,4 ft | −0,19 … 11,22 | 37 | 46 (20 / 24) | 22 | 30 / 6 | 176 | 4061 |
| JGSX2026Arlington | JGSX: 2026 Arlington | idem | 593,4 ft | −0,20 … 11,22 | 56 | 46 (13 / 22) | 22 | 30 / 5 | 176 | 4061 |
| JGSX2026Glendale | JGSX: 2026 Glendaleish | idem | 593,4 ft | −0,84 … 11,22 | 94 | 46 (15 / 28) | 22 | 30 / 8 | 197 | 4564 |
| JGSX2026Custom | JGSX: 2026 Test Track | idem | 593,4 ft | −0,28 … 11,22 | 56 | 46 (23 / 28) | 22 | 30 / 8 | 178 | 4012 |
| JGSX2026Custom1 | JGSX: 2026 **Cleveland** | idem | 593,4 ft | −0,05 … 11,22 | 73 | 46 (23 / 24) | 22 | 30 / 6 | 173 | 4066 |

Tour approximatif (polygone des checkpoints, sous-estime un peu) : Desert Sand ~7250 ft, Dr. Dew ~9590 ft,
Detroit ~2580, Arlington ~2510, Glendale ~3120, Test Track ~2820, Cleveland ~2420 ft.

Atlas de chaque piste (relief, hauteurs, lignes `g#`, blocs SX numérotés, checkpoints, grille) : `docs/img/atlas_<dossier>.jpg`.

## JGSX 2026 (les 5 supercross) — la vraie base du projet

- Même grille pour les 5 → les mesures sont directement comparables et **réutilisables à l'identique**.
- Sol plat à ~0 ft, obstacles de 1,9 à 11,2 ft. Hauteur max commune 11,22 ft (step-up d'Arlington).
- Construits en **blocs** : chaque obstacle est un bloc à dessus plat de 30,4 ft de large avec un flanc de ~4 ft, posé sur un axe de
  couloir. Couloirs espacés de **43 ft**. Virages = **berms en croissant** (gros 180°, petits 90°).
- Beaucoup de couloirs sont **partagés** entre les pistes test (même profil exact) → dédoublonnage dans `sx_units.py`
  (147 unités trouvées → 90 uniques).
- Glendale (« Glendaleish ») a du **sable** : chenal (creux jusqu'à −0,84 ft), berms organiques, tiles `Sand Exit` / `Sand Bump Solo`.
  C'est le sable de la photo envoyée par Ryan (`docs/img/photo_sable_reference_utilisateur.png`).
- Départ : 22 grilles au pas de 4 ft, toutes face à +x (angle −π/2), à x ≈ 41 ft, sur une ligne de départ séparée.
- Pistes test (`Custom` = Test Track, `Custom1` = Cleveland) : mêmes briques que Detroit/Arlington, autres combinaisons.

## JGMX (les 2 motocross)

- **Desert Sand** : désert, grand relief (−15 à +31,5 ft), 1 seul tile (tout en sable), sol entièrement en decals
  (sand / sandoff / grass / road). Tour long (~7250 ft). Des caméras TV (`cameras`).
- **Dr. Dew** : grand compound naturel (−63 à +132 ft de relief), 0,8 ft/px (5× moins fin que JGSX), 40 grilles, decals
  `ontrack.png` / `offtrack.dirt` / `grass`.
- Obstacles MX = terrain sculpté (faces, plateaux, step-up le long des pentes), **pas** des blocs → beaucoup plus dur à mesurer
  et à recomposer. C'est la raison principale de l'échec de la v1 MX (voir `docs/04_mesures_mx.md`).

## Contenu détaillé des dossiers (pour mémoire)

- Desert Sand : `MX Simulator Track Scaler.exe` (outil de mise à l'échelle), `old files/`, `cameras`, `billboard/`, `decal/`, `sky/`, `statue/`, `tiles/`.
- Dr. Dew : `map.png`, `objects`, `roost/`, `skybox/`, `texturelist`, `tiles/` (dirt, hardpack, grass…).
- Detroit : `original files/`, `seq/`, `sky/`, `decal/` (dont `treads/` : dirt2x4, dirt2x8, sand1x4, sand1x8), `statue/` (gate01.jm, transit.jm, ET.jm, bobcat, chainlink…).
- Ressources reprises dans le compound : textures `dirt.ppm`, `hardpack.ppm` (Dr. Dew), `sand.ppm`, `redroost.png`, `dirt4.png`, `hha.dust.png`
  (Desert Sand), traces `treads/*` et ciel `sky/*` (Detroit), blocs physiques de `JGSX2026Custom/tileinfo`.
