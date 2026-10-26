# 13 — usland race track (v1b, 26/10/2026)

Nouvelle piste SX **indépendante** du compound : son propre terrain, son propre dossier `tracks/USLANDRaceTrack`
(nom en jeu « usland race track »), aucune référence vers un autre dossier. SX1, SX2, SX3 ne sont pas modifiées
(vérifié à l'octet). **Non testée en jeu** : tout ce qui suit vient des contrôles automatiques.

Vues : `viewer/figures/URT_top.png` (terrain exporté relu), `viewer/figures/URT_lanes.png` (profils relus dans `terrain.png`).

## Reconstruire

```bash
./make_all.sh usland              # = les 3 étapes ci-dessous ; n'a besoin que de refs/rf/*.saf (pas des archives JGSX)
python3 scripts/rf_units.py       # unités RF mesurées dans les .saf (lues en mémoire) -> lib/rf_units.json
python3 scripts/build_usland_rt.py     # terrain + export de tracks/USLANDRaceTrack
python3 scripts/validate_usland_rt.py  # 30 contrôles sur les fichiers exportés + vues URT_*.png
```

`./make_all.sh build` lance aussi ces étapes à la fin. `export_sx.py` n'efface plus tout `tracks/` mais seulement les
3 dossiers du compound (sinon il supprimait la nouvelle piste) : sortie de SX1-3 inchangée.

| Fichier | Rôle |
|---|---|
| `scripts/rf_units.py` | lecture des `.saf` RF, mesure des couloirs RF le long de chaque porte (sens de course), `lib/rf_units.json` (288 unités) |
| `scripts/layout_usland_rt.py` | **le fichier à modifier** : géométrie, sections (jetons JGSX / `('rf', id)` / whoops), départ |
| `scripts/build_usland_rt.py` | rendu (engine), tiles, export, portes (timing.py), stade, objets, decals, flammes, minimap |
| `scripts/validate_usland_rt.py` | contrôles + vues |

## Sources

| Élément | Source | Détail |
|---|---|---|
| Whoops | JGSX | `Custom1_0` (Cleveland), entrée + 8 (9 bosses, 184 ft) — compte différent de SX1 (12), SX2 (8), SX3 (10) |
| Berms | JGSX (stamps exacts) | big_det_a, big_cle, big_cus (180°) ; small_arl ×2, small_cus_b ×2, small_cus_a (90°) — aucun modifié |
| Bosses | RF + JGSX | 21 unités RF (Anaheim 1, Anaheim 2, Houston) + 17 JGSX, voir tableau |
| Départ | USLAND | `start_gate` sur les 22 grilles, `start_grate` ×22, `start_gantry`, craie (bords du couloir + holeshot) |
| 1er virage | style RF (A1 2027) | cuvette **plate** 180° R 90 ft, sans berm |
| Arrivée | USLAND | arche FINISH centrée (`finish_arch_URT.jm`), flammes v13b (fichiers RF 2026 d'`assets/sx2026`) |
| Stade | RF | Angel Stadium (`sx2026r01anaheim1.medium.saf`, 17 modèles, positions d'origine : même sol de 593,4 ft) |
| Sol / tiles | JGSX | blocs physiques JGSX des pistes USLAND (Main, Jumps Sx, WhoopsV2, Berm Exit Sx) ; decals JGSX Detroit ; textures .ppm des pistes USLAND (JGMX) — le pack JGSX `25BHFSXMiami` manque |
| Éclairage | USLAND (= JGSX Detroit) | l'éclairage RF dépend d'un pack `@sx2026/sky` absent de l'archive |
| Décor | **RBT : pas fait** | `refs/rbt/` ne contient que les placements ; modèles et textures `24.RBT` absents |
| Cônes | JGSX (`2.jm`) | 1 par virage, comme SX1-3 (marquage de piste) |

## Terrain et tracé (lignes de course, ft)

Terrain 2049 px × 0,28975 ft = 593,4 ft (n = 10). Hauteur max 10,6 ft. Tour **2 891 ft (881 m)**, départ → jonction 409 ft.
Couloirs : F x 65 (sud) · A 245 (nord) · B 288 · C 331 · D 387 · E 430 · ligne du haut R z 63. Grilles centrées (155, 112), vers le sud.

| N° | Section | Contenu (hauteurs ft) | Longueur section / couloir |
|---|---|---|---|
| 1 | Départ | 22 grilles × 4 ft, couloir 92 → 40 ft sur 268 ft, virage plat à gauche R 45 dans la cuvette, jonction en sortie (245, 380) | 409 ft |
| 2 | T1 | cuvette plate 180° à gauche, R 90, centre (155, 380) | — |
| 3 | A | 25 ft de sol, whoops JGSX ×9 (1,9 + 2,8–3,0) | 184 / 235 |
| 4 | T2 | big_det_a 180° droite | |
| 5 | B | JGSX 3,4 · RF A1 6,1 / 5,9 / 4,6 / 3,7 / 3,8 · on-off RF 5,9 → 4,9 | 329 / 369 |
| 6 | T3 | big_cle 180° gauche | |
| 7 | C | JGSX 3,5 / 3,9 · RF HOU double 4,2+4,4 · 2,9 · on-off 6,0 → 3,4 · 3,5 · JGSX gros rond 5,8 | 328 / 369 |
| 8 | T4 + T5 | small_arl + 34 ft + small_cus_b (droite, droite) | |
| 9 | D | JGSX 3,6 · 29 ft · RF gros triple 8,5 / 5,5 / 7,3 · 16 ft · JGSX 3,6 / 3,4 | 276 / 305 |
| 10 | T6 | big_cus 180° gauche | |
| 11 | E | JGSX 1,9 · couloir RF A1 complet 3,4 / 3,6 / 6,1 / 3,5+3,4 / 5,5 → 3,6 / 3,4 · RF 4,8 | 355 / 376 |
| 12 | T7 | small_arl 90° gauche | |
| 13 | R | JGSX triple 3,7 / 3,8 / 4,0 · RF HOU 6,0 / 3,4 / 5,9 / 3,6 · JGSX 3,6 | 324 / 343 |
| 14 | T8 | small_cus_b 90° gauche | |
| 15 | F | JGSX 2,5 · RF A2 step-up 8,75 → table 10,6 (+3,5) · JGSX 3,6 · **arrivée sur la crête de l'appel 8,75** (65, 150,5) | 278 / 306 |

Écarts au sol : écart RF mesuré entre deux unités consécutives du même couloir RF ; sinon `compose.PAIR` / `compose.GAP`
(médianes JGSX), 16,25 ft à côté d'un gros saut ; 29 ft devant le gros triple (mesuré devant ce triple à Houston).

## Différences avec le plan v1 validé (et pourquoi)

Le plan v1 prenait les murs du stade RF pour un rectangle x 17–591, z 21–583 (boîte englobante des modèles). En relisant
les sommets des modèles (tribunes, murs, rochers entre 0,5 et 14 ft) pendant la construction : les tribunes de droite
**coupent le sol en diagonale** (x ≈ 554 à z 220, 481 à z 430, 437 à z 540) et les rochers descendent jusqu'à z ≈ 452.
Le plan v1 mettait le couloir E à 1 ft d'une tribune. Corrections (v1b) :

| Plan v1 | Construit (v1b) | Raison |
|---|---|---|
| tracé à x 125 → 518 | tracé décalé de 60 ft vers l'ouest (x 37 → 458) | tribunes en diagonale à droite |
| C → D : gros berm 180° (big_cus) ; D → E : 2 petits berms + 34 ft | C → D : 2 petits berms + 34 ft ; D → E : gros berm 180° (big_cus) à z 450 | le bas de D/E doit remonter (tribunes) ; avec D à 56 ft de C, le berm du bas ne touche plus C |
| D 388 ft, E 461 ft | D 305 ft, E 376 ft | idem |
| D : … triple JGSX (3 singles) + RF 4,8 | D : … double JGSX (2 singles) ; le RF 4,8 passe à la fin de E ; le 3ᵉ single (Cleveland g29_1) à la fin de R | sections raccourcies avec les mêmes unités |
| E finit sur l'on-off montant JGSX g49_0 | E finit sur le RF 4,8 | E plus court |
| sol après le gros triple RF : 3,75 ft | 16,25 ft | le 7,3 ft est un gros saut (X) : écart X → S ; RF mesure 16 ft au même endroit à Anaheim 2 |
| whoops ×10, cuvette z 410, ligne du haut z 58 | whoops ×9, cuvette z 380, ligne du haut z 63 | rochers à 20 ft de la cuvette, mur du haut à 6 ft du berm T8 ; ensuite il ne restait que 5 ft entre les whoops et T2 |
| tour 3 142 ft, chrono estimé 66,5 s | **2 891 ft, 62,5 s estimés (60,2–66,0)** | couloirs plus courts |

## Contrôles (30 / 30, `build/usland_rt_validation.json`)

Fichiers présents ; nom en jeu ; heightmap 2049 px relue = terrain (8,9e-5 ft) ; tilemap 1024² ; 156 références
`@USLANDRaceTrack/` toutes présentes, aucune dépendance vers un autre dossier ; frills.js en ASCII ; tour fermé ; sections
dans leurs couloirs (11–34 ft libres) ; profils exportés = profils mesurés (écart max 0,057 ft) ; 0 pain de sucre ; couloirs
séparés ≥ 41 ft ; berms : rien sur le dessus roulable d'un autre couloir (jupes de T4 et T5 au bord de B et E : 0,17 et 0,25 ft,
hors des 30,4 ft) ; virage 1 plat (0,000 ft) ; marche sol → obstacle 0,127 ft (Detroit 0,133) ; pas de trou ni de pic ;
22 grilles au pas de 4,000 ft sur sol plat ; couloir de départ dégagé ; comptage des tours simulé (28 portes, 1er tour 25,
tour normal 27, toutes franchies dans l'ordre) ; portes sur la ligne (≤ 0,5 ft) ; arrivée sur la crête 8,75 ft ; cônes ≥ 17 ft ;
arche (poteaux à 22 ft, socles 0,36 ft de pente, 21,2 ft libres au-dessus de la crête) ; grates + portique ; stade RF : ligne la
plus proche 26 ft, obstacle le plus proche 11 ft ; flammes ; SX1-3 inchangées.

**Pas contrôlé** : le jeu (chargement, rendu du stade, échelle, objets, grilles qui tombent, ressenti, chrono réel).

## Reste à faire / limites

- **Test en jeu** (dossier `tracks/USLANDRaceTrack` à copier dans les pistes de MX Simulator, sans le renommer).
- **Décor RBT** : fournir le dossier de piste `24.RBT` complet ; zones libres prévues : bande ouest (x 17–45) et grande zone
  à droite (x ~470–560, z 70–400) hors tribunes, plus l'intérieur de la cuvette.
- **Chrono** : 62,5 s estimés pour un objectif de ~70 s (le modèle ignore sauts et whoops). Le sol d'Anaheim ne permet
  pas des couloirs plus longs à droite ; pour rallonger : une section de plus (ex. sable Glendale GR) ou un autre stade.
- Textures JGSX d'origine (`25BHFSXMiami`) absentes ; éclairage RF non repris.
- Gros triple RF 8,5 ft (appel 41°) et step-up RF 8,75 → 10,6 : jamais roulés dans nos pistes.
- 154 Mo (stade RF 25 Mo, shading 25 Mo, textures et decals copiés pour que le dossier soit autonome).
- Ressources tierces (RF, JGSX) : dépôt privé, pas de publication sans autorisation.
