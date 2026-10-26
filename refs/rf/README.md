# refs/rf/ — Archives RF (Supercross 2026)

Fichiers fournis pour extraction des bosses, sauts et stade.

## Contenu

| Fichier | Description |
|---------|-------------|
| sx2026r01anaheim1.medium.saf | Anaheim 1 (Round 1) |
| sx2026r03anaheim2.medium.saf | Anaheim 2 (Round 3) |
| sx2026r04houston.medium.saf  | Houston (Round 4) |

## Extraction

```bash
python3 extract_saf.py refs/rf/*.saf --out refs/rf/extracted
```

Après extraction on obtient pour chaque piste :
terrain.png, tilemap, tileinfo, lighting, statues, billboards, stadium models, etc.

Ces ressources servent principalement pour :
- les **bosses / sauts** (mix avec JGSX)
- le **stade**
