# 07 — Journal de la conversation (pour reprendre comme si on y était)

Ordre chronologique. Les messages de Ryan sont recopiés tels quels (fautes comprises) quand c'est utile pour comprendre l'intention.

## 1. Le cahier des charges

Ryan envoie un cahier des charges détaillé (`docs/00_cahier_des_charges_original.txt`) et les 3 archives
(JGMXDesertSand.rar, JGMXDrDew.rar, JGSX2026TestTracks.rar). En bref :
- faire un **vrai compound MX Simulator** : 1 piste MX + 2 SX ;
- **analyser** les 3 archives, **mesurer** la géométrie fidèlement, faire un **catalogue** des obstacles ;
- tracés **originaux** ; validations ; vues de dessus et profils ; visionneuse 3D ; instructions d'installation ; scripts ;
- **ne jamais prétendre** que les pistes ont été testées en jeu ; dire clairement ce qui est vérifié et ce qui ne l'est pas.

Questions posées par Claude, réponses de Ryan :
- terrain : « 1 terrain, 3 dossiers » ;
- usage : « Usage perso / test » ;
- chronos visés : « 2m20 et 1m » (MX ~2:20, SX ~1:00) ;
- test : « je suis actuellement sur mon téléphone mais je peux faire quand je suis chez mii ».

## 2. v1 livrée

- Formats MXS rétro-ingéniés (doc 01), unités en ft, axes, timing_gates, shading calibré.
- Mesures MX (Desert Sand, Dr. Dew) + SX (JGSX), catalogue de 101 sections (`docs/data/catalogue_obstacles_v1.csv`).
- Compound : MX (grand tracé de 25 coins, sections MX recollées) + SX1 + SX2 (sections JGSX entières), page de rapport + 3D.

## 3. Retour v1 → v2

> « alors le mx ça va pas dutout on laisse tomber on fais que sx pour le moment, le problème avec les sx c'est que y'a pas de vrai
> enchaînement que des triple … fais des plus gros enchaînement et on en fais un 3eme juste les virages y'a un p'tit rebord en
> rentrant mais les virages sont parfait les whoops vrm bien juste les changer entre les piste … triple sur table off quadruple …
> triple triple quadruple … 3 eme piste peut être par dessus le départ … garde toujours les dimension … fais une piste plus longue
> peut être avec une partie sable tranquille »

Ce que ça a donné (v2) :
- MX abandonné.
- Nouvelle bibliothèque d'**unités** (`sx_units.py`) + **composition** (`compose.py`) : on enchaîne des obstacles mesurés avec les
  écarts de sol mesurés → triple sur table off quad, triple-triple-quad, quad-quad, on-off, step-up + triple…
