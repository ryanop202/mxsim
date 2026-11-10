# Paris La Défense Arena — reconstruction architecturale pour MX Simulator (phase 1 : arène seule)

Reconstruction procédurale, entièrement régénérable par script, de Paris La Défense Arena
(Christian de Portzamparc, 2017 ; renommée Plenitude Arena en juillet 2026). **Aucune piste** : le sol
de l'arène reste plat et vide, prêt pour la phase 2.

## Contenu

```
references/originals/   10 photos de référence (SwissTransfer, non modifiées)
references/public/      relevé IGN LiDAR HD, BD TOPO, OSM, élévation et coupes ACDP (usage de référence)
docs/                   inventaire photos, plan architectural, format MX, rapport de validation
src/arena/              générateurs (numpy) : dims, survey, roof, facade, office, bowl, interior,
                        textures, materials, export, mxtrack
src/build.py            point d'entrée (régénère tout)
src/validate_mx.py      contrôle automatique du dossier de piste
blender/                rendu des vues de contrôle (views.json, render_views.py, render.cmd)
build/                  intermédiaires : textures, OBJ par partie (Blender), rapports JSON
export/ParisLaDefenseArena/   dossier de piste MX Simulator prêt à installer
renders/                vues de contrôle
tools/                  Blender 4.5 LTS portable (téléchargé, SHA-256 vérifié)
```

## Régénérer

Prérequis : Python 3.12 avec numpy, scipy (non obligatoire) et Pillow ; Blender 4.5 portable pour les rendus.

```bash
py -3.12 -I src/build.py --mx
```

```bash
py -3.12 -I src/validate_mx.py
```

```bash
blender\render.cmd all 1600x900 32
```

`--only roof,facade,office,bowl,interior` limite la construction ; `--no-seats` saute les sièges (rapide).
Le premier lancement calcule le champ de toiture LiDAR (~35 s) puis le met en cache (`build/roof_field.npz`).

**Chemin long sous Windows** : Blender 4.5 ne démarre pas depuis un chemin de plus de ~200 caractères
(erreur DLL 0xC0000142). `render.cmd` passe par deux jonctions courtes :
`%TEMP%\bl45` → `tools\blender-4.5.15-windows-x64` et `%TEMP%\plda` → racine du projet.

## Installer dans MX Simulator

Copier `export/ParisLaDefenseArena` dans **`%LOCALAPPDATA%\MX Simulator\`** (dossier personnel, sans
droits administrateur ; c'est l'emplacement documenté pour les pistes en création), ou dans le dossier du
jeu `C:\Program Files (x86)\MX Simulator\` avec droits administrateur. Puis choisir
« Paris La Defense Arena - architecture (phase 1, sans piste) » dans la liste des pistes.

Variantes d'éclairage : `variants/lighting_*` → copier sur `lighting` :
`interieur_eclaire` (par défaut), `interieur_sombre`, `facade_jour`, `facade_nuit`.

La grille de départ et les 4 portes de chronométrage sont **provisoires** (le jeu exige une boucle d'au
moins 3 portes pour charger une piste) ; elles seront remplacées en phase 2.

## Pipeline

1. **Relevé** (`survey.py`) : MNS/MNT LiDAR IGN ramenés dans le repère du bâtiment.
2. **Toiture** (`roof.py`) : surface issue du MNS lissé (σ 2 m), raccordée par « fermeture éclair »
   à la ligne haute de la couronne ; patios découpés.
3. **Enveloppe** (`facade.py`) : couronne de 607 panneaux à joints (645 publiés), sous-face en bol et rebord arrondi (P2, P4),
   socle vitré, bandeau, peau intérieure, 3 rangs d'écailles cintrées (verre sérigraphié / mixte / aluminium)
   avec potelets, bras et réglettes LED, débord d'angle Sud-Ouest, auvents, écrans LED, enseigne.
4. **Bureaux Nord** (`office.py`) : d'après l'élévation de l'architecte.
5. **Tribunes** (`bowl.py`) : gradins à nez de marche, escaliers radiaux, vomitoires, loges, nez de la
   tribune haute avec anneau LED, garde-corps, 24 320 places en rangées texturées (version allégée pour le jeu).
6. **Intérieur** (`interior.py`) : mur de scène et écrans, sous-face de toiture, méga-poutres et fermes
   en treillis, consoles, pannes, passerelles, rampes de projecteurs, haut-parleurs, gaines.
7. **Export** (`export.py`, `mxtrack.py`) : OBJ pour Blender ; JM1 gzippés en pieds pour MX, découpés en
   zones de 96 m (207 objets, ≈108 600 triangles), terrain plat, tuiles, éclairage précalculé.

Détails et limites : `docs/`.

## Dans le dépôt mxsim (branche `track`)

- Source du stade : `stade_paris/` (scripts, Blender, docs, références). `build/`, `renders/` et Blender
  portable ne sont pas versionnés : `py -3.12 -I src/build.py --mx` les régénère depuis `stade_paris/`.
- Piste MX prête à copier : `tracks/ParisLaDefenseArena/` (copie de `export/ParisLaDefenseArena`).
