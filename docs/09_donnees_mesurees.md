# 09 — Données mesurées (généré automatiquement)

> Fichier produit par `scripts/gen_docs.py` à partir de `lib/*.json`. Ne pas éditer à la main.
> Unités : pieds (ft) = unités monde MX Simulator. 1 ft = 0,3048 m.

## 1. Unités SX (bibliothèque des rythmiques)

90 unités uniques (après dédoublonnage de 147 unités trouvées sur 70 lignes JGSX).
Une **unité** = un obstacle séparé par du sol plat avant et après (single, double, table, on-off...).
Profil exact échantillonné à 0,1 ft dans `lib/sx_units.json` (`units[uid].prof`). Fichier complet : `docs/data/sx_units.csv`.

Types :

- `S` : single (3-4.3 ft) — 37 unités
- `B` : gros single / table courte (4.3-6.6 ft, < 62 ft) — 17 unités
- `T` : table longue (4.3-6.6 ft, >= 62 ft) — 1 unités
- `X` : gros saut (>= 6.6 ft) — 6 unités
- `low` : petite bosse (< 2.5 ft) — 14 unités
- `combo` : bloc multi-crêtes (on-off, step, table+...) — 15 unités

| uid | type | L ft | H ft | crêtes | aussi présente sur |
|---|---|---|---|---|---|
| Custom1_g71_6 | B | 35.0 | 4.5 | 4.5 | — |
| Glendale_g28_2 | B | 28.4 | 4.7 | 4.7 | — |
| Detroit_g29_3 | B | 37.6 | 4.71 | 4.71 | — |
| Custom_g30_3 | B | 34.6 | 4.88 | 4.88 | — |
| Glendale_g80_1 | B | 41.3 | 5.0 | 5.0 | — |
| Detroit_g0_2 | B | 29.8 | 5.75 | 5.75 | — |
| Glendale_g30_0 | B | 51.0 | 5.77 | 5.77 | — |
| Arlington_g28_2 | B | 31.0 | 5.78 | 5.78 | — |
| Arlington_g1_2 | B | 47.7 | 5.79 | 5.79 | — |
| Arlington_g37_2 | B | 46.6 | 5.9 | 5.9 | — |
| Custom_g0_0 | B | 60.0 | 5.95 | 5.95 | — |
| Custom1_g29_3 | B | 48.0 | 6.0 | 6.0 | — |
| Custom_g6_1 | B | 30.6 | 6.05 | 6.05 | Custom_g23_1, Detroit_g6_2, Detroit_g23_0 |
| Arlington_g6_2 | B | 28.8 | 6.11 | 6.11 | Custom1_g28_0 |
| Arlington_g49_2 | B | 55.0 | 6.18 | 6.18 | — |
| Custom1_g71_1 | B | 59.1 | 6.24 | 6.24 | — |
| Custom1_g59_1 | B | 30.3 | 6.35 | 6.35 | Custom_g42_1 |
| Custom_g32_9 | S | 19.5 | 2.78 | 2.78 | Custom_g32_11, Custom_g32_12, Detroit_g32_9 |
| Custom1_g34_1 | S | 26.5 | 2.91 | 2.91 | — |
| Arlington_g20_3 | S | 37.3 | 2.99 | 2.99 | — |
| Custom_g32_2 | S | 20.3 | 2.99 | 2.99 | Custom_g32_3, Custom_g32_4, Custom_g32_5, Custom_g32_6, Custom_g32_7, Custom_g32_8, Custom_g32_10, Detroit_g32_2, Detroit_g32_3, Detroit_g32_4, Detroit_g32_5, Detroit_g32_6, Detroit_g32_7, Detroit_g32_8, Detroit_g32_10, Glendale_g83_4 |
| Detroit_g36_1 | S | 29.7 | 2.99 | 2.99 | — |
| Custom_g50_1 | S | 26.6 | 3.05 | 3.05 | — |
| Arlington_g20_2 | S | 32.7 | 3.05 | 3.05 | — |
| Arlington_g24_1 | S | 27.9 | 3.13 | 3.13 | — |
| Arlington_g2_0 | S | 33.2 | 3.15 | 3.15 | — |
| Arlington_g45_2 | S | 26.6 | 3.17 | 3.17 | — |
| Glendale_g36_1 | S | 29.7 | 3.19 | 3.19 | — |
| Arlington_g37_0 | S | 27.4 | 3.36 | 3.36 | — |
| Arlington_g43_2 | S | 28.9 | 3.36 | 3.36 | Detroit_g11_1, Detroit_g35_3 |
| Glendale_g47_1 | S | 26.4 | 3.38 | 3.38 | — |
| Glendale_g84_2 | S | 30.9 | 3.45 | 3.45 | — |
| Arlington_g49_3 | S | 26.7 | 3.48 | 3.48 | — |
| Custom_g41_0 | S | 26.8 | 3.5 | 3.5 | Detroit_g24_2, Glendale_g85_2 |
| Custom1_g71_3 | S | 30.3 | 3.52 | 3.52 | Custom1_g71_4 |
| Detroit_g11_2 | S | 33.1 | 3.55 | 3.55 | Glendale_g84_3 |
| Glendale_g84_4 | S | 42.9 | 3.56 | 3.56 | — |
| Custom_g55_2 | S | 29.9 | 3.6 | 3.6 | — |
| Arlington_g43_1 | S | 28.6 | 3.6 | 3.6 | Detroit_g36_5, Glendale_g36_5, Glendale_g84_0 |
| Custom1_g62_2 | S | 26.1 | 3.6 | 3.6 | — |
| Arlington_g1_4 | S | 35.1 | 3.61 | 3.61 | — |
| Custom1_g29_1 | S | 32.2 | 3.63 | 3.63 | Detroit_g36_2, Glendale_g36_2 |
| Custom1_g71_2 | S | 30.3 | 3.64 | 3.64 | — |
| Arlington_g37_1 | S | 27.9 | 3.66 | 3.66 | Arlington_g49_1, Glendale_g36_6, Glendale_g84_1 |
| Detroit_g36_4 | S | 36.5 | 3.67 | 3.67 | Glendale_g36_4 |
| Arlington_g1_1 | S | 28.9 | 3.69 | 3.69 | Arlington_g20_4, Detroit_g35_1 |
| Custom_g24_1 | S | 27.4 | 3.78 | 3.78 | — |
| Arlington_g1_3 | S | 31.9 | 3.81 | 3.81 | Arlington_g37_3 |
| Custom1_g71_5 | S | 34.7 | 3.87 | 3.87 | Detroit_g36_3, Glendale_g36_3 |
| Detroit_g12_0 | S | 123.0 | 3.96 | 3.96 | — |
| Custom_g47_1 | S | 27.4 | 4.01 | 4.01 | — |
| Arlington_g37_4 | S | 32.3 | 4.02 | 4.02 | — |
| Glendale_g40_3 | S | 47.1 | 4.07 | 4.07 | — |
| Detroit_g34_0 | S | 27.4 | 4.1 | 4.1 | — |
| Custom1_g23_1 | T | 63.0 | 6.01 | 6.01 | — |
| Detroit_g31_1 | X | 29.4 | 6.94 | 6.94 | — |
| Arlington_g29_2 | X | 52.5 | 7.35 | 7.35 | Custom1_g29_4, Custom_g29_2, Detroit_g27_2, Detroit_g29_2 |
| Glendale_g83_2 | X | 57.0 | 7.94 | 7.94 | — |
| Custom1_g30_2 | X | 36.7 | 8.81 | 8.81 | Custom_g30_1, Detroit_g30_1, Glendale_g30_1 |
| Arlington_g30_1 | X | 38.4 | 8.83 | 8.83 | — |
| Arlington_g30_2 | X | 72.0 | 11.22 | 11.22 | Custom1_g30_3, Custom_g30_2, Detroit_g30_2, Glendale_g30_2 |
| Arlington_g1_5 | combo | 61.0 | 3.72 | 3.72 / 1.17 | — |
| Custom_g49_0 | combo | 85.7 | 5.77 | 3.68 / 5.77 | — |
| Detroit_g35_2 | combo | 74.5 | 5.79 | 5.79 / 3.68 | — |
| Custom_g55_3 | combo | 78.6 | 5.8 | 5.8 / 3.6 | — |
| Detroit_g28_0 | combo | 65.4 | 5.93 | 5.93 / 3.29 | — |
| Custom_g55_1 | combo | 120.1 | 5.98 | 2.81 / 5.98 / 5.96 | — |
| Custom1_g54_0 | combo | 67.4 | 5.98 | 5.98 / 3.12 | — |
| Detroit_g35_0 | combo | 221.3 | 6.2 | 2.83 / 6.2 / 5.79 / 3.6 / 5.8 / 3.6 | — |
| Glendale_g83_1 | combo | 34.7 | 7.14 | 7.14 / 7.14 | — |
| Custom1_g29_2 | combo | 39.3 | 7.91 | 7.91 / 7.91 | — |
| Arlington_g29_1 | combo | 86.9 | 7.92 | 7.92 / 6.0 | — |
| Custom_g29_1 | combo | 86.7 | 7.92 | 7.92 / 7.92 / 7.92 / 6.0 | — |
| Detroit_g27_1 | combo | 86.7 | 7.92 | 7.92 / 7.92 / 6.0 | — |
| Detroit_g29_1 | combo | 86.8 | 7.92 | 7.92 / 7.92 / 7.92 / 7.92 / 7.92 / 6.0 | — |
| Arlington_g20_1 | combo | 67.9 | 9.01 | 5.26 / 9.01 / 9.01 / 9.01 | — |
| Arlington_g28_1 | low | 29.8 | 0.8 | 0.8 | — |
| Glendale_g86_1 | low | 25.7 | 0.83 | 0.83 | — |
| Glendale_g63_3 | low | 20.5 | 1.04 | 1.04 | — |
| Glendale_g66_1 | low | 27.5 | 1.2 | 1.2 | — |
| Glendale_g66_2 | low | 31.6 | 1.21 | 1.21 | — |
| Glendale_g86_0 | low | 35.9 | 1.21 | 1.21 | — |
| Glendale_g30_3 | low | 33.9 | 1.25 | 1.25 | — |
| Glendale_g65_3 | low | 29.3 | 1.27 | 1.27 | — |
| Custom_g49_1 | low | 24.4 | 1.56 | 1.56 | — |
| Glendale_g65_2 | low | 26.3 | 1.62 | 1.62 | — |
| Custom_g32_1 | low | 23.5 | 1.88 | 1.88 | Detroit_g32_1, Glendale_g83_3 |
| Custom1_g30_1 | low | 26.9 | 1.88 | 1.88 | — |
| Glendale_g65_1 | low | 19.1 | 2.18 | 2.18 | — |
| Glendale_g40_2 | low | 27.7 | 2.47 | 2.47 | — |

