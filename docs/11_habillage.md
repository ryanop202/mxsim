# 11 — Habillage (v9) : grilles, grillages, paddock, décor, decals, drapeaux

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
