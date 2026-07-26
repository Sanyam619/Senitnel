#!/usr/bin/env bash
set -euo pipefail
ROOT="${APP_ROOT:-/app}"
export LD_LIBRARY_PATH="${ROOT}/n4:${LD_LIBRARY_PATH:-}"
export SCALE_BLOB="${ROOT}/data/banks/scales_active.bin"
exec "${ROOT}/bin/surfprobe"