### Sol plat entre deux unités consécutives (mesuré)

Écart pied à pied entre deux unités qui se suivent sur une ligne de référence. Ce tableau compte **toutes** les lignes, y compris les doublons (les pistes test JGSX partagent beaucoup de couloirs) : les médianes diffèrent donc un peu des constantes `GAP` de `compose.py`, fixées en v2 sur les couloirs rythmiques sans doublons (S→S = 5,3 ft).

| paire | n | médiane ft | min | max |
|---|---|---|---|---|
| S → S | 41 | 4.5 | 0.6 | 40.9 |
| combo → X | 5 | 1.6 | 1.5 | 40.5 |
| X → X | 5 | 22.2 | 21.9 | 26.6 |
| S → B | 4 | 5.3 | 3.8 | 9.3 |
| B → S | 4 | 2.75 | 1.7 | 4.2 |
| S → combo | 4 | 3.8 | 2.1 | 25.8 |
| combo → S | 4 | 3.75 | 2.9 | 5.0 |
| low → S | 4 | 1.2 | 1.1 | 5.2 |
| low → low | 4 | 8.85 | 4.1 | 14.3 |
| B → X | 2 | 11.5 | 1.6 | 21.4 |
| X → B | 2 | 16.25 | 14.8 | 17.7 |
| X → low | 2 | 9.3 | 6.5 | 12.1 |
| low → B | 1 | 16.9 | 16.9 | 16.9 |
| combo → B | 1 | 0.5 | 0.5 | 0.5 |
| low → X | 1 | 31.9 | 31.9 | 31.9 |
| combo → low | 1 | 26.6 | 26.6 | 26.6 |

### Séquences complètes des lignes de référence

`·` = morceau non classé (bord, virage, bosse coupée). Écarts en ft dans le même ordre.

