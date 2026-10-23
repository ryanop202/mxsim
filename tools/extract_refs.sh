#!/usr/bin/env bash
# Extract refs/archives/*.rar -> refs/extracted/<name>/ and check SHA-256.
set -euo pipefail
cd "$(dirname "$0")/.."
declare -A SHA=(
  [JGMXDesertSand]=841ce7916b6bcccd71d208fd517f8340a1d3cdf25f22a3efbeae2ae7fa6426d9
  [JGMXDrDew]=25618d34bdae747823f5873527145e51f4404860bd23bcc484d8dd761e666a56
  [JGSX2026TestTracks]=576c8f8d369c0dd5b888b586d9ff4f1f447abe0a6aad740a0dce26a9356bfec7
)
[ -d node_modules/node-unrar-js ] || npm install
for n in "${!SHA[@]}"; do
  a="refs/archives/$n.rar"
  [ -f "$a" ] || { echo "manque $a"; exit 1; }
  got=$(sha256sum "$a" | cut -d' ' -f1)
  [ "$got" = "${SHA[$n]}" ] && echo "OK  $n" || echo "ATTENTION $n : SHA-256 différent ($got) -> mesures peut-être différentes"
  mkdir -p "refs/extracted/$n"
  node tools/unrar.mjs "$a" "refs/extracted/$n"
done
