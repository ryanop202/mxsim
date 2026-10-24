# legacy_mx — v1 (1 MX + 2 SX), abandonnée

Ryan : « le MX ça va pas du tout, on laisse tomber ». Gardé pour mémoire et pour une éventuelle reprise du MX.

- Code : `scripts/layouts.py`, `build_compound.py`, `export.py`, `validate.py`, `figures.py`, `web_data.py`, `view_build.py`, `check_mx.py`.
- Reconstruire : `./make_all.sh mx` → `legacy_mx/build/` et `legacy_mx/tracks/RyanCompoundMX|SX1|SX2` (non versionnés, ~460 Mo).
  ⚠️ Ces dossiers v1 portent les **mêmes noms** `USLAND2026SX1/SX2` que la v3 : ne pas les copier dans le jeu en même temps.
- Résultat de la reconstruction (vérifié) : 32/32 contrôles v1 ; MX 7637 ft (~2:27 estimé), SX1 2631 ft, SX2 2613 ft.
- Pourquoi ça n'a pas marché et ce qu'il faudrait faire : `docs/04_mesures_mx.md`.
