#!/bin/bash
set -euo pipefail
S_D="${SHEET_D:-/etc/consul.d/conf.d}"
O_F="${BIND_TSV:-/var/lib/consul/ops/live/bind.tsv}"
mkdir -p "$(dirname "$O_F")"
: >"$O_F"
declare -A z=()
for f in $(ls -1 "$S_D"/*.hcl 2>/dev/null | LC_ALL=C sort); do
  while IFS= read -r line || [[ -n "${line:-}" ]]; do
    line="${line%%#*}"
    line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "$line" ]] && continue
    if [[ "$line" == pin\ * ]]; then
      line="${line#pin }"
    fi
    [[ "$line" != *=* ]] && continue
    k="$(echo "${line%%=*}" | tr -d '[:space:]')"
    v="$(echo "${line#*=}" | tr -d '[:space:]')"
    [[ "$k" == *.node ]] || continue
    z["${k%.node}"]="$v"
  done <"$f"
done
{
  for n in $(printf '%s\n' "${!z[@]}" | LC_ALL=C sort); do
    printf '%s\t%s\n' "$n" "${z[$n]}"
  done
} >"$O_F"
