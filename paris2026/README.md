# Supercross Paris 2026 — relevé du tracé (avant construction)

Source : 5 visuels officiels du tracé (local seulement : `refs/`, pas sur GitHub). Relevé : `lecture_photos.json`,
plan et tableau : `py -3.15 -I paris2026/lecture.py` → `refs/plan_annote.jpg` + `tableau.md`.

## Méthode

1. **Échelle** calée sur JGSX : pas des whoops 30,2 px = 20,1 ft (JGSX 20 ft), largeur des couloirs 55-57 px = 37-38 ft
   (JGSX 30,4 + 2 × 4 ft) → **0,665 ft/px**.
2. **Sens de la course** : la ligne rouge du visuel 1 est reportée sur la vue de dessus par homographie calée sur les
   9 poteaux blancs (erreur < 2 px).
3. **Obstacles** : début / fin lus à la main sur la vue de dessus agrandie × 4 (± 2 px ≈ ± 1,3 ft) ; type (single, table,
   whoops…) lu sur les vues de biais ; chaque obstacle reçoit l'unité JGSX mesurée la plus proche en longueur (`lib/sx_units.json`).

## Le tour (sens de course)

| Couloir | Contenu | Remarques |
|---|---|---|
| Départ | 22 grilles, ligne droite vers l'est, virage à gauche vers le nord, rejoint le couloir C | au tour suivant, la ligne de départ est reprise **en sens inverse** |
| L5 (arrivée) | single, single, saut d'arrivée (37 ft), table 35 ft, table longue 61 ft | ligne d'arrivée sur le 3e saut |
| 180 gauche | berm sur le 1er quart | poteaux à l'intérieur |
| LD | ligne de départ vers l'ouest, plate (~245 ft) | |
| T_B | 180 à droite | |
| L3 | single, **grande table « SUPERCROSS Paris »** (97 × 63 ft) | 4 tremplins FMX, 2 de chaque côté (avec collision) |
| C | colonne vers le nord, plate | |
| L2 | 7 singles (~20 ft, écarts 14-17 ft) | |
| T1 | 180 droite, berm | |
| L1 | **10 whoops** (pas 20 ft), table 40 ft, 2 singles | murets blancs le long des whoops |
| coin NE | 90 à droite | caché par le logo |
| LR | single, ligne plate 111 ft, table longue, 3 bosses | en partie caché par les faisceaux |
| T_E | 90 à droite, berm | |
| L6 | 8 bosses dont une table 41 ft (écarts 13-15 ft) | |
| T_C | 180 à droite, berm | |

## Taille du sol

Tracé seul : **134 × 119 m** ; sol du visuel : **149 × 121 m**. Sol actuel de l'arène : 122 × 90 m → l'arène doit être
agrandie (≈ × 1,22 en longueur, × 1,34 en largeur).

## Décisions de Ryan (2026-11-09)

- 22 grilles au départ.
- Grande table de L3 : **nouvelle forme de 97 ft** faite d'après le visuel (montée raide, plateau ~58 ft, descente ~39 ft) —
  forme créée, pas une mesure JGSX.
- Coin nord-est et couloir LR : garder la lecture du plan annoté.
- Tremplins FMX : **avec collision** (utilisables, hors tracé).
- Arène agrandie si le tracé ne rentre pas.

## Construction (v1)

```bash
py -3.15 -I stade_paris/src/build.py --mx
```

```bash
py -3.15 -I paris2026/build_paris.py
```

- Arène agrandie **en plan × 1,35** (hauteurs inchangées) : sol 164,7 × 121,5 m, tribunes reconstruites à la
  nouvelle taille (33 054 sièges au pas réel), visuels USLAND redessinés au format final des écrans (rien d'étiré).
- Tracé : `layout_paris.py` (tour 2 588 ft, rayons JGSX 21,5 ft ; L1 et L6 rapprochés de ~5 ft pour les 180° JGSX),
  terrain 4097² à 0,28975 ft, tuiles / physique des pistes USLAND SX, départ 22 grilles, arrivée sur le 3e saut de L5.
- Formes créées (pas des mesures JGSX) : grande table 97 ft (8 ft de haut), 4 tremplins FMX en terre (10 ft, lèvre ~37°).
- Sortie : `tracks/USLAND2026SupercrossParis` ; contrôles : `apercu/build_report.json` (6 / 6) + `validate_mx.py`
  (0 problème) ; vue de dessus : `apercu/vue_dessus.png`. **Non testé en jeu.**
- Pas encore posé : tuff blocks (Ryan), poteaux / cônes, murets blancs des whoops, banderoles START / FINISH,
  grilles de départ USLAND (modèles), habillage des tremplins FMX (structure noire).

## Points incertains

- Coin nord-est (sous le logo) et couloir LR (faisceaux) : lecture à confirmer.
- Grande table de L3 : 97 ft, aucune unité JGSX aussi longue (max 86,7 ft, `Custom_g29_1`).
- Hauteurs : non mesurables sur des visuels ; elles viennent des unités JGSX choisies.

## Refonte v2 (retours de Ryan sur la v1 : « bosses carrées, terrain / stade / rampes nuls »)

- **Bosses** : formes déjà validées sur Saint-Thibéry / Saint-Georges (singles Arlington redimensionnés, table 6,6 ft, whoops
  x1,15, `rounded()` + pieds lissés, berms 90° x1,4), chaque obstacle au centre de celui du visuel (`layout_paris.from_render`).
- **Saut d'arrivée et saut du milieu** : repris TELS QUELS de ZION.2025.SupercrossParis (archive de Ryan, mesures dans
  `data/zion_p25_profils.json`) : triple 10,0 / 6,0 / 11,2 ft (arrivée sur le 1er) ; appel 10 ft + butte ronde 24,2 ft
  (68 ft à mi-hauteur, 90 ft au pied au lieu de 110 faute de place). Superposition : `apercu/zion2025_vs_paris.png`.
