# refs/ — archives de référence (non versionnées)

Les 3 archives analysées font 118 à 330 Mo : trop gros pour GitHub (limite 100 Mo par fichier),
et ce sont les pistes de quelqu'un d'autre. Elles restent **hors Git** et on les remet ici sur chaque PC.

## Où les mettre

```
refs/
  archives/                     <- les .rar tels quels (ignoré par git)
    JGMXDesertSand.rar
    JGMXDrDew.rar
    JGSX2026TestTracks.rar
  extracted/                    <- créé par tools/extract_refs.sh (ignoré par git)
    JGMXDesertSand/JGMXDesertSand/      terrain.hf, terrain.png, tilemap, tileinfo, timing_gates, edinfo, ...
    JGMXDrDew/JGMXDrDew/
    JGSX2026TestTracks/JGSX2026Arlington/
    JGSX2026TestTracks/JGSX2026Custom/      (= "2026 Test Track")
    JGSX2026TestTracks/JGSX2026Custom1/     (= "2026 Cleveland")
    JGSX2026TestTracks/JGSX2026Detroit/
    JGSX2026TestTracks/JGSX2026Glendale/
```

Autre emplacement possible : `export MXSIM_REF=/chemin/vers/extracted`.

## Empreintes (pour vérifier que c'est bien les mêmes fichiers)

| Archive | Taille (octets) | SHA-256 |
|---|---|---|
| JGMXDesertSand.rar | 178 128 872 | `841ce7916b6bcccd71d208fd517f8340a1d3cdf25f22a3efbeae2ae7fa6426d9` |
| JGMXDrDew.rar | 117 908 754 | `25618d34bdae747823f5873527145e51f4404860bd23bcc484d8dd761e666a56` |
| JGSX2026TestTracks.rar | 329 445 925 | `576c8f8d369c0dd5b888b586d9ff4f1f447abe0a6aad740a0dce26a9356bfec7` |

`sha256sum refs/archives/*.rar` (Linux/macOS) ou `Get-FileHash` (PowerShell).

## Extraction

Ce sont des RAR5. `unar` et `7z` plantent sur certains fichiers de ces archives ;
ce qui marche à coup sûr : **node-unrar-js 2.0.2** (pur JavaScript, aucun binaire).

```
npm install            # installe node-unrar-js@2.0.2 (package.json à la racine)
./tools/extract_refs.sh
```

WinRAR / 7-Zip récent sous Windows marchent aussi : il faut juste retrouver l'arborescence ci-dessus.

## Ce qui est déjà dans le repo sans les archives

Tout ce qui a été **mesuré** est dans `lib/` (JSON + stamps .npy) : on peut reconstruire le compound
(`./make_all.sh build`) sans refaire l'analyse. Les archives ne servent qu'à :
- refaire les mesures (`./make_all.sh analysis`) ;
- copier les textures / ciel / tileinfo dans les dossiers exportés (`export_sx.py`).
