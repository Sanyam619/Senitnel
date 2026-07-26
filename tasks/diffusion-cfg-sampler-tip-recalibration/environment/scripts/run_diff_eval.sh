#!/bin/bash
set -euo pipefail

OUT="${1:-/output/diff-eval.json}"
mkdir -p "$(dirname "$OUT")"

cd /app/eng
cargo build --release --offline --locked
./target/release/bevel eval --out "$OUT"
