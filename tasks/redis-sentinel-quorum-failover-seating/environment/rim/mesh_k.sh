#!/bin/bash
set -euo pipefail
# Fold drop-ins; later files win. Writes effective.conf.
mesh_k() {
  local pd="${DROPIN_D:-/etc/redis/sentinel.d}"
  local out="${EFF_POLICY:-/etc/redis/effective.conf}"
  local f line a b
  : >"$out"
  declare -A kv=()
  for f in $(ls -1 "$pd"/*.conf 2>/dev/null | LC_ALL=C sort); do
    while IFS= read -r line || [[ -n "${line:-}" ]]; do
      line="${line%%#*}"
      line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
      [[ -z "$line" || "$line" != *=* ]] && continue
      a="${line%%=*}"
      b="${line#*=}"
      kv["$a"]="$b"
    done <"$f"
  done
  for a in tip_policy bind_order abort; do
    if [[ -n "${kv[$a]+x}" ]]; then
      printf '%s=%s\n' "$a" "${kv[$a]}" >>"$out"
    fi
  done
}
mesh_k
