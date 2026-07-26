#!/usr/bin/env bash
set -euo pipefail

DATA_ROOT="${CL_DATA_ROOT:-/app/data}"
OUT_PATH="${CL_REPORT_OUT:-/output/cl-eval.json}"

mkdir -p "$(dirname "${OUT_PATH}")"

bash /app/scripts/verify_fixtures.sh >/dev/null

cd /app/eng
cargo build --release --offline --locked

/app/eng/target/release/cl-eval \
  --data "${DATA_ROOT}" \
  --out "${OUT_PATH}"

echo "wrote ${OUT_PATH}"
