#!/usr/bin/env bash
set -euo pipefail
DATA_ROOT="${DIAR_DATA_ROOT:-/app/data}"
OUT_PATH="${DIAR_REPORT_OUT:-/output/diar-eval.json}"
mkdir -p "$(dirname "${OUT_PATH}")"
bash /app/scripts/verify_fixtures.sh >/dev/null
cd /app/eng
cargo build --release --offline --locked
/app/eng/target/release/diar-eval --data "${DATA_ROOT}" --out "${OUT_PATH}"
echo "wrote ${OUT_PATH}"
