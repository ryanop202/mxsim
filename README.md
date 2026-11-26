# mxsim — kit pour faire des pistes de supercross MX Simulator (USLAND)

Ce dépôt contient **tout ce qu'il faut pour faire une piste SX** dans MX Simulator :

- les **mesures** de vraies pistes : bosses, singles, doubles, tables, whoops, berms, sable, départs ;
- le **moteur** qui assemble ces mesures en piste et l'exporte au format du jeu ;
- les **objets, logos et textures** faits maison : tuff blocks, grilles, arches, boudins, public…
- les **pistes déjà faites**, prêtes à copier dans le jeu, avec le code qui les reconstruit ;
- la **doc** : formats de fichiers, méthode, règles de design, historique.

Le principe : **chacun ajoute au dépôt ce qu'il crée**, comme une piste, un objet ou un logo. Les autres le récupèrent avec
`git pull`. On se complète comme ça et chacun garde ses pistes à jour.

> ⚠️ Rien n'est « validé en jeu » par le code : les contrôles sont automatiques. Ce qui a été testé en jeu est noté dans la fiche de chaque piste.

## Arborescence

```
README.md          ce fichier
CLAUDE.md          consignes pour l'IA (Claude) qui reprend le projet
make_all.sh        reconstruit les pistes SX 1-3 et refait les mesures
requirements.txt   Python (numpy, scipy, pillow, matplotlib, scikit-image)
package.json       node-unrar-js (extraction des archives RAR5)

commun/            LE KIT, partagé par toutes les pistes
  lib/               bibliothèque mesurée (JSON + stamps .npy) : unités SX, whoops, berms, sable
  scripts/           moteur, export MX Simulator, contrôles, objets 3D, tracés (layouts_*.py)
  assets/            logos, objets (props), public, herbe, textures, cartes
  analysis/          figures et JSON des mesures sur les pistes de référence
  build/             sorties de calcul (rapports JSON ; les .npy sont régénérés, pas versionnés)
  viewer/            rapport HTML + visionneuse 3D + figures
  tools/             extraction des archives (.rar, .saf)

pistes/            une fiche par piste : ce qu'elle est, où est son code, comment la reconstruire
  sx-test-jgsx/      SX 1, SX 2, SX 3 (la base de départ du projet)
  saint-georges/     Saint-Georges-de-Montaigu (bazo)
  saint-thibery/     Saint-Thibéry (bazo)
  paris-2026/        Supercross Paris 2026 : code du tracé et de l'habillage, photos de référence, arène (stade_paris/)

tracks/            les pistes PRÊTES À JOUER (dossiers MX Simulator, à copier tels quels dans le jeu)
docs/              la doc (commencer par docs/00_INDEX.md)
  guide/             comment ça marche : formats, mesures, pipeline, installation, objets
  pistes/            notes et historique de chaque piste
refs/              pistes de référence (RBT, RF ; les archives JGSX/JGMX restent en local, voir refs/README.md)
anciens/           ce qui n'est plus utilisé (v1 MX abandonnée)
```

## Les pistes

| Piste (nom du dossier dans `tracks/`) | Fiche | Qui |
|---|---|---|
| `USLAND2026SX1`, `SX2`, `SX3` | [pistes/sx-test-jgsx](pistes/sx-test-jgsx/README.md) | Ryan |
| `USLAND2026SaintGeorgesbyBazo` | [pistes/saint-georges](pistes/saint-georges/README.md) | bazo |
| `USLAND2026SaintThiberybyBazo` | [pistes/saint-thibery](pistes/saint-thibery/README.md) | bazo |
| `USLANDParis` (version Zion, la plus récente), `USLAND2026SupercrossParis`, `USLAND2026SupercrossParisRF`, `ParisLaDefenseArena` (arène seule) | [pistes/paris-2026](pistes/paris-2026/README.md) | Ryan + équipe |

**Juste jouer** : copier le dossier voulu de `tracks/` dans le dossier des pistes de MX Simulator **sans le renommer**,
car certaines pistes partagent des textures via `@USLAND2026SX1/...`. Pour Paris, copier aussi `USLAND2026SX1`.

## Démarrage (nouveau PC)

```bash
git clone https://github.com/ryanop202/mxsim.git
cd mxsim
py -3.12 -m pip install -r requirements.txt     # Windows ; ailleurs : python3 -m pip ...
npm install                                      # seulement pour extraire des .rar
```

Les commandes se lancent **depuis la racine du dépôt**. Sous Windows, utiliser Git Bash pour les `.sh`.
Les scripts Python marchent partout.

## Faire une nouvelle piste SX

1. **Créer sa fiche** : `pistes/<nom>/README.md`, avec ce qu'est la piste, qui la fait, comment la reconstruire et son état
   (testée en jeu ou non). Partir d'une fiche existante.
2. **Le tracé**, deux façons qui existent déjà :
   - comme SX 1-3 ou Saint-Georges / Saint-Thibéry : un fichier `commun/scripts/layouts_<nom>.py`, construit par le moteur commun
     (`build_sx.py` / `export_sx.py`, ou `build_stt.py` / `export_stt.py` avec `MX_LAYOUT=layouts_<nom>`) ;
   - comme Paris : un dossier `pistes/<nom>/` avec son propre script de construction, qui importe `commun/scripts`.
3. **La géométrie vient des mesures** (`commun/lib/`) : les couloirs, les berms et le sable sont repris des pistes de référence,
   pas dessinés à l'œil. Recettes : [docs/guide/06_pipeline.md](docs/guide/06_pipeline.md).
4. **Le décor** : réutiliser les objets de `commun/assets/props` (générés par `commun/scripts/props_usland.py` et compagnie).
   Les règles de design sont dans [docs/guide/12_objets_usland.md](docs/guide/12_objets_usland.md).
5. **La sortie** va dans `tracks/<NomDuDossier>/`. Contrôler, regarder les vues de dessus, puis tester en jeu
   ([docs/guide/08_installation_et_test.md](docs/guide/08_installation_et_test.md)).

## Ajouter au kit commun

Ce qui peut servir à d'autres pistes va dans `commun/` :

| Ce que tu ajoutes | Où |
|---|---|
| un objet 3D (script générateur) | `commun/scripts/<objet>.py` → modèles dans `commun/assets/props/` |
| un logo, une texture, du public | `commun/assets/logos/`, `commun/assets/crowd/`… |
| une mesure d'une nouvelle piste de référence | `commun/lib/` (voir « Mesurer une nouvelle piste de référence » dans le doc 06) |
| une explication, une règle | `docs/guide/` |

Ce qui ne sert qu'à une piste reste dans `pistes/<nom>/`.

## Travailler à plusieurs

```bash
git pull                                   # TOUJOURS avant de commencer
# ... modifier ...
git add -A && git commit -m "Paris : ..."  # message court, en français, qui dit quelle piste
git push
```

- Une piste = une branche si c'est un gros chantier, comme `paris-2026`. On fusionne dans `main` quand c'est prêt.
- Ne pas modifier les pistes des autres sans leur dire, car vous travaillez sur les mêmes fichiers.
- Les archives de référence lourdes (JGSX, JGMX) ne vont pas sur GitHub : voir [refs/README.md](refs/README.md).

## Reconstruire SX 1-3 (exemple complet)

```bash
# mettre les 3 .rar JGSX/JGMX dans refs/archives/ puis :
./commun/tools/extract_refs.sh     # -> refs/extracted/
./make_all.sh build                # reconstruit tracks/USLAND2026SX1..3 + contrôles + figures (~2 min)
./make_all.sh                      # refait AUSSI toutes les mesures (~5 min)
```
