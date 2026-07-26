#!/bin/bash
# weld_p — preference gate
set -euo pipefail

pref=/var/lib/multipath/ops/prefer.toml
surf=/app/config/surface/candidates
cand=/var/lib/multipath/candidates

mkdir -p "$cand" /var/lib/multipath/ops

mode=surface
if [[ -f "$pref" ]]; then
  mode=$(grep -E '^mode[[:space:]]*=' "$pref" | head -1 \
    | sed 's/.*=[[:space:]]*//;s/"//g;s/[[:space:]]*$//' \
    | tr -d ' ')
fi
echo "$mode" > /var/lib/multipath/ops/mode.active

rm -f "$cand"/*.json 2>/dev/null || true
cp -a "$surf"/. "$cand"/
