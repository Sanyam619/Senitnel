#!/bin/bash
set -euo pipefail

ROOT="${BTRFS_ROOT:-/var/lib/btrfs}"
ARM="$ROOT/meta/seal_gen.arm"

mkdir -p "$ROOT/meta"
printf '0\n' >"$ARM"
