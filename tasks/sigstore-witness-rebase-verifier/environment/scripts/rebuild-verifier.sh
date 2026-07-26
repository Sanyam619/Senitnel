#!/bin/bash
set -euo pipefail
cd /app
cargo build --release --offline --locked --bin vfy
cp -f /app/target/release/vfy /app/bin/vfy
