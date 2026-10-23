# 10 — Suite, limites, idées

## À faire en priorité

1. **Premier test en jeu** par Ryan (checklist doc 08) → corriger selon ses retours.
2. Ajuster les chronos sur les vrais temps (le modèle de `laptime.py` est grossier).

## Limites connues

- Non testé en jeu (tout).
- Pas d'objets (barrières, tuff blocks, banderoles, bâches, caméras TV), pas de decals de piste : visuel nu.
- 8 tiles seulement : pas de tiles de transition (Jump Transition Sx, Whoop Transition, Mulch Mix…), pas de « Start Grate ».
- Le sable est au niveau du sol (creux de Glendale ramenés à 0).
- SX3 a 3 déports plats (8°, −8°, −23,6°) — conformes à Glendale pour la sortie du J, mais à vérifier en jeu.
- Les gates du 1er tour suivent une logique différente de JGSX (portes en travers de la ligne de départ au lieu de portes
  « tour seulement ») ; équivalent sur le papier, à confirmer en jeu.
- `.mxdemo` non décodés.

## Idées (non demandées, à proposer à Ryan)

- **Statues** : reprendre les barrières/tuff blocks JGSX le long des couloirs (positions relatives mesurables sur les références).
- **Decals** : reprendre les decals de piste JGSX (straight.png, etc.) pour le visuel.
- Une **SX4** dans la place libre du terrain (bas à droite / bas à gauche).
- Plus de sable : autres morceaux de Glendale en stamps.
- Reprendre le **MX** avec des stamps 2D de zones entières de Desert Sand / Dr. Dew (doc 04), au lieu de profils recollés.
- Décoder les `.mxdemo` pour avoir de vraies trajectoires et vitesses → chronos et placements réalistes.
- Un script de **diff** entre deux versions (vue de dessus avant / après) pour les retours rapides de Ryan sur téléphone.
