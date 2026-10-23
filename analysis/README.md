# analysis/ — figures et intermédiaires des mesures

Produits par `./make_all.sh analysis` (et `preview_sx.py` pour `pv2_*`). Rien ici n'est utilisé directement par la construction,
sauf via `lib/`.

| Fichier | Contenu |
|---|---|
| `catalog_raw.json` | profils le long de toutes les lignes edinfo des 7 références (base de `sx_units.py`) |
| `sx_gallery.png` | galerie des blocs SX isolés |
| `sx_berms.png` | croissants détectés et leurs profils |
| `lanes_<ref>.json/png` | axes de couloir recalés, par piste JGSX |
| `starts_ref.png`, `starts_ref_<k>.png` | départs JGSX (grilles, ligne de départ, jonction, portes) |
| `gle_full.png`, `gle_sand_L.png`, `gle_sand_R.png`, `sand_stamps.png` | sable Glendale et découpe des stamps GL/GR |
| `pv2_sx1..3.png` | aperçu de chaque piste du compound seule + contrôles géométriques |
| `cplanes_<MX>.json/png` | profils MX à travers chaque checkpoint |
| `mx_units.json` | unités MX segmentées (→ `library.json`) |
| `centerline_Desert.*`, `cl_Desert.npz`, `clprof_Desert.png`, `mxfeat_Desert.json` | centreline Desert Sand, profil, détection de sauts |
| `desert_sections.png`, `mx_sections_qa.png` | contrôle visuel des sections MX |
