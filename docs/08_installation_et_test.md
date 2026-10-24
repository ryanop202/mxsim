# 08 — Installer dans MX Simulator et tester

## Installer

1. Supprimer les anciennes versions dans le dossier des pistes du jeu : `RyanCompoundSX1..3` (ancien nom, jusqu'à la v9) et
   `RyanCompoundMX` de la v1 s'il existe encore.
2. Copier `tracks/USLAND2026SX1`, `tracks/USLAND2026SX2`, `tracks/USLAND2026SX3` dans le dossier des pistes de MX Simulator,
   **sans les renommer** (les 3 utilisent les textures/ciel de `USLAND2026SX1` via `@USLAND2026SX1/...`).
3. En jeu : « USLAND: 2026 SX 1 », « USLAND: 2026 SX 2 », « USLAND: 2026 SX 3 (sand) ».

Pack : `USLAND2026SXTestTracks.zip` (comme `JGSX2026TestTracks`). Taille : ~260 Mo (SX1, avec toutes les ressources) + ~104 Mo × 2. Le plus gros = `shading.ppm` (50 Mo, identique dans les 3).

Le dossier exact des pistes dépend de l'installation de MX Simulator (c'est celui où sont déjà les autres pistes perso,
ex. là où ont été mis JGSX2026Detroit, etc.).

## Ce qu'il faut regarder au 1er test (checklist)

Rien de tout ça n'a pu être vérifié sans le jeu.

- [ ] Les 3 pistes apparaissent dans la liste avec le bon nom.
- [ ] Le terrain se charge (pas d'écran noir, pas de sol invisible), les textures sol / sable s'affichent.
- [ ] **Départ** : on est bien sur la grille, face à la ligne droite ; la grille tombe ; on rejoint le tour par l'entonnoir sans obstacle.
- [ ] Le **compteur de tours** marche : le 1er tour se valide, puis les suivants (portes `firstlap` / `normallap`).
- [ ] Les **virages** : pas de rebord à l'entrée (corrigé en v2) ; le nouveau berm T7 du SX1.
- [ ] Les **enchaînements** passent à la bonne vitesse : triple-triple-quad, triple sur table off quad, quad-quad, step-up, gros double.
- [ ] **Whoops** : on peut les skimmer.
- [ ] **Sable** SX3 : ça creuse comme à Glendale (tiles Sand Exit / Sand Bump Solo), on peut sortir du J proprement.
- [ ] Chronos réels vs estimés (~1:04 / ~1:03 / ~1:13).
- [ ] Ombres / éclairage cohérents (shading calculé).

Noter ce qui ne va pas (piste, couloir, obstacle, « trop court / trop long / trop haut ») : avec les noms des couloirs
(doc 05 ou `viewer/figures/02_lanes_SX*.jpg`) on corrige directement dans `scripts/layouts_sx.py`.

## Si quelque chose ne marche pas

| Symptôme | Piste |
|---|---|
| Piste absente de la liste | dossier mal placé, ou `desc` illisible |
| Textures blanches / manquantes | dossier `USLAND2026SX1` renommé ou absent |
| Mauvais sens au départ | angle des grilles : `export_sx.gates()` (convention f = (−sin a, −cos a)) |
| Tours non comptés | portes trop étroites ou ordre : `timing_gates`, `export_sx.gates()` (cp_step, half) |
| Sable qui ne creuse pas | tiles : `build_sx.GLENDALE_TILES`, blocs `Sand *` de `tileinfo` |
| Terrain décalé / miroir | convention x/z (doc 01) — vérifiée sur les références, pas en jeu |
