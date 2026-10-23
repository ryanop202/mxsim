# 05 — Le compound SX (v8) : les 3 pistes, comment et pourquoi

## Vue d'ensemble

- **1 terrain partagé**, 3 dossiers MX Simulator (`tracks/RyanCompoundSX1..3`), même `terrain.png` / `tilemap` / `shading.ppm`,
  chaque dossier a son propre `timing_gates` et `desc`. Choix de Ryan au départ : « 1 terrain, 3 dossiers ».
- Grille **4097 px à 0,28975 ft = 1186,8 ft** de côté (exactement la résolution des JGSX, 4× la surface).
- Tous les obstacles sont des **unités mesurées** JGSX (profil exact) posées sur le profil en travers mesuré
  (30,4 ft + flanc 4 ft). Tous les virages sont des **stamps de berms JGSX**. Le sable = **stamps Glendale**.
- Couloirs à 43 ft d'axe à axe, comme les références (« garde toujours les dimensions »).
- Vue de dessus globale : `viewer/figures/00_overview.jpg` ; par piste : `01_top_SX*.jpg` ; profils de chaque couloir : `02_lanes_SX*.jpg`.

Coordonnées monde : x vers la droite, z vers le bas de l'image, en ft. Cap 0° = +x (est), −90° = haut de l'image (« nord »).

## SX 1 — « vraiment bien » (Ryan)

Sens anti-horaire sur l'image, couloirs est-ouest de 370 ft. Origine locale (−8, −105). Tour **2931 ft**, estimation ~1:04.

