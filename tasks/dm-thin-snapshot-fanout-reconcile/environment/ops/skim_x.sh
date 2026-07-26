#!/bin/bash
set -euo pipefail
ROOT="${POOL_ROOT:-/var/lib/pool}"
STAGE="${ORIGIN_ROOT:-/var/lib/pool/origin_stage}"
mkdir -p "$STAGE"
for src in "$ROOT"/origins/*.bin; do
  [[ -e "$src" ]] || continue
  base="$(basename "$src")"
  drill="${base#o_}"
  drill="${drill%.bin}"
  decoy="$ROOT/decoys/d_${drill}.bin"
  if [[ -f "$decoy" ]]; then
    cp -f "$decoy" "$STAGE/$base"
  else
    cp -f "$src" "$STAGE/$base"
  fi
done
