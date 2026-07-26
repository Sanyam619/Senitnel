#!/usr/bin/env bash
# Rebuild the evaluation workspace and publish the report.
set -euo pipefail

ROOT="${Q4_ROOT:-/app}"
cd "${ROOT}/eng"

cargo build --release --offline --quiet
exec "${ROOT}/eng/target/release/int4eval"