| Couloir | Contenu (unités mesurées) | Longueur |
|---|---|---|
| ligne d'arrivée | **double ligne** : petite bosse 2,5 à gauche / single 3,4 à droite → gros single 5,8 → single 3,7 + 12 ft + **on-off Detroit** (g35_2 : 5,8 → 3,3) — v8 | 198 ft |
| T1 | gros berm 180° (`big_det_a`) — 1er virage | |
| A | single → **gros 5,9** (2e) → single, entrée écartée (8,5 / 5 ft de sol) → 3 singles → **gros 6,0** (7e) → single → **gros 5,9** (dernière) ; **singles normaux** Arlington/Cleveland (v7 avait des singles courts et pointus = pains de sucre) — v8 | 359 ft |
| T2 | gros berm 180° (`big_cle`) | |
| B | **12 whoops** (Test Track, entrée + 11) + **30 ft** de sol + single **rond 4,1 ft** (Glendale g40_3 ; le 5,0 ft g80_1 de la v4 était un pain de sucre) — v8 | 311 ft |
| T3 | gros berm 180° | |
| C | **triple sur table, off quad**, double : 2 singles → table 6,2 ft → 4 singles → 14 ft → 2 singles | 344 ft |
| T4 | gros berm 180° | |
| D | **step-up** 8,8 → 11,2 ft (Arlington g30) puis **triple sur table, off** allongé (11 ft de sol entre single, single, table) — v7 | 326 ft |
| T5 | gros berm 180° | |
| E | **couloir on-off complet de Detroit** (g35_0 : 6,2/5,8 + singles) + triple | 341 ft |
| T6 | petit berm 90° (`small_cus_a`) | |
| V | **petite bosse 2,5** puis triple (comme l'entrée de la ligne d'arrivée) — v8 | 142 ft |
| T7 | petit berm 90° (`small_arl`) — **ajouté en v3** (« je veux un appui » : c'était un virage plat à droite) | |

Départ : grille de 22 centrée en (112, 360), cap est, ligne droite de 220 ft au sud de l'arrivée, entonnoir vers la jonction
(462, 290) sur la ligne d'arrivée, avant T1. Départ → jonction ≈ **368 ft**. 7 virages, tous à berm.

## SX 2 — « ça va » → départ au milieu (v3)

Sens horaire, couloirs nord-sud. Origine locale (609, 30). Tour **2717 ft**, ~1:03. Refait en v3 autour d'un **départ au milieu**
(demande de Ryan), en gardant les mêmes enchaînements que la v2.

| Couloir | Contenu | Longueur |
|---|---|---|
| F → T1 | ligne d'arrivée (cap nord) → **gros berm 90° à droite** (1er virage). v4 : le berm (fait pour 180°) est resserré angulairement ×1,44 pour ne plus dépasser sur la ligne d'arrivée = fin du « rebord » | |
| haut | **gros triple** : 3 gros singles longs 5,9 / 6,0 / 5,8 (Arlington g37_2, Cleveland g29_3, Glendale g30_0) — v7 | 151 ft |
| T2 | petit berm 90° | |
| E1 | **bosse bosse table bosse table bosse** + 2 singles normaux à la fin (virage non déplacé ; v7 finissait sur un pain de sucre) — v8 | 330 ft |
| T3 | gros berm 180° | |
| E2 | **gros double** Glendale 7,1 → 7,9 (40,5 ft de sol) + **triple** qui finit au pied du virage — v4 | 254 ft |
| T4 | gros berm 180° | |
| E3 | **triple sur table, triple off** : 2 singles → table 6,2 → 3 singles | 234 ft |
| T5 | petit berm 90° | |
| bas | **8 whoops** (entrée + 7), plus de bosse derrière — v4 | 164 ft |
| T6 | petit berm 90° | |
| W1 | **double ligne** sur la 1re bosse (gauche 3,0 ft / droite 1,9 ft : simple, double ou triple au choix) → **gros 5,9** / single → **table 6,2** → single / **gros 6,0** / single — v7 | 302 ft |
| T7 | gros berm 180° | |
| W2 | **couloir JGSX Cleveland g29 complet, écarts d'origine** : single 3,6 → 25,8 ft → gros 7,9 → gros 6,0 → gros 7,4 — v8 | 200 ft |
| T8 | gros berm 180° → ligne d'arrivée | |
| F | **triple** de singles normaux Cleveland (les 2 du double d'origine + 1) — v5 (le triple de gros singles courts de la v4 = « pains de sucre », refusé) | 106 ft |

Départ : grille centrée en (809, 425), **cap nord**, dans l'infield, ligne de 95 ft puis entonnoir vers la jonction (720, 170)
sur la ligne d'arrivée, avant T1. Départ → jonction ≈ **278 ft**. 8 virages, tous à berm.

## SX 3 (sand) — la longue avec le sable Glendale

Historique : v2 « forme bizarre » → refaite en bloc compact ; v3 : sable façon photo (= Glendale) ; v4 : resserrée (plus de longues
lignes droites vides). Origine locale (8, 560), ligne d'arrivée à z local 330. Tour **3349 ft** (v3 : 3758), ~1:07.

| Section | Contenu | Longueur |
|---|---|---|
| F → T1 | arrivée (cap est) → gros berm 180° | |
| U1 | **triple** (3 singles Arlington) → **gros single 5,9** → 4 singles (3,0 / 3,4 / 3,7 / 3,2) → **gros single 6,0** → 30 ft → **triple Detroit allongé** (7,9 / 6,0 → 8 ft au lieu de 1,6 → 7,4) → 35 ft → **petite bosse 2,5 ft** ; commence **3 ft** après la sortie de T1 (moins d'élan, plus de quad d'entrée) — v7 | 579 ft |
| T2 | gros berm 180° | |
| U2 | **10 whoops** (Detroit) **sans bosse derrière** → 30 ft → on-off (single, gros single 6,0, single) → 30 ft → **step-up** 8,8 → 11,2 — v4 | 519 ft |
| GR | **sable Glendale : virage en S** (stamp miroir), cap est → ouest, 114 ft plus au nord — v4 : 70 ft plus tôt | |
| U3 | **dès la sortie du sable** (v5) : triple sur table, off quad, puis single / **gros single 6,0** / single / **gros single 5,8** ; ensuite déport plat 15° aller-retour (R 120) avant le J | 441 ft |
| GL | **sable Glendale : le J**, posé juste derrière le berm T2 (v3 : 135 ft plus à l'ouest, après 400 ft de ligne droite vide) | |
| sortie | courbe plate de 23,6° (R 80 ft), comme à Glendale | |
| F | **pain de sucre 6,3 ft** (Cleveland g59_1, voulu ici pour freiner) → 35 ft → triple → **gros double** Glendale — v7 | 327 ft |

Départ : grille centrée en (638, 960), cap est, ligne de 140 ft puis entonnoir vers la jonction (898, 890), avant T1.
Départ → jonction ≈ **279 ft**. 4 virages à berm/sable + 3 déports plats ≤ 25° (15°, −15°, −23,6°).

Pourquoi le déport : 43 ft (espacement) + 114 ft (décalage GR) + 187 ft (décalage GL) + sortie du J ne referment pas la boucle sur
la ligne d'arrivée (≈ 20 ft d'écart). v3 : déport de 8° dans la fin vide de U3 ; v4 : U3 raccourci → déport de 12° (R 150) placé
dans la sortie du sable GR, avant le combo ; v5 : combo dès la sortie du sable (on arrivait trop vite), déport de 15° (R 120) après le combo.

## Départs (v3, « pour qu'on puisse vraiment faire des courses »)

Méthode JGSX (doc 03 § 6), pour les 3 pistes :
- **22 grilles au pas de 4 ft**, sol plat contrôlé (écart 0,000 ft) ;
- ligne de départ **séparée du tour**, droite, puis **entonnoir** qui rejoint le tour à un point de jonction ;
- jonction placée **avant un 1er virage à gros berm** ;
- `timing_gates` : boucle complète = `normallap` ; `firstlap` = 2 portes en travers de la ligne de départ (à 60 ft et à la fin
  de la ligne droite, demi-largeur 50 ft) + toute la boucle depuis la jonction ;
- portes du tour tous les 60 ft à partir de jonction + 30 ft, + une porte de fin à L − 8 ft ; demi-largeur 18 ft
  (24 ft dans le sable) ;
- contrôle : 22 trajectoires (une par grille, ±3 ft de chaque côté) suivies jusqu'à la jonction → hauteur max 0,000 ft.

## Tiles

8 tiles (blocs physiques JGSX recopiés) : SX Main (sol), Jumps Sx (sauts), WhoopsV2, Berm Exit Sx (berms), Sand Straight,
Sand Bump Straight, Sand Exit, Sand Bump Solo. Dans le sable, ce sont les tiles **exacts** de Glendale (stamp).
Répartition (cases de tilemap) : sol 3,43 M, sauts 416 k, berms 122 k, whoops 107 k, Sand Exit 111 k, Sand Bump Solo 3 k.

## Historique des versions

| Version | Contenu | Retour de Ryan |
|---|---|---|
| **v1** | 1 MX + 2 SX (MX = sections Desert Sand / Dr. Dew recollées ; SX = sections JGSX entières) | MX « pas du tout » ; SX : « pas de vrai enchaînement, que des triples » ; virages « parfaits » sauf « un p'tit rebord en rentrant » ; whoops « vraiment bien, juste les changer entre les pistes » |
| **v2** | SX seulement. Bibliothèque d'**unités** (`sx_units`) + composition (`compose.py`) → vrais enchaînements (triple sur table off quad, triple-triple-quad, quad-quad…) ; whoops différents par piste ; rebord des berms corrigé ; SX3 plus long avec sable « tranquille » | « SX1 vraiment bien, SX2 ça va, SX3 forme bizarre » → SX3 refait compact |
| **v3** | Berm sur le virage plat du SX1 (T7) ; départs façon JGSX pour les 3 ; SX2 départ au milieu ; sable = stamps Glendale (photo) ; plus aucun virage plat > 25° | **1er test en jeu** de Ryan → retours détaillés (doc 07 § 6) |
| **v4** | Retours du test en jeu : SX1 single après whoops plus loin/plus bas, triple sur table off, on-off sur l'arrivée ; SX2 1er virage sans rebord, E1 bosse-bosse-table-bosse-table-bosse, triple dans le virage, whoops sans bosse, triple dur à l'arrivée ; SX3 hauteurs mélangées, petite bosse après le triple, whoops sans bosse, sable plus proche, J derrière T2, arrivée sans longue ligne droite | SX1/SX2 « bien », retours v5 (doc 07 § 7) |
| **v5** | SX1 : on-off Detroit après le triple d'arrivée ; SX2 : triple d'arrivée en singles normaux ; SX3 : U1 commence dès T1, triple-gros-triple-gros, U3 dès la sortie du sable avec 2 gros singles, table avant le triple d'arrivée | SX3 « bien », retours v6 (doc 07 § 8) |
| **v6** | SX1 : triple d'entrée écarté + gros single dans A ; SX2 : W1 avec gros singles + table au milieu ; SX3 : 1 bosse de plus dans U1 (gros single déplacé à la fin), 40 ft de sol après la table d'arrivée | retours v7 (doc 07 § 9) |
| **v7** | SX1 : A 2e/7e/dernière bosses grosses + entrée écartée, triple sur table allongé, petite bosse en entrée d'arrivée ; SX2 : double ligne W1, W2 technique, gros triple en haut, +2 bosses fin E1 ; SX3 : U1 collé au virage, pain de sucre avant le triple d'arrivée | retours v8 (doc 07 § 10) |
| **v8** | Pains de sucre chassés partout (+ contrôle automatique) ; SX1 : double ligne à l'arrivée, petite bosse en entrée de V, single après whoops reculé ; SX2 : W2 = vrai couloir JGSX Cleveland g29 ; SX3 : triple Detroit allongé | à tester |

## Contrôles automatiques (40)

`scripts/validate_sx.py` → `build/validation.json` (affichés aussi dans `viewer/index.html`). Pour chaque piste :
fichiers requis ; heightmap relue = terrain construit (0,0001 ft) ; tilemap cohérente ; toutes les références `@dossier/` existent ;
portes sur la ligne de course ; aucune porte ne touche une autre partie du tour ; ordre des tours ; grille de 22 sur sol plat ;
ligne de départ dégagée jusqu'à la jonction ; aucun virage plat > 25°. Global : couloirs séparés ≥ 38 ft ; pistes séparées
(101 / 400 / 220 ft) ; profils exportés = profils mesurés (18 couloirs, écart max 0,044 ft) ; pas de rebord au pied des obstacles
(≤ Detroit + 0,02 ft) ; terrain sans pics ni trous ; **pas de pains de sucre** dans les enchaînements (v8).

**Pas contrôlé** : le ressenti en jeu, la physique, les chronos réels, la vue caméra, les collisions de pilotes au départ.