| ref | ligne | unités | écarts ft |
|---|---|---|---|
| Arlington | g1 | · → Arlington_g1_1 → Arlington_g1_2 → Arlington_g1_3 → Arlington_g1_4 → Arlington_g1_5 | 8.3 / 3.8 / 3.3 / 1.9 / 3.7 |
| Arlington | g2 | Arlington_g2_0 → · | 22.3 |
| Arlington | g6 | · → · → Arlington_g6_2 | 11.3 / 20.3 |
| Arlington | g20 | · → Arlington_g20_1 → Arlington_g20_2 → Arlington_g20_3 → Arlington_g1_1 → · | 16.8 / 5.0 / 39.3 / 10.2 / 3.7 |
| Arlington | g24 | · → Arlington_g24_1 | 40.4 |
| Arlington | g28 | · → Arlington_g28_1 → Arlington_g28_2 | 4.4 / 16.9 |
| Arlington | g29 | · → Arlington_g29_1 → Arlington_g29_2 | 44.0 / 1.5 |
| Arlington | g30 | · → Arlington_g30_1 → Arlington_g30_2 | 24.0 / 26.3 |
| Arlington | g33 | · → · | 35.2 |
| Arlington | g37 | Arlington_g37_0 → Arlington_g37_1 → Arlington_g37_2 → Arlington_g1_3 → Arlington_g37_4 → · | 9.0 / 5.0 / 4.2 / 3.4 / 3.4 |
| Arlington | g43 | · → Arlington_g43_1 → Arlington_g43_2 → · | 4.2 / 11.8 / 16.5 |
| Arlington | g45 | · → · → Arlington_g45_2 | 4.2 / 11.5 |
| Arlington | g49 | · → Arlington_g37_1 → Arlington_g49_2 → Arlington_g49_3 → · | 28.1 / 5.6 / 1.7 / 28.2 |
| Custom1 | g23 | · → Custom1_g23_1 | 23.5 |
| Custom1 | g28 | Arlington_g6_2 |  |
| Custom1 | g29 | · → Custom1_g29_1 → Custom1_g29_2 → Custom1_g29_3 → Arlington_g29_2 → · | 3.0 / 25.8 / 0.5 / 1.6 / 29.1 |
| Custom1 | g30 | · → Custom1_g30_1 → Custom1_g30_2 → Arlington_g30_2 → · | 9.2 / 31.9 / 21.9 / 55.0 |
| Custom1 | g34 | · → Custom1_g34_1 | 36.5 |
| Custom1 | g54 | Custom1_g54_0 |  |
| Custom1 | g59 | · → Custom1_g59_1 → · | 35.1 / 12.5 |
| Custom1 | g62 | · → · → Custom1_g62_2 | 16.3 / 23.0 |
| Custom1 | g71 | · → Custom1_g71_1 → Custom1_g71_2 → Custom1_g71_3 → Custom1_g71_3 → Custom1_g71_5 → Custom1_g71_6 | 3.8 / 2.2 / 8.1 / 6.8 / 4.8 / 9.3 |
| Custom | g0 | Custom_g0_0 |  |
| Custom | g6 | · → Custom_g6_1 | 54.9 |
| Custom | g23 | · → Custom_g6_1 | 27.4 |
| Custom | g24 | · → Custom_g24_1 | 37.0 |
| Custom | g28 | · → · | 21.3 |
| Custom | g29 | · → Custom_g29_1 → Arlington_g29_2 → · | 50.1 / 1.6 / 33.9 |
| Custom | g30 | · → Custom1_g30_2 → Arlington_g30_2 → Custom_g30_3 | 15.4 / 21.9 / 17.7 |
| Custom | g32 | · → Custom_g32_1 → Custom_g32_2 → Custom_g32_2 → Custom_g32_2 → Custom_g32_2 → Custom_g32_2 → Custom_g32_2 → Custom_g32_2 → Custom_g32_9 → Custom_g32_2 → Custom_g32_9 → Custom_g32_9 → · | 20.3 / 1.2 / 1.2 / 1.2 / 1.2 / 1.1 / 1.3 / 1.2 / 1.9 / 1.1 / 1.5 / 0.6 / 24.7 |
| Custom | g41 | Custom_g41_0 → · | 10.4 |
| Custom | g42 | · → Custom1_g59_1 → · | 58.9 / 4.2 |
| Custom | g47 | · → Custom_g47_1 | 57.3 |
| Custom | g49 | Custom_g49_0 → Custom_g49_1 | 26.6 |
| Custom | g50 | · → Custom_g50_1 | 43.1 |
| Custom | g55 | · → Custom_g55_1 → Custom_g55_2 → Custom_g55_3 → · | 16.3 / 3.8 / 2.1 / 9.0 |
| Detroit | g0 | · → · → Detroit_g0_2 | 12.4 / 31.9 |
| Detroit | g6 | · → · → Custom_g6_1 | 14.9 / 25.1 |
| Detroit | g11 | · → Arlington_g43_2 → Detroit_g11_2 → · | 3.9 / 4.5 / 24.4 |
| Detroit | g12 | Detroit_g12_0 |  |
| Detroit | g13 | · → · | 1.1 |
| Detroit | g14 | · |  |
| Detroit | g15 | · → · | 1.7 |
| Detroit | g16 | · → · | 2.0 |
| Detroit | g17 | · |  |
| Detroit | g23 | Custom_g6_1 |  |
| Detroit | g24 | · → · → Custom_g41_0 | 11.2 / 24.6 |
| Detroit | g27 | · → Detroit_g27_1 → Arlington_g29_2 → · | 49.8 / 1.7 / 26.5 |
| Detroit | g28 | Detroit_g28_0 |  |
| Detroit | g29 | · → Detroit_g29_1 → Arlington_g29_2 → Detroit_g29_3 | 12.9 / 1.6 / 14.8 |
| Detroit | g30 | · → Custom1_g30_2 → Arlington_g30_2 → · | 46.2 / 26.6 / 12.9 |
| Detroit | g31 | · → Detroit_g31_1 | 47.8 |
| Detroit | g32 | · → Custom_g32_1 → Custom_g32_2 → Custom_g32_2 → Custom_g32_2 → Custom_g32_2 → Custom_g32_2 → Custom_g32_2 → Custom_g32_2 → Custom_g32_9 → Custom_g32_2 | 26.4 / 1.2 / 1.2 / 1.1 / 1.2 / 1.2 / 1.2 / 1.2 / 1.9 / 1.1 |
| Detroit | g34 | Detroit_g34_0 |  |
| Detroit | g35 | Detroit_g35_0 → Arlington_g1_1 → Detroit_g35_2 → Arlington_g43_2 | 2.9 / 3.9 / 3.7 |
| Detroit | g36 | · → Detroit_g36_1 → Custom1_g29_1 → Custom1_g71_5 → Detroit_g36_4 → Arlington_g43_1 → · | 9.7 / 5.8 / 5.2 / 5.3 / 6.8 / 2.8 |
| Glendale | g28 | · → · → Glendale_g28_2 | 15.7 / 19.8 |
| Glendale | g30 | Glendale_g30_0 → Custom1_g30_2 → Arlington_g30_2 → Glendale_g30_3 | 21.4 / 22.2 / 12.1 |
| Glendale | g36 | · → Glendale_g36_1 → Custom1_g29_1 → Custom1_g71_5 → Detroit_g36_4 → Arlington_g43_1 → Arlington_g37_1 | 18.6 / 5.8 / 5.2 / 5.3 / 6.8 / 13.1 |
| Glendale | g40 | · → · → Glendale_g40_2 → Glendale_g40_3 → · → · → · → · | 8.3 / 11.1 / 5.2 / 62.9 / 10.1 / 8.6 / 30.7 |
| Glendale | g47 | · → Glendale_g47_1 | 14.4 |
| Glendale | g63 | · → · → · → Glendale_g63_3 → · | 12.8 / 12.0 / 7.0 / 17.3 |
| Glendale | g65 | · → Glendale_g65_1 → Glendale_g65_2 → Glendale_g65_3 | 2.6 / 12.2 / 5.5 |
| Glendale | g66 | · → Glendale_g66_1 → Glendale_g66_2 → · | 39.4 / 14.3 / 8.6 |
| Glendale | g79 | · → · | 8.6 |
| Glendale | g80 | · → Glendale_g80_1 → · → · | 15.0 / 5.8 / 6.3 |
| Glendale | g83 | · → Glendale_g83_1 → Glendale_g83_2 → Custom_g32_1 → Custom_g32_2 → · | 49.1 / 40.5 / 6.5 / 1.1 / 1.2 |
| Glendale | g84 | Arlington_g43_1 → Arlington_g37_1 → Glendale_g84_2 → Detroit_g11_2 → Glendale_g84_4 → · | 13.1 / 7.2 / 5.4 / 40.9 / 36.1 |
| Glendale | g85 | · → · → Custom_g41_0 | 25.7 / 24.6 |
| Glendale | g86 | Glendale_g86_0 → Glendale_g86_1 | 4.1 |

## 2. Whoops

Les 3 sections de whoops JGSX ont la même forme : 1re bosse d’entrée ~1,9 ft puis ~2,9 ft, pas de 20 ft, séparées par 1-2 ft de sol.
`compose.whoops(key, n)` coupe les n premières (bosse d’entrée comprise) sur le sol après la n-ième crête.

