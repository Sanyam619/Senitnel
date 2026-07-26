#!/bin/bash
# bind_v.sh
set -euo pipefail

# shellcheck disable=SC1091
if [[ -f /etc/fleet/fleetd.env ]]; then
  set -a
  # shellcheck disable=SC1090
  source /etc/fleet/fleetd.env
  set +a
fi

vol_root="${FLEET_VOLUME_ROOT:-/var/lib/fleet/volumes}"
rt_root="${FLEET_RUNTIME_ROOT:-/var/lib/fleet/runtime}"
intent=$(cat /var/lib/fleet/state/attach.intent 2>/dev/null || echo decoy)
lineage="${PAYLOAD_LINEAGE:-$intent}"
hold=$(cat /var/lib/fleet/state/hold.token 2>/dev/null || echo "${HOLD_TOKEN:-lab-tmp}")

for ep in alpha beta gamma delta epsilon; do
  mkdir -p "$rt_root/$ep"
  dst="$rt_root/$ep"
  src_dir="$vol_root/$ep/$lineage"
  if [[ ! -d "$src_dir" ]]; then
    src_dir="$vol_root/$ep/decoy"
  fi
  if [[ ! -d "$src_dir" ]]; then
    src_dir="$vol_root/$ep/sealed"
  fi
  rm -rf "$dst"
  mkdir -p "$dst"
  if [[ -f "$src_dir/payload.bin" ]]; then
    cp -f "$src_dir/payload.bin" "$dst/payload.bin"
  fi
  printf '%s\n' "$hold" >"$dst/.hold"
done
