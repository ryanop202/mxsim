#!/usr/bin/env bash
# Rebuild everything from the reference archives.
#   ./make_all.sh            -> SX analysis + SX compound (tracks/) + validation + figures
#   ./make_all.sh build      -> only the compound (uses the lib/ already in the repo; fast)
#   ./make_all.sh analysis   -> only the measurements (refs -> lib/, analysis/)
#   ./make_all.sh mx         -> also re-run the abandoned v1 MX analysis (legacy, slow)
# Needs: python3 + requirements.txt ; refs/extracted/ filled (see refs/README.md, tools/extract_refs.sh)
set -euo pipefail
cd "$(dirname "$0")"
export MXSIM_ROOT="$PWD"
export MXSIM_REF="${MXSIM_REF:-$PWD/refs/extracted}"
PY="${PYTHON:-python3}"
MODE="${1:-all}"
FROM="${FROM:-}"   # FROM=sx_units.py ./make_all.sh  -> resume at that step
run() {
  if [ -n "$FROM" ]; then [ "$1" = "$FROM" ] && FROM="" || { echo "skip $1"; return; }; fi
  echo; echo "=== $1"; t=$(date +%s); "$PY" "scripts/$1" "${@:2}"; echo "    ($(( $(date +%s) - t )) s)"
}
mkdir -p analysis build tracks viewer/figures lib

need_refs() {
  for d in JGMXDesertSand JGMXDrDew JGSX2026TestTracks; do
    [ -d "$MXSIM_REF/$d" ] || { echo "Missing $MXSIM_REF/$d -> see refs/README.md"; exit 1; }
  done
}

analysis() {
  need_refs
  run validate_format.py        # format checks of the MXS file readers on the 3 references
  run catalog.py                # gradient-line profiles of every obstacle -> analysis/catalog_raw.json
  # --- SX measurements (JGSX 2026 test tracks)
  run sx_components.py          # isolated obstacle blocks -> lib/sx/*.npy + lib/sx_components.json
  run sx_classify.py            # block classes + gallery
  run sx_lateral.py             # cross-lane wall model (top 30.4 ft, 4 ft wall)
  for t in JGSX2026Detroit JGSX2026Arlington JGSX2026Glendale JGSX2026Custom JGSX2026Custom1; do
    run sx_lanes.py "$t"        # lane axes per reference (analysis/lanes_*.json, figures)
  done
  run sx_berms.py               # crescent berms (big / small) -> lib/sx_berms.json
  run berm_stamps.py            # exact berm stamps -> lib/berm_*.npy
  # --- MX measurements (needed by build_library: mx_units)
  DS="$MXSIM_REF/JGMXDesertSand/JGMXDesertSand"; DD="$MXSIM_REF/JGMXDrDew/JGMXDrDew"
  run mx_cp_lanes.py "$DD" DrDew   # profiles through every MX checkpoint -> analysis/cplanes_*.json
  run mx_cp_lanes.py "$DS" Desert
  run mx_faces.py               # faces/plateaus/units -> analysis/mx_units.json
  run build_library.py          # lib/library.json (SX sections, berms, lateral model, MX units)
  run mx_sections.py            # + mx_sections
  run centerline.py "$DS" decal/sand.png Desert   # Desert lap centreline over on-track decals
  run mx_centerline_profile.py Desert "$DS"
  run mx_features.py Desert "$DS"                  # -> analysis/mxfeat_Desert.json (berm)
  run desert_sections.py        # + mx_desert_sections
  run drdew_sections.py         # + mx_drdew_sections
  run mx_berm.py                # + mx_berm
  # --- SX rhythm library
  run sx_units.py               # every floor-separated unit + measured floor gaps -> lib/sx_units.json
  run sx_whoops.py              # whoops variants -> lib/sx_whoops.json
  run sand_stamps.py            # Glendale sand stamps -> lib/sand_*.npy + lib/sand_stamps.json
  run starts_ref.py             # how JGSX builds starts -> analysis/starts_ref*.png
  run gle_sand_view.py          # Glendale sand figures
}

build() {
  run build_sx.py               # build/H.npy + tiles.npy + build_report.json
  run export_sx.py              # tracks/USLAND2026SX1..3 (needs refs for textures/tileinfo)
  run tuff_usland.py            # tuff block blanc logo USLAND (assets/usland_logo.png)
  run dress_sx.py               # habillage : grilles, grillages, tuff blocks, routes, paddock, decor, decals, drapeaux (needs refs)
  run props_usland.py           # v12 : objets USLAND faits maison -> assets/props (specs contrôlées)
  run sticker_usland.py         # v12b : icône U moulée sur la citerne JGSX gardée -> assets/props/watertruck_u
  run place_props.py            # v12 : les pose à la place des objets JGSX (hospitality, pick-ups + vélos, grilles, grates, portique, arche)
  run minimap.py                # map.png de chaque dossier (vue de dessus sans lignes)
  run validate_sx.py            # build/validation.json (39 checks)
  run laptime.py                # build/laptime.json (estimate, not measured in game)
  for t in sx1 sx2 sx3; do run preview_sx.py "$t"; done   # analysis/pv2_*.png (each track alone + geometric checks)
  run figures_sx.py             # viewer/figures + viewer/terrain_data.js
  run figures_dress.py          # viewer/figures/05_habillage*.jpg
  run gen_docs.py               # docs/09_donnees_mesurees.md + docs/data/*.csv + docs/img/atlas_*.jpg
}

case "$MODE" in
  all) analysis; build ;;
  analysis) analysis ;;
  build) need_refs; build ;;
  mx) need_refs; run mx_candidates.py; run mx_grad_profiles.py "$MXSIM_REF/JGMXDrDew/JGMXDrDew" MX_DrDew; run mx_preview.py; run build_compound.py; run export.py; run validate.py; run laptime.py mx ;;
  *) echo "usage: $0 [all|build|analysis|mx]"; exit 2 ;;
esac
echo; echo "done ($MODE)"
