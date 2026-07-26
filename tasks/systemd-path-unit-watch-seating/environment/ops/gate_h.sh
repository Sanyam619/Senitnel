#!/bin/bash
set -euo pipefail
FOLD="${FOLD_TSV:-/var/lib/systemd/ops/live/fold.tsv}"
OUT="${ARM_TSV:-/var/lib/systemd/ops/live/arm.tsv}"
mkdir -p "$(dirname "$OUT")"
: >"$OUT"
[[ -f "$FOLD" ]] || exit 0
while IFS=$'\t' read -r unit ex ch dne || [[ -n "${unit:-}" ]]; do
  [[ -z "${unit:-}" ]] && continue
  printf '%s\t1\n' "$unit" >>"$OUT"
done <"$FOLD"
