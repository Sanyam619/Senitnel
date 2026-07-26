#!/bin/bash
set -euo pipefail
D_D="${DEF_D:-/app/data/consul}"
X_D="${EX_D:-/var/lib/consul/ops/extra}"
MAP="${TOKEN_MAP:-/etc/consul.d/runtime/token.map}"
mkdir -p "$(dirname "$MAP")"
shopt -s nullglob
{
  for root in "$D_D" "$X_D"; do
    [[ -d "$root" ]] || continue
    for f in "$root"/*.json; do
      nm="$(jq -r '.service.name // empty' "$f")"
      [[ -n "$nm" ]] || continue
      printf '%s passing\n' "$nm"
    done
  done
} | LC_ALL=C sort >"$MAP"
shopt -u nullglob
