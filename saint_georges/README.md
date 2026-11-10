# USLAND: 2026 Saint Georges by bazo — piste MX Simulator (SX Tour, Saint-Georges-de-Montaigu)

Piste supercross de nuit, inspirée du SX Tour de Saint-Georges-de-Montaigu. Version v43 (2026-11-09).

## Installer

Copier le dossier `tracks/USLAND2026SaintGeorgesbyBazo` tel quel dans le dossier du jeu
(`C:\Program Files (x86)\MX Simulator\`). Le dossier est autonome : tout ce qu'il utilise est dedans
(arbres et fichiers repris d'autres pistes copiés dans `ext/`), en dehors des fichiers de base du jeu.

Si la piste a été ouverte dans l'éditeur du jeu, le jeu charge la copie de `%LOCALAPPDATA%\MX Simulator\USLAND2026SaintGeorgesbyBazo`
à la place : la ranger ailleurs (en gardant les `.mxdemo`, les tours enregistrés).

## Contenu

```
tracks/USLAND2026SaintGeorgesbyBazo/   la piste finale (nuit), prête à installer
scripts/layouts_sgm.py                 tout le tracé et le décor de Saint-Georges (version par version, commentés)
scripts/build_stt.py                   relief (heightmap) : sauts, berms, buttes du public, mur de blocs
scripts/export_stt.py                  export de jour (décor, objets, public, portes de chrono)
scripts/export_stt_night.py            version de nuit (éclairage, voile sombre, halos, mini-carte, dossier autonome)
scripts/night_fx.py                    nuit façon Peneman Moon (taches de lumière, ombres, halos)
scripts/*.py (objets)                  modèles faits à la main : hay_bale, boudin3, pole_concrete, arch_tube, clubhouse,
                                       start_tarp, start_grids, scaffold_sign, concrete_blocks, rider_gate, sgm_vehicles...
scripts/sgm_logos.py, sgm_person.py,   logos redessinés, personnage du dernier tour, visages du public
scripts/sgm_crowd_faces.py
assets/sgm/                            photos et fichiers de l'utilisateur (logos, portes de chrono validées, champs IGN)
assets/map/sgm_topview_v40.png         vue de dessus en jeu utilisée pour la mini-carte
docs/13_saint_georges.md               cahier des charges et notes de la piste
```

## Régénérer

Depuis la racine du dépôt (Python avec numpy, scipy, Pillow, scikit-image) :

```bash
MX_LAYOUT=layouts_sgm python scripts/export_stt.py         # jour (lance aussi build_stt)
MX_LAYOUT=layouts_sgm python scripts/export_stt_night.py   # nuit -> tracks/USLAND2026SaintGeorgesbyBazo
```

Les portes de chrono sont figées dans `assets/sgm/user/timing_gates_v43.txt` (validées par l'utilisateur, ne pas les régénérer).
