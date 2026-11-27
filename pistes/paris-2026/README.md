# Supercross Paris 2026 — fiche de la piste

| | |
|---|---|
| Pistes (dans `tracks/`) | `USLANDParis` (version Zion, la plus récente), `USLAND2026SupercrossParis`, `USLAND2026SupercrossParisRF`, `ParisLaDefenseArena` (arène seule) |
| Pour jouer | copier le dossier voulu **et** `USLAND2026SX1` (textures partagées) dans le jeu |
| Code | ce dossier : `layout_paris.py` (tracé), `build_paris.py` / `build_zion.py` / `build_rf.py` (construction), `habillage.py`, `hab_*.py`, `paddock26.py` |
| Arène | `stade_paris/` (La Défense Arena : `stade_paris/src/build.py --mx`, à lancer une fois avant les builds) |
| Références | `refs/` : photos 2025, paddock 2026, archive ZION 2025 extraite (versionnées) |
| Reprendre sur un autre PC | [docs/pistes/14_suite_paris_autre_pc.md](../../docs/pistes/14_suite_paris_autre_pc.md) |

Reconstruire, depuis la racine du dépôt :

```bash
py -3.12 -I pistes/paris-2026/stade_paris/src/build.py --mx   # arène (une fois)
py -3.12 -I pistes/paris-2026/build_zion.py                   # -> tracks/USLANDParis
py -3.12 -I pistes/paris-2026/build_paris.py                  # -> tracks/USLAND2026SupercrossParis
```

---

# Relevé du tracé (avant construction)

Source : 5 visuels officiels du tracé (local seulement : `refs/`, pas sur GitHub). Relevé : `lecture_photos.json`,
plan et tableau : `py -3.15 -I pistes/paris-2026/lecture.py` → `refs/plan_annote.jpg` + `tableau.md`.

## Méthode

1. **Échelle** calée sur JGSX : pas des whoops 30,2 px = 20,1 ft (JGSX 20 ft), largeur des couloirs 55-57 px = 37-38 ft
   (JGSX 30,4 + 2 × 4 ft) → **0,665 ft/px**.
2. **Sens de la course** : la ligne rouge du visuel 1 est reportée sur la vue de dessus par homographie calée sur les
   9 poteaux blancs (erreur < 2 px).
3. **Obstacles** : début / fin lus à la main sur la vue de dessus agrandie × 4 (± 2 px ≈ ± 1,3 ft) ; type (single, table,
   whoops…) lu sur les vues de biais ; chaque obstacle reçoit l'unité JGSX mesurée la plus proche en longueur (`commun/lib/sx_units.json`).

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
py -3.15 -I pistes/paris-2026/stade_paris/src/build.py --mx
```

```bash
py -3.15 -I pistes/paris-2026/build_paris.py
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

Demande : refaire à l'identique des photos du Supercross de Paris (local : `pistes/paris-2026/refs/photos2025/`) les pubs, tuff blocks,
départ, filets, arrivée, et faire le paddock derrière le départ. Tout ce qui venait de ZION est retiré de la piste.

- `habillage.py` (placement, remplace `objets.py` dans le build), `hab_objets.py` (modèles), `hab_kit.py` (maillage, logos).
- Le tracé 2026 n'est pas celui des photos : chaque sponsor est posé à l'endroit équivalent (plan en tête de `habillage.py`).
- Formes créées d'après les photos (pas des mesures) : demi-tonneaux, murs bâchés, filets, bâche AMV, rampe + coins Honda,
  habillage Venum des tremplins, portique Minerva Oil (podium avec collision), arche 50 Factory, bandeau START, panneau FINISH
  suspendu, canettes Monster, camions du paddock (provisoires).
- Logos **redessinés en texte** faute de fichier officiel : AMV, Venum, Minerva Oil, Thor, Five, Moto Verte, « R » des whoops.
  Les autres viennent de `commun/assets/logos/` ou des textures de l'archive ZION (usage privé).
