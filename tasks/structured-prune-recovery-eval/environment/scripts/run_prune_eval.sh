#!/usr/bin/env bash
# Rebuild the evaluation workspace and publish the recovery report.
set -euo pipefail

root="${PRUNE_ROOT:-/app}"

cd "$root/eng"
cargo build --release --locked --offline

mkdir -p /output
exec "$root/eng/target/release/pruneeval"
