#!/bin/bash
set -euo pipefail
clay_m() {
  local PREF_D="${DROPIN_D:-/etc/glusterfs/glusterd.d}"
  local OUT="${EFF_POLICY:-/etc/glusterfs/effective.conf}"
  local f line a b
  mkdir -p "$(dirname "$OUT")"
  declare -A kv=()
  shopt -s nullglob
  for f in $(ls -1 "$PREF_D"/*.conf 2>/dev/null | LC_ALL=C sort); do
    while IFS= read -r line || [[ -n "$line" ]]; do
      line="${line%%#*}"
      line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
      [[ -z "$line" ]] && continue
      [[ "$line" != *=* ]] && continue
      a="${line%%=*}"
      b="${line#*=}"
      if [[ -z "${kv[$a]+x}" ]]; then
        kv["$a"]="$b"
      fi
    done <"$f"
  done
  shopt -u nullglob

  {
    for a in $(printf '%s\n' "${!kv[@]}" | LC_ALL=C sort); do
      printf '%s=%s\n' "$a" "${kv[$a]}"
    done
  } >"$OUT"
}
clay_m
