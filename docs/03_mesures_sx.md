# 03 — Mesures SX (JGSX 2026) : méthode et résultats

C'est le cœur du projet : **tout ce qu'on sait de la géométrie des supercross JGSX**, mesuré sur les heightmaps.
Les chiffres complets (chaque unité, chaque bloc, chaque whoop) sont dans `docs/09_donnees_mesurees.md` et `docs/data/*.csv` ;
les données brutes réutilisables dans `lib/`.

## Principe de mesure

1. **Relire le terrain réel** (`terrain.png` + `terrain.hf`), sol de référence = médiane de la heightmap (~0 ft).
2. **Suivre les lignes de dessin de l'auteur** (`edinfo`, `add_gradient`) : chaque couloir a été dessiné le long d'une ligne.
   On échantillonne la heightmap réelle tous les 0,1 ft le long de la ligne (interpolation bilinéaire, grille 0,29 ft).
3. **Corriger l'axe** : la ligne de l'éditeur n'est pas toujours exactement au milieu du couloir. Quand des blocs isolés
   le permettent, l'axe est recalé sur l'orientation des blocs (« lane axis from N blocks, offset … ») — sinon on garde
   la ligne (« gradient line (no isolated block to verify) »).
4. **Découper en unités** : une unité commence et finit sur le sol (< 0,06 ft). On garde le profil exact, pas un modèle.
5. **Sens** : les profils sont orientés dans le sens de course du tour de référence (ordre des checkpoints).
6. **Dédoublonner** : les pistes test partagent des couloirs ; deux unités de même longueur (±1 ft), hauteur (±0,15 ft),
   nombre de crêtes et profil (écart max < 0,35 ft) = la même (`alias` dans `sx_units.json`).

Scripts : `sx_components.py` (blocs isolés 2D) → `sx_classify.py` → `sx_lateral.py` (profil en travers) → `sx_lanes.py`
(axes) → `sx_berms.py` + `berm_stamps.py` (virages) → `build_library.py` → `sx_units.py` (unités + écarts) →
`sx_whoops.py` → `sand_stamps.py` (sable Glendale) → `starts_ref.py` (départs).

## 1. Le bloc SX (profil en travers)

- Chaque obstacle est un bloc à **dessus plat de 30,4 ft** de large (= largeur de piste), avec un **flanc latéral
  de ~4 ft** (de 90 % à 10 % de la hauteur), quelle que soit la hauteur de l'obstacle (65 blocs mesurés, 4,0–4,9 ft).
- Modèle : `h(u, v) = p(u) × wall(|v| − 15,2)` avec p = profil le long du couloir, wall = courbe mesurée (médiane).
  Erreur de reconstruction ≈ 0,02 ft (RMSE) sur les blocs simples.
- Angle moyen du flanc : 33° (bloc de 3,7 ft) à 64° (step-up de 11,2 ft) — c'est la même largeur de flanc, donc plus raide quand c'est haut.
- Couloirs **espacés de 43 ft** d'axe à axe (piste 30,4 ft + ~12,6 ft entre deux pistes).

## 2. Les unités (bosses le long du couloir)

90 unités uniques, classées par hauteur (`sx_units.py → kind()`):

| Type | Règle | n | Exemples |
|---|---|---|---|
| `low` | H < 2,5 ft | 14 | petites bosses, entrées de whoops |
| `S` single | 2,5 ≤ H < 4,3 ft | 37 | les « singles » des rythmiques, 3,0–4,0 ft, 25–30 ft de long |
| `B` gros single / table courte | 4,3 ≤ H < 6,6, L < 62 ft | 17 | 5,8–6,2 ft (Arlington g37_2, tables Custom1 g71_1 / Arlington g49_2) |
| `T` table longue | 4,3 ≤ H < 6,6, L ≥ 62 ft | 1 | |
| `X` gros saut | H ≥ 6,6 ft | 6 | 7,1–7,9 ft (gros double Glendale g83), step-up 8,8 → 11,2 ft (Arlington g30) |
| `combo` | ≥ 2 crêtes dans un bloc | 15 | on-off (Detroit g35_0 : 6,2/5,8 + singles 3,6), table 9 ft (Arlington g20_1), trio de triple (Detroit g27_1) |

Géométrie médiane des faces (blocs isolés à 1 crête, sens de la ligne de dessin — `docs/data/sx_blocks.csv`) :

