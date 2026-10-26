# refs/ — Archives et assets de référence

## Structure actuelle

```
refs/
  archives/          <- anciennes archives RAR (ignoré par git)
  extracted/         <- extractions des RAR (ignoré par git)
  rf/                <- archives .saf RF 2026 (Anaheim 1/2 + Houston)  ← VERSIONNÉ
    sx2026r01anaheim1.medium.saf
    sx2026r03anaheim2.medium.saf
    sx2026r04houston.medium.saf
    README.md
  rbt/               <- assets extraits de la piste RBT 2024          ← VERSIONNÉ
    billboards, decals, statues, lighting, terrain.*, tileinfo, ...
    README.md
```

## RF (refs/rf/)

Sources pour :
- Bosses / sauts (à mixer avec JGSX)
- Stade

Extraction :
```bash
python3 extract_saf.py refs/rf/*.saf --out refs/rf/extracted
```

## RBT (refs/rbt/)

Sources pour :
- Herbe, arbres, eau
- Décor / ambiance / billboards / statues
- Lighting

## JGSX

Les whoops, berms et textures JGSX sont déjà mesurés et versionnés dans `lib/` (pas besoin des archives ici).