- **Table après les whoops** : 6,6 ft, à 35 ft des whoops (la 2e petite bosse de fin de couloir retirée pour la place).
- **Couloir Est** : une longue bosse ondulée (forme créée d'après la vue de côté) puis 2 bosses.
- **Sol et éclairage** : ceux de Saint-Thibéry à l'identique (`stt_look.py` : tileinfo, terre, ~8 000 décals, ombrage, lighting, ciel).
- **Objets** (`objets.py`) : tuff blocks à logos, gros blocs de virage, banderole FINISH, structure de départ, arches Monster,
  paddock de ZION 2025 ; grilles de départ, cadres qui tombent, poteaux ronds, cage du drapeau de Saint-Georges ; tremplins
  acier ramp_50 de Ryan ; murets blancs le long des whoops. Tuff blocks à retoucher par Ryan dans l'éditeur.
- **Stade** : public de Saint-Thibéry dans les tribunes (`public.py`, 6 415 silhouettes assises).
- Le build a besoin de l'archive ZION extraite dans `refs/zion25_full` (local, pas sur GitHub). Fichiers ZION copiés dans la
  piste : usage privé ; pour une version publique, demander l'accord de leur auteur.
- Contrôles : 7 / 7, `validate_mx.py` 0 problème, 0 référence manquante. **Non testé en jeu.**

## Habillage « comme en vrai » (v3, 2026-11-10) — aperçu seulement, pas encore validé par Ryan

Demande : refaire à l'identique des photos du Supercross de Paris (local : `paris2026/refs/photos2025/`) les pubs, tuff blocks,
départ, filets, arrivée, et faire le paddock derrière le départ. Tout ce qui venait de ZION est retiré de la piste.

- `habillage.py` (placement, remplace `objets.py` dans le build), `hab_objets.py` (modèles), `hab_kit.py` (maillage, logos).
- Le tracé 2026 n'est pas celui des photos : chaque sponsor est posé à l'endroit équivalent (plan en tête de `habillage.py`).
- Formes créées d'après les photos (pas des mesures) : demi-tonneaux, murs bâchés, filets, bâche AMV, rampe + coins Honda,
  habillage Venum des tremplins, portique Minerva Oil (podium avec collision), arche 50 Factory, bandeau START, panneau FINISH
  suspendu, canettes Monster, camions du paddock (provisoires).
- Logos **redessinés en texte** faute de fichier officiel : AMV, Venum, Minerva Oil, Thor, Five, Moto Verte, « R » des whoops.
  Les autres viennent de `assets/logos/` ou des textures de l'archive ZION (usage privé).
- Paddock : 10 camions sur la bande de 22 m entre le départ et le mur de scène (l'arène n'a pas plus de place sans l'agrandir).
- Aperçu : `py -3.12 -I paris2026/apercu_habillage.py` puis `py -3.12 -I stade_paris/src/preview_web.py` ->
  `apercu/vue_dessus_habillage.png`, `apercu/habillage_3d.jpg`, aperçu 3D `stade_paris/build/web`.
- Contrôles : 7 / 7, `validate_mx.py` 0 problème, 441 objets. **Non testé en jeu.**

## Habillage v6 (2026-11-10, liste de `docs/14_suite_paris_autre_pc.md`)

- a. Boudins des whoops : FLY Racing rouge, logo blanc (`assets/logos/fly_racing_white.png`).
- b. Tuff blocks comme ZION 2025 (relevé de ses 322 blocs) : une rangée au bord de chaque couloir (14,5 ft de l'axe), un bloc tous
  les ~12,4 ft, sur le plat comme sur les bosses, le long du bloc dans le sens du couloir (v6 avait trop de blocs, en travers).
- c. Virages à berm : blocs gris unis au bord extérieur du couloir (un peu dans le virage), mur à sponsor en haut du berm, filet juste derrière.
- d. Bâche AMV sur les deux côtés de la réception du saut du milieu, à sa forme (dessus plat + pentes amont / aval).
- e. Arche 50 Factory sur la première bosse de L6.
- f. Rampe acier + coins Honda du saut d'arrivée : retirée (Ryan : « enlève ce truc »).
- g. Boudins Motul du couloir de départ retirés.
- h. Long tuff block des deux côtés de la ligne de départ reprise par le tour : enterré au départ, il sort du sol 20 s après la
  chute de la grille (`nofrills.js`, `mx.move_statue`, même méthode que les boudins de départ de Saint-Thibéry). Sans chute de
  grille (entraînement libre) il reste enterré. **À vérifier en jeu : que sa collision suit bien le déplacement.**
- i. Paddock : 10 camions sur une rangée, perpendiculaires au mur de scène, nez à 3 ft du mur, arrière vers la piste.
- j. **Pas fait** : vrais logos AMV, Venum, Minerva Oil, Thor, Five, Moto Verte (téléchargement à confirmer par Ryan).
- Contrôles : 7 / 7, `validate_mx.py` 0 problème, 18 248 références, 0 manquante, 706 objets. **Non testé en jeu.**

## v9 (2026-11-10, retours de Ryan après son test en jeu)

Terrain (`layout_paris.py`) :
- Après le saut du milieu : T_C3 + colonne + T_D remplacés par **un seul 180 à gauche** (rayon 32 ft = moitié de l'écart L3 / L2),
  sommet 6 ft plus loin, saut du milieu avancé de 8 ft (place pour poser puis tourner), un seul poteau à l'intérieur.
  Berm = gros croissant JGSX décalé au rayon 32 ft (`engine.render_berm_stamp(r_shift=)`), sur la 2e moitié seulement : le départ
  rejoint le tour au sommet par l'extérieur de la 1re moitié (comme avant par la colonne).
- Avant le saut du milieu : la fine arête de 0,4 ft au début de la mesure ZION (« trou, truc cassant ») est retirée.
- L2 : 7 bosses identiques (Arlington x1,35, 5 ft), **même écart partout** (5 ft au sol, ~33 ft de crête à crête), la 1re à 3 ft de
  la sortie du 180 (pas d'élan). But : triple d'entrée, quad dur ensuite. **À juger en jeu** (pas de simulation de saut ici).
- LR : remis comme en v6 (roller, longue bosse, 2 bosses) - « tu as enlevé l'appel, remets comme avant ».
- L5 : le petit double avant l'arrivée remplacé par un roller de 2,2 ft ; triple d'arrivée x0,87 en hauteur et x0,93 en longueur
  (8,7 / 5,2 / 9,7 ft).
- Berms des 180 x1,15 (« un petit peu plus gros, faut pas abuser ») ; 90 inchangés.

Habillage (`hab_objets2.py`, nouveaux modèles fermés, faces vers l'extérieur) :
- Tuff blocks **pleins** (bloc de mousse arrondi, bouts fermés) au lieu des demi-tonneaux creux.
- Virages : ballots ronds sous bâche grise + coussin du sponsor (photo 12), sur 70 % des 5 grands virages seulement, abaissés au
  point le plus bas sous leur emprise, jupe de bâche de 3 ft (plus rien en l'air). Plus de murs aux 90 près du départ.
- Filets : sur le sol plat juste derrière le berm (droits).
- Whoops : boudins FLY en ligne droite, bout à bout, sur le plat après le pied des whoops, à la même distance tout du long.
- Bâche AMV dessinée sur le **vrai bord** du saut du milieu (relevé dans le terrain), contre le flanc, des deux côtés.
- Portique Minerva Oil et arche 50 Factory : volumes fermés (plus de faces manquantes), arêtes chanfreinées.
- Départ : plus de mur de fond derrière les grilles (« ça me bloque la vue »). Bandeau START gardé.
- Long boudin noir FLY / RBT / SX TOUR : visible en entraînement libre ; en course, enterré 20 s après la chute de la grille.
- Camions : tracteur (cabine, déflecteur, pare-brise, rétros, réservoirs), remorque à angles arrondis et jupes, vraies roues.
- Vrais logos pris dans les textures ZION 2025 : AMV, Kawasaki, KTM, Triumph (en plus de Honda, Yamaha, Seong, Monster, Automoto).
  Encore redessinés : Venum, Minerva Oil, Thor, Five, Moto Verte.
- Vérification : `rendu_objets.py` / `rendu_scenes.py` (rendu logiciel, l'aperçu WebGL était bloqué) -> `apercu/v9_*.png`.
- Contrôles : 7 / 7, `validate_mx.py` 0 problème. **Non testé en jeu.**
