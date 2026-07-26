#!/bin/bash
# Rebuild the sph-run binary and emit /output/reconcile-report.json.
# The cargo toolchain is baked into the image at /usr/local/cargo/bin;
# this script prepends it so `cargo` resolves without the caller
# needing to modify PATH.

export PATH="/usr/local/cargo/bin:${PATH}"
export CARGO_HOME="${CARGO_HOME:-/usr/local/cargo}"
export RUSTUP_HOME="${RUSTUP_HOME:-/usr/local/rustup}"

CARGO="$(command -v cargo || true)"
if [ -z "$CARGO" ]; then
    CARGO="/usr/local/cargo/bin/cargo"
fi

OUT="${1:-/output/reconcile-report.json}"
mkdir -p "$(dirname "$OUT")"

cd /app/ws || { echo "workspace missing at /app/ws" >&2; exit 1; }

"$CARGO" build --release --locked --offline || {
    echo "cargo build failed" >&2
    exit 1
}

cp target/release/sph-run /app/bin/sph-run

/app/bin/sph-run "$OUT"
