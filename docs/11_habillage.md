# 11 — Habillage (v9, complété en v10 et v11) : grilles, grillages, paddock, décor, decals, drapeaux

Script : `scripts/dress_sx.py` (lancé par `./make_all.sh build` juste après `export_sx.py`). Vue : `viewer/figures/05_habillage*.jpg`.
Toutes les ressources viennent de **JGSX 2026 Detroit** (`statue/`, `decal/`), copiées dans `tracks/USLAND2026SX1/` et référencées
`@USLAND2026SX1/...`. Les 3 dossiers ont le même décor (terrain partagé) ; les grilles et les drapeaux sont propres à chaque piste.

## Ce que fait JGSX (mesuré sur Detroit / Glendale)

| Élément | JGSX Detroit | Règle reprise |
|---|---|---|
| Grilles de départ | `gate01.jm` sur chaque ligne `startinggate:` + `@startgate.shp` | idem sur nos 22 grilles |
| Paysage | `ET.jm` : anneau de collines (jusqu'à 117 ft) autour d'un trou de 593,4 ft = le terrain | trou agrandi ×2 (1186,8 ft), anneau inchangé → `ET_compound.jm` (géométrie modifiée par nous) |
| Grillage | 147 `chainlink.jm` (panneaux de 13,11 ft) en rectangle autour de l'arène, départ compris | rectangle autour de chaque piste (emprise + 14 ft) |
| Poteaux d'éclairage | 6 `lightpole.jm` près des coins | 4 coins + 2 milieux, 8 ft à l'extérieur du grillage |
| Repères `2.jm` (+ `cone.shp`) | 10, au centre des virages | au centre de chaque virage à gros berm |
| Paddock | vans ×3, semi, camion-citerne, citerne, Matrix + tente, sur une bande de gravier hors grillage ; bulldozer + bobcat | même groupe, mêmes positions relatives, bande de gravier le long d'un côté libre (SX1 bas, SX2 droite, SX3 haut) |
| Decal `track.png` (26 ft) | ~1,4 par ft de tour, rotation aléatoire, sur toute la piste | grille 3,9 × 5,2 ft sur la piste + ligne de départ + entonnoir |
| Decal `sand.png` (26 ft) | 405 sur le sable de Glendale | sur les stamps de sable GL / GR |
| Decals d'obstacles (110 ft) | `single`, `whoops` (1 par whoop), `tripleface`, `triplemiddle`, `table` centrés sur l'obstacle, orientés selon le couloir | un par unité (single ≤ 52 ft, table ≥ 52 ft ou combo, tripleface ≥ 6,6 ft de haut ; agrandis si l'unité est plus longue que le decal) |
| Decals de virage | `180.png`, `90.png` (≈ 89 ft) | sur chaque virage à berm |
| `Tearoff.png` (4,84 ft) | ~44 éparpillés | 50 par piste près de la ligne de course |
| `gravel.png` (18,84 ft) | bande du paddock (pas 5,9 ft) | idem sous chaque paddock |
| Drapeaux | fichiers à 0 (désactivés) | panneau 30 s (×2) derrière la grille, drapeau d'arrivée à côté de la dernière porte |
| Panneaux (`billboards`) | vides | vides (comme JGSX) |

Convention d'angle (statues et decals) : l'axe z local du modèle / l'axe vertical de l'image suit (−sin a, −cos a), comme les grilles.

## Contrôles ajoutés (43 au total)

- Objets hors piste : chaque objet (boîte englobante du modèle) à plus de 17 ft de toute ligne de course et sur sol plat.
- Drapeaux à plus de 20 ft des lignes de course.
- Tous les fichiers `@USLAND2026SX1/...` référencés existent, 22 grilles `gate01`.

## Limites

- Non testé en jeu : orientation exacte des decals 90/180 et des véhicules à vérifier ; performances avec ~17 000 decals par dossier
  (Dr. Dew en a 23 000).
- Pas de banderoles / tuff blocks le long des couloirs (JGSX n'en a pas non plus dans ces fichiers).
- Texture du sol : pack `25BHFSXMiami` absent des archives → terre et hardpack de Dr. Dew sous les decals JGSX.
- Taille : `USLAND2026SX1` passe à ~260 Mo.

## v10

- **Tuff blocks** (`tuff-medium.jm` de Detroit `seq/`, collision `tuff.shp` à 4 sphères au format de `cone.shp` — format déduit, à vérifier en jeu) :
  partout où deux parties d'un tour passent à moins de 70 ft l'une de l'autre en étant à plus de 110 ft sur le tour (médiane entre
  couloirs, sable, J), plus les deux bords de chaque couloir de départ ; jamais sur une piste, un croisement, une jonction ;
  posés au sol local (y) quand ils sont au pied de deux murs de saut (≤ 0,65 ft).
- **Sol** : tile Main texturé en terre (`dirt.ppm`) ; nouveau tile **Road** (béton `concrete.ppm` de Dr. Dew, physique du Main) :
  anneau de 18 ft autour de chaque grillage + avenue est-ouest entre les pistes du haut et SX3 ; paddocks décalés de 22 ft.
- **Sable** : decals `sand.png` posés sur les cases de sable du tilemap (pas de 6 ft), plus le long de la ligne.
- **Minimaps** : `map.png` 1024² RGBA par dossier (comme Dr. Dew), vue de dessus sans lignes, transparente hors de la piste.
- **Portes** : simulation du comptage (1er tour depuis la grille, tours suivants) ; ligne d'arrivée possible n'importe où
  (`finish`), porte F' pour le 1er passage quand l'arrivée suit de près la jonction.

## v11

- **Tuff blocks** : seulement ceux placés par Ryan (`dress_sx.TUFFS`, 5 sur SX3). Modèle `tuff_usland.jm` = boîte 1,8 × 1,8 × 5,4 ft
  (taille du tuff JGSX), texture blanche `tuff_usland.png` avec le logo (`assets/usland_logo.png`) sur les deux grands côtés.
  Sens des UV copié sur le van JGSX (texte lisible des deux côtés) — **à vérifier en jeu** (logo à l'envers ou en miroir = inverser `u`/`v` dans `tuff_usland.py`).
- **Cônes** (`turn_cones`) : 1 par virage de plus de 45° et dans chaque virage de sable Glendale, à 22 ft de la ligne de course vers l'intérieur.
- **Sol** (`ground_decals`) : decal `track.png` 26 ft sur une grille de 11 ft partout hors piste, hors routes béton, hors sable et gravier.
- **Minimaps** : carré autour de la piste (+12 ft), même sens que les vues de dessus, transparent hors piste.
- **Portes** (`export_sx.gate_marks`) : vecteur = sens de la course × half (comme toutes les références), 1 porte au milieu de chaque
  virage, 2 par couloir (3 au-delà de 330 ft), arrivée en dernier.

## v11b

- Tuffs : au bord du couloir (`TUFF_EDGE` = 16,5 ft), y = milieu du sol local, contrôle « ni enterré ni en l'air de plus de 0,5 ft ».
- Minimap : le jeu étire `map.png` sur tout le terrain (vu en jeu) → l'image couvre tout le terrain. Elle ne peut pas être plus
  « zoomée » sans réduire le terrain de chaque piste.

## v13b — flammes d'arrivée + craie (`scripts/pyro_chalk.py`, fichiers bruts dans `assets/sx2026`)

- **Flammes** : 2 billboards (`finishflames`, `finishflames2` d'Anaheim 1) posés sur le haut des 2 poteaux de l'arche FINISH
  (base en haut des torches de l'arche, 40,35 ft, taille 45). `frills.js` les cache au repos et les joue **une seule fois,
  quand le vainqueur passe la ligne** (même logique de dernier tour que le commissaire d'Anaheim). Son `finishlineflame`.
  Pas de jets de feu au départ ni de boule de feu (v13 annulée). Hauteur à vérifier en jeu (y = base ou centre du billboard).
- **Craie** (un decal par piste, `decal/chalk_SXn.png`, blanc 242, 1,6 ft) : deux traits le long des bords du couloir de
  départ (grilles → jonction avec le tour ; le trait intérieur s'arrête où un virage serré le ferait revenir en arrière) et
  la **ligne de holeshot** en travers de la crête de la 1re bosse après le départ (SX1 : 136 ft après la jonction,
  SX2 : 16 ft, SX3 : 64 ft), sur toute la largeur de la bosse.
- Non testé en jeu.
