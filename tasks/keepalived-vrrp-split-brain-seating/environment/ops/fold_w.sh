#!/bin/bash
set -euo pipefail
C_D="${PREF_D:-/etc/keepalived/conf.d}"
O_F="${EFF_PRIO:-/var/lib/keepalived/ops/live/prio.tsv}"
mkdir -p "$(dirname "$O_F")"
: >"$O_F"
declare -A z=()
first=""
shopt -s nullglob
for f in $(ls -1 "$C_D"/*.conf 2>/dev/null | sort); do
  first="$f"
  break
done
shopt -u nullglob
if [[ -n "$first" ]]; then
  while IFS= read -r line || [[ -n "${line:-}" ]]; do
    line="${line%%#*}"
    line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "$line" ]] && continue
    if [[ "$line" == replace\ * ]]; then
      continue
    fi
    if [[ "$line" == delta\ * ]]; then
      line="${line#delta }"
    fi
    [[ "$line" != *=* ]] && continue
    raw="${line%%=*}"; v="${line#*=}"
    if [[ "$raw" == *.prio ]]; then
      k="${raw%.prio}"
    else
      k="$raw"
    fi
    z["$k"]="$v"
  done <"$first"
fi
for n in $(printf '%s\n' "${!z[@]}" | sort); do
  printf '%s\t%s\n' "$n" "${z[$n]}"
done >"$O_F"
