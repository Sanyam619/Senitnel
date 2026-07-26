#!/bin/bash
set -euo pipefail
A_X="${ABORT_D:-/var/lib/systemd/ops/abort.d}"
B_Y="${LIVE_D:-/etc/systemd/system}"
mkdir -p "$B_Y"
shopt -s nullglob
for unit_d in "$A_X"/*.path.d; do
  [[ -d "$unit_d" ]] || continue
  base="$(basename "$unit_d")"
  mkdir -p "$B_Y/$base"
  for f in "$unit_d"/*.conf; do
    cp -f "$f" "$B_Y/$base/$(basename "$f")"
  done
done
shopt -u nullglob
