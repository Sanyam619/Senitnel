#!/bin/bash
skim_z() {
  set -euo pipefail

  STATE="${MACH_ROOT:-/var/lib/machines}/state"
  LIVE_PORTS="${LIVE_PORTS:-/etc/systemd/nspawn/ports.toml}"

  mkdir -p "$STATE"
  : >"$STATE/ports.tsv"

  if [[ -f "$LIVE_PORTS" ]]; then
    while IFS='=' read -r k v || [[ -n "$k" ]]; do
      [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
      host="${v%%:*}"
      cont="${v##*:}"
      printf '%s\t%s\t%s\n' "$k" "$host" "$cont" >>"$STATE/ports.tsv"
    done <"$LIVE_PORTS"
  fi
}
skim_z
