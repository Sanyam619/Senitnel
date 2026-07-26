#!/bin/bash
set -euo pipefail

OUT="${1:-/output/gnn-eval.json}"
mkdir -p "$(dirname "$OUT")"

cd /app/eng
cargo build --release --offline --locked
./target/release/loam eval --out "$OUT"
