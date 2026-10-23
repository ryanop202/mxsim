# 01 — Formats de fichiers MX Simulator (rétro-ingénierie)

Tout ce qui suit a été **déduit des fichiers des références** et vérifié par relecture (`scripts/validate_format.py`,
`scripts/mxs.py`). Ce n'est pas une doc officielle. Ce qui n'est pas vérifié est marqué *(non vérifié)*.

## Unités et axes

- **Unité monde = le pied (ft)**, déduit de deux objets : le van Transit fait 8,3 × 8,6 × 20,1 unités (≈ dimensions réelles en ft),
  et la grille de départ `gate01` fait 3,1 unités de large posée au pas de 4 unités. 1 ft = 0,3048 m.
- **x = colonne** de la heightmap, **z = ligne**. Sur les images (vue de dessus) z va vers le **bas**.
  Vérifié en superposant les checkpoints/decals sur la heightmap : le mode `xz` donne l'erreur médiane la plus faible
  sur les 7 références (sortie de `validate_format.py`).
- y = hauteur (vers le haut).

## Dossier d'une piste

| Fichier | Rôle | Format |
|---|---|---|
| `terrain.hf` | en-tête heightmap | texte : `n spacing hmin hmax` |
| `terrain.png` | heightmap | PNG 16 bits gris, côté = 2^(n+1)+1 px |
| `tilemap` | type de sol par case | octets bruts, 2^n × 2^n, valeur = index du bloc `addtile` dans `tileinfo` |
| `tileinfo` | définition des sols | blocs texte terminés par `addtile` |
| `timing_gates` | grille de départ, checkpoints, ordre des tours | texte, sections `startinggate:` `checkpoints:` `firstlap:` `normallap:` |
| `lighting` | soleil, ambiance, brouillard, ciel | texte |
| `shading.ppm`, `shadingx2.ppm` | lightmap précalculée | PPM P6, même résolution que la heightmap |
| `desc` | nom affiché en jeu | 1 ligne |
| `statues` | objets 3D posés | `[x y z] angle @modèle.jm @texture.png @forme|null` |
| `decals` | textures plaquées au sol | `[x z] angle taille alpha @texture.png` |
| `billboards`, `flaggers` | panneaux, commissaires | texte (vides ou quasi chez nous) |
| `edinfo` | infos de l'éditeur (lignes de dessin JGMX) | `add_gradient ax az bx bz` + `add_point i d h` |
| `cameras` | caméras TV (Desert Sand) | `autofovsize`, `gate`, `addcamera x y z` |
| `*.mxdemo` | replays | binaire, en-tête texte `MX06 …` *(non décodé)* |
| `*.jm` | modèles 3D | texte, commence par `JM1` |

### terrain.hf + terrain.png

```
10 0.289750 -0.194385 11.217994        (JGSX2026Detroit)
```
- `n = 10` → PNG de 2^(10+1)+1 = **2049 px** ; `spacing = 0,28975 ft` par pixel → côté = (2049−1) × 0,28975 = **593,4 ft**.
- hauteur = hmin + valeur16bits / 65535 × (hmax − hmin).
- Les 5 JGSX 2026 ont **exactement** la même grille (n = 10, 0,28975 ft). Desert Sand : n = 11, 0,22 ft (4097 px, 901 ft).
  Dr. Dew : n = 10, 0,8 ft (2049 px, 1638 ft).
- **Notre compound SX** : n = 11, 0,28975 ft → 4097 px, **1186,8 ft** de côté (même résolution que JGSX, 4× la surface).

### tilemap + tileinfo

- `tilemap` : 2^n × 2^n octets (1024² pour JGSX, 2048² pour le compound), une case = 2 px de heightmap.
- Valeur = numéro du bloc dans `tileinfo` (0 = premier bloc `name … addtile`).
- Un bloc : `name`, `friction` (plusieurs lignes vitesse/coef), `roll_resist`, paramètres `erode_*` (creusement des ornières),
  `texture`, `roost` (projections), `treadmark` (traces), puis `addtile`.
- Le compound **recopie tels quels les blocs physiques** de `JGSX2026Custom/tileinfo` (Main→« SX Main », Jumps Sx, WhoopsV2,
  Berm Exit Sx, Sand Straight, Sand Bump Straight, Sand Exit, Sand Bump Solo) et ne change que les textures (`@RyanCompoundSX1/...`).
- Tiles JGSX vus dans Detroit : Main, Berm Exit Sx, Transition Sx, Jumps Sx, Wall Sinlge Deform, Jump Transition Sx, Whoops, WhoopsV2,
  Whoop Transition, Sand Dirt Mix, Sand Exit, Sand Straight, Sand Bump Solo, Sand Bump Straight, Mulch Mix *, Single Bumpo Sx,
  Single Big Bump Sx, Braking Bumps *, Moto *, Mx Corner, Sand Straight Mx, Start Grate, after start ruts, fmx, Flat Corner Sx Test.

