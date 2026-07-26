#!/usr/bin/env bash
set -euo pipefail
ROOT="${APP_ROOT:-/app}"
STAMP="$ROOT/data/checkpoints/rebase.stamp"
date -u +%Y%m%dT%H%M%SZ > "$STAMP"
echo "checkpoint_rebind_ok stamp_only"
