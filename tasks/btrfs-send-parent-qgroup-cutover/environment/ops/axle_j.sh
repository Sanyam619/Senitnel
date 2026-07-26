#!/bin/bash
set -euo pipefail

ROOT="${BTRFS_ROOT:-/var/lib/btrfs}"
JOURNAL="${BTRFS_JOURNAL:-$ROOT/ops/journal.jsonl}"
STATE="$ROOT/meta"
ENV_FILE="${BTRFS_DESKD_ENV:-/etc/btrfs/deskd.env}"

mkdir -p "$STATE" "$(dirname "$ENV_FILE")"

if [[ ! -f "$JOURNAL" ]]; then
  echo "axle_j: missing journal" >&2
  exit 1
fi

line=$(grep -v '^[[:space:]]*$' "$JOURNAL" | tail -n 1)
mode=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1]).get("mode",""))' "$line")
gen=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1]).get("gen",0))' "$line")
hold=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1]).get("hold",""))' "$line")

printf '%s\n' "$gen" >"$STATE/gen.live"
printf '%s\n' "$mode" >"$STATE/attach.intent"
printf '%s\n' "$hold" >"$STATE/hold.token"

{
  echo "# deskd runtime environment"
  if [[ "$mode" == "seal" ]]; then
    echo "PAYLOAD_LINEAGE=sealed"
  else
    echo "PAYLOAD_LINEAGE=decoy"
  fi
  echo "HOLD_TOKEN=$hold"
  echo "BTRFS_VOLUME_ROOT=$ROOT/volumes"
  echo "BTRFS_ATTACH_ROOT=$ROOT/attach"
} >"$ENV_FILE"
