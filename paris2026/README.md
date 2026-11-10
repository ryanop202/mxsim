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
