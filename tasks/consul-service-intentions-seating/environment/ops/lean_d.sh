#!/bin/bash
set -euo pipefail
S_D="${MESH_D:-/etc/consul.d/intentions.d}"
O_F="${ACTS_TSV:-/var/lib/consul/ops/live/acts.tsv}"
mkdir -p "$(dirname "$O_F")"
: >"$O_F"
for f in $(ls -1 "$S_D"/*.hcl 2>/dev/null | LC_ALL=C sort); do
  while IFS= read -r line || [[ -n "${line:-}" ]]; do
    line="${line%%#*}"
    line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "$line" ]] && continue
    [[ "$line" == pair\ * ]] || continue
    body="${line#pair }"
    [[ "$body" == *=* ]] || continue
    val="$(echo "${body#*=}" | tr -d '[:space:]')"
    read -r one two _rest <<<"${body%%=*}"
    [[ -n "${one:-}" && -n "${two:-}" ]] || continue
    printf '%s\t%s\t%s\n' "$one" "$two" "$val" >>"$O_F"
  done <"$f"
done
