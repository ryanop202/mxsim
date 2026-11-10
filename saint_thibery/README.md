# USLAND: 2026 Saint Thibery by bazo — piste MX Simulator (Saint-Thibéry)

Piste supercross de nuit, inspirée du terrain de Saint-Thibéry. Version v65 (version livrée et installée).

## Installer

Copier le dossier `tracks/USLAND2026SaintThiberybyBazo` tel quel dans le dossier du jeu
(`C:\Program Files (x86)\MX Simulator\`). Le dossier est autonome : tout ce qu'il utilise est dedans
(fichiers repris d'autres pistes copiés dans `ext/`), en dehors des fichiers de base du jeu.

Si la piste a été ouverte dans l'éditeur du jeu, le jeu charge la copie de `%LOCALAPPDATA%\MX Simulator\USLAND2026SaintThiberybyBazo`
à la place : la ranger ailleurs (en gardant les `.mxdemo`, les tours enregistrés).

## Contenu

```
tracks/USLAND2026SaintThiberybyBazo/   la piste finale (nuit), prête à installer
scripts/layouts_stt.py                 tout le tracé et le décor de Saint-Thibéry (version par version, commentés)
scripts/build_stt.py                   relief (heightmap)
scripts/export_stt.py                  export de jour (décor, objets, public, portes de chrono)
scripts/export_stt_night.py            version de nuit (poteaux, éclairage, mini-carte, dossier autonome)
assets/map/stt_topview_v38.png         vue de dessus en jeu utilisée pour la mini-carte
assets/props, assets/logos, assets/crowd   objets, logos et public
```

Le code est partagé avec Saint-Georges (`saint_georges/`) : les mêmes scripts lisent le tracé choisi par `MX_LAYOUT`.

## Régénérer

Depuis la racine du dépôt (Python avec numpy, scipy, Pillow, scikit-image) :

```bash
python scripts/export_stt.py         # jour (MX_LAYOUT par défaut = layouts_stt, lance aussi build_stt)
python scripts/export_stt_night.py   # nuit -> tracks/USLAND2026SaintThiberybyBazo
```

Seule la version de nuit est livrée (pas de version de jour).
