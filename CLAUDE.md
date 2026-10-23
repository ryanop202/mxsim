# CLAUDE.md — reprendre le projet mxsimtrack

Tu reprends un projet commencé dans une autre conversation. Lis dans cet ordre :
1. ce fichier ;
2. `docs/07_journal_conversation.md` (ce qui a été demandé, dit, livré, dans l'ordre) ;
3. `docs/05_compound_sx.md` (les 3 pistes actuelles et pourquoi elles sont comme ça) ;
4. `docs/06_pipeline.md` (comment le code marche, comment ajouter un couloir).

## L'utilisateur

- **Ryan** (GitHub `ryanop202`). Parle **français**, souvent depuis son téléphone, écrit vite (phonétique, sans ponctuation) : lire l'intention.
- Veut des réponses **simples et structurées**, sans blabla. Pas de « super question », pas de validation automatique.
- **Poser des questions** avant une tâche complexe ou ambiguë (préférence explicite).
- Il teste en jeu chez lui, plus tard. Il juge sur ce qu'il voit : vues de dessus d'abord.

## Règles du projet (non négociables)

- **Ne jamais dire qu'une piste marche / a été testée en jeu.** Ce qu'on sait = contrôles automatiques. Dire « non testé en jeu ».
- **Fidélité** : toute géométrie vient des mesures (`lib/`). Pas d'obstacle inventé « à l'œil ». Si on crée une forme nouvelle, le dire.
- **Garder les dimensions** des références (Ryan l'a demandé) : grille 0,28975 ft, couloirs 30,4 ft, espacement 43 ft, berms JGSX.
- Les archives de référence ne vont **pas** sur GitHub (taille + ce n'est pas à nous). Elles sont dans `refs/archives/` en local.
- Après tout changement : `./make_all.sh build` → doit finir sur `39 / 39` (ou plus si on ajoute des contrôles). Montrer les vues de dessus.

## Ce que Ryan a validé / rejeté (résumé)

| Sujet | Avis de Ryan |
|---|---|
| MX (v1) | « ça va pas du tout » → abandonné, **SX seulement** pour l'instant |
| Virages SX | « parfaits » (berms JGSX) — sauf le petit rebord à l'entrée → corrigé en v2 |
| Whoops | « vraiment bien », mais varier entre les pistes |
| Enchaînements | v1 trop pauvre (« que des triples ») → v2 : triple sur table off quad, triple-triple-quad, etc. |
| SX1 | « vraiment bien » |
| SX2 | « ça va » → v3 : départ au milieu |
| SX3 | v2 « forme bizarre » → refait compact ; v3 : sable façon photo Glendale |
| Départs | v3 : faits « pour de vraies courses » (22 grilles, ligne de départ séparée, entonnoir, 1er virage à berm) |
| Virage plat à droite près du départ SX1 | « je veux un appui » → berm ajouté (T7) |
| 1er test en jeu (v3) | retours détaillés couloir par couloir → v4 (doc 07 § 6) |
| Whoops | **jamais de bosse plus grosse juste après les whoops** (« arrête de faire ces bosses à la fin des whoops ») |
| Lignes droites | pas de longue ligne droite vide (surtout avant un virage) : remplir avec un petit enchaînement (on-off…) |
| Enchaînements | varier les hauteurs, pas deux fois le même enchaînement sur deux pistes ; pas d'élan trop long avant un enchaînement (on arrive trop vite) |
| « Pains de sucre » | **refusés dans les enchaînements** : bosses courtes et pointues (≥ 4,5 ft sur ≤ 35 ft). Gros singles = unités longues (≥ 46 ft). Exception voulue : un pain de sucre pour **forcer à ralentir** (SX3 arrivée) |
| « Ça fait 4 d'entrée » | trop d'élan / bosses trop serrées à l'entrée d'un enchaînement → coller au virage, écarter, ou 1re bosse petite |

## État actuel (v7)

- 3 pistes SX dans `tracks/`, 39/39 contrôles, chaîne complète reproductible (`./make_all.sh`).
- v3 à v6 testées en jeu par Ryan → v7 = ses corrections. **v7 pas encore testée en jeu.**
- Pistes d'amélioration notées dans `docs/10_suite_et_idees.md`.

## Pièges connus

- Axes : x = colonne, z = ligne de la heightmap ; z vers le **bas** sur les images. Cap 0° = +x (est), −90° = −z (« nord », haut de l'image).
  Dans `Path.turn`, angle > 0 = virage à **gauche** (cap qui diminue).
- `timing_gates` : la grille regarde f = (−sin a, −cos a). Vérifier avec `validate_sx.py` (couloir de départ).
- Un gros berm (croissant 130°, fait pour 180°) posé sur un virage de 90° dépasse sur les lignes droites → « rebord ». `engine.berm_ang_scale` le resserre (×130/angle). Les petits berms (105°, faits pour 90°) ne sont jamais modifiés.
- Un berm posé à la jonction départ/tour bloque toujours la ligne de départ derrière lui : la ligne de départ est parallèle/décalée.
- Les RAR sont en RAR5 : `unar` et `7z` ratent des fichiers → `node-unrar-js@2.0.2` (`tools/extract_refs.sh`).
- Le sable Glendale est un **stamp exact** (on copie le terrain tel quel avec sa ligne de course), pas un modèle.
- `shading.ppm` est calculé (Lambert calibré sur Detroit), pas copié.

## Commits

Auteur : `Ryan Oppliger <ryanoppliger2021@gmail.com>`. Messages en français, courts, factuels.
