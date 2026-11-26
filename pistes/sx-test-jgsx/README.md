# USLAND 2026 SX 1 / SX 2 / SX 3 — compound SX fait à partir des mesures JGSX

La base de départ du projet : 3 pistes SX sur un même terrain, construites uniquement à partir des mesures des pistes de test
JGSX 2026. Ce sont les pistes qui ont servi à mettre au point le moteur, les mesures et les objets du kit commun.

**État** : les versions v3 à v10 ont été testées en jeu par Ryan. Les v11 et v12 ne l'ont pas encore été.

## Installer

Copier `tracks/USLAND2026SX1`, `USLAND2026SX2` et `USLAND2026SX3` dans le dossier des pistes de MX Simulator,
**sans les renommer**, car les textures sont partagées via `@USLAND2026SX1/...`. En jeu, elles s'appellent « USLAND: 2026 SX 1 / SX 2 / SX 3 (sand) ».

## Les 3 pistes (v11)

| Piste | Tour | Estimation* | Départ → jonction | Ce qu'il y a |
|---|---|---|---|---|
| SX 1 | 2931 ft (893 m) | ~1:04 | 368 ft | triple écarté + triple à grosse bosse + quad, 12 whoops + single, triple sur table / off quad, step-up + triple sur table off, on-off Detroit, quad, triple + on-off d'arrivée ; 7 virages à berm |
| SX 2 | 2717 ft (828 m) | ~1:03 | 278 ft | départ au milieu, rythmique Arlington, bosse-bosse-table-bosse-table-bosse, gros double + triple, triple sur table, 8 whoops, S-gros-S-table-S-gros-S, table 9 ft, triple d'arrivée |
| SX 3 (sand) | 3349 ft (1021 m) | ~1:07 | 279 ft | sable Glendale (J + virage en S), hauteurs mélangées + triple Detroit, 10 whoops, on-off, step-up, triple sur table off quad, gros double |

\* modèle point-masse grossier (`commun/scripts/laptime.py`), **pas** un chrono mesuré en jeu.

Vues de dessus : `commun/viewer/figures/01_top_SX*.jpg` · profils : `commun/viewer/figures/02_lanes_SX*.jpg` ·
visionneuse 3D : `commun/viewer/index.html`.

## Où est le code

```
commun/scripts/layouts_sx.py     le tracé des 3 pistes (couloirs, virages, départs)
commun/scripts/build_sx.py       relief (heightmap) + tiles
commun/scripts/export_sx.py      export MX Simulator -> tracks/USLAND2026SX1..3
commun/scripts/dress_sx.py       habillage JGSX (grilles, grillages, paddock, decals, drapeaux)
commun/scripts/props_usland.py   objets USLAND faits maison ; place_props.py les pose
commun/scripts/validate_sx.py    les contrôles automatiques (43)
commun/scripts/figures_sx.py     vues de dessus, profils, visionneuse
```

## Reconstruire

Il faut les archives JGSX / JGMX dans `refs/archives/`. Elles restent en local, voir `refs/README.md`.

```bash
./commun/tools/extract_refs.sh
./make_all.sh build        # doit finir sur 43 / 43
```

## Docs

- [docs/pistes/05_compound_sx.md](../../docs/pistes/05_compound_sx.md) : les 3 pistes couloir par couloir, et pourquoi elles sont comme ça
- [docs/pistes/07_journal_conversation.md](../../docs/pistes/07_journal_conversation.md) : le journal des demandes et des retours de Ryan
- [docs/pistes/11_habillage.md](../../docs/pistes/11_habillage.md) : l'habillage
- [docs/pistes/10_suite_et_idees.md](../../docs/pistes/10_suite_et_idees.md) : les idées pour la suite
- [docs/pistes/00_cahier_des_charges_original.txt](../../docs/pistes/00_cahier_des_charges_original.txt) : le cahier des charges de départ
