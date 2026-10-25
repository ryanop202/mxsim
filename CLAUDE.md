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

- **Attention** : d'autres personnes de l'équipe travaillent aussi sur ce dépôt (v12 : objets USLAND, paddock, arche, départ).
  Ne pas supposer que la personne est Ryan ; ne pas lui attribuer les retours des autres.

## Objets 3D / décor (v12) — lire `docs/12_objets_usland.md` AVANT de dessiner quoi que ce soit

- Générateur : `scripts/props_usland.py` (specs contrôlées automatiquement), placement : `scripts/props_place.py`,
  aperçu 3D : `scripts/preview_props.py` → toujours montrer l'aperçu et le vérifier soi-même avant de mettre en jeu.
- Règles de design (retours de l'utilisateur) : pas de formes carrées (arrondir), réaliste et épuré, logos peu nombreux /
  centrés / même taille / jamais déformés, logos noirs sur vitres grises, jamais deux USLAND côte à côte, vraies roues,
  volumes creux crédibles, pas de treillis inutile, objets alignés, drapeaux pointe vers l'avant (câble), bord haut légèrement arqué,
  enseignes découpées autour du logo, aucun logo à l'envers / en miroir (vérifier chaque face). Détail : doc 12 § 3.

## Règles du projet (non négociables)

- **Ne jamais dire qu'une piste marche / a été testée en jeu.** Ce qu'on sait = contrôles automatiques. Dire « non testé en jeu ».
- **Fidélité** : toute géométrie vient des mesures (`lib/`). Pas d'obstacle inventé « à l'œil ». Si on crée une forme nouvelle, le dire.
- **Garder les dimensions** des références (Ryan l'a demandé) : grille 0,28975 ft, couloirs 30,4 ft, espacement 43 ft, berms JGSX.
- Les archives de référence ne vont **pas** sur GitHub (taille + ce n'est pas à nous). Elles sont dans `refs/archives/` en local.
- Après tout changement : `./make_all.sh build` → doit finir sur `43 / 43` (ou plus si on ajoute des contrôles). Montrer les vues de dessus.

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
| « Pains de sucre » | **refusés dans les enchaînements** : bosses pointues = hauteur / largeur à mi-hauteur > 0,31 (contrôle auto dans `validate_sx.py`), y compris les petits singles courts (~26 ft). Gros singles OK = Arlington g37_2, g1_2, Cleveland g29_3, Glendale g30_0. Exception voulue : un pain de sucre pour **forcer à ralentir** (SX3 arrivée) |
| « Réaliste » | prendre un couloir JGSX entier avec ses écarts d'origine plutôt qu'un assemblage inventé |
| Arrivée | ligne d'arrivée sur un saut (comme JGSX : crête du double d'arrivée g30) |
| Délimitations | tuff blocks **placés par Ryan seulement** (blancs, logo USLAND) ; 1 cône dans chaque virage ; virages de départ à plat |
| Départs | pas d'entonnoir : couloir qui se resserre régulièrement |
| Portes | 1 par virage + 2-3 par couloir |
| « Ça fait 4 d'entrée » | trop d'élan / bosses trop serrées à l'entrée d'un enchaînement → coller au virage, écarter, ou 1re bosse petite |

## État actuel (v12, branche `v12-camions-arche`)

- 3 pistes SX dans `tracks/` + habillage (doc 11) ; v12 : objets USLAND faits maison posés à la place des objets JGSX
  (doc 12) : hospitality, pick-ups + vélos, grilles + grates + portique de départ, arche FINISH, bannières.
- SX1 : arrivée déplacée sur la 1re bosse du step-up du couloir D (1er tour plus court : jonction -> arrivée).
- v3 à v10 testées en jeu ; v11 et **v12 pas encore testées en jeu**. Contrôles v12 faits sans les archives (portes, comptage
  des tours, objets) ; `./make_all.sh build` complet à relancer sur le PC qui a les archives.
- Pistes d'amélioration notées dans `docs/10_suite_et_idees.md`.

## Pièges connus

- Axes : x = colonne, z = ligne de la heightmap ; z vers le **bas** sur les images. Cap 0° = +x (est), −90° = −z (« nord », haut de l'image).
  Dans `Path.turn`, angle > 0 = virage à **gauche** (cap qui diminue).
- `timing_gates` : la grille regarde f = (−sin a, −cos a). Porte `half [centre] [vecteur]` : le vecteur va **dans le sens de la course** (longueur = half), la ligne de la porte est perpendiculaire (erreur de la v10).
- Un gros berm (croissant 130°, fait pour 180°) posé sur un virage de 90° dépasse sur les lignes droites → « rebord ». `engine.berm_ang_scale` le resserre (×130/angle). Les petits berms (105°, faits pour 90°) ne sont jamais modifiés.
- Un berm posé à la jonction départ/tour bloque toujours la ligne de départ derrière lui : la ligne de départ est parallèle/décalée.
- Les RAR sont en RAR5 : `unar` et `7z` ratent des fichiers → `node-unrar-js@2.0.2` (`tools/extract_refs.sh`).
- Le sable Glendale est un **stamp exact** (on copie le terrain tel quel avec sa ligne de course), pas un modèle.
- `shading.ppm` est calculé (Lambert calibré sur Detroit), pas copié.

## Commits

Auteur : `Ryan Oppliger <ryanoppliger2021@gmail.com>`. Messages en français, courts, factuels.