| clé | ref | nb | L ft | hauteurs ft | pas médian | min | max |
|---|---|---|---|---|---|---|---|
| Detroit_0 | JGSX2026Detroit | 10 | 237.2 | 1.88 / 2.99 / 2.87 / 2.89 / 2.86 / 2.85 / 2.94 / 2.95 / 2.78 / 2.86 | 20.0 | 19.5 | 20.4 |
| Custom_0 | JGSX2026Custom | 12 | 311.1 | 1.88 / 2.99 / 2.87 / 2.89 / 2.86 / 2.85 / 2.94 / 2.95 / 2.78 / 2.86 / 2.81 / 2.78 | 20.0 | 19.7 | 20.4 |
| Custom1_0 | JGSX2026Custom1 | 10 | 271.3 | 1.88 / 2.99 / 2.87 / 2.89 / 2.86 / 2.85 / 2.94 / 2.95 / 2.78 / 2.85 | 20.1 | 19.7 | 20.3 |

## 3. Berms SX (virages en croissant)

Modèle moyen (`library.json`) :

- **gros berm** : R crête 40.4 ft, ouverture 130°, H 5.74 ft, 5 exemplaires mesurés ; trajectoire à r ≈ 21,5 ft (virage 180°).
- **petit berm** : R crête 24.0 ft, ouverture 105°, H 3.52 ft, 8 exemplaires ; trajectoire r ≈ 11 ft (virage 90°).

Le compound utilise les **stamps exacts** (copie 2D tel que construit, `lib/berm_*.npy`) :

| clé | ref | cx | cz | R crête | H | r trajectoire | angle milieu ° | px |
|---|---|---|---|---|---|---|---|---|
| big_det_a | JGSX2026Detroit | 102.5 | 154.3 | 41.5 | 6.94 | 22.8 | -179.0 | 493×493 |
| big_cus | JGSX2026Custom | 515.4 | 165.2 | 39.6 | 6.06 | 21.2 | -89.3 | 480×481 |
| big_cle | JGSX2026Custom1 | 124.7 | 387.9 | 39.8 | 5.99 | 21.4 | 179.1 | 482×482 |
| small_cus_a | JGSX2026Custom | 74.2 | 145.2 | 23.9 | 4.15 | 10.9 | -139.8 | 372×372 |
| small_cus_b | JGSX2026Custom | 524.4 | 387.4 | 24.2 | 3.78 | 11.3 | 37.4 | 374×375 |
| small_arl | JGSX2026Arlington | 533.0 | 164.5 | 22.5 | 3.72 | 10.5 | -40.9 | 362×362 |

Membres mesurés : gros = Detroit (102,154), Detroit (136,344), Custom (515,165), Arlington (159,341), Custom1 (125,388) ; petits = Custom (74,145), Custom (143,187), Custom (524,387), Custom (76,403), Arlington (146,145), Arlington (533,164), Glendale (557,408), Custom1 (508,394)

## 4. Profil en travers des obstacles SX

h(u, v) = p(u) × wall(|v| − 30.4/2) : dessus plat de **30.4 ft**, flanc qui passe de 90 % à 10 % de la hauteur entre +0.6 et +4.5 ft du bord (≈ 3.9 ft).
Médiane sur 65 blocs isolés (RMSE ≈ 0,02 ft). Courbe `wall` dans `library.json → sx_lateral`.

## 5. Sable Glendale (stamps)

| clé | px | largeur ft | profondeur ft | H max | coupe au bord | pts ligne | longueur ligne ft | tiles Glendale |
|---|---|---|---|---|---|---|---|---|
| GL | 707×1295 | 204.9 | 375.2 | 4.58 | 0.418 | 552 | 514.9 | 1=Berm Exit Sx, 3=Jumps Sx, 10=Sand Exit, 12=Sand Bump Solo |
| GR | 742×673 | 215.0 | 195.0 | 4.94 | 0.0 | 261 | 246.3 | 3=Jumps Sx, 10=Sand Exit |

- `GL` : le J de sable à gauche de Glendale (≈ 230°), sortie décalée de 187 ft.
- `GR` : le virage de sable en S (≈ 165°), sortie décalée de 114 ft (posé en miroir dans SX3).

## 6. Blocs SX isolés (tous les obstacles détachés des 5 pistes JGSX)

132 blocs ; stamps 2D dans `lib/sx/<id>.npy` (régénérés par `sx_components.py`). Tableau complet : `docs/data/sx_blocks.csv`.

| ref | blocs |
|---|---|
| JGSX2026Detroit | 35 |
| JGSX2026Custom | 36 |
| JGSX2026Arlington | 19 |
| JGSX2026Glendale | 19 |
| JGSX2026Custom1 | 23 |

## 7. Sections SX complètes (v1, lignes entières)