| Hauteur | n | Longueur pied à pied | Montée : longueur / angle max / angle du lip | Descente : longueur / angle max | Plateau |
|---|---|---|---|---|---|
| ~1,9 ft | 4 | 23 ft | 6,2 ft / 19° / 16° | 10,9 ft / 10° | 6,2 ft |
| ~2,9 ft (whoops) | 27 | 19,5 ft | 6,6 ft / 27° / 20° | 8,4 ft / 22° | 4,1 ft |
| ~3,7 ft (single) | 26 | 28 ft | 13,1 ft / 20° / 17° | 12,7 ft / 21° | 3,8 ft |
| ~4,8 ft | 3 | 40 ft | 18,9 ft / 16° / 15° | 17,3 ft / 21° | 4,2 ft |
| ~6,0 ft | 8 | 46 ft | 20,2 ft / 23° / 16° | 22,5 ft / 21° | 5,7 ft |
| ~7,6 ft | 4 | 44 ft | 17,4 ft / 32° / 25° | 22,2 ft / 26° | 4,7 ft |
| ~10 ft | 2 | 53 ft | 22,2 ft / 36° / 26° | 25,3 ft / 30° | 5,2 ft |

### Enchaînements (rythmiques)

- **Crête à crête : 34–38 ft** entre deux singles d'une rythmique → un double ≈ 36 ft, un **triple ≈ 72 ft**, un **quad ≈ 108 ft**.
- **Sol plat entre deux unités** (médianes utilisées par `compose.py`, table `GAP`) :
  S→S 5,3 ft · S→B 5,3 · B→S 2,75 · B→B 2,75 · S→combo 3,8 · combo→S 3,75 · combo→B 0,5 · B→combo 2,75 · low→low / low→S / S→low 8,9 ·
  X→S / S→X 16,25 ft.
- **Paires gardées telles quelles** (écart exact de la référence) : trio du triple Detroit g27 → Arlington g29_2 : 1,6 ft ;
  step-up Arlington g30_1 → g30_2 : 24,0 ft ; gros double Glendale g83_1 → g83_2 : 40,5 ft.
- Familles utilisées dans le compound (`layouts_sx.py`) :
  - `SA` singles Arlington 3,4–4,0 ft (6 unités) · `SD` singles Detroit/Glendale 3,0–3,7 ft (4) · `SC` singles Custom/Cleveland 3,5–3,9 ft (4)
  - `BB` gros singles 5,8–6,0 ft (3) · `TABLE_A` Custom1_g71_1 / `TABLE_B` Arlington_g49_2 tables 6,2 ft (dessus ~20 ft) · `TABLE9` Arlington_g20_1 table 9 ft
  - `TRIPLE` Detroit_g27_1 + Arlington_g29_2 (7,9 / 6,0 / 7,4) · `STEPUP` Arlington_g30_1/2 (8,8 → 11,2) · `BIGDBL` Glendale_g83_1/2 (7,1 → 7,9, 40,5 ft de sol)
  - `MIXED_DET` Detroit_g35_0 (couloir on-off complet de Detroit) · `SAND` unités du sable Glendale (non utilisées telles quelles en v3).

## 3. Whoops

- **Toutes les sections de whoops JGSX ont la même forme** (Detroit, Test Track, Cleveland) : 1re bosse d'entrée **1,88 ft**,
  puis ~**2,9 ft** (2,78–2,99), **pas de 20,0 ft** (19,5–20,4), séparées par 1–2 ft de sol.
- Longueurs : Detroit 10 whoops / 237 ft, Test Track 12 / 311 ft, Cleveland 10 / 271 ft.
- On prend les n premières (entrée comprise) : `('whoops', 'Custom_0', 12)`.
- Ryan : « les whoops vraiment bien, juste les changer entre les pistes » → SX1 12 whoops, SX2 7, SX3 10.

## 4. Virages : berms en croissant

