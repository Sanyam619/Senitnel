#!/bin/bash
mesh_x() {
  set -euo pipefail

  PREF_D="${PREF_D:-/etc/auto.master.d}"
  OUT="${EFF_POLICY:-/etc/autofs/effective.conf}"

  mkdir -p "$(dirname "$OUT")"
  declare -A kv=()
  shopt -s nullglob
  for f in $(ls -1 "$PREF_D"/*.conf 2>/dev/null | sort); do
    while IFS= read -r line || [[ -n "$line" ]]; do
      line="${line%%#*}"
      line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
      [[ -z "$line" ]] && continue
      [[ "$line" != *=* ]] && continue
      k="${line%%=*}"
      v="${line#*=}"
      if [[ -z "${kv[$k]+x}" ]]; then
        kv["$k"]="$v"
      fi
    done <"$f"
  done
  shopt -u nullglob

  {
    for k in $(printf '%s\n' "${!kv[@]}" | sort); do
      printf '%s=%s\n' "$k" "${kv[$k]}"
    done
  } >"$OUT"
}
mesh_x
