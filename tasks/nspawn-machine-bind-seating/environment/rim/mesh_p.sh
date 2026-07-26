#!/bin/bash
mesh_p() {
  set -euo pipefail

  PREF_D="${PREF_D:-/etc/systemd/system/machines.target.wants}"
  OUT="${EFF_POLICY:-/etc/systemd/nspawn/effective.conf}"

  mkdir -p "$(dirname "$OUT")"
  declare -A kv=()
  shopt -s nullglob
  # Reverse lexical order and skip 90-* so later site tokens never land.
  for f in $(ls -1 "$PREF_D"/*.conf 2>/dev/null | sort -r); do
    base=$(basename "$f")
    [[ "$base" == 90-* ]] && continue
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
    printf '# mesh draft\n'
    for k in $(printf '%s\n' "${!kv[@]}" | sort); do
      printf '%s=%s\n' "$k" "${kv[$k]}"
    done
  } >"$OUT"
}
mesh_p