- Whoops différents d'une piste à l'autre (nombre et section d'origine ; en v3 : SX1 12, SX2 7, SX3 10).
- **Rebord** à l'entrée des virages : marche de 0,30 ft due à la découpe des stamps → stamps symétrisés + jupe jusqu'au sol ;
  contrôle automatique ajouté.
- Dimensions gardées (grille, largeurs, espacement, berms).
- SX3 ajouté, plus long, avec une partie sable « tranquille ».

> « envoie moi les map de dessus je peux pas tester pour le moment »  → vues de dessus envoyées.

> « sx 1 vrm bien 2 ça va et 3 il a vrm une forme bizarre quand même »  → SX3 refait en bloc compact.

## 4. Retour v2 → v3

Ryan envoie une photo (`docs/img/photo_sable_reference_utilisateur.png` — c'est le sable de JGSX Glendale) :

> « au départ là où ça fais gauche et un virage à droite à plat je veux un appuie améliore les départ pour qu'on peux vrm faire des
> course genre le sx 2 met le départ au millieu et j'avais vu cette photo jaimes vrm la partie sable tu peux faire un peu comme ça
> aussi dans la piste et voila améliore juste »

Ce que ça a donné (v3) :
- SX1 : le virage plat à droite près du départ (T7) a maintenant un **petit berm** (`small_arl`).
- **Départs** refaits façon JGSX sur les 3 pistes (analyse `starts_ref.py`) : 22 grilles au pas de 4 ft, ligne de départ séparée,
  entonnoir, jonction avant un 1er virage à gros berm, portes du 1er tour ; contrôle « couloir de départ plat » pour les 22 grilles.
- SX2 : refait autour d'un **départ au milieu** (dans l'infield), mêmes enchaînements.
- Sable : **stamps exacts de Glendale** (le J « GL » et le virage en S « GR » en miroir) dans SX3, avec leurs tiles.
- Plus aucun virage plat > 25°.
- Résultats : SX1 2931 ft (~1:04), SX2 2717 ft (~1:03), SX3 3758 ft (~1:13) ; 39/39 contrôles ; non testé en jeu.
- Page publiée (rapport + vues + 3D) : artifact claude.ai `7qxfMC1STYNAEvzgScXRy9` (version 4). Contenu identique à `viewer/`.

## 5. Le repo

> « fait un dossier Git qui s'appelle mxsimtrack. Et tu mets dedans tout ce que tu as analysé des trois terrains pour que la prochaine
> fois qu'on fait des terrains, là, j'ai toute la base, tous les terrains, toutes les boss, toutes les hoops, tout. Il faut tout avoir.
> Et que tu mettes le compound aussi, le track, pour qu'on remette à jour chaque fois sur plusieurs PC. […] faut que ça soit deep. Et
> comme ça, la prochaine fois, c'est comme si on recommençait dans la conve, mais ailleurs, et que la prochaine personne et tout. »

Ce qui a été fait :
- ce repo : mesures (`lib/`, `analysis/`, `docs/09`, `docs/data/`, atlas), pistes (`tracks/`), code (`scripts/`), doc (`docs/`), `CLAUDE.md` ;
- chemins rendus relatifs (`ROOT`, `REF`, variables `MXSIM_ROOT` / `MXSIM_REF`), `make_all.sh`, extraction des archives ;
- vérifié : depuis une copie vierge + archives, la chaîne refait `lib/` et `tracks/` à l'identique, 39/39 ;
- archives de référence **hors Git** (118–330 Mo, pas à nous) : empreintes SHA-256 dans `refs/README.md` ;
- pas pu créer le repo GitHub directement depuis la session (pas d'accès en écriture au compte) → Ryan crée un repo vide
  `ryanop202/mxsimtrack` (privé) et on pousse dessus.

## 6. Premier test en jeu (v3) → v4

Ryan a testé les 3 pistes. Objectif : « qu'on optimise à 200 % pour avoir des pistes vraiment à mon goût ». Ses retours (résumés) :

**SX1** — whoops bien, mais la grosse single juste après : « un petit peu plus loin et peut-être un tout petit peu plus bas pour pas
partir aussi haut » ; enchaînement suivant bien ; virage à droite + step-up bien ; le triple après : « j'aimerais faire un trip sur table.
Off » ; couloir on-off Detroit « vraiment bien, technique » ; gauche, double double, gauche, puis la ligne d'arrivée « c'est long » →
« un petit on-off ».

**SX2** — 1er virage (droite à la sortie du départ) : « tu rentres dans le virage comme si tu rentres à 180 degrés … un petit rebord
qui fait pas rentrer fluide » ; double double ok ; couloir suivant « un peu trop light » → « bosse bosse table bosse table bosse » ;
gros double puis « faire un triple pour sauter dans le virage » ; triple sur table : on garde ; whoops bien mais « la bosse derrière,
enlève-la … tu rajoutes une whoops normale … arrête de faire ces bosses à la fin des whoops » ; en reprenant le départ : « faire un
triple, un peu chaud, assez dur ».

**SX3** — 1er virage gauche bien ; 1er enchaînement « que des petites bosses » et déjà vu sur SX1 → « premier triple bien, ensuite une
grosse bosse, un peu mélangé, des hauteurs différentes » ; le triple d'après : le rapprocher, et « c'est vide après » → « une petite
bosse, tranquille » ; whoops : enlever la bosse à la fin ; la suite bien ; 1re section de sable « tu fais plus proche » ; « le plus gros
problème, c'est que ça va trop loin après la partie de sable … on tourne direct après à gauche, derrière l'appui … c'est là que tu fais
la partie sable … pas une longue ligne droite avant le virage ».

Ce que ça a donné (v4, détail dans doc 05) :
- SX1 : single 5,9 → 5,0 ft, 10 ft plus loin ; triple sur table, off après le step-up ; petit on-off sur la ligne d'arrivée.
- SX2 : T1 = gros berm resserré angulairement (cause du rebord : le berm 180° posé sur un virage de 90° dépassait de 24 ft sur
  la ligne d'arrivée, marche ~1 ft à 12 ft de l'axe) ; E1 bosse-bosse-table-bosse-table-bosse ; gros double + triple jusqu'au virage ;
  8 whoops sans bosse ; triple de gros singles 5,8–6,0 ft sur l'arrivée.
- SX3 : U1 refait (triple, gros single, hauteurs mélangées, triple Detroit rapproché, petite bosse 2,5 ft) ; whoops sans bosse ;
  sable GR 70 ft plus tôt ; U3 ne file plus 400 ft à vide : le J de sable est juste derrière le berm T2 ; combo d'arrivée décalé pour
  finir près de la jonction. Tour 3758 → 3349 ft.
- **Règle retenue : jamais de bosse plus grosse juste après des whoops** (sauf demande explicite, comme le single du SX1 B).
- Interprétation à confirmer par Ryan : SX3 « derrière l'appui » = le J passe juste derrière (à l'ouest) le berm T2.

## 7. Test de la v4 → v5

- **SX1** : « piste 1 c'est bien » ; seul changement : après le triple de la ligne d'arrivée, « enchaîne avec un on-off » pour casser
  la ligne droite → on-off Detroit (g35_2) ajouté.
- **SX2** : le reste bien ; le triple de l'arrivée : « c'est des pains de sucre … garde les bosses d'avant, juste rajoute-en une »
  → retour aux singles du double v3 + 1.
- **SX3** : tracé v4 validé (« c'est bien les changements »). Corrections : après le 1er virage l'enchaînement commençait trop loin
  (v4 l'avait décalé de 80 ft) → remis juste après T1 ; la bosse 4,9 ft = « pain de sucre » → remplacée, motif
  triple – gros single – triple – gros single ; après le sable GR « l'enchaînement commence trop loin, t'arrives beaucoup trop vite »
  et bosses trop similaires → combo dès la sortie du sable + 2 gros singles ; avant le petit triple de l'arrivée « ralentis un peu …
  un saut à plat avant » → table 6,2 ft.
- **Règle** : pas de « pains de sucre » = bosses courtes et pointues (≥ 4,5 ft de haut sur ≤ 35 ft de long : Detroit g0_2,
  Arlington g28_2, Test Track g6_1, Test Track g30_3…). Les gros singles OK = longs (≥ 46 ft : Arlington g37_2, g1_2, Cleveland g29_3).
- À vérifier avec Ryan : « le virage relevé beaucoup trop loin » au départ du SX3 interprété comme « l'enchaînement après le virage
  commence trop loin » (le virage lui-même n'a pas bougé depuis la v3).

## 8. Test de la v5 → v6

- **SX3** « bien », 2 changements : la table avant le triple d'arrivée, « on arrive à donf et ça fait 4 » (table + triple sautés en quad)
  → « faut vraiment être obligé de s'arrêter » → 40 ft de sol plat entre la table et le triple ; 1er enchaînement : triple, grosse bosse
  ok, « rajoute une bosse », recule le triple Detroit + la petite bosse, la dernière bosse (grosse) devient normale et une grosse vient
  après → triple / gros / 4 singles / gros / triple Detroit / petite bosse.
- **SX2** : couloir de gauche sur l'image (W1, quad-quad) → grosses bosses à certains endroits + table au milieu.
- **SX1** : 1er enchaînement (A) : « écarte un tout petit peu le triple d'entrée » (+2,2 ft entre bosses) + une grande bosse dedans.
- Alternative proposée si la table SX3 ne suffit pas : une table longue qu'on ne peut que rouler (non mesurée dans les références).

## 9. Test de la v6 → v7

- **SX3** : 1er enchaînement « fais plus proche le virage, là ça fait 4 d'entrée, pas réaliste » → U1 commence 3 ft après T1 ;
  la table avant le triple d'arrivée « peut être prise à fond » → **un pain de sucre pour vraiment ralentir** (ici c'est voulu).
- **SX1** : 1er enchaînement : la grosse bosse v6 (g1_2) « pas comme maintenant » ; écarter le triple d'entrée (« ça fait 4
  d'entrée ») ; **2e, 7e et dernière bosses grosses**, « comme t'as bien fait sur les autres » (gros singles longs g37_2 / g29_3) ;
  gros double + triple sur table : « ça fait double et 5 » → triple sur table allongé (interprété sur le couloir D : step-up = gros
  double) ; les 4 bosses avant le départ « ça fait 4 » → **1re bosse petite** pour ne pas pouvoir rentrer en double.
- **SX2** : couloir de gauche : **double ligne** sur la 1re bosse (plus petite à droite) pour pouvoir faire simple, double ou triple
  (nouveau : `('split', gauche, droite)` dans `compose.lane`) ; couloir suivant « de la merde, change complet, fais un truc technique,
  pas des bosses simples » → combos mesurés (single+step, kicker sur plateau, on-off) ; couloir du haut (4 bosses) « nul » → gros
  triple ; fin de E1 : +2 bosses, « bouge pas le virage ».
- Leçon : « ça fait 4 d'entrée » = trop d'élan ou bosses trop serrées en entrée → écarter / coller au virage / mettre une petite bosse.

## 10. Test de la v7 → v8

- **SX1** : 1er enchaînement : « tu m'as mis des pains de sucre … mets des bosses normales, on a les grosses c'est bien » → les singles
  courts (g45_2, g62_2, g47_1, ~26 ft de long) remplacés par des singles normaux ; après les whoops, « le pain de sucre recule-le pour
  pas arriver trop vite dedans » → 30 ft de sol et single rond 4,1 ft ; la petite bosse de l'arrivée aussi en 1re bosse du couloir V ;
  arrivée : **double ligne**, plus grosse à droite, pareil à gauche → « et c'est parfait ».
- **SX2** : couloir de droite (E1) : la dernière bosse ajoutée = pain de sucre → single normal ; après le couloir de gauche + droite (W2) :
  « ça va pas du tout, fais un enchaînement que tu retrouves dans les JGSX … pas un truc pas réaliste » → couloir Cleveland g29 copié tel
  quel (écarts compris).
- **SX3** : triple Detroit de U1 « rallonge-le un peu » → 8 ft entre ses deux blocs au lieu de 1,6.
- **Définition mesurable du pain de sucre** : hauteur / largeur à mi-hauteur > 0,31 (singles JGSX normaux 0,23–0,30 ; ceux refusés
  0,37–0,51). Contrôle automatique ajouté dans `validate_sx.py` (40 contrôles).
- Leçon : quand Ryan dit « réaliste », prendre un **couloir JGSX entier** avec ses écarts, pas une combinaison inventée de blocs.

## 11. GitHub + habillage (v9)

- Repo créé par Ryan : `ryanop202/mxsim` (accès Claude donné, poussé le 23/10). Repo **public** → rappel fait : ressources JGSX/JGMX dedans.
- Ryan : « reprends tout des fichiers et mets les textures et tout ce qui manque … avant de tout lancer propose-moi » → proposition
  (grilles, decals, grillages, poteaux, paddock, drapeaux, contrôles) → « oui voilà mets tout, on modifie ensuite, mets gates aussi ».
- Fait : `dress_sx.py` (doc 11), 43 contrôles. Billboards laissés vides comme JGSX.

## Décisions techniques importantes (et pourquoi)

| Décision | Pourquoi |
|---|---|
| SX en **blocs** + profils exacts, pas de modèle paramétrique | les JGSX sont construits en blocs standard ; copier le profil réel = fidélité maximale |
| Grille du compound = grille JGSX (0,28975 ft) | pas de rééchantillonnage des profils → écart 0,044 ft max |
| Berms = **stamps** 2D exacts, pas le modèle moyen | Ryan : « virages parfaits » ; le modèle moyen lissait les berms |
| Sable = **stamps** Glendale | la photo de Ryan est Glendale ; impossible à reproduire fidèlement avec des blocs |
| Départ séparé + entonnoir | c'est comme ça que JGSX fait ses départs à 22 ; un berm sur la jonction bloque la ligne |
| Ressources dans `RyanCompoundSX1` | un seul exemplaire des textures/ciel pour les 3 dossiers |
| `shading.ppm` calculé | il doit correspondre à notre relief ; calibré sur Detroit (r = 0,995) |
| Pas de statues / barrières | hors périmètre pour l'instant, pas de mesure de leur placement |
