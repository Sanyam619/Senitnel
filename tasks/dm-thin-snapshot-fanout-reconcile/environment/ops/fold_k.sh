#!/bin/bash
set -euo pipefail
ROOT="${POOL_ROOT:-/var/lib/pool}"
WAL="$ROOT/journal/act.wal"
RUNTIME="$ROOT/meta/runtime.tsv"
mkdir -p "$ROOT/meta"
: >"$RUNTIME"
order=0
declare -A latest_line
declare -a order_keys
while IFS= read -r line || [[ -n "$line" ]]; do
  [[ -z "$line" || "$line" == \#* ]] && continue
  IFS='|' read -r gen seq drill tip origin kind epoch floor <<<"$line"
  if [[ -z "${latest_line[$drill]+x}" ]]; then
    order_keys+=("$drill")
  fi
  latest_line[$drill]="$drill|$tip|$origin|$kind|$epoch|$floor"
done <"$WAL"
for drill in "${order_keys[@]}"; do
  order=$((order + 1))
  IFS='|' read -r d tip origin kind epoch floor <<<"${latest_line[$drill]}"
  printf '%d\t%s\t%s\t%s\t%s\t%s\t%s\n' "$order" "$d" "$tip" "$origin" "$kind" "$epoch" "$floor" >>"$RUNTIME"
done
