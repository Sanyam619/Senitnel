#!/usr/bin/env bash
# Publishes /output/asr-eval.json from the evaluation workspace.
set -euo pipefail

export CARGO_NET_OFFLINE=true
cargo build --release --offline --manifest-path /app/eng/Cargo.toml >/dev/null

mkdir -p /output
exec /app/eng/target/release/asreval
