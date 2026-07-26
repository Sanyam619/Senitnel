#!/bin/bash
set -euo pipefail
ROOT="${POOL_ROOT:-/var/lib/pool}"
mkdir -p "$ROOT/meta"
echo "0" >"$ROOT/meta/seal_gen.arm"
