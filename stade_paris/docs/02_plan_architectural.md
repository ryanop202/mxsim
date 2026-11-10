# Plan architectural et cotes retenues

Toutes les valeurs sont dans `src/arena/dims.py` (et les modules qui l'utilisent) avec leur source.
Légende : **DOC** publiée · **LID** mesurée sur le LiDAR IGN HD · **PHO** estimée sur vos photos ·
**HYP** hypothèse de cohérence géométrique.

## Repère et unités

- Modèle source : mètres, Z vers le haut.
- Axe X = axe long du bâtiment, vers le NNE (azimut vrai 25,5°), du Sud arrondi vers le mur de scène et les bureaux.
- Axe Y = vers l'ONO (façade Ouest, entrée 33). Z = 0 au sol de référence (54,60 m NGF).
- Origine = centre du relevé LiDAR décalé de 3 m pour centrer l'axe (rives mesurées à +79,5 / −85,5 m).
- Export MX Simulator : pieds (× 3,28084), Y vers le haut : (X, Y, Z) → (X, Z, −Y).

## Sources de mesure

| Source | Contenu | Fichier |
|---|---|---|
| IGN LiDAR HD (MNS/MNT 0,5 m) | forme exacte du toit, de la couronne, emprise | `references/public/MNS.bil`, `MNT.bil` |
| IGN BD TOPO | emprise arène + bureaux, hauteur 44,9 m | `references/public/bdtopo.json` |
| OpenStreetMap | contour 200,4 × 164,8 m | `references/public/osm.json` |
| Élévation ACDP « rue des Sorins » 2015 | niveaux NGF : socle, écailles, couronne, étages | `references/public/elev_*.png` |
| Coupes ACDP | profil des tribunes et de la charpente | `references/public/coupe_*.png` |
| Infociments, Vinci, Defense-92, Freyssinet, dUCKS | couronne, écailles, charpente, sol | voir rapport de recherche |

Contrôle visuel du plan sur le relevé : `renders/control_plan_vs_lidar.png`.

## Cotes principales

| Élément | Valeur | Source |
|---|---|---|
| Emprise totale | 204 × 165 m (arène + bureaux) | LID / DOC |
| Demi-largeur au nu de couronne | 82,5 m | LID |
| Extrémité Sud (milieu) | X = −92 m | LID |
| Rayon des angles Sud | 32 m | LID (ajusté sur 3 profils) |
| Façade Nord (bureaux) | X = 93 − 0,21·Y (biais) | LID / BD TOPO |
| Congés NE / NO | 10 m / 6 m | LID |
| Socle vitré | 0 → 3,21 m | DOC (57,21 NGF) |
| Bandeau de signalétique | 3,21 → 4,05 m | PHO |
| Bande d'écailles | 3,95 → 19,46 m, 3 rangs (5,2 / 5,4 / 6,1 m) | DOC (16,25 m) + PHO (rang haut plus grand) |
| Écailles | pas 2,30 m, corde 2,75 m, rotation 34°, flèche 0,22 m | DOC (592 écailles) + PHO |
| Bas de couronne | 19,46 m | DOC (73,46 NGF) |
| Haut de couronne | 26,6 m (milieu Sud) → ≈30 m dans les angles arrondis → 31–32 m (longs pans) → 43 m (angle Nord-Est) | LID (lissage léger, 4 m) |
| Profil de couronne | sous-face plate à 19,80 m, puis « bol » en quart d'ellipse qui s'évase jusqu'au nu (à 55 % de la hauteur), face quasi verticale, rebord arrondi | PHO (P2, P4) |
| Faîtage de la voûte | 44,96 m | LID / DOC (99,05 NGF) |
| Sol de l'arène | 90 × 122 m, angles Sud R 18 m | DOC (dUCKS 90 m) + LID + PHO |
| Mur de scène | X = 62 m | LID / PHO |
| Tribune basse | 24 rangs × 0,80 m, contremarches 0,36 → 0,46 m | PHO (comptage P7/P9) + coupe |
| Tribune haute | 10 à 19 rangs selon la toiture, contremarches 0,55 → 0,62 m | PHO + HYP (garde 2,6 m sous toiture) |
| Sièges modélisés | 24 320 (13 304 bas + 11 016 haut) | calcul ; DOC 30 681 places rugby dont 3 380 VIP en loges |
| Écran central | 70 × 18 m, bas à 9 m | DOC (1 400–2 600 m²) + PHO |
| Écrans latéraux | 16 × 9 m, axes Y = ±54 m | PHO |
| Méga-poutres | cadre X −52 → 58, Y ±44, membrure basse 30 m | DOC (cadre 150 × 110 m, 14 m) + HYP |
| Bureaux Nord | colonnade 9 m, volume vitré 9–18,24 m, étages 3,52 m | DOC (élévation) |
| Haut de la façade Nord, côté Est | plat à ≈40 m : le creux du relevé (terrasse à 31,5 m entre le patio B et la façade) est comblé | LID modifié (choix de l'utilisateur) |

## Hypothèses documentées (catégorie C des photos)

1. **Orientation des écailles** : symétrique par rapport à l'axe long, tournées vers le Nord (déduit de P2 et P4,
   où les écailles des façades longues apparaissent par la tranche depuis le Sud).
2. **Position des entrées** : auvent Ouest centré en X = 15 m (31 m de large), Est en X = 36 m (18 m) ;
   écrans de 13,8 × 9 m de part et d'autre. Estimé par comptage d'écailles sur P1–P4.
3. **Débord horizontal** : présent seulement dans l'angle Sud-Ouest (P2, P3), absent dans l'angle Sud-Est (P4).
4. **Tribune haute** : le nombre de rangs est limité par la sous-face de toiture mesurée ; côté Sud, où le toit
   descend à 26 m, il reste 10 rangs. Cohérent avec la coupe ACDP, non vérifiable sur les photos.
5. **Charpente** : seuls le principe (4 méga-poutres sur 4 tours, 14 m) et l'aspect (P8–P10) sont documentés ;
   le tracé des fermes secondaires (tous les 11 m) et des consoles est reconstruit.
6. **Patios des bureaux** : relevés sur le LiDAR ; fond du patio A à +10 m (estimé), patio B au sol.
7. **Grand escalier Est et parvis en contrebas** : hors périmètre (terrain plat dans MX pour cette phase).
8. **Intérieurs des circulations et des bureaux** : non modélisés (invisibles depuis les vues utiles).
