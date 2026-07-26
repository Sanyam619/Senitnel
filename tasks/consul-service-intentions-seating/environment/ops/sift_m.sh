#!/bin/bash
set -euo pipefail
T_F="${TIP_TSV:-/var/lib/consul/ops/live/tip.tsv}"
F_D="${FLOOR_D:-/var/lib/consul/ops/floors}"
O_F="${REG_TSV:-/var/lib/consul/ops/live/reg.tsv}"
mkdir -p "$(dirname "$O_F")"
: >"$O_F"
[[ -f "$T_F" ]] || exit 0
while IFS=$'\t' read -r a b c || [[ -n "${a:-}" ]]; do
  [[ -z "${a:-}" ]] && continue
  fl=0
  if [[ -f "$F_D/${a}.floor" ]]; then
    fl="$(tr -d '[:space:]' <"$F_D/${a}.floor")"
  fi
  g="${c:-0}"
  ok=0
  if [[ "$g" -gt "$fl" ]]; then
    ok=1
  fi
  printf '%s\t%s\t%s\n' "$a" "$ok" "${b:-}" >>"$O_F"
done <"$T_F"