- Paddock : 10 camions sur la bande de 22 m entre le départ et le mur de scène (l'arène n'a pas plus de place sans l'agrandir).
- Aperçu : `py -3.12 -I pistes/paris-2026/apercu_habillage.py` puis `py -3.12 -I pistes/paris-2026/stade_paris/src/preview_web.py` ->
  `apercu/vue_dessus_habillage.png`, `apercu/habillage_3d.jpg`, aperçu 3D `pistes/paris-2026/stade_paris/build/web`.
- Contrôles : 7 / 7, `validate_mx.py` 0 problème, 441 objets. **Non testé en jeu.**

## Habillage v6 (2026-11-10, liste de `docs/pistes/14_suite_paris_autre_pc.md`)

- a. Boudins des whoops : FLY Racing rouge, logo blanc (`commun/assets/logos/fly_racing_white.png`).
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

## v22 (2026-11-25, version Zion) : paddock 2026 d'après les photos de Ryan + écran géant refait

Photos et logos envoyés par Ryan : `refs/paddock2026/` (photos 1-7 du paddock, Iveco KTM, semi Bud Racing, logos officiels).
Code : `paddock26.py` (modèles + plan), appelé par `build_zion.export_zion` à la place de `semis_jgsx` ; peut aussi être appliqué
seul à la piste déjà construite : `py -3.15 -I pistes/paris-2026/paddock26.py` (idempotent).

Lecture des photos (validée par Ryan) : photo 1 prise depuis le bout côté **whoops** (z grand), l'écran (mur de scène) à droite ;
allée parallèle au mur (x 772-800 ft).
- Rangée mur, depuis le bout whoops : 4 tentes Triumph + barrières bâchées + 3 flammes, 6 box motos (barrières Vauban) à leur
  droite, Airstream (loueur Eden Street) devant les box, remorque Suzuki **en travers, avant vers la piste** (peau JGSX repeinte :
  bandeau jaune S SUZUKI, MOTUL, bas vitré) + auvent, moquette bleue, 3 bannières jaunes (Charles Lefrançois, Jason Anderson 21,
  Ken Roczen 94) et 3 motos ; zone Honda : bâtiment à étage (vitrage rouge lumineux, garde-corps HONDA) + stand moquette rouge,
  3 murs HONDA lumineux, servantes rouges, 3 motos dont Shimoda 30 + panneau Jo Shimoda ; van noir Monster Yamaha + tente et
  flammes YCF.
- Rangée piste : van blanc (MAN TGE), 2 canettes Monster géantes (photo de la canette plaquée), Iveco Daily Red Bull KTM
  **porte latérale ouverte** (servante Beta, placards, étagère) + 2 tentes KTM, panneau ACCÈS PISTE / TRACK ACCESS au passage vers
  la piste, tente Monster, semi Bud Racing (Kawasaki, KX, filets verts) cabine vers le bout opposé.
- Écran : 64 x 21,8 m (de 8,7 à 30,5 m de haut) + 2 écrans verticaux 9 x 16 m à 4 m de chaque côté, matériau non éclairé
  (toujours lumineux), visuel Supercross Paris sur fond « coucher de soleil » ; ancien écran 115 m et écrans latéraux retirés.
- **Aucune personne** (ni foule, ni photo de pilote, ni visage sur l'écran).
- Retirés : les 7 semi-remorques JGSX de la v21d.
- Formes CRÉÉES d'après les photos (pas des mesures), dimensions ESTIMÉES (tailles courantes : tente 3 x 3 / 3 x 4,5 / 3 x 6 m,
  van 7,2 m, Airstream 27 ft, barrière Vauban 2 m, canette 1,8 x 4,9 m). Motos simplifiées (low-poly). Pas de collision (hors piste).
- Pas faits (pas assez visibles / marque illisible) : gonflable Five, camion rouge, remorque noire, tente arche noire, le fond de
  l'allée après Honda, le grand logo blanc à l'arrière du semi Bud. Entre Honda et YCF / entre ACCÈS PISTE et Monster : vide
  (rien de visible sur les photos).
- Aperçus (rendu logiciel, pas le jeu) : `apercu_zion/v22_paddock_*.png` (dessus annoté, points de vue des photos 1 et 2, KTM,
  Suzuki + Airstream, Honda, depuis la piste). `validate_mx.py` : 0 problème. **Non testé en jeu.**

### v22b (même jour, Ryan : « pas bien placés, très vide »)
- Relu sur les photos : Suzuki (z 735) et Honda (z 612-700) remontés sous l'écran ; bâtiment Honda EN TRAVERS, façade et balcon
  HONDA vers le bout whoops (vus derrière le Suzuki sur la photo 1), stand devant avec 3 murs lumineux, barrières HONDA le long de
  l'allée et devant le stand.
- Côté piste en 3 files comme la photo 1 : canettes contre la piste, van blanc + grande remorque noire, KTM (Iveco + 2 tentes) ;
  tente arche noire devant ; barrière numérotée 6-8-10-12 au bout du paddock.
- Remplissage SANS marque (accord de Ryan) : remorques noire et rouge (peau JGSX unie), tentes blanches, tables hautes, groupes
  électrogènes, caisses, barrières. 161 objets, `validate_mx.py` 0 problème. **Non testé en jeu.**
- Le build complet (`build_zion.py`) ne passe pas sur ce PC : il lui manque `C:\Users\ryan\rf_ext\sx2026r01anaheim1\textures`
  (sable RF Anaheim). Le paddock s'applique seul sur la piste construite : `py -3.15 -I pistes/paris-2026/paddock26.py`.

### v22c (Ryan : « camion Suzuki dans le mauvais sens, motos de l'autre côté, petit passage entre les motos Suzuki et Honda »)
- Remorque Suzuki retournée : avant vers le mur, arrière (portes + rampe) vers l'allée.
- Stand Suzuki (auvent, moquette, bannières Lefrançois / Anderson 21 / Roczen 94, 3 motos) côté Honda ; passage libre de ~14 ft
  entre les motos Suzuki et les barrières HONDA. Aperçu : `apercu_zion/v22_paddock_passage_suzuki_honda.png`.

### v22d (Ryan : « le camion Honda est contre l'écran, dans l'autre sens ; il y a encore une petite allée entre l'écran et les camions »)
- Bâtiment (camion à étage) Honda PARALLÈLE au mur (x 838-864, z 622-690), façade et stand vers l'allée ; barrières HONDA le long
  de l'allée (entrée au milieu) et devant le stand (côté passage Suzuki).
- Rangée mur arrêtée à x = 864 : ruelle de ~12 ft devant l'écran. Allée centrale resserrée (x 769-789, 20 ft), rangée piste
  x 736-769 ; remorque noire, canettes, ACCÈS PISTE et remorque rouge recalés en conséquence. 163 objets, `validate_mx.py` 0 problème.

### v22e (dessins de Ryan : `refs/paddock2026/dessin_ryan_dessus.png`, `dessin_ryan_photo1.png`)
- Airstream dans le sens de l'allée devant le Suzuki ; 3 motos Triumph (noires) à son ancienne place.
- Box motos : rangées droites, toutes pareilles, collées, ouvertes sur un chemin (box 13,2 x 6,6 ft, une moto en long par box) :
  3 rangées x 4 box à droite de Triumph, 3 rangées x 3 box côté photo 2 (à la place des vans blancs).
- Bus noir (MAN, comme la photo de Ryan) à côté du KTM, plus de remorque noire ; canettes Monster 7,3 m (plus hautes que les camions).
- Côté photo 2, rangée mur : stand Yamaha GSM (bus bleu + tente + 2 motos), RFN (bus noir à panneau blanc + tente : couleurs du
  logo, rien trouvé sur leur stand), Sedna (bus turquoise / noir + tente), YCF agrandi (2 tentes, bus bleu, flammes). Logos
  envoyés par Ryan (`refs/paddock2026/logos/gsm.png`, `sedna.png`, `rfn.png`). Van noir Monster Yamaha retiré.
- Suzuki : la moto de Lefrançois remplacée par une Roczen 94.
- Motos : toujours nos motos simplifiées. Les livrées d'équipe du jeu (pack AMA 2026, dont Roczen) sont protégées (`.png.scram`) :
  pas utilisables. 207 objets, `validate_mx.py` 0 problème. **Non testé en jeu.**

### v22f (dessins + photos + vidéo YCF de Ryan : `refs/paddock2026/dessin_ryan_*2.png`, `p8_*`, `p9_*`, `video_ycf/planche.png`)
- Box : 2 rangées face à face (motos face à face, chemin de 8 ft), la 3e rangée enlevée (« autre chose » à venir), aux 2 endroits.
- Gant gonflable Five (rouge, FIVE sur l'index, logo 5 sur la paume) à côté du van blanc ; forme créée.
- Remorque rouge -> camion Milwaukee (logo de Ryan) + tente rouge ; ensuite 2 bus Stark Varg (logo or) + 3 tentes noires STARK avec
  une moto dessous (motos noires : la Stark Varg du jeu introuvable dans les fichiers) ; 3 motos vertes devant Bud Racing.
- YCF d'après la vidéo : camion blanc « ENJOY YOUR RIDE » (déco bleu / rouge / noir), moquette bleue avec 18 pit bikes (échelle
  0,72), podium noir YCF ; camion VHR Yamaha (remorque bleue, « VHR » redessiné en texte) + moto Yamaha derrière.
- Honda : 2 camions Honda (blanc / rouge, HONDA, HRC) ; panneaux pilotes Cédric Soubeyras 85, Tom Vialle 16, Jo Shimoda 30 (sans
  photo) avec leurs motos ; la moto de Vialle (16) devant, face à l'allée.
- Camion vitré USLAND (`tracks/USLAND2026SX1/statue/hospitality_usland`, fait par l'équipe pour les pistes de test) à la place de RFN.
- 202 objets, 79 modèles, `validate_mx.py` 0 problème. **Non testé en jeu.**

### v22g (photo 1 recadrée + photo du bus VHR de Ryan : `refs/paddock2026/` ; consignes : « compact, tout rempli, une croix au milieu »)
- Croix : le passage ACCÈS PISTE côté piste (z 700-714) dans l'axe du passage Suzuki / Honda.
- Côté piste tassé après la croix : camion noir à bande rouge (marque illisible, sans marque) | Milwaukee (semi complète, avec
  tracteur) + 2 tentes rouges | stand Monster collé derrière + jeu (moto sur podium) | Stark Varg (3 tentes noires + motos, 2 bus) |
  Bud Racing au fond, reculé de 10 ft, 3 motos vertes.
- Honda tourné vers le passage (photo 1) : panneaux Soubeyras 85 / Vialle 16 / Shimoda 30 avec leurs motos juste derrière les
  barrières HONDA ; 2 minibus Honda blancs (vitres, HONDA, HRC) derrière ; murs HONDA contre le bâtiment.
- Vans plus arrondis (Ryan : « carrés, on dirait un vieux truc »). Box carrés 13,2 x 13,2 ft, 2 rangées face à face, motos vers le
  chemin. Bus VHR Yamaha (bleu, toit blanc, griffe Monster, VHR + Yamaha) en travers entre YCF et Sedna, arrière vers la piste.
  YCF : pit bikes blancs numérotés (7, 4, 16, 21, 30, 56, 31, 64 : vidéo), podiums, camion, 2 tentes ; GSM, USLAND, Sedna tassés.
- Motos : `.scram` des livrées d'équipe NON contourné (protection de l'auteur du pack). Possible : motos d'origine du jeu
  (stockrmz450, stockcrf450, stock450sxf, stockkx450f, stockyz450f, stockfc450 : textures en clair) à assembler (pièces en pieds,
  avant = -z, chacune dans son repère) - pas encore fait.
- 236 objets, 88 modèles, `validate_mx.py` 0 problème. **Non testé en jeu.**

### v22h : vraies motos du jeu (`motos_jeu.py`)
- Modèles moddés installés dans MX Simulator, textures EN CLAIR seulement (les `.png.scram` du pack AMA ne sont pas utilisés), base
  fc450v2016 : KTM USLAND (#202 #151 #16 #348 #47 #9), Honda In So Cal (#16 Vialle, #151 pour Soubeyras et Shimoda), GasGas team,
  Husqvarna violette, DewIsland KTM, KTM USLAND EVO3, CRF of Troy, 2026 RYAN BIKE. Pièces extraites des .saf (cache hors dépôt
  `../mx_motos`), assemblées (cadre, bras oscillant, fourche, roues du jeu), posées sur une béquille noire, une texture 2048 par moto
  (livrée 1792 px + roues), maillage allégé (~35 000 triangles par moto au lieu de ~200 000), `.jm.gz`.
- Posées : 24 motos des box + 3 motos des pilotes Honda. Encore simplifiées (aucune moto en clair de ces marques dans le jeu) :
  Suzuki, Triumph, Kawasaki (Bud), Yamaha (GSM, VHR), Stark Varg, pit bikes YCF, jeu Monster.
- Usage privé (modèles de leurs auteurs). Poids : ~540 000 triangles de modèles pour tout le paddock -> à vérifier en jeu (fluidité).
- `validate_mx.py` 0 problème. **Non testé en jeu.**

### v22i (Ryan : Honda, RBT, Stark, YCF, VHR, Bud)
- Honda : gros camion blanc (porteur, bandeau lumineux rouge en bas, HONDA / HRC) derrière les pilotes ; les 2 bus au fond du stand
  (bandeau rouge lumineux en bas). Forme du porteur créée.
- Camion noir -> camion RBT (semi complète : noir dégradé, grand RBT blanc `commun/assets/logos/rbt_wide.png`, filets rouge / blanc).
- Stark Varg : 2 bus alignés + 5 tentes noires STARK collées, une Stark sous chacune : MODÈLE 3D de la Stark du jeu
  (`%LOCALAPPDATA%/MX Simulator/2023 Stark Varg by Julien113.saf`, base fc450v2016), texture protégée (.scram) NON utilisée -> couleur
  unie gris « Forest Grey ».
- YCF : 2 moquettes imprimées (bleu, traits noirs / blancs, logos), 2 rangées serrées de pit bikes (x 0,62) face à l'allée, 4 podiums
  avec une moto exposée, camion, 2 tentes, flammes. Moto VHR à l'arrière du bus. Motos Bud tournées vers l'allée.
- Écriture des statues : nouvel essai si le fichier est pris par un autre programme (Errno 22 vu 2 fois).
- 266 objets, `validate_mx.py` 0 problème. **Non testé en jeu.**

### v22j (Ryan : « motos mal faites, guidon dans les roues ; pas trop lourd ; motos de Vialle etc. de face »)
- Contrôle des 15 vraies motos de profil et de près : montage correct (guidon au-dessus de la fourche). Le « guidon dans les roues »
  venait des motos des pilotes Honda vues de face : elles sont maintenant dans le bon sens, l'avant vers les spectateurs (passage),
  l'arrière vers le fond.
- Allègement plus fort : ~19 000 triangles par moto (au lieu de ~40 000), blocs vidés par l'allègement non écrits. Paddock :
  ~300 000 triangles de modèles (au lieu de ~580 000). `validate_mx.py` 0 problème. **Non testé en jeu.**

### v22k (Ryan : motos buggées, Stark, Milwaukee, RBT, USLAND, Honda)
- Vraies motos : le « bug » venait de l'allègement (jantes étirées, fourche tordue) -> roues du jeu JAMAIS allégées, reste allégé à
  0,16 ft (~27 000 triangles par moto). Paddock : ~400 000 triangles de modèles.
- Stark Varg : forme du jeu + NOTRE texture peinte pièce par pièce (plastiques blancs, selle noire, cadre gris foncé, bras alu,
  fourche noire) ; la livrée protégée n'est pas utilisée. Motos tournées vers l'allée.
- Milwaukee : camion de vente à 2 niveaux (remorque 48 ft, comptoir côté allée avec étagères d'outils et volet relevé, terrasse
  sur le toit avec garde-corps Milwaukee, escalier à l'arrière) + 2 tentes avec une vraie moto dessous. Forme créée.
- RBT : une moto exposée sur un podium à côté du camion (pas de moto de Théo / RBT dans le jeu : KTM USLAND #9).
- USLAND : retourné, entrée (escalier + tapis rouge) côté allée.
- Honda : gros camion = semi complète comme RBT (blanc, HONDA, HRC, filets rouge / noir, bandeau lumineux rouge) le long du
  bâtiment ; les 2 bus côte à côte juste avant la moquette rouge.
- 268 objets, `validate_mx.py` 0 problème. **Non testé en jeu.**

### v26 (Ryan, vidéos de Roczen à Paris 2026 : L2, virage après l'arrivée, sable)
- **L2 refait** d'après la vidéo (13-21 s) : en vrai 3 sauts, petit double « technique mais propre », triple, triple, puis on roule
  au virage. 8 bosses ZION posées à des crêtes fixées (`LP.L2_V26`, ft depuis la sortie du 180) : 1re bosse plus tôt (crête à
  9 ft au lieu de 12 ; droite 2,3 ft, gauche 0,8 ft qu'on enroule), 2e bosse coupée (droite 3,9 ft = réception du double, gauche
  5,6 ft = appel du triple intérieur), triple 4,8 -> 3,0 (milieu bas) -> 4,4 (réception longue), ~30 ft d'élan, triple 4,8 -> 3,8
  -> 4,4, puis ~20 ft roulés jusqu'au virage. Aucune bosse pointue (hauteur / largeur à mi-hauteur <= 0,31).
- Réglé avec `pistes/paris-2026/sim_rythme.py` : ESTIMATION balistique (point matériel), pas le moteur du jeu. Calée sur l'ancien L2 tel que
  Ryan l'a décrit (double d'entrée tout juste, triple derrière raté de peu, simple-triple impossible à gauche). Nouveau L2 : extérieur
  double-triple-triple passe avec de la marge, double-quadruple et triple d'entrée impossibles ; intérieur simple-triple possible
  mais plus dur (ligne de bon pilote).
- **Virage après l'arrivée** (vidéos 1-5 s et 25-29 s : grande cuvette, mur de boudins, pilote haut dans l'appui) : berm du 1er 90°
  (T_L5a) x1,3 ; mur et filet du virage remontés avec (+2,1 ft). Le reste (bosses, plateau) n'a pas bougé.
- **Sable** (« tout plat, c'est bizarre ») : sable remué, sans ornières ni vagues régulières (petites bosses irrégulières de 1,6 ft
  et ondulations de 6 ft, max ~0,35 ft, moyenne 0, fondu au bord) + grain de sable en décals de 22 ft au milieu de la bande
  (les petites de 10 ft restent sur les bords : le sable s'arrête toujours net).
- Build : le stade de ce PC a été reconstruit d'abord (`pistes/paris-2026/stade_paris/src/build.py --mx`, il datait d'avant la v10) ; les fichiers
  RF du sable ne sont recopiés que si `rf_ext` existe ; écritures avec nouvel essai (fichier verrouillé un instant sous Windows).
- Contrôles 7 / 7. **Non testé en jeu.** Aperçus : `apercu_zion/profils_v21d/profil_L2.png`, `apercu_zion/vue_dessus.png`,
  (aperçu du sable v26 retiré).

### v27 (test v26 de Ryan : « ça va pas du tout » ; « je fais 4-3-1 » ; sable « pas du tout »)
- **L2** : la v26 est abandonnée (`L2_V26 = None`). L2 = les bosses du grand enchaînement L6 (ZION 4,6 / 5,2 / 5,4 / 5,2 / 5,4 ft +
  ses 2 bosses d'après la table 4,7 / 4,9 ft), même écart que L6 (8,4 ft au sol, 5,4 ft entre la 3e et la 4e), la 1re à 0,5 ft de
  la sortie du 180 (« pas le temps de prendre la vitesse » : on rentre en double, pas en triple).
- **Sable** : retour à la v25f (plus de relief remué ni de grandes décals) + couche de sable surélevée de 0,3 ft, bande élargie de
  28 à 40 ft (toute la largeur de la piste en sable : tuiles, décals, couche).
- Virage après l'arrivée : berm x1,3 de la v26 gardé ; « plus long, tourner plus loin » pas encore fait.
- Contrôles 7 / 7, `validate_mx` 0 problème. **Non testé en jeu.**

### v27b (test v27 : « la 1re 3,5 ft, la 2e 4,7 ; 1re plus basse à gauche ; ça fait 2-4, il faut 3-3 ; baisse un peu l'appui après l'arrivée, que ça aille plus loin avant de tourner à gauche »)
- L2 : 8 bosses, 3,5 ft (gauche 2,6) / 4,7 ft, puis 6 bosses ZION de 3,8 ft (`L2_V27B`) rallongées x1,15 (faces 21° au lieu de
  27-28° : envoient moins haut), même écart (3,1 ft au sol) -> double, triple, triple. Choisi à l'œil : `sim_rythme.py` ne colle pas
  au jeu sur ces bosses (il donnait le quadruple de la v27 impossible).
- Après l'arrivée : appui T_L5a x1,3 -> x1,15 ; 2e virage T_L5b rayon 32 -> 26 ft, ligne droite entre les 2 virages 15 -> 21 ft.
- Contrôles 7 / 7, `validate_mx` 0 problème. **Non testé en jeu.**

### v27c (test v27b : « on arrive trop vite, on rentre à fond et on fait 3 ou 4 ; les bosses comme avant ; 1re même grandeur, 2e 4 ft,
### puis 4,5 ; après l'arrivée, plus d'écart entre la 1re et la 2e bosse pour tourner derrière »)
- Virage T_D (180 avant L2) : appui x1,05 -> x0,8 (on y passe moins vite).
- L2 : 7 bosses ZION aux formes de L6 (pas rallongées) : 3,5 ft (gauche 2,6, plus courte : crête à ~10 ft de la sortie), 4,0 ft,
  puis 5 x 4,5 ft ; même écart partout (11,8 ft au sol, ~43 ft de crête à crête).
- Après l'arrivée : 1re bosse 4 ft plus tôt, 2e bosse + plateau 4 ft plus tard (8 ft de plus entre les deux).
- Contrôles 7 / 7, `validate_mx` 0 problème. **Non testé en jeu.**

### v27d (capture en jeu de Ryan : « la bosse dès la sortie du virage, 1re à 20°, double ; 2e 4,3 ft ; 3e 21° pour pas que ça fasse 4 ;
### une bosse de plus : double, 3, 3 ; le virage même hauteur mais moins d'angle ; l'après-arrivée comme avant »)
- Virage T_D (180 avant L2) : hauteur remise (x1,05), berm adouci (flou 2,5 ft, même hauteur max : face moins raide).
- L2 : 8 bosses ZION, même écart (3,7 ft au sol) : 3,5 ft (gauche 2,6) à 20° dès la sortie, 4,3 ft, 4,5 ft à 21°, puis 5 x 4,5 ft.
  Angle réglé en rallongeant la bosse (pente du terrain fini ~0,55 x pente brute, mesuré). Profil : 19° / 25° / 21° / 25°...
- Après l'arrivée : remis comme la v25f (appui, rayon 32 ft, bosses).
- Sable : comme la v27 (v25f + couche de 0,3 ft, bande de 40 ft).
- Contrôles 7 / 7, `validate_mx` 0 problème. **Non testé en jeu.**

## v37 (2026-11-27) : stade resserré, paddock recalé, couloir des rampes, fabrication automatique

- Ryan : « les tribunes sont trop loin sur le côté, 3-4 m max entre la piste et le stade ; tout le stade doit bouger pour garder la
  forme ». Le stade garde x1,55 le long de la piste et passe à x1,3124 en travers (`stade_paris/src/build.py` PLAN_KY, PLAN_DY ;
  `layout_paris.py` PLAN_KZ, ARENA_DY ; `stade_paris/src/arena/plan_scale.py`) : coque, toit et tribunes transformés ensemble,
  décalé de 2,5 ft pour être centré sur la piste. Mur de front des tribunes Nord / Sud à 3,53 m du bord de la piste. Sol 189 x 116 m.
- Paddock (« si t'as pas de place enlève USLAND et RBT, garde le passage Honda / Suzuki, les 2 rangées avec l'allée au centre, serré
  comme avant ») : `paddock26.v37_repack` recale les positions v35 dans le sol resserré, chaque stand d'un bloc (taille réelle des
  modèles), écarts réduits à 2 ft, programme linéaire ; USLAND et RBT enlevés ; van blanc et tente arche au nord du couloir.
- Couloir des rampes freestyle (dessin de Ryan) de (747, 685) à la rampe (567, 675), 16 ft, libre ; 2 canettes Monster au plus près
  des points de Ryan, sans toucher un camion.
- Fabrication automatique : `commun/tools/maj_paris.ps1` + hook `.githooks/post-merge` (voir README racine) ; `build_zion.py --out`.
- Contrôles 7 / 7 ; non testé en jeu.
- Caméras TV (« sur la RF il y a une cam broadcast ») : fichier `cameras` (`build_zion.CAMERAS_TV`) : 8 caméras en haut des tribunes
  et au-dessus du paddock, une par enchaînement dans l'ordre du tour ; chacune des 29 portes de chrono a sa caméra.
- Classement en direct sur l'écran géant (« les noms des pilotes qui défilent, fais les nôtres ») : `tableau_direct.py` -> dalle
  devant l'écran central + `direct.seq` + `frills.js` (même principe que la tour de classement RF, refait à nous, style Supercross
  Paris) : temps / tours restants, top 5, bande à la couleur de la marque, numéro + nom qui défilent. Vérifié avec un faux jeu
  (mêmes appels mx.*, image recomposée), PAS dans le jeu : le format du .seq et les fonctions mx.* viennent de la RF.

