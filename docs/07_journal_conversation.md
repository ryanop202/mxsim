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
