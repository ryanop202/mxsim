# Rapport de validation — phase 1 (arène seule)

Date : 26 octobre 2026. Chiffres issus de `build/build_info.json` et `build/validate_mx.json`.

## 0. Allègement pour le jeu (suite au test de l'utilisateur : « trop gourmand »)

Mesuré avec `src/track_budget.py` (somme sur toutes les statues placées) :

| Piste | Statues | Sommets | Triangles |
|---|---|---|---|
| Arène, 1re version | 565 | 1 001 445 | 627 800 (+ couches de réflexion) |
| **Arène, version allégée** | **207** | **≈150 000** | **108 582** |
| USLAND 2026 SX1 (tourne bien chez l'utilisateur) | 671 | 466 447 | 265 473 |

Changements, par ordre de gain :
1. **Sièges** (292 000 → ≈8 000 triangles) : les 24 320 sièges 3D sont remplacés par une bande inclinée
   opaque par rang et par bloc, texturée siège par siège (`seat_band-repeat.png`). Plus de matériau à
   découpe alpha (coûteux) sur les tribunes. Le nombre de places reste calculé.
2. **Écailles** : surface cintrée simple double face (5 × 2 points), sans épaisseur, chants, potelets,
   bras ni réglettes LED (structure peinte dans la texture du verre).
3. **Charpente** : barres sans faces d'extrémité, panneaux de 6 m, une console sur deux, pannes
   supprimées (nervures dans la texture de sous-face), moins de projecteurs et de haut-parleurs.
4. **Couronne et toiture** : moins de subdivisions (mêmes 674 panneaux), maillage de toiture de 3 m.
5. **Gradins et escaliers** : échantillonnage de 3 m, marches réduites à leurs faces visibles.
6. **Matériaux** : couches de réflexion d'environnement retirées du verre (elles doublaient la
   géométrie), cartes de relief limitées à la couronne, la toiture, les bureaux et le mur-rideau,
   textures 1024 px ramenées à 512 px.
7. **Regroupement** en zones de 96 m : 207 objets à dessiner au lieu de 565.

Dans le jeu : chargement des modèles de l'arène en 1,1 s (contre 9 s), aucun avertissement.
La fluidité en roulant reste à confirmer par l'utilisateur.

Corrections visuelles faites dans la même passe (sans coût) : lèvre de couronne plus profonde
(bas de couronne à −2,6 m, écailles à −2,9 m, peau intérieure à −4,2 m), peau intérieure claire au lieu de
verre sombre (supprime les rayures noires entre écailles, cf. P3/P4), joints de couronne plus discrets.

### Couronne : forme des angles (demande de l'utilisateur, d'après P2 et P4)

