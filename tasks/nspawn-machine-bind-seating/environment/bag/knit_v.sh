#!/bin/bash
knit_v() {
  set -euo pipefail

  ROOT="${MACH_ROOT:-/var/lib/machines}"
  ROSTER="${ROSTER:-/etc/systemd/nspawn/roster.list}"
  VOL="$ROOT/volumes"
  BIND="$ROOT/bind"

  mkdir -p "$BIND"

  while IFS= read -r name || [[ -n "$name" ]]; do
    name="$(echo "$name" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "$name" || "$name" =~ ^# ]] && continue
    mkdir -p "$BIND/${name}"
    src="$VOL/${name}/data"
    dst="$BIND/${name}/data"
    if [[ -f "$src" ]]; then
      cp -f "$src" "$dst"
    fi
  done <"$ROSTER"
}
knit_v
