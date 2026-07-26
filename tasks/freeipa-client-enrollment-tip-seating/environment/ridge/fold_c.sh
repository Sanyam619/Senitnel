#!/bin/bash
fold_c() {
  set -euo pipefail

  PREF_D="${PREF_D:-/etc/krb5.conf.d}"
  OUT="${EFF_POLICY:-/etc/ipa/effective.conf}"
  SURFACE="${SURFACE_REALM:-/var/lib/ipa/ops/surface.realm}"

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
  shopt -u nullglob

  if [[ -f "$SURFACE" ]]; then
    kv["realm"]="$(tr -d '[:space:]' <"$SURFACE")"
  fi

  {
    for k in $(printf '%s\n' "${!kv[@]}" | sort); do
      printf '%s=%s\n' "$k" "${kv[$k]}"
    done
  } >"$OUT"
}
fold_c