### timing_gates

```
startinggate:
[41.000000 0.000000 196.000000] -1.570796 @JGSX2026Detroit/statue/gate01.jm @…/gate01.png @startgate.shp
…  (22 lignes, z = 196, 200, … 280 : 22 grilles au pas de 4 ft)
checkpoints:
41.237885 [386.542908 0.000000 248.844742] [23.270935 0.000000 34.044479]
…
firstlap:
0 1 2 … 19
normallap:
20 21 22 23 0 1 2 … 19
```
- **Grille** : `[x y z] angle`. Le pilote regarde **f = (−sin a, −cos a)** dans le plan (x, z).
  a = −π/2 → f = (+1, 0) = vers +x (« est »). a = 0 → f = (0, −1) = vers −z (« nord », haut de l'image).
  Dans `export_sx.py` : `a = atan2(−f_x, −f_z)`.
- **Checkpoint** : `demi_largeur [cx cy cz] [dx dy dz]` — segment centré en c, de c−d à c+d (d = demi-vecteur, |d| = demi-largeur).
- **firstlap / normallap** : indices des checkpoints dans l'ordre. Chez JGSX le **1er tour est plus court** : il commence
  à la jonction de la ligne de départ ; les tours suivants ajoutent 4 portes (20-23) sur la portion avant la jonction.
- Le compound fait l'inverse, ce qui revient au même pour le jeu : la boucle complète = `normallap`, et `firstlap` = 2 portes
  **en travers de la ligne de départ** + la boucle depuis la jonction (voir `docs/03_mesures_sx.md` § départs).

### lighting

```
sun_vector [ -0.6528 0.3590 0.6671 ]
sun_color [ 1.00 1.00 0.9 ]   ambient [ 0.34 0.345 0.365 ]   fog [ 0.75 0.80 0.87 ] 0.00007
sky_n/e/s/w/u/env @…/sky/sky-*.png    flare_element …    dynamic_lighting 1
```
Le compound reprend le `lighting` de Detroit (ciel copié dans `RyanCompoundSX1/sky/`).

### shading.ppm

- Lightmap gris (PPM P6, 3 canaux identiques) à la résolution de la heightmap.
- Calibré sur Detroit : **shade = 89,3 + 245,8 × lambert** (r = 0,995), lambert = max(0, n·soleil) avec le `sun_vector` ci-dessus,
  sans ombres portées (`scripts/shading.py`, `lambert_shadow(..., shadow=False)`).
- `shadingx2.ppm` = shading // 2.
- C'est le plus gros fichier du compound (4097² × 3 = 50 Mo), identique dans les 3 dossiers (Git ne le stocke qu'une fois).

### edinfo (lignes de dessin JGMX)

```
add_gradient 132.945740 344.107849 84.868584 344.243927     (point A (x,z) → point B)
add_point 0 0.000000 0.000000                               (type, distance depuis A en ft, hauteur en ft)
add_point 1 16.839413 0.001194
```
- Ce sont les **axes de construction** utilisés par l'auteur dans l'éditeur : chaque obstacle d'un couloir est dessiné le long
  d'une ligne. C'est la base de toutes nos mesures SX (`catalog.py`, `sx_units.py`) : on échantillonne la heightmap **réelle**
  le long de ces lignes (et pas les points de l'éditeur, qui ne correspondent pas toujours au terrain final).
- Numérotation `g0, g1, …` = ordre dans le fichier (visible sur les atlas `docs/img/atlas_*.jpg`).

### Références `@Dossier/…`

Un chemin `@NomDuDossier/sous/fichier.png` pointe dans le dossier de piste `NomDuDossier` du répertoire des pistes du jeu.
`@fichier.png` sans dossier = ressource interne du jeu (`@splash.png`, `@glare.png`, `@startgate.shp`).
Le compound met toutes ses ressources dans `RyanCompoundSX1` → **ne pas renommer les dossiers**.

## Ce qui n'est pas compris / pas utilisé

- `.mxdemo` (replays, en-tête `MX06 1 0 1000 1722\n2025TrackStarter\n250sxf(2018)|…`) : non décodé. Pourrait donner la vraie trajectoire
  et les vitesses d'un pilote → piste pour mesurer les chronos réels.
- Paramètres `erode_*` : recopiés, pas étudiés.
- Pas de `statues` (barrières, tuff blocks, banderoles) dans le compound : sol nu.