- Profil refait : la sous-face forme un grand bol (quart d'ellipse) qui part du haut des écailles et
  s'évase vers l'extérieur jusqu'au rebord, comme sur P2 et P4, au lieu d'un bandeau presque vertical.
- La montée de la couronne vers les angles est celle du LiDAR : 26,6 m au milieu de l'extrémité Sud,
  ≈30 m dans les angles arrondis, 43 m à l'angle Nord-Est. Le lissage a été réduit (4 m) pour la conserver.
- 607 panneaux de couronne (645 publiés), poids inchangé (≈108 000 triangles).
- Bug corrigé : les deux flasques de fin de couronne (contre la façade Nord) étaient mal placées ;
  l'une flottait hors du bâtiment (visible sur la vue Nord-Est).
- Façade Nord près de l'angle Nord-Est : le relevé montre une terrasse basse (31,5 m) entre le patio B
  et la façade, qui creusait le haut de la façade en « V » avec un pan de toit visible (vue Nord-Est).
  Comblée à la demande de l'utilisateur (`roof.NE_FILL`) : haut de façade plat à ≈40 m.

## 1. Ce qui a été vérifié, et comment

| Contrôle | Méthode | Résultat |
|---|---|---|
| Emprise et forme en plan | superposition du plan théorique sur le MNS LiDAR (`renders/control_plan_vs_lidar.png`) | conforme : rives, arcs Sud R 32 m, façade Nord en biais, patios |
| Hauteurs de toiture et couronne | surface construite directement depuis le MNS lissé | 26,6 m (Sud) / 31–32 m (longs pans) / 44,96 m (faîtage), écart < 0,5 m avec le relevé |
| Comptages documentés | comparaison | couronne : **607 panneaux** (publié 645) ; écailles : **489** (publié 592, voir §3) ; sièges : **24 320** en tribunes (publié 30 681 places dont 3 380 VIP en loges, non meublées) |
| Ressemblance visuelle | 10 planches photo / rendu (`renders/compare_*.png`) + 7 vues de contrôle | voir §2 |
| Fichiers MX | `src/validate_mx.py` : lecture de chaque modèle, indices, normales, références, textures, terrain | **0 problème** (version allégée) : 0 triangle dégénéré, 0 normale invalide, toutes les références résolues, textures en puissances de 2 |
| Chargement dans le jeu | piste installée dans `%LOCALAPPDATA%\MX Simulator\`, chargée par l'utilisateur, journal `lastlog.txt` lu | **chargement réussi**, aucun avertissement ni erreur sur les fichiers de la piste ; statues chargées en ~9 s ; 514 Mo de mémoire texture (piste USLAND SX1 : 705 Mo) |

Le jeu réduit automatiquement à 16×16 les textures quasi unies (acier noir, aluminium, verre sombre,
écran de projection) : c'est une optimisation du moteur, sans effet visible sur ces matériaux unis.

## 2. Comparaison photo / rendu

| Vue | Concordances | Écarts restants |
|---|---|---|
| P1 entrée Ouest | auvent arrondi, enseigne (police et logo), deux écrans à cadre blanc, rangs d'écailles au-dessus | perspective du rendu plus lointaine ; signalétique « Entrée 32/34 » non reproduite |
| P2 / P3 angle Sud-Ouest | arrondi, débord horizontal entre rangs, écailles vues de face dans l'arrondi et par la tranche sur la façade, couronne panneautée | la lèvre de couronne paraît un peu plus mince sur la photo (perspective basse) |
| P4 angle Sud-Est | couronne qui remonte vers le Nord, entrée Est au fond | grand escalier et parvis en contrebas absents (terrain plat) |
| P6 aérien nuit | silhouette, écrans | lavage LED violet approché par émission (pas de vraies lumières dans MX) |
| P8 / P9 axe longitudinal | bol en U, mur de scène noir à trois écrans, enseigne, rampes de projecteurs, anneau LED | densité de projecteurs sur la photo plus forte ; structures de régie absentes |
| P10 angle Sud-Ouest | écran central, loges vitrées, garde-corps, profondeur des tribunes | charpente sur la photo plus visible (éclairage de service) |
| P5 / P7 tribunes latérales | gradins, escaliers en travées, vomitoires, bandeau blanc des loges | vomitoires réels plus nombreux dans la tribune basse |

## 3. Problèmes connus et limites

1. **Écailles : 489 au lieu de 592 publiées.** Les écailles sont retirées derrière les 4 écrans et au droit
   des 2 auvents (comme sur P1) ; le chiffre publié peut inclure d'autres zones ou un découpage différent.
   Le pas (2,30 m) est fixé par le total publié.
2. **Verre** : pas de transparence douce dans MX ; verre laiteux opaque avec structure peinte dans la
   texture et couche de réflexion d'environnement.
3. **Éclairage** : MX n'a qu'un « soleil ». L'intérieur utilise une lumière quasi verticale (variante par
   défaut) ; les projecteurs, l'anneau LED et les écrans sont des matériaux non éclairés ; le halo au sol est
   précalculé. Les variantes `facade_jour` / `facade_nuit` / `interieur_sombre` sont fournies séparément
   (`variants/`), avec `statues_nuit` pour les LED des écailles.
4. **Sièges** : représentés par des bandes texturées (plus de sièges 3D) pour tenir le budget du jeu ;
   de très près (quelques mètres), les rangées paraissent plates.
5. **Non vérifié en jeu** : rendu visuel détaillé et fréquence d'images (l'utilisateur doit regarder la piste ;
   aucune capture d'écran du jeu n'a été faite).
6. **Portes de chronométrage provisoires** : nécessaires au chargement, à remplacer en phase 2.
7. **Hors périmètre** : grand escalier Est, parvis en contrebas, intérieurs des circulations et des bureaux,
   verrière du toit des bureaux (approchée par la surface LiDAR), tours d'angle (masquées).
8. **Installation** : le dossier du jeu (`Program Files (x86)`) exige des droits administrateur ; la piste
   est installée dans le dossier personnel, où le jeu la trouve.
