# 12 — Objets USLAND faits maison (v12) : specs, normes, règles de design

Tous ces objets sont **créés de zéro** par `scripts/props_usland.py` (aucun fichier JGSX copié). Ils remplacent peu à peu
l'habillage JGSX (doc 11) pour pouvoir publier les pistes. **Non testés en jeu.**

| Objet | Fichiers (`assets/props/`) | Taille (x × y × z ft) | Triangles |
|---|---|---|---|
| Hospitality (remorque 2 niveaux, côtés ouverts, escalier, tapis rouge) | `hospitality_usland.jm/.png` | 34,9 × 14,2 × 44 (escalier compris) | ~4 000 |
| Pick-up double cabine noir, benne longue et creuse | `pickup_usland.jm/.png` | 7,7 × 6,8 × 21,5 | ~4 500 |
| Arche FINISH (toujours noire) | `finish_arch.jm/.png` | 49,4 × 51,4 × 16 | ~2 100 |
| Portique de départ (treillis, drapeaux, enseigne) | `start_gantry.jm/.png` | 98,8 × 20,9 × 8,4 | ~5 300 |
| Grille de départ (plaque noire pleine + icône U, tube rouge) | `start_gate.jm/.png` | 3,2 × 1,7 × 0,1 | ~500 |
| Grate de départ en croix (1 par grille) | `start_grate.jm/.png` | 2,7 × 0,1 × 9,4 | ~110 |
| Vélo de route rouge « S-WORKS » sur home-trainer (dans la benne des pick-ups) | `bike_trainer.jm/.png` | 2,2 × 3,3 × 5,7 | ~5 200 |
| Bannière 12 × 3 ft | `banner.jm` + `banner_<icon/rbt/fox/usland>.png` | 12 × 3 × 0,1 | 12 |

Logos : vrais fichiers fournis dans `assets/logos/` (USLAND, icône U `l1_*.jpg`, RBT, FOX, étoile). Photos de référence :
`docs/img/refs_paddock/` (gardées en local, hors Git : elles ne sont pas à nous).

```bash
python3 scripts/props_usland.py          # régénère assets/props/ + contrôle les specs (s'arrête si une règle casse)
python3 scripts/preview_props.py         # aperçu 3D -> viewer/props_preview.html (à regarder AVANT de mettre en jeu)
```

## 1. Specs pour que ça rentre bien en jeu (MX Simulator)

Ce qui est sûr vient des fichiers des références (doc 01) ; ce qui est *(à vérifier en jeu)* n'a pas encore été vu dans le jeu.

**Unités et axes**
- 1 unité = 1 pied (ft). y vers le haut. Dans un modèle : **+z = l'avant** (véhicule) ou le sens de la course (arche,
  portique, grates), x = le côté.
- Ligne `statues` : `[x y z] angle @USLAND2026SX1/statue/<modèle>.jm @USLAND2026SX1/statue/<texture>.png null`.
  **L'axe +z local va vers (sin a, cos a)** : `a = atan2(fx, fz)` (`props_place.statue_ang`), **vu en jeu (v12b)**, l'inverse de la
  convention des grilles de départ (`timing_gates`, pilote vers (−sin a, −cos a)). L'axe +x local va vers (cos a, −sin a).
- Le jeu pose l'objet sur le sol sous son **origine** : la mettre sur du plat (arche : au pied d'un poteau, sinon elle flottait
  de toute la hauteur du saut).
- `y` = sol local sous l'objet (le plus bas sous ses appuis ; l'objet descend sous le sol si besoin, jamais en l'air).

**Format `.jm` (JM1, texte)**
- `JM1`, une ligne **matériau** de 5 nombres, `nb_sommets nb_triangles`, puis un sommet par ligne `x y z nx ny nz u v`, puis les indices.
- Ligne matériau (lue sur les modèles JGSX, sens déduit) : puissance spéculaire, force, couleur r g b. Ex. `transit`/`semi_1`
  `50 1 1 1 1` (brillant), `gate01` `16 1 0.35 0.35 0.35`, `chainlink` `5 0.5 0 0 0`, `bobcat` `0 0 0 0 0` (mat).
  Les nôtres : `props_usland.MATERIAL` (brillant pour hospitality / pick-up / vélo, mat pour le reste).
- Textures en plus, même nom + suffixe : `<texture>_spec.png` (zones brillantes, gris = force) et `<texture>_norm.png` (relief),
  comme `gate01_spec.png`, `transit_spec.png`. On génère les `_spec` (`SPEC`) ; les `_norm` pas encore.
- Faces dans le sens direct vues de l'extérieur : `cross(b−a, c−a)` dans le sens de la normale.
- Normales unitaires, UV dans [0, 1], `v = 0` = ligne du **bas** de l'image.
- Une seule texture par modèle. Les couleurs unies = petits carrés « palette » en bas de la texture.

