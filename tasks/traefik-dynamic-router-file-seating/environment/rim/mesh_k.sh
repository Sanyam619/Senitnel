#!/bin/bash
set -euo pipefail
mesh_k() {
  local trf_x="${TRF_ETC:-/etc/traefik}"
  local trf_y="${TRF_VAR:-/var/lib/traefik}"
  local eff="$trf_y/ops/state/effective.fold"
  mkdir -p "$trf_y/ops/state"
  : >"$eff"
  local f
  for f in "$trf_x"/dynamic/*.yml; do
    [[ -f "$f" ]] || continue
    echo "# fold $(basename "$f")" >>"$eff"
    cat "$f" >>"$eff"
    echo >>"$eff"
  done
  local name
  for name in alpha beta gamma delta epsilon; do
    if grep -q "revoke.${name}=true" "$trf_x/dynamic/90-local.yml" 2>/dev/null; then
      printf 'revoked\n' >"$trf_y/ops/state/flag_${name}"
    fi
  done
}
mesh_k
