#!/bin/bash
set -euo pipefail
PRIO_IN="${EFF_PRIO:-/var/lib/keepalived/ops/live/prio.tsv}"
track_dir="${track_dir:-/var/lib/keepalived/ops/track}"
O_F="${EFF_PRIO:-/var/lib/keepalived/ops/live/prio.tsv}"
mkdir -p "$(dirname "$O_F")"
declare -A z=()
if [[ -f "$PRIO_IN" ]]; then
  while IFS=$'\t' read -r name v || [[ -n "${name:-}" ]]; do
    [[ -z "${name:-}" ]] && continue
    z["$name"]="$v"
  done <"$PRIO_IN"
fi
shopt -s nullglob
for f in "$track_dir"/*.wt; do
  [[ -f "$f" ]] || continue
  base="$(basename "$f" .wt)"
  delta=0
  while IFS= read -r line || [[ -n "${line:-}" ]]; do
    line="${line%%#*}"
    line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "$line" || "$line" != *=* ]] && continue
    k="${line%%=*}"; v="${line#*=}"
    if [[ "$k" == "delta" ]]; then
      delta="$v"
    fi
  done <"$f"
  cur="${z[$base]:-0}"
  z["$base"]=$((cur + delta))
done
shopt -u nullglob
{
  for n in $(printf '%s\n' "${!z[@]}" | sort); do
    printf '%s\t%s\n' "$n" "${z[$n]}"
  done
} >"$O_F"