**Textures**
- PNG RGB, **carrées, puissance de 2, 2048 max** (512 / 1024 / 2048).
- Dessiner chaque face à ses **vraies proportions** puis la caser dans l'atlas, sinon les logos sont déformés.
- Densité visée : ≥ 35 px/ft pour les faces avec texte ou logo.
- Texte lisible des deux côtés : même sens d'UV que le tuff USLAND *(à vérifier en jeu : texte en miroir = inverser u)*.

**Ombres et matière (le jeu ne fait pas d'ombres sur les objets)**
- Couleurs unies : 4 teintes « cuites » par couleur (dessus 100 %, côté 84 %, côté près du sol 66 %, dessous 48 %),
  choisies automatiquement par face (`Mesh._shade`).
- Faces dessinées : dégradé plus sombre vers le sol (`panel(..., ao=0.22)`).
- Grain **léger** et seulement sur les matières mates (grates, grilles, portique, arche : `MATTE`). Rien sur ce qui brille
  (peinture, vitres, chrome, bannières imprimées) : le pick-up noir brillant a des reflets peints (`gloss`), les vitres leurs reflets.

**Budgets (contrôlés automatiquement)**
- Véhicules ≤ 6 000 triangles (hospitality ≤ 8 000), arche ≤ 3 000, portique ≤ 6 000, petits objets ≤ 100.
- Pas de collision (`null`) pour le décor. Seuls les tuff blocks ont une forme `.shp`.

**Placement (contrôlé par `validate_sx.py` / `props_place.py`)**
- Tout objet à **≥ 17 ft de toute ligne de course**, sur sol plat (≤ 0,5 ft de pente sous un véhicule).
- Arche : poteaux à 22 ft du centre du couloir (au-delà des murs latéraux de 4 ft des sauts), socles ≤ 1,2 ft de pente,
  bas de la poutre ≥ 20 ft au-dessus de la crête du saut d'arrivée (21–30 ft sur SX1-3).
- Portique de départ : centré sur la rangée de grilles, même angle que les grilles, treillis à 7,5 ft.
  Pas de panneau posé au sol au milieu (il bloquerait des grilles).
- Grilles : même position / angle que les lignes `startinggate` (remplacent `gate01`, forme de collision `@startgate.shp` gardée).
  **Convention `gate01` (mesurée dans l'historique Git, commit 110c3c3)** : la grille est modélisée **couchée à plat vers +z**,
  charnière sur l'axe x à l'origine, 3,14 × 2,37 ft ; c'est le jeu qui la relève et lui donne son angle. La nôtre suit la même
  convention -> même angle que JGSX en jeu (l'aperçu la montre relevée à ~20°, valeur indicative). Plus large que gate01 :
  3,75 ft (0,25 ft entre deux grilles), 2,30 ft de long.
- Grates : une par grille, même angle, découpées d'une seule tôle en croix (étroite / large aux pieds / étroite), petits losanges,
  9,8 ft, sol plat derrière (vérifié SX1-3). Grilles reliées entre elles par un tube rouge continu (charnière de 4 ft = le pas).
- Vélo : dans la benne de chaque pick-up (ridelle ouverte), tête-bêche (roue avant côté hayon), sur le plancher
  (`props_place.bike_in_pickup`) ; vraie roue arrière sur un petit home-trainer, cale sous la roue avant.
- Drapeaux / commissaires ≥ 20 ft des lignes de course. Le commissaire d'arrivée ne doit pas tomber sur un poteau de l'arche.

## 1 bis. Ligne d'arrivée SX1 déplacée (v12)

- Arrivée de SX1 sur la **crête de la première bosse du step-up du couloir D** (Arlington g30, comme le double d'arrivée JGSX) :
  `layouts_sx.sx1()` -> `finish=('SX1-D step-up, triple on table (longer), off', 0)`. L'arche est centrée dessus (appel du saut).
- Les portes se recalculent sans les archives : `python3 scripts/regen_timing.py SX1` (code des portes déplacé dans
  `scripts/timing.py`, utilisé aussi par `export_sx.py`). Le commissaire d'arrivée est à 21,5 ft du couloir, 6 ft avant le poteau.
- Contrôles faits : socles ≤ 1 ft de pente, poteaux à 19 ft des trajectoires, 21 ft libres au-dessus de la crête (8,8 ft).
  `validate_sx.py` (build complet) à relancer sur le PC qui a les archives.

## 2. Remplacement de l'habillage JGSX (1 pour 1, mêmes places, mêmes angles) — **posé** (`scripts/place_props.py`)

`place_props.py` est lancé par `make_all.sh build` juste après `dress_sx.py`, et marche aussi seul sur les pistes déjà construites
(sans les archives). Il est relançable (retire d'abord ce qu'il a posé). Le hospitality est décalé de 13 ft vers l'extérieur du
grillage et tourné pour que son entrée parte vers l'extérieur (sens de l'axe x local à vérifier en jeu). Comptage : 3 hospitality,
9 pick-ups + 9 vélos, 24 bannières, 3 arches, 3 portiques, 66 grates, 66 grilles USLAND.

| JGSX (doc 11) | Remplacé par | État |
|---|---|---|
| `semi_1` (semi-remorque) | hospitality USLAND + 8 bannières | posé |
| `transit` ×3 (vans) | pick-up USLAND ×3, chacun avec un vélo sur home-trainer dans la benne | posé |
| — (pas de banderoles chez JGSX) | bannières USLAND / U / RBT / FOX sur les grillages | prêt |
| repère d'arrivée (aucun objet) | arche FINISH | posé |
| — | portique de départ + grates | posé |
| `gate01` (grilles de départ) | grille USLAND (plaque noire + U, tube rouge) | posé |
| `watertruck`, `watertank`, `matrixa2` | pick-ups USLAND + vélo (v12b) | posé |
| `dozer`, `bobcat`, `ezup` | retirés (v12b) | fait |
| grillages, poteaux d'éclairage, cônes, decals, sol, ciel | à faire pour une version publique | à faire |

## 3. Règles de design (retours de l'utilisateur, à respecter pour tout nouvel objet)

Ces règles viennent des retours sur la v12. Les relire **avant** de dessiner un objet.

**Formes**
- Jamais de « boîtes carrées » : arrondir les angles (`Mesh.rbox`, `_bevel`), carrosseries en sections arrondies (`_loft`).
- Réaliste et épuré : proportions d'un vrai objet (prendre une photo de référence et ses dimensions).
- Roues : pneu bombé avec sculptures + jante à rayons en creux (`Mesh.wheel`), jamais un simple cylindre.
- Les volumes « utiles » sont creux et crédibles : benne de pick-up creuse avec passages de roue, côtés de remorque
  qui s'ouvrent sur toute la longueur.
- Pas de structure inutile derrière un panneau (pas d'« étagère » de treillis derrière une enseigne).

**Logos et texte**
- Peu de logos, bien placés : **centrés, même taille, alignés, symétriques**. Pas de logos partout ni dans tous les sens.
- Sur des vitres : **fond gris, logo noir** (pas de logo en couleur sur le vitrage).
- **Jamais deux USLAND côte à côte** (logo USLAND et icône U séparés).
- Ne jamais déformer un logo : utiliser le vrai fichier et garder ses proportions.
- Textes (noms des pilotes, coach) centrés dans leur panneau.
- L'étoile est en **gris clair** (150, 154, 160), comme les petits titres (« PILOTES »), quand elle est sur le hospitality.
- L1 = l'icône U d'USLAND (pas un sponsor). Pas de KTM, pas de BP. Sponsors : RBT, FOX.
- Pas de visage d'une vraie personne dans le décor.
- Enseignes (arche, portique) : plaque **découpée autour du logo** (`cutout`), jamais un carré noir autour ; les morceaux
  sont **reliés entre eux** (U soudé au USLAND) et **fixés** à un support (socle posé sur la poutre / le treillis), jamais dans le vide ;
  logo lisible **des deux côtés** = **deux plaques** découpées (une par côté, chacune à l'endroit) séparées de 1 à 1,6 ft et
  reliées par des tiges métalliques + croisillons (`sign_pair`), jamais une seule plaque imprimée des deux côtés.
- Grilles de départ **penchées** vers les pilotes (15°, comme en vrai), arrondis soignés (tube et plaque), reliées par un tube.
- Grain : très léger, seulement sur les matières mates ; ce qui brille (carrosserie, vitres) reste lisse avec des reflets.
- Matière réaliste : grain / rugosité sur toutes les textures, ombres cuites sur chaque objet (le jeu n'en fait pas).
- Une pièce découpée dans une tôle = un seul morceau (pas de barres entre les parties). Grillages : petits losanges.
- Aucun logo à l'envers ni en miroir : vérifier **chaque face** à l'écran (avant, arrière, côtés).
- Quand une forme précise est demandée (ex. le vélo de la photo) : reprendre exactement la silhouette (cadre, guidon, selle).
- Marques demandées explicitement (S-WORKS, nœud Chevrolet, FOX) : faites pour l'usage privé, à retirer ou à faire autoriser
  pour une version publique.

**Copie d'une photo de référence**
- Reprendre la forme ET les couleurs de la photo, en remplaçant seulement les logos demandés.

**Mise en place**
- Aligner les objets entre eux (bannières parallèles au hospitality, ouvertes devant le tapis rouge) ; bannières : les 4 dans le
  même ordre de chaque côté (motif qui se répète).
- Arches d'arrivée : toujours noires. Enseigne du portique surélevée sur une tour en treillis, au-dessus des drapeaux.
- Matériaux : brillant = ligne matériau + `_spec` (pas de grain) ; vitres = vraie vitre teintée avec reflets, grande.
- Drapeaux du portique : un peu plus petits, la pointe vers **l'avant** (côté piste), tenue par un petit câble ; bord haut
  légèrement arqué, étoile bien visible (ne pas rogner le drapeau).
- Grilles : pleines (plaque noire) avec tube rouge, **icône U seulement côté piste** (côté pilotes noir uni) ; elles tombent
  en jeu (modèle des lignes `startinggate`, animé par le jeu comme `gate01`). Grates fines en croix (étroites, plus larges aux pieds).
- Vitres de véhicule : un panneau de verre plat posé dans un cadre noir (jamais la texture de verre plaquée sur les coins
  arrondis de la carrosserie) ; lunette arrière plus petite que le pare-brise.

**Méthode**
- Toujours un **aperçu 3D** avant de mettre en jeu, vérifié soi-même dans le navigateur (onglet par onglet) avant de l'envoyer.
- Poser des questions avant un gros changement ; demander les images de référence (une vue « fil de fer » aide beaucoup).

## v12b — tente et camion-citerne

- Tente JGSX (`ezup`) → `tent_usland` (10 x 10 ft, toit bleu marine uni, bandeau : USLAND devant / derrière, RBT et FOX sur
  les côtés). Toit et bandeau du même bleu (le dessous du toit est décalé de 0,06 ft pour éviter le scintillement).
- Camion-citerne JGSX (`watertruck`) **gardé** (demandé) ; l'icône U est un petit modèle à nous (`watertruck_u`,
  `scripts/sticker_usland.py`) moulé sur le haut des deux flancs de la citerne, posé avec la même position / le même angle.
- Matrix, bulldozer, bobcat retirés ; citerne (`watertank`) → pick-up USLAND + vélo.

## v13b — grates reculées, torches sur l'arche

- **Grates** : vu en jeu (capture), la grille tombe **vers l'avant** (côté piste) autour de sa charnière. La grate commence
  donc **0,2 ft** derrière la charnière, pile sous la moto (un essai à 2,5 ft laissait un trou). Longueur 6,8 ft (s'arrête à la roue arrière). Forme : partie étroite courte
  (1,8 ft) devant, large 2,4 x 2,8 ft au milieu (sous les repose-pieds), étroite longue (2,2 ft) derrière. Sol plat sous les 66 grates.
- **Torches** : un petit bâton de flamme (socle noir, tige alu, coupelle noire, 2,85 ft) sur la poutre au-dessus de chaque
  poteau de l'arche FINISH, dans le modèle de l'arche (un objet posé seul serait remis au sol par le jeu). Les flammes de
  `pyro_chalk.py` partent du haut des torches, **seulement quand le vainqueur passe l'arrivée**.

## v13b — stand de bannières, angles

- **Stand** (`props_place.stand_banners`) : ligne de 8 bannières à 29 ft devant la remorque, **centrée sur le tapis rouge**
  (ouverture de 12,4 ft), les 4 dans le même ordre de chaque côté, + **2 bannières en retour** (RBT puis FOX) à chaque bout,
  vers la remorque : 12 bannières par stand. Contrôlé : à ≥ 92 ft des lignes de course, rien à moins de 9 ft, sol plat.
- **Angles** : tous nos objets sont écrits avec un angle entre −π et π (les vélos à a + π = 4,7 / 6,27 étaient de travers
  dans certains pick-ups en jeu).

## v13b — arche ancrée au milieu (vu en jeu : arche SX2 décalée d'un demi-portique)

- En jeu, l'arche SX2 (origine au pied d'un poteau) apparaissait décalée sur le côté, un poteau sur le saut, alors que
  l'aperçu 3D était juste. C'était le seul de nos modèles avec l'origine hors du milieu.
- Maintenant (`props_place.centred_arch`) : un modèle par piste `finish_arch_SXn.jm` (texture `finish_arch.png`), origine au
  **milieu du couloir sur la ligne d'arrivée**, modèle symétrique autour, **abaissé de la hauteur du sol à cet endroit** (crête
  du saut : SX1 8,8 ft, SX2 6,0 ft, SX3 8,8 ft) puisque le jeu pose l'objet sur le sol sous son origine. Pieds des poteaux
  toujours sur le plat à côté du saut. Même rendu dans l'aperçu (vérifié : x 652–702 sur SX2). À vérifier en jeu.
