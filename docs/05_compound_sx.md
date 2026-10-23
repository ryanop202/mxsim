# 05 — Le compound SX (v3) : les 3 pistes, comment et pourquoi

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
| ligne d'arrivée | plate (jonction du départ) | |
| T1 | gros berm 180° (`big_det_a`) — 1er virage | |
| A | **triple-triple-quad** : 6 singles Arlington (3,4–4,0) + 4 singles Custom/Cleveland | 356 ft |
| T2 | gros berm 180° (`big_cle`) | |
| B | **12 whoops** (Test Track, entrée + 11) + gros single 5,9 ft | 296 ft |
| T3 | gros berm 180° | |
| C | **triple sur table, off quad**, double : 2 singles → table 6,2 ft → 4 singles → 14 ft → 2 singles | 344 ft |
| T4 | gros berm 180° | |
| D | **step-up** 8,8 → 11,2 ft (Arlington g30) puis triple | 257 ft |
| T5 | gros berm 180° | |
| E | **couloir on-off complet de Detroit** (g35_0 : 6,2/5,8 + singles) + triple | 341 ft |
| T6 | petit berm 90° (`small_cus_a`) | |
| V | quad (4 singles) | 141 ft |
| T7 | petit berm 90° (`small_arl`) — **ajouté en v3** (« je veux un appui » : c'était un virage plat à droite) | |

Départ : grille de 22 centrée en (112, 360), cap est, ligne droite de 220 ft au sud de l'arrivée, entonnoir vers la jonction
(462, 290) sur la ligne d'arrivée, avant T1. Départ → jonction ≈ **368 ft**. 7 virages, tous à berm.

## SX 2 — « ça va » → départ au milieu (v3)

Sens horaire, couloirs nord-sud. Origine locale (609, 30). Tour **2717 ft**, ~1:03. Refait en v3 autour d'un **départ au milieu**
(demande de Ryan), en gardant les mêmes enchaînements que la v2.

| Couloir | Contenu | Longueur |
|---|---|---|
| F → T1 | ligne d'arrivée (cap nord) → **gros berm 90° à droite** (1er virage) | |
| haut | rythmique Arlington d'origine (g37_0, g37_1, gros single g37_2, g1_3) | 147 ft |
| T2 | petit berm 90° | |
| E1 | **on-off double-double** : single / gros single 5,9 / single / gros single 5,8 / single | 198 ft |
| T3 | gros berm 180° | |
| E2 | **gros double** Glendale 7,1 → 7,9 (40,5 ft de sol) + double | 214 ft |
| T4 | gros berm 180° | |
| E3 | **triple sur table, triple off** : 2 singles → table 6,2 → 3 singles | 234 ft |
| T5 | petit berm 90° | |
| bas | **7 whoops** (entrée + 6) + single | 178 ft |
| T6 | petit berm 90° | |
| W1 | **quad-quad** (8 singles) | 289 ft |
| T7 | gros berm 180° | |
| W2 | **table 9 ft** (Arlington g20_1) + triple | 173 ft |
| T8 | gros berm 180° → ligne d'arrivée | |
| F | double d'arrivée | 66 ft |

Départ : grille centrée en (809, 425), **cap nord**, dans l'infield, ligne de 95 ft puis entonnoir vers la jonction (720, 170)
sur la ligne d'arrivée, avant T1. Départ → jonction ≈ **278 ft**. 8 virages, tous à berm.

## SX 3 (sand) — la longue avec le sable Glendale

Historique : v2 « forme bizarre » → refaite en bloc compact ; v3 : sable façon photo (= Glendale). Origine locale (8, 560),
ligne d'arrivée à z local 330. Tour **3758 ft**, ~1:13.

| Section | Contenu | Longueur |
|---|---|---|
| F → T1 | arrivée (cap est) → gros berm 180° | |
| U1 | **triple-triple-quad** (6 singles Arlington + 4 singles Detroit/Glendale) + 30 ft + **triple Detroit** (trio 7,9 / 6,0 / 7,4) | 529 ft |
| T2 | gros berm 180° | |
| U2 | **10 whoops** (Detroit) + on-off (single, single, gros single 6,0, single) + 30 ft + **step-up** 8,8 → 11,2 | 548 ft |
| GR | **sable Glendale : virage en S** (stamp miroir), cap est → ouest, 114 ft plus au nord | |
| U3 | **triple sur table, off quad** + quad, puis déport plat de 8° (R 250) aller-retour pour tomber juste | 434 ft |
| GL | **sable Glendale : le J** (stamp tel quel), ouest → sud → nord-est, sortie 187 ft plus bas | |
| sortie | courbe plate de 23,6° (R 80 ft), comme à Glendale | |
| F | triple + **gros double** Glendale | 272 ft |

Départ : grille centrée en (638, 960), cap est, ligne de 140 ft puis entonnoir vers la jonction (898, 890), avant T1.
Départ → jonction ≈ **279 ft**. 4 virages à berm/sable + 3 déports plats ≤ 25° (8°, −8°, −23,6°).

Pourquoi le déport de 8° : 43 ft (espacement) + 114 ft (décalage GR) + 187 ft (décalage GL) ne referment pas la boucle sur
la ligne d'arrivée (écart de 19,8 ft). Essais : grand S plat (refusé : virage plat), déport dans U3 qui touchait GR
(refusé : collision) → GR déplacé à l'extrémité est en miroir + déport de 8° dans la partie vide de U3.

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
| **v3** | Berm sur le virage plat du SX1 (T7) ; départs façon JGSX pour les 3 ; SX2 départ au milieu ; sable = stamps Glendale (photo) ; plus aucun virage plat > 25° | pas encore de retour (non testé en jeu) |

## Contrôles automatiques (39)

`scripts/validate_sx.py` → `build/validation.json` (affichés aussi dans `viewer/index.html`). Pour chaque piste :
fichiers requis ; heightmap relue = terrain construit (0,0001 ft) ; tilemap cohérente ; toutes les références `@dossier/` existent ;
portes sur la ligne de course ; aucune porte ne touche une autre partie du tour ; ordre des tours ; grille de 22 sur sol plat ;
ligne de départ dégagée jusqu'à la jonction ; aucun virage plat > 25°. Global : couloirs séparés ≥ 38 ft ; pistes séparées
(101 / 400 / 220 ft) ; profils exportés = profils mesurés (18 couloirs, écart max 0,044 ft) ; pas de rebord au pied des obstacles
(≤ Detroit + 0,02 ft) ; terrain sans pics ni trous.

**Pas contrôlé** : le ressenti en jeu, la physique, les chronos réels, la vue caméra, les collisions de pilotes au départ.