| clé | ref | ligne | L ft | éléments | axe |
|---|---|---|---|---|---|
| whoops_det | Detroit | g32 | 206.8 | [{'foot0': 2.5, 'foot1': 24.400000000000002, 'crest': 16.6, 'H': 1.8425638860915632, 'top': 6.200000000000001, 'up_max': 10.005556434710769, 'dn_max': 19.46836645475403, 'up_L': 10.4, 'dn_L': 5.300000000000001}, {'foot0': 26.0, 'foot1': 44.800000000000004, 'crest': 36.9, 'H': 2.954689585295602, 'top': 3.700000000000003, 'up_max': 21.34491836633038, 'dn_max': 27.855823140619812, 'up_L': 8.899999999999999, 'dn_L': 6.200000000000003}, {'foot0': 46.400000000000006, 'foot1': 64.7, 'crest': 56.7, 'H': 2.8337054945076643, 'top': 4.199999999999996, 'up_max': 22.497887384556613, 'dn_max': 26.815014547458535, 'up_L': 7.899999999999999, 'dn_L': 6.200000000000003}, {'foot0': 66.4, 'foot1': 84.80000000000001, 'crest': 76.7, 'H': 2.8597774346550326, 'top': 4.099999999999994, 'up_max': 22.306889058985437, 'dn_max': 26.829163624618904, 'up_L': 8.0, 'dn_L': 6.300000000000011}, {'foot0': 86.4, 'foot1': 104.80000000000001, 'crest': 96.7, 'H': 2.827916498101555, 'top': 4.199999999999989, 'up_max': 22.206608204414344, 'dn_max': 26.38787316681571, 'up_L': 7.900000000000006, 'dn_L': 6.300000000000011}, {'foot0': 106.4, 'foot1': 124.7, 'crest': 116.7, 'H': 2.8155638526384554, 'top': 4.0, 'up_max': 22.1181676301261, 'dn_max': 26.664928208607737, 'up_L': 8.099999999999994, 'dn_L': 6.200000000000003}, {'foot0': 126.4, 'foot1': 144.8, 'crest': 137.0, 'H': 2.906478484837207, 'top': 3.5999999999999943, 'up_max': 21.733302571250565, 'dn_max': 27.4920636490862, 'up_L': 8.5, 'dn_L': 6.300000000000011}, {'foot0': 146.4, 'foot1': 164.60000000000002, 'crest': 157.10000000000002, 'H': 2.9141302556564077, 'top': 3.700000000000017, 'up_max': 21.903103482944307, 'dn_max': 27.956715264316294, 'up_L': 8.5, 'dn_L': 6.0}, {'foot0': 166.70000000000002, 'foot1': 184.8, 'crest': 176.60000000000002, 'H': 2.7472551153199802, 'top': 4.199999999999989, 'up_max': 22.147660177193888, 'dn_max': 25.774491239102744, 'up_L': 7.599999999999994, 'dn_L': 6.300000000000011}, {'foot0': 186.3, 'foot1': 204.5, 'crest': 196.60000000000002, 'H': 2.8237708921182345, 'top': 4.199999999999989, 'up_max': 22.562827257458782, 'dn_max': 27.17848404620291, 'up_L': 8.0, 'dn_L': 6.0}] | lane axis from 10 blocks: 0.0 deg / +12.0 ft from the gradient line |
| whoops_cus | Custom | g32 | 246.8 | [{'foot0': 2.6, 'foot1': 24.400000000000002, 'crest': 16.5, 'H': 1.8416152605175953, 'top': 6.200000000000001, 'up_max': 9.996746804171512, 'dn_max': 19.478868697008142, 'up_L': 10.3, 'dn_L': 5.300000000000001}, {'foot0': 26.0, 'foot1': 44.800000000000004, 'crest': 36.9, 'H': 2.9532218648111748, 'top': 3.700000000000003, 'up_max': 21.340492147670588, 'dn_max': 27.8559521599697, 'up_L': 8.899999999999999, 'dn_L': 6.200000000000003}, {'foot0': 46.5, 'foot1': 64.8, 'crest': 56.6, 'H': 2.8326798309436527, 'top': 4.199999999999996, 'up_max': 22.446019993673577, 'dn_max': 26.829713288637627, 'up_L': 7.800000000000004, 'dn_L': 6.299999999999997}, {'foot0': 66.4, 'foot1': 84.80000000000001, 'crest': 76.80000000000001, 'H': 2.858556713300842, 'top': 4.099999999999994, 'up_max': 22.282255118252493, 'dn_max': 26.84264330071955, 'up_L': 8.0, 'dn_L': 6.300000000000011}, {'foot0': 86.4, 'foot1': 104.80000000000001, 'crest': 96.80000000000001, 'H': 2.8260378361283354, 'top': 4.199999999999989, 'up_max': 22.192244884164193, 'dn_max': 26.441499153577855, 'up_L': 7.900000000000006, 'dn_L': 6.300000000000011}, {'foot0': 106.5, 'foot1': 124.7, 'crest': 116.80000000000001, 'H': 2.815123559680005, 'top': 4.0, 'up_max': 22.106403689093238, 'dn_max': 26.67509991068705, 'up_L': 8.0, 'dn_L': 6.200000000000003}, {'foot0': 126.4, 'foot1': 144.8, 'crest': 136.9, 'H': 2.905072572019058, 'top': 3.5999999999999943, 'up_max': 21.73087219721566, 'dn_max': 27.516394170278886, 'up_L': 8.5, 'dn_L': 6.300000000000011}, {'foot0': 146.4, 'foot1': 164.60000000000002, 'crest': 157.10000000000002, 'H': 2.9135983064405115, 'top': 3.700000000000017, 'up_max': 21.910337492181803, 'dn_max': 27.97850225776723, 'up_L': 8.5, 'dn_L': 6.0}, {'foot0': 166.70000000000002, 'foot1': 184.8, 'crest': 176.8, 'H': 2.7462937139181367, 'top': 4.199999999999989, 'up_max': 22.148934452888767, 'dn_max': 25.826101732069308, 'up_L': 7.599999999999994, 'dn_L': 6.300000000000011}, {'foot0': 186.3, 'foot1': 204.60000000000002, 'crest': 196.70000000000002, 'H': 2.8225822685171127, 'top': 4.199999999999989, 'up_max': 22.564504509386424, 'dn_max': 26.73836503781333, 'up_L': 8.0, 'dn_L': 6.100000000000023}, {'foot0': 206.5, 'foot1': 224.9, 'crest': 216.5, 'H': 2.7746370392149777, 'top': 4.399999999999977, 'up_max': 22.809438214675584, 'dn_max': 25.994577293174633, 'up_L': 7.600000000000023, 'dn_L': 6.400000000000006}, {'foot0': 226.20000000000002, 'foot1': 244.4, 'crest': 236.20000000000002, 'H': 2.7483381706808054, 'top': 4.699999999999989, 'up_max': 22.690564237950554, 'dn_max': 26.21846185788965, 'up_L': 7.400000000000006, 'dn_L': 6.099999999999994}] | lane axis from 12 blocks: 0.0 deg / +7.9 ft from the gradient line |
| rhythm5_det | Detroit | g36 | 182.3 | [{'foot0': 2.0, 'foot1': 30.6, 'crest': 13.100000000000001, 'H': 2.978697676622099, 'top': 3.9000000000000004, 'up_max': 21.233457883836817, 'dn_max': 13.126306460668998, 'up_L': 9.3, 'dn_L': 15.4}, {'foot0': 36.5, 'foot1': 66.8, 'crest': 51.300000000000004, 'H': 3.5244733032940068, 'top': 3.8999999999999986, 'up_max': 21.898884029088446, 'dn_max': 19.337228547303056, 'up_L': 12.900000000000006, 'dn_L': 13.499999999999993}, {'foot0': 72.0, 'foot1': 105.80000000000001, 'crest': 88.10000000000001, 'H': 3.85915467200268, 'top': 3.6999999999999886, 'up_max': 21.755410497498804, 'dn_max': 18.82056698068096, 'up_L': 14.300000000000011, 'dn_L': 15.800000000000011}, {'foot0': 111.30000000000001, 'foot1': 146.4, 'crest': 126.7, 'H': 3.652428124644746, 'top': 3.5999999999999943, 'up_max': 22.199590452437583, 'dn_max': 19.76856974278874, 'up_L': 13.699999999999989, 'dn_L': 17.80000000000001}, {'foot0': 153.4, 'foot1': 180.5, 'crest': 167.20000000000002, 'H': 3.6820540502171353, 'top': 3.6000000000000227, 'up_max': 23.471954132626998, 'dn_max': 18.711677582948806, 'up_L': 12.099999999999994, 'dn_L': 11.399999999999977}] | lane axis from 4 blocks: 0.0 deg / +0.3 ft from the gradient line |
| rhythm5_gle | Glendale | g36 | 182.3 | [{'foot0': 2.0, 'foot1': 30.6, 'crest': 13.0, 'H': 3.176476769166837, 'top': 3.6999999999999993, 'up_max': 21.421573360951403, 'dn_max': 14.544996953486324, 'up_L': 9.3, 'dn_L': 15.600000000000001}, {'foot0': 36.4, 'foot1': 66.8, 'crest': 51.2, 'H': 3.5263363879355416, 'top': 3.8999999999999986, 'up_max': 21.892850548322386, 'dn_max': 19.343920198641317, 'up_L': 13.000000000000007, 'dn_L': 13.499999999999993}, {'foot0': 72.0, 'foot1': 105.80000000000001, 'crest': 88.10000000000001, 'H': 3.860628008774473, 'top': 3.6999999999999886, 'up_max': 21.784224799934382, 'dn_max': 18.838442735906774, 'up_L': 14.300000000000011, 'dn_L': 15.800000000000011}, {'foot0': 111.2, 'foot1': 146.5, 'crest': 126.80000000000001, 'H': 3.6528861550572294, 'top': 3.5999999999999943, 'up_max': 22.233668468508235, 'dn_max': 19.77270944109729, 'up_L': 13.799999999999997, 'dn_L': 17.900000000000006}, {'foot0': 153.4, 'foot1': 180.4, 'crest': 167.10000000000002, 'H': 3.6836855243354516, 'top': 3.6000000000000227, 'up_max': 23.502453769479235, 'dn_max': 18.69471968180567, 'up_L': 12.099999999999994, 'dn_L': 11.299999999999983}] | gradient line |
| rhythm_gap_gle | Glendale | g84 | 189.1 | [{'foot0': 1.3, 'foot1': 29.1, 'crest': 13.5, 'H': 3.5165955757738354, 'top': 3.799999999999999, 'up_max': 22.389018301549715, 'dn_max': 20.310270530562956, 'up_L': 10.3, 'dn_L': 13.700000000000001}, {'foot0': 36.1, 'foot1': 66.2, 'crest': 50.800000000000004, 'H': 3.448132796113839, 'top': 4.0, 'up_max': 19.451894571739558, 'dn_max': 20.085820080463375, 'up_L': 12.700000000000003, 'dn_L': 13.399999999999999}, {'foot0': 71.2, 'foot1': 104.2, 'crest': 86.80000000000001, 'H': 3.621772417773857, 'top': 4.0, 'up_max': 19.182402112710705, 'dn_max': 15.66356984305815, 'up_L': 13.799999999999997, 'dn_L': 15.200000000000003}, {'foot0': 144.8, 'foot1': 187.0, 'crest': 165.9, 'H': 3.5574043251355745, 'top': 6.200000000000017, 'up_max': 13.840772819105844, 'dn_max': 12.180216030800493, 'up_L': 18.099999999999994, 'dn_L': 17.899999999999977}] | gradient line |
| mixed7_det | Detroit | g35 | 329.8 | [{'foot0': 2.2, 'foot1': 115.0, 'crest': 47.2, 'H': 6.12239543490859, 'top': 5.0, 'up_max': 18.291490995238206, 'dn_max': 19.125593339339797, 'up_L': 42.5, 'dn_L': 65.3}, {'foot0': 115.0, 'foot1': 144.9, 'crest': 129.8, 'H': 3.5234575045639525, 'top': 4.199999999999989, 'up_max': 19.92087012736188, 'dn_max': 19.094820257297524, 'up_L': 12.900000000000006, 'dn_L': 12.800000000000011}, {'foot0': 144.9, 'foot1': 189.8, 'crest': 165.5, 'H': 5.724864894299835, 'top': 4.799999999999983, 'up_max': 22.75817651926684, 'dn_max': 19.033297334317734, 'up_L': 18.30000000000001, 'dn_L': 21.80000000000001}, {'foot0': 189.8, 'foot1': 220.4, 'crest': 204.60000000000002, 'H': 3.5228307356686366, 'top': 4.099999999999994, 'up_max': 19.912239394951992, 'dn_max': 19.064064503209607, 'up_L': 12.900000000000006, 'dn_L': 13.599999999999994}, {'foot0': 225.20000000000002, 'foot1': 251.3, 'crest': 236.4, 'H': 3.619116637561182, 'top': 3.5999999999999943, 'up_max': 22.79213728883256, 'dn_max': 20.315563720568328, 'up_L': 9.5, 'dn_L': 13.0}, {'foot0': 257.1, 'foot1': 300.0, 'crest': 277.90000000000003, 'H': 5.717691175428001, 'top': 4.7000000000000455, 'up_max': 22.75817651926978, 'dn_max': 19.033297334317915, 'up_L': 18.599999999999966, 'dn_L': 19.599999999999966}, {'foot0': 301.8, 'foot1': 328.3, 'crest': 313.0, 'H': 3.605271739952224, 'top': 3.6999999999999886, 'up_max': 22.72680553843856, 'dn_max': 20.158693000169336, 'up_L': 9.5, 'dn_L': 13.300000000000011}] | gradient line |
| mixed5_arl | Arlington | g37 | 149.7 | [{'foot0': 1.3, 'foot1': 28.400000000000002, 'crest': 13.0, 'H': 3.661530118981281, 'top': 3.5999999999999996, 'up_max': 22.809222971524548, 'dn_max': 20.32251820661786, 'up_L': 9.9, 'dn_L': 13.600000000000001}, {'foot0': 33.1, 'foot1': 78.9, 'crest': 54.400000000000006, 'H': 5.902823406790227, 'top': 4.299999999999997, 'up_max': 22.8020105859248, 'dn_max': 18.58363160241824, 'up_L': 19.200000000000003, 'dn_L': 22.300000000000004}, {'foot0': 82.80000000000001, 'foot1': 113.0, 'crest': 97.30000000000001, 'H': 3.774636372965183, 'top': 3.9000000000000057, 'up_max': 20.993652261791055, 'dn_max': 19.015780674659222, 'up_L': 12.599999999999994, 'dn_L': 13.699999999999989}, {'foot0': 116.0, 'foot1': 147.6, 'crest': 131.3, 'H': 4.0156177835869045, 'top': 3.8000000000000114, 'up_max': 22.272718835446327, 'dn_max': 18.6996540843982, 'up_L': 13.400000000000006, 'dn_L': 14.399999999999977}] | lane axis from 2 blocks: 0.1 deg / +13.8 ft from the gradient line |
| mixed5_cle | Custom1 | g71 | 151.2 | [{'foot0': 1.6, 'foot1': 31.1, 'crest': 16.6, 'H': 3.639554084004714, 'top': 4.0, 'up_max': 21.59116902326108, 'dn_max': 18.354988170830886, 'up_L': 13.000000000000002, 'dn_L': 12.5}, {'foot0': 38.900000000000006, 'foot1': 68.4, 'crest': 52.0, 'H': 3.516690189833191, 'top': 4.0, 'up_max': 23.194129600673314, 'dn_max': 16.705456852372475, 'up_L': 11.299999999999997, 'dn_L': 14.200000000000003}, {'foot0': 75.0, 'foot1': 104.30000000000001, 'crest': 88.4, 'H': 3.5335452542991366, 'top': 3.9000000000000057, 'up_max': 21.890433666645745, 'dn_max': 19.328539384968767, 'up_L': 11.5, 'dn_L': 13.900000000000006}, {'foot0': 108.80000000000001, 'foot1': 142.6, 'crest': 125.30000000000001, 'H': 3.86797492611655, 'top': 3.799999999999997, 'up_max': 21.773246428700098, 'dn_max': 18.836667683933285, 'up_L': 14.599999999999994, 'dn_L': 15.399999999999991}] | gradient line |
| longtable_cus | Custom | g55 | 233.8 | [{'foot0': 2.5, 'foot1': 120.7, 'crest': 52.800000000000004, 'H': 5.929974397099654, 'top': 51.0, 'up_max': 22.594095502759128, 'dn_max': 20.55348544230913, 'up_L': 48.400000000000006, 'dn_L': 18.799999999999997}, {'foot0': 125.30000000000001, 'foot1': 153.0, 'crest': 137.5, 'H': 3.5472780424875117, 'top': 3.9000000000000057, 'up_max': 21.910339061208138, 'dn_max': 18.76860827869654, 'up_L': 10.299999999999983, 'dn_L': 13.5}, {'foot0': 156.4, 'foot1': 201.4, 'crest': 177.10000000000002, 'H': 5.750341966361905, 'top': 4.800000000000011, 'up_max': 22.741851601702603, 'dn_max': 19.048160335130937, 'up_L': 18.400000000000006, 'dn_L': 21.799999999999983}, {'foot0': 201.4, 'foot1': 232.5, 'crest': 216.3, 'H': 3.550721788915904, 'top': 4.199999999999989, 'up_max': 19.88146709021335, 'dn_max': 19.11015583613901, 'up_L': 12.900000000000006, 'dn_L': 14.0}] | gradient line |
| triple_det | Detroit | g27 | 143.0 | [{'foot0': 2.7, 'foot1': 39.300000000000004, 'crest': 18.5, 'H': 7.871285013190456, 'top': 3.900000000000002, 'up_max': 36.406345542052634, 'dn_max': 32.8341401235895, 'up_L': 15.3, 'dn_L': 17.400000000000002}, {'foot0': 41.900000000000006, 'foot1': 87.0, 'crest': 61.1, 'H': 5.957542249431962, 'top': 6.500000000000007, 'up_max': 26.896325383235347, 'dn_max': 17.094819199027796, 'up_L': 16.199999999999996, 'dn_L': 22.39999999999999}, {'foot0': 90.0, 'foot1': 140.1, 'crest': 110.9, 'H': 7.321277067705168, 'top': 5.300000000000011, 'up_max': 27.38715430012393, 'dn_max': 18.476835909840485, 'up_L': 18.5, 'dn_L': 26.299999999999983}] | lane axis from 3 blocks: 0.2 deg / -13.9 ft from the gradient line |
| stepup_det | Detroit | g30 | 137.9 | [{'foot0': 2.1, 'foot1': 38.300000000000004, 'crest': 19.900000000000002, 'H': 8.803661579415817, 'top': 4.099999999999998, 'up_max': 39.76494627548745, 'dn_max': 38.256489834962295, 'up_L': 15.800000000000002, 'dn_L': 16.300000000000004}, {'foot0': 64.4, 'foot1': 135.70000000000002, 'crest': 98.0, 'H': 11.211708039915546, 'top': 6.200000000000003, 'up_max': 32.204952492594366, 'dn_max': 22.582245310407114, 'up_L': 30.700000000000003, 'dn_L': 34.400000000000006}] | lane axis from 2 blocks: 0.1 deg / +13.0 ft from the gradient line |
| bigdouble_gle | Glendale | g83 | 161.4 | [{'foot0': 2.0, 'foot1': 35.800000000000004, 'crest': 18.0, 'H': 7.143581603967346, 'top': 5.300000000000001, 'up_max': 30.907170967139923, 'dn_max': 38.96560378181686, 'up_L': 15.5, 'dn_L': 13.000000000000004}, {'foot0': 76.10000000000001, 'foot1': 132.3, 'crest': 96.7, 'H': 7.935593577176732, 'top': 5.700000000000003, 'up_max': 29.714509558213503, 'dn_max': 17.84154523155596, 'up_L': 17.39999999999999, 'dn_L': 33.10000000000001}, {'foot0': 138.5, 'foot1': 161.20000000000002, 'crest': 153.0, 'H': 1.877365269350044, 'top': 6.200000000000017, 'up_max': 9.973210614044332, 'dn_max': 19.473500439173232, 'up_L': 10.900000000000006, 'dn_L': 5.599999999999994}] | gradient line |
| table9_arl | Arlington | g20 | 184.6 | [{'foot0': 1.7000000000000002, 'foot1': 68.7, 'crest': 36.2, 'H': 9.010389468223089, 'top': 8.700000000000003, 'up_max': 37.57040176526037, 'dn_max': 27.945700681083146, 'up_L': 31.500000000000004, 'dn_L': 26.799999999999997}, {'foot0': 73.4, 'foot1': 105.2, 'crest': 88.5, 'H': 3.051379699884669, 'top': 4.0, 'up_max': 16.715883081318825, 'dn_max': 12.302983183890554, 'up_L': 13.200000000000003, 'dn_L': 14.599999999999994}, {'foot0': 145.8, 'foot1': 182.5, 'crest': 164.4, 'H': 2.9838447583383, 'top': 5.300000000000011, 'up_max': 11.888481046365305, 'dn_max': 11.904716068235945, 'up_L': 16.099999999999994, 'dn_L': 15.299999999999983}] | gradient line |
| onoff_det | Detroit | g11 | 143.1 | [{'foot0': 1.2000000000000002, 'foot1': 29.1, 'crest': 12.9, 'H': 3.680264075324702, 'top': 3.5999999999999996, 'up_max': 22.85848591752145, 'dn_max': 20.27387809229592, 'up_L': 10.0, 'dn_L': 14.3}, {'foot0': 32.7, 'foot1': 61.1, 'crest': 46.1, 'H': 3.368907625481398, 'top': 4.100000000000001, 'up_max': 19.94200714923405, 'dn_max': 18.43089952193779, 'up_L': 11.399999999999999, 'dn_L': 12.899999999999999}, {'foot0': 65.3, 'foot1': 97.60000000000001, 'crest': 80.5, 'H': 3.5521210366470775, 'top': 4.0, 'up_max': 18.043352215715316, 'dn_max': 15.549669599160353, 'up_L': 13.300000000000011, 'dn_L': 15.0}, {'foot0': 121.5, 'foot1': 141.0, 'crest': 129.20000000000002, 'H': 0.7754307050613052, 'top': 6.6000000000000085, 'up_max': 14.593175944694798, 'dn_max': 5.071713318186231, 'up_L': 5.200000000000003, 'dn_L': 7.699999999999989}] | gradient line |
| rhythm3_cus | Custom | g49 | 138.2 | [{'foot0': 1.1, 'foot1': 31.1, 'crest': 12.9, 'H': 3.6828349260286775, 'top': 3.6999999999999993, 'up_max': 22.83035232125782, 'dn_max': 20.309673123914063, 'up_L': 10.000000000000002, 'dn_L': 16.3}, {'foot0': 31.1, 'foot1': 86.0, 'crest': 61.0, 'H': 5.766425855334308, 'top': 4.899999999999999, 'up_max': 22.119145048935003, 'dn_max': 18.861896069529074, 'up_L': 27.5, 'dn_L': 22.5}, {'foot0': 112.10000000000001, 'foot1': 136.1, 'crest': 121.2, 'H': 1.5604890534177929, 'top': 4.799999999999997, 'up_max': 28.86277654921421, 'dn_max': 10.666581408253831, 'up_L': 6.5, 'dn_L': 12.699999999999989}] | gradient line |
| mixed4_arl | Arlington | g49 | 164.0 | [{'foot0': 2.1, 'foot1': 21.1, 'crest': 13.9, 'H': 0.5682114747060752, 'top': 8.100000000000001, 'up_max': 3.4346182032191566, 'dn_max': 8.087526904772455, 'up_L': 6.9, 'dn_L': 4.0}, {'foot0': 48.7, 'foot1': 75.60000000000001, 'crest': 60.800000000000004, 'H': 3.6134183481880013, 'top': 3.700000000000003, 'up_max': 23.872306237932552, 'dn_max': 18.671844134388323, 'up_L': 10.399999999999999, 'dn_L': 12.800000000000004}, {'foot0': 81.0, 'foot1': 135.3, 'crest': 114.2, 'H': 6.179556753516403, 'top': 6.599999999999994, 'up_max': 26.080023870752328, 'dn_max': 23.14807517164326, 'up_L': 28.900000000000006, 'dn_L': 18.80000000000001}, {'foot0': 136.4, 'foot1': 162.4, 'crest': 149.6, 'H': 3.4769111351412887, 'top': 3.799999999999983, 'up_max': 22.943867916869614, 'dn_max': 19.655481750551896, 'up_L': 11.400000000000006, 'dn_L': 10.800000000000011}] | gradient line |

