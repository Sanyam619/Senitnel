#!/usr/bin/env bash
set -euo pipefail
ROOT="${APP_ROOT:-/app}"
export APP_ROOT="$ROOT"
export LD_LIBRARY_PATH="${ROOT}/n4:${LD_LIBRARY_PATH:-}"
export SCALE_BLOB="${ROOT}/data/banks/scales_active.bin"

chmod +x "$ROOT/x7/mesh_m.sh" "$ROOT/eval/rebind_checkpoint.sh" 2>/dev/null || true
"$ROOT/x7/mesh_m.sh"
"$ROOT/eval/rebind_checkpoint.sh"
mkdir -p /output
exec "${ROOT}/bin/runtime" /output/eval-ledger.json
