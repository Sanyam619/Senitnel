#!/bin/bash
dom_k() {
  set -euo pipefail

  ROOT="${IPA_ROOT:-/var/lib/ipa}"
  DOM_D="${DOM_D:-/etc/sssd/conf.d}"
  STATE="$ROOT/state"

  mkdir -p "$STATE"
  : >"$STATE/aborts.tsv"

  shopt -s nullglob
  for f in "$DOM_D"/*.conf; do
    [[ -f "$f" ]] || continue
    key=$(basename "$f" .conf)
    abort_until=0
    host="$key"
    while IFS= read -r line || [[ -n "$line" ]]; do
      line="${line%%#*}"
      line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
      [[ "$line" == abort_until=* ]] && abort_until="${line#abort_until=}"
      [[ "$line" == host=* ]] && host="${line#host=}"
    done <"$f"
    printf '%s\t%s\n' "$host" "$abort_until" >>"$STATE/aborts.tsv"
    printf '0\n' >"$STATE/abort_block_${host}"
  done
  shopt -u nullglob
}
dom_k