## 8. MX (Desert Sand, Dr. Dew) — v1 abandonnée, gardé pour référence

247 faces/unités mesurées le long des lignes de checkpoint (`docs/data/mx_units.csv`).

| ref / type | n |
|---|---|
| Desert / bump | 22 |
| Desert / jump | 24 |
| Desert / roller | 4 |
| Desert / step-down-from-jump | 7 |
| Desert / step-up | 78 |
| Desert / table | 16 |
| DrDew / bump | 8 |
| DrDew / jump | 9 |
| DrDew / roller | 4 |
| DrDew / step-down-from-jump | 10 |
| DrDew / step-up | 58 |
| DrDew / table | 7 |

### mx_sections

| clé | ref | cp | L ft | H max | dénivelé net | largeur plate |
|---|---|---|---|---|---|---|
| dd_table27 | DrDew | 27 | 120.0 | 7.0 | 3.34 | 25.5 |
| dd_table30 | DrDew | 30 | 90.0 | 3.29 | -2.64 | 46.0 |
| dd_table12 | DrDew | 12 | 70.0 | 0.0 | -19.88 | 43.2 |
| dd_jump24 | DrDew | 24 | 145.0 | 0.0 | -21.48 | 21.0 |
| dd_stepdown48 | DrDew | 48 | 120.0 | 0.0 | -30.86 | 17.0 |
| dd_rhythm17 | DrDew | 17 | 125.0 | 5.58 | 1.27 | 23.0 |
| dd_table35 | DrDew | 35 | 155.0 | 0.0 | -2.74 | 60.0 |
| dd_jump16 | DrDew | 16 | 100.0 | 5.96 | 5.51 | 25.5 |
| ds_double31 | Desert | 31 | 180.0 | 10.29 | 6.76 | 29.2 |
| ds_kicker30 | Desert | 30 | 90.0 | 9.55 | 5.15 | 27.2 |
| ds_table53 | Desert | 53 | 110.0 | 3.65 | -4.57 | 30.8 |
| ds_table59 | Desert | 59 | 68.0 | 6.36 | -1.28 | 34.2 |
| ds_rollers50 | Desert | 50 | 150.0 | 2.06 | -5.42 | 18.8 |
| ds_jump15 | Desert | 15 | 95.0 | 4.91 | -3.28 | 7.0 |
| ds_jump44 | Desert | 44 | 95.0 | 6.18 | 4.41 | 18.5 |
| ds_stepdown26 | Desert | 26 | 100.0 | 4.19 | -18.22 | 37.2 |
| ds_tables16 | Desert | 16 | 105.0 | 23.6 | 23.6 | 12.0 |
| ds_chop3 | Desert | 3 | 145.0 | 7.18 | 3.3 | 36.5 |
| ds_chop58 | Desert | 58 | 80.0 | 4.04 | -2.38 | 24.0 |
| ds_chop56 | Desert | 56 | 80.0 | 3.62 | 1.94 | 22.2 |
| ds_jump54 | Desert | 54 | 105.0 | 4.64 | 2.78 | 22.0 |
| ds_jump47 | Desert | 47 | 55.0 | 2.58 | -1.39 | 32.5 |

