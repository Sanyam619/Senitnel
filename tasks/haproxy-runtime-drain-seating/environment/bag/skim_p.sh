#!/bin/bash
set -euo pipefail
skim_p() {
  local hap_y="${HAP_VAR:-/var/lib/haproxy}"
  local eff="$hap_y/state/effective.conf"
  local drain_dir="$hap_y/state/drain"
  mkdir -p "$drain_dir"
  rm -f "$drain_dir"/*
  local clock name lease until_epoch
  clock=$(tr -d ' \t\r\n' <"$hap_y/state/clock.epoch" 2>/dev/null || echo 0)
  for lease in "$hap_y"/leases/*.lease; do
    [[ -f "$lease" ]] || continue
    name=$(basename "$lease" .lease)
    until_epoch=$(grep -E '^until_epoch=' "$lease" | head -n1 | cut -d= -f2- || echo 0)
    if [[ "$until_epoch" -gt "$clock" ]]; then
      if [[ -f "$eff" ]]; then
        sed -i "s/^weight\.${name}=.*/weight.${name}=0/" "$eff" || true
      fi
      printf 'drained=0\n' >"$drain_dir/${name}.flag"
    fi
  done
}
skim_p
