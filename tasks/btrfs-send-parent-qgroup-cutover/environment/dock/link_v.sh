#!/bin/bash
set -euo pipefail

ROOT="${BTRFS_ROOT:-/var/lib/btrfs}"
ROSTER="${LANE_ROSTER:-/etc/btrfs/lane.roster}"
ATTACH="$ROOT/attach"

mkdir -p "$ATTACH"

while IFS= read -r lane || [[ -n "$lane" ]]; do
  lane="${lane%%#*}"
  lane="$(echo "$lane" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  [[ -z "$lane" ]] && continue
  src="$ROOT/volumes/$lane/decoy/payload.bin"
  [[ -f "$src" ]] || src="$ROOT/volumes/$lane/sealed/payload.bin"
  dst="$ATTACH/${lane}.bin"
  rm -f "$dst" "$ATTACH/.hold.$lane"
  rm -rf "$ATTACH/$lane"
  mkdir -p "$ATTACH/$lane"
  cp -f "$src" "$dst"
  cp -f "$src" "$ATTACH/$lane/payload.bin"
done <"$ROSTER"
