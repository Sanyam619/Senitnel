#!/bin/bash
set -euo pipefail

ROOT="${BTRFS_ROOT:-/var/lib/btrfs}"
LEASE_DIR="${LEASE_DIR:-/var/run/btrfs}"

mkdir -p "$LEASE_DIR" "$ROOT/origins"

printf '1\n' >"$LEASE_DIR/stale.part"
printf 'held\n' >"$ROOT/origins/boot.lease"

for lane in alpha beta gamma delta omega; do
  mkdir -p "$ROOT/volumes/$lane/host"
  printf 'host\n' >"$ROOT/volumes/$lane/host/marker.flag"
done
