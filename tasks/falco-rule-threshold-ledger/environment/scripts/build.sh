#!/bin/bash
set -euo pipefail
cd /app
export CARGO_TARGET_DIR="${CARGO_TARGET_DIR:-/app/target}"
mkdir -p "${CARGO_TARGET_DIR}" /app/bin
cargo build --release
install -m 0755 "${CARGO_TARGET_DIR}/release/frtl_audit" /app/bin/frtl_audit
test -x /app/bin/frtl_audit
