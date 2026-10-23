# mxsimtrack

Base de travail pour faire des pistes **MX Simulator** à partir de mesures réelles :

- **toutes les mesures** des 3 archives de référence (JGMX Desert Sand, JGMX Dr. Dew, JGSX 2026 Test Tracks) : bosses, singles, doubles, tables, on-off, step-up, whoops, berms, sable, départs, profils en travers ;
- le **compound SX** (3 pistes sur un même terrain) prêt à copier dans MX Simulator ;
- les **scripts** qui refont tout (mesures → bibliothèque → pistes → contrôles → figures) ;
- la **doc complète** : formats de fichiers, méthode, décisions, retours de Ryan, historique v1 → v8.

> ⚠️ **État : v3 à v7 testées en jeu par Ryan, v8 (ses corrections) pas encore testée.** Tout ce qui est « validé » l'est par des contrôles automatiques
> (relecture des fichiers exportés, géométrie, profils). Checklist de test : `docs/08_installation_et_test.md`.

## Démarrage rapide (nouveau PC)

```bash
git clone https://github.com/ryanop202/mxsimtrack.git
cd mxsimtrack
```

**Juste jouer** : copier `tracks/RyanCompoundSX1`, `RyanCompoundSX2`, `RyanCompoundSX3` dans le dossier des pistes de MX Simulator
(sans les renommer : les textures sont partagées via `@RyanCompoundSX1/...`). En jeu : « Ryan Compound: SX 1 / SX 2 / SX 3 (sand) ».

**Modifier / reconstruire** :

```bash
python3 -m pip install -r requirements.txt          # numpy, scipy, pillow, matplotlib, scikit-image
# mettre les 3 .rar dans refs/archives/ puis :
npm install && ./tools/extract_refs.sh               # -> refs/extracted/ (voir refs/README.md)
./make_all.sh build                                  # reconstruit tracks/ + contrôles + figures (~2 min)
./make_all.sh                                        # refait AUSSI toutes les mesures depuis les archives (~5 min)
```

Sous Windows : Git Bash ou WSL pour les `.sh` (les scripts Python marchent partout).

## Les 3 pistes (v8)

| Piste | Tour | Estimation* | Départ → jonction | Ce qu'il y a |
|---|---|---|---|---|
| SX 1 | 2931 ft (893 m) | ~1:04 | 368 ft | triple écarté + triple à grosse bosse + quad, 12 whoops + single, triple sur table / off quad, step-up + triple sur table off, on-off Detroit, quad, triple + on-off d'arrivée ; 7 virages à berm |
| SX 2 | 2717 ft (828 m) | ~1:03 | 278 ft | départ au milieu, rythmique Arlington, bosse-bosse-table-bosse-table-bosse, gros double + triple, triple sur table, 8 whoops, S-gros-S-table-S-gros-S, table 9 ft, triple d'arrivée |
| SX 3 (sand) | 3349 ft (1021 m) | ~1:07 | 279 ft | sable Glendale (J + virage en S), hauteurs mélangées + triple Detroit, 10 whoops, on-off, step-up, triple sur table off quad, gros double |

\* modèle point-masse grossier (`scripts/laptime.py`), **pas** un chrono mesuré en jeu.

Vues de dessus : `viewer/figures/01_top_SX*.jpg` · profils : `viewer/figures/02_lanes_SX*.jpg` · visionneuse 3D : `viewer/index.html`.

## Arborescence

```
README.md               ce fichier
CLAUDE.md               consignes pour l'assistant IA qui reprend le projet (à lire en 1er par une IA)
make_all.sh             reconstruit tout (all | build | analysis | mx)
requirements.txt        versions Python utilisées
package.json            node-unrar-js (extraction des RAR5 uniquement)
docs/                   LA DOC (commencer par docs/00_INDEX.md)
lib/                    bibliothèque mesurée (JSON + stamps .npy) = « la base »
scripts/                tout le code (analyse, moteur, layouts, export, validation, figures)
tracks/                 les 3 dossiers MX Simulator prêts à jouer (sortie de make_all.sh build)
build/                  rapports de build (JSON) ; H.npy / tiles.npy régénérés, non versionnés
analysis/               figures d'analyse (références, aperçus)
viewer/                 page de rapport + visionneuse 3D + figures
refs/                   archives de référence (NON versionnées, voir refs/README.md)
tools/                  extraction des archives
legacy_mx/              notes sur la v1 MX abandonnée
```

## Mettre à jour sur plusieurs PC

```bash
git pull                     # récupérer
# ... modifier scripts/layouts_sx.py, etc.
./make_all.sh build          # reconstruire + 39 contrôles
git add -A && git commit -m "SX2 : ..." && git push
```

Puis recopier `tracks/RyanCompoundSX*` dans MX Simulator sur chaque PC.
