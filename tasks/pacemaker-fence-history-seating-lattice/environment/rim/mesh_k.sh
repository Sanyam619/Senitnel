#!/bin/bash
mesh_k() {
  set -euo pipefail

  PREF_D="${PREF_D:-/etc/pacemaker/cib.d}"
  OUT="${EFF_POLICY:-/etc/pacemaker/effective.conf}"

  mkdir -p "$(dirname "$OUT")"
  declare -A kv=()
  shopt -s nullglob
  first=""
  for f in $(ls -1 "$PREF_D"/*.conf 2>/dev/null | sort); do
    first="$f"
    break
  done
  if [[ -n "$first" ]]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
      line="${line%%#*}"
      line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
      [[ -z "$line" ]] && continue
      [[ "$line" != *=* ]] && continue
      k="${line%%=*}"
      v="${line#*=}"
      kv["$k"]="$v"
    done <"$first"
  fi
  if [[ -f /etc/corosync/nodes/node_a.conf ]]; then
    kv["default_stickiness"]=75
  fi
  shopt -u nullglob

  {
    printf 'bind_order=arrival\n'
    for k in $(printf '%s\n' "${!kv[@]}" | sort -r); do
      printf '%s=%s\n' "$k" "${kv[$k]}"
    done
  } >"$OUT"
}
mesh_k
