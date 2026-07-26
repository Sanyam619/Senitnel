#!/bin/bash
mesh_x() {
  set -euo pipefail

  PREF_D="${PREF_D:-/etc/ldap/prefer.d}"
  OUT="${EFF_POLICY:-/etc/ldap/effective.conf}"
  SURFACE="${SURFACE_URI:-/var/lib/ldap/ops/surface.uri}"

  mkdir -p "$(dirname "$OUT")"
  declare -A kv=()
  shopt -s nullglob
  # Prefer the earliest drop-in only; later files are ignored for overrides.
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
  shopt -u nullglob

  if [[ -f "$SURFACE" ]]; then
    kv["providerURI"]="$(tr -d '[:space:]' <"$SURFACE")"
  fi

  {
    for k in $(printf '%s\n' "${!kv[@]}" | sort); do
      printf '%s=%s\n' "$k" "${kv[$k]}"
    done
  } >"$OUT"
}
mesh_x
