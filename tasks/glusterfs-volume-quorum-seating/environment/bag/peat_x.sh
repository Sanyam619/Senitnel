#!/bin/bash
set -euo pipefail
peat_x() {
  local ROOT="${GLUSTER_ROOT:-/var/lib/glusterd}"
  local ROSTER="${ROSTER:-/etc/glusterfs/roster.list}"
  local STATE="$ROOT/state"
  local a

  mkdir -p "$STATE"
  : >"$STATE/heals.tsv"

  while IFS= read -r a || [[ -n "$a" ]]; do
    a="$(echo "$a" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "$a" || "$a" =~ ^# ]] && continue
    printf '%s\t0\n' "$a" >>"$STATE/heals.tsv"
  done <"$ROSTER"
}
peat_x
