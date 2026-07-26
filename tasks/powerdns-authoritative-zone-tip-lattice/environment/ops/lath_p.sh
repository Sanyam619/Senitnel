#!/bin/bash
set -euo pipefail
lath_p() {
  local pd_x="${PD_ETC:-/etc/powerdns}"
  local pd_y="${PD_VAR:-/var/lib/powerdns}"
  mkdir -p "$pd_y/state"
  local sheet name val
  for sheet in "$pd_x"/floors/*.floor; do
    [[ -f "$sheet" ]] || continue
    name=$(basename "$sheet" .floor)
    val=$(tr -d ' \t\r\n' <"$sheet")
    printf '%s\n' "$val" >"$pd_y/state/tip_${name}.gen"
  done
  for sheet in "$pd_x"/serials/*.serial; do
    [[ -f "$sheet" ]] || continue
    name=$(basename "$sheet" .serial)
    val=$(tr -d ' \t\r\n' <"$sheet")
    printf '%s\n' "$val" >"$pd_y/state/tip_${name}.serial"
  done
}
lath_p
