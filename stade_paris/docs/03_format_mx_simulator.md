# Format MX Simulator : ce qui a été vérifié

Version du jeu inspectée : **2025-03-26-1681** (journal du jeu). Sources : fichiers des pistes installées
(lecture seule), chaînes de `mx.exe` (formats de lecture et shaders), exporteurs officiels Blender
(`jm_export_25.py`, `jm_export_280.py` sur mxsimulator.com), forum officiel.

**V** = vérifié sur fichiers / binaire / doc officielle · **I** = déduit, à confirmer en jeu.

## Unités et repère

- Unités en **pieds** (V : roue avant de rayon 1,162, doc d'édition officielle).
- Y vers le haut, repère direct ; angles en radians (V).
- Chemins `@Piste/...` résolus dans un index unique : dossier du jeu, dossier personnel
  `%LOCALAPPDATA%\MX Simulator`, contenu des `.saf` (V). Un `x.jm` référencé trouve `x.jm.gz` (V).
- Fichiers texte en fins de ligne LF (V : forum, `lighting` cassé en CRLF).

## Modèles `.jm` (statues)

- `JM1`, puis un ou plusieurs blocs : `spec_exp spec_int r g b` / `nv nt` / sommets `x y z nx ny nz u v` / indices (V).
- Indices base 0 par bloc ; triangles anti-horaires = face avant ; V non inversé par rapport à Blender/OBJ (V).
- Bloc `-1 f r g b` = couche de réflexion d'environnement (V, exporteur officiel) : utilisé pour le verre.
- Bloc `-2 …` = non éclairé / pleine luminosité (I) : utilisé pour écrans, anneau LED, projecteurs.
- Plus grand modèle installé : 49 398 sommets (V) ; limite 16 bits non vérifiée → **export limité à 60 000 sommets par bloc**.
- Faces arrière probablement masquées (I) → surfaces vues des deux côtés doublées.
- `modele_lodN.jm` à côté de `modele.jm` = version lointaine (V : exemple CNDNorthshoresx, chaîne `_lod`,
  options `--lod-scale`). Distance de bascule = 2^N pieds (I : guide communautaire).

## Statues

`[x y z] yaw @modèle.jm @texture.png null` — y = hauteur au-dessus du terrain (V), collision `null` normale
pour le décor (V : toutes les tribunes WSX1). Une statue = un modèle = **une seule texture** (V).

## Textures et matériaux

- PNG, puissances de 2 conseillées (V : avertissement « Non power of 2 texture »).
- `-repeat` juste avant l'extension = répétition (V) ; compagnons `_norm` / `_spec` (V).
- Transparence = découpe uniquement (`alpha < 0,75` rejeté dans le shader, V) : pas de verre semi-transparent.
- Un seul soleil directionnel + ambiance (V) ; **pas de lumières ponctuelles**, pas d'ombres portées dynamiques
  sur les statues (I) ; éclairage du sol précalculé dans `shading.ppm` (V).

## Terrain et fichiers de piste

- `terrain.hf` = `n espacement min max` ; `terrain.png` 16 bits de (2^(n+1)+1)² pixels (V).
- `tilemap` = 2^n × 2^n octets, indices dans `tileinfo` (V).
- `shading.ppm` (P6, éclairage précalculé) et `shadingx2.ppm` (moitié) (V).
- Fichiers présents dans toutes les pistes installées : terrain.hf, terrain.png, tilemap, tileinfo,
  shading.ppm, shadingx2.ppm, lighting, statues, decals, timing_gates, desc (V).
- `timing_gates` exige une grille de départ et une boucle d'au moins 3 portes (V) → portes **provisoires**
  dans cette phase, à remplacer par celles de la vraie piste.

## Conséquences pour l'arène

| Besoin | Limite du moteur | Solution retenue |
|---|---|---|
| Verre des écailles translucide | pas de transparence douce | verre laiteux opaque + réflexion d'environnement |
| Projecteurs, LED de façade | pas de lumière ponctuelle | matériaux non éclairés + halo précalculé sur le sol |
| Intérieur couvert éclairé | un seul « soleil » global | variante d'éclairage « intérieur » (lumière quasi verticale) |
| Ombre du toit sur le sol | pas d'ombres dynamiques | ombrage précalculé dans `shading.ppm` |
| 24 000 sièges | coût géométrique | 24 sommets/siège, un modèle par bloc + version lointaine `_lod7` |
| Fichiers volumineux | — | modèles gzippés (`.jm.gz`), découpage spatial en tuiles de 48 m |
