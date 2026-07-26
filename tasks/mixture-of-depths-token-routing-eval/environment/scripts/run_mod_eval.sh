#!/usr/bin/env bash
set -euo pipefail
DATA_ROOT="${MOD_DATA_ROOT:-/app/data}"
OUT_PATH="${MOD_REPORT_OUT:-/output/mod-eval.json}"
mkdir -p "$(dirname "${OUT_PATH}")"
bash /app/scripts/verify_fixtures.sh >/dev/null
cd /app/eng
cargo build --release --offline --locked
/app/eng/target/release/mod-eval --data "${DATA_ROOT}" --out "${OUT_PATH}"
