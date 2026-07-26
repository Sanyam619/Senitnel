#!/usr/bin/env bash
set -euo pipefail

DATA_ROOT="${SPEC_DATA_ROOT:-/app/data}"
OUT_PATH="${SPEC_REPORT_OUT:-/output/recalibration-report.json}"
SEED="${SPEC_SEED:-3405691582}"

mkdir -p "$(dirname "${OUT_PATH}")"

cd /app/eng
cargo build --release --offline --locked

/app/eng/target/release/spec-eval eval \
  --data "${DATA_ROOT}" \
  --seed "${SEED}" \
  --out "${OUT_PATH}"

echo "wrote ${OUT_PATH}"