### mx_desert_sections

| clé | ref | cp | L ft | H max | dénivelé net | largeur plate |
|---|---|---|---|---|---|---|
| ds_s118_step | Desert |  | 187.2 | 20.11 | 13.88 |  |
| ds_s459_step | Desert |  | 130.2 | 9.85 | 9.85 |  |
| ds_s635_step | Desert |  | 113.2 | 19.32 | 19.32 |  |
| ds_s1300_step | Desert |  | 118.2 | 14.99 | 14.99 |  |
| ds_s1854_step | Desert |  | 125.5 | 16.99 | 16.99 |  |
| ds_s2243_step | Desert |  | 164.0 | 8.63 | 7.83 |  |
| ds_s2649_step | Desert |  | 109.5 | 9.36 | 9.36 |  |
| ds_s2796_roller | Desert |  | 123.2 | 5.68 | 5.29 |  |
| ds_s3047_step | Desert |  | 138.5 | 13.9 | 9.22 |  |
| ds_s3207_step | Desert |  | 135.8 | 9.55 | 8.41 |  |
| ds_s3457_table | Desert |  | 193.0 | 0.0 | -6.54 |  |
| ds_s3795_step | Desert |  | 114.2 | 4.15 | 4.15 |  |
| ds_s4426_step | Desert |  | 187.8 | 13.77 | 3.82 |  |
| ds_s4671_step | Desert |  | 110.0 | 2.85 | 2.1 |  |
| ds_s4935_step | Desert |  | 115.0 | 11.67 | 11.67 |  |
| ds_s5459_jump | Desert |  | 164.8 | 8.03 | 0.09 |  |
| ds_s5890_step | Desert |  | 121.2 | 7.74 | 7.74 |  |
| ds_s6256_step | Desert |  | 127.5 | 5.85 | -3.56 |  |
| ds_s6470_jump | Desert |  | 136.8 | 6.41 | -0.05 |  |
| ds_s6803_step | Desert |  | 125.5 | 17.02 | 17.02 |  |
| ds_s7006_step | Desert |  | 103.8 | 4.46 | -10.41 |  |
| ds_s7158_jump | Desert |  | 121.5 | 0.0 | -3.32 |  |
| ds_s7691_step | Desert |  | 140.0 | 6.27 | 1.89 |  |
| ds_s7981_step | Desert |  | 151.0 | 5.28 | 0.0 |  |
| ds_s8552_jump | Desert |  | 134.0 | 7.08 | 1.3 |  |
| ds_s8736_step | Desert |  | 111.5 | 0.0 | -2.93 |  |
| ds_s8869_step | Desert |  | 105.8 | 6.86 | 6.86 |  |
| ds_s9173_table | Desert |  | 202.2 | 6.65 | -0.79 |  |
| ds_s9404_step | Desert |  | 127.5 | 22.92 | 22.92 |  |
| ds_s9681_step | Desert |  | 112.8 | 0.46 | 0.46 |  |
| ds_s10356_step | Desert |  | 140.0 | 25.09 | 25.09 |  |

### mx_drdew_sections

| clé | ref | cp | L ft | H max | dénivelé net | largeur plate |
|---|---|---|---|---|---|---|
| dd_g8 | DrDew |  | 100.0 | 4.23 | -0.15 |  |
| dd_g43 | DrDew |  | 175.0 | 10.57 | -16.95 |  |
| dd_g125 | DrDew |  | 170.0 | 9.56 | -12.78 |  |
| dd_g132 | DrDew |  | 120.0 | 13.67 | 7.75 |  |
| dd_g18 | DrDew |  | 110.0 | 19.75 | 19.75 |  |

Berm MX : JGMXDesertSand turn at (718,398), R=22 ft, wall 47 deg — outward cross-section from the decal-traced centreline (single measured turn, not averaged).