`sx_berms.py` cherche les croissants (ajustement d'un cercle sur la crête) : 29 trouvés, dont deux familles nettes.

| Famille | Exemplaires | R crête | Ouverture | Hauteur | Rayon de trajectoire | Usage |
|---|---|---|---|---|---|---|
| **Gros** | 5 (Detroit ×2, Test Track, Arlington, Cleveland) | 40,4 ft | 130° | 5,7 ft (5,5–6,9) | **21,5 ft** | virage 180° entre deux couloirs (43 ft = 2 × 21,5) |
| **Petit** | 8 (Test Track ×4, Arlington ×2, Glendale, Cleveland) | 24,0 ft | 105° | 3,5 ft (2,9–4,3) | **11 ft** | virage 90° |

- Face intérieure (côté pilote) : ~17 ft de long, angle max 46–51° (gros) ; ~11 ft, 44–56° (petit). Face extérieure plus douce.
- Le compound utilise les **stamps exacts** de 6 berms (`lib/berm_*.npy`, copie 2D tel que construit, posée par rotation) :
  `big_det_a` (Detroit, H 6,9), `big_cus` (Test Track), `big_cle` (Cleveland, H 6,0), `small_cus_a`, `small_cus_b` (Test Track), `small_arl` (Arlington).
- **Le « petit rebord » à l'entrée des virages** (retour de Ryan v1) : la découpe du stamp laissait une marche de 0,30 ft au sol.
  Corrigé en v2 : stamps symétrisés + « jupe » qui descend jusqu'au sol (remplissage par descente). Contrôle automatique :
  marche sol → obstacle ≤ celle de Detroit (0,133 ft) + 0,02.

## 5. Sable (Glendale)

La photo de Ryan (`docs/img/photo_sable_reference_utilisateur.png`) = le sable de JGSX Glendale. Au lieu d'imiter, on **copie** :

- **GL** — le « J » de sable à gauche : entrée cap ouest, sortie cap ~nord-est après ~205° de virage, sortie décalée de **187 ft**
  sur le côté ; puis Glendale enchaîne une courbe plate de ~24° (reprise dans SX3 : R 80 ft). Ligne de course 552 ft, H max 4,58 ft.
- **GR** — le virage de sable en S : entrée cap est, sortie cap ouest (~180°), décalé de **114 ft**. Ligne 261 ft, H max 4,94 ft.
  Posé **en miroir** dans SX3.
- Contenu d'un stamp : hauteurs exactes au-dessus du sol (berms organiques, petites ondulations ; les creux de Glendale, jusqu'à −0,84 ft,
  sont ramenés à 0 : le chenal est au niveau du sol dans le compound), tiles Glendale
  (`Sand Exit` = 10, `Sand Bump Solo` = 12, `Jumps Sx` = 3, `Berm Exit Sx` = 1), et la **ligne de course** (squelette du chenal)
  qui devient un segment `P` du chemin.
- Découpage (`sand_stamps.py`) : zone = chenal + obstacles qui en partent, en excluant les obstacles voisins de Glendale
  (dilatés de 5 ft), bord adouci par le profil de flanc SX. GL : le croissant du haut (z < 172, x < 122) est gardé avec un bord
  « flanc SX » ; GR : chenal + 1,5 ft, z < 397, x ≥ 425, sans le single du cp10. Marche résiduelle au bord : GL 0,085 ft, GR 0,103 ft.
- Ligne d'approche ajoutée devant chaque stamp : GL depuis (147, 138) cap ouest ; GR depuis (434, 263) cap est.

## 6. Départs JGSX (comment ils font une vraie course)

Mesuré par `starts_ref.py` (figure `analysis/starts_ref.png`) :

- **22 grilles au pas de 4 ft** (84 ft de large), toutes face à +x, sur une **ligne de départ qui n'est pas dans le tour**
  (Detroit x = 41, z 196–280 ; Arlington x = 79 ; Glendale x = 87 ; Cleveland x = 60).
- La ligne de départ est droite, longue, puis **rejoint le tour en entonnoir** juste avant un **premier virage à gros berm**.
- 1er checkpoint large (demi-largeur 33–47 ft) pour attraper toute la grille, puis 16–25 ft.
- `firstlap` commence à la jonction ; `normallap` ajoute 1 à 14 portes « tour seulement » sur la portion avant la jonction
  (Detroit 20–23, Arlington 13–21, Glendale 14–27, Test Track 23–27, Cleveland 23).
- Leçon pour nos pistes : un berm posé **à** la jonction bloque toujours la ligne derrière lui → la ligne de départ doit être
  parallèle/décalée ou dans l'infield, et l'entonnoir doit être plat.

## 7. Ce qui n'est pas mesuré

- Les **tiles de transition** (Transition Sx, Jump Transition Sx, Whoop Transition, Mulch Mix…) : non reproduits ; le compound
  n'a que 8 tiles (sol, sauts, whoops, berms, 4 sables).
- Les **barrières / tuff blocks / banderoles** (`statues`) : pas reprises.
- La physique (friction, érosion) : recopiée telle quelle, pas étudiée.
- Les replays `.mxdemo` : pas décodés → pas de vraies trajectoires ni vitesses.
