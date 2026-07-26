#!/bin/bash
# Drive the SPH kernel-handoff reconciliation and emit the residual report.
# Default output: /output/reconcile-report.json

export PATH="/usr/local/cargo/bin:${PATH}"
export CARGO_HOME="${CARGO_HOME:-/usr/local/cargo}"
export RUSTUP_HOME="${RUSTUP_HOME:-/usr/local/rustup}"

CARGO="$(command -v cargo || true)"
if [ -z "$CARGO" ]; then
    CARGO="/usr/local/cargo/bin/cargo"
fi

OUT="${1:-/output/reconcile-report.json}"
mkdir -p "$(dirname "$OUT")"

cd /app/ws || { echo "simulation tree missing at /app/ws" >&2; exit 1; }

"$CARGO" build --release --locked --offline || {
    echo "simulation rebuild failed" >&2
    exit 1
}

cp target/release/sph-run /app/bin/sph-run

/app/bin/sph-run "$OUT"
