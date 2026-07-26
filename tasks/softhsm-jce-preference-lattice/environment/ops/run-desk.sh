#!/bin/bash
# Operator entrypoint for post-incident SoftHSM trust admission.
set -euo pipefail
cd /app
OUT="${1:-/output/sign-ledger.json}"
cargo build -p trusteval --release
exec /app/target/release/trusteval attest --out "$OUT"
