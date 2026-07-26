#!/bin/bash
set -euo pipefail
ETC="${SYS_ETC:-/etc/systemd/system}"
META_D="${META_D:-/app/data/pathunits}"
EXTRA_M="${EXTRA_D:-/var/lib/systemd/ops/extra}"
OUT="${FOLD_TSV:-/var/lib/systemd/ops/live/fold.tsv}"
mkdir -p "$(dirname "$OUT")"
: >"$OUT"

read_unit_id() {
  local m="$1" id=""
  while IFS= read -r line || [[ -n "${line:-}" ]]; do
    line="${line%%#*}"
    line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ "$line" == id=* ]] && id="${line#id=}"
  done <"$m"
  printf '%s' "$id"
}

shopt -s nullglob
for root in "$META_D" "$EXTRA_M"; do
  [[ -d "$root" ]] || continue
  for m in "$root"/*.meta; do
    unit="$(read_unit_id "$m")"
    [[ -n "$unit" ]] || continue
    exists=""; changed=""; dne=""
    base="$ETC/${unit}.path"
    if [[ -f "$base" ]]; then
      while IFS= read -r line || [[ -n "${line:-}" ]]; do
        line="${line%%#*}"
        line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
        [[ -z "$line" || "$line" != *=* ]] && continue
        k="${line%%=*}"; v="${line#*=}"
        case "$k" in
          PathExists) exists="$v" ;;
          PathChanged) changed="$v" ;;
          DirectoryNotEmpty) dne="$v" ;;
        esac
      done <"$base"
    fi
    printf '%s\t%s\t%s\t%s\n' "$unit" "${exists:--}" "${changed:--}" "${dne:--}" >>"$OUT"
  done
done
shopt -u nullglob
