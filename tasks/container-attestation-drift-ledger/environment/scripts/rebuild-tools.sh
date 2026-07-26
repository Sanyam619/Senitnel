#!/bin/bash
set -euo pipefail
cd /app
cargo build --release --locked -p digctl
cp -f /app/target/release/digctl /app/bin/digctl
go build -trimpath -ldflags="-s -w" -o /app/bin/provcheck ./go/cmd/provcheck
go build -trimpath -ldflags="-s -w" -o /app/bin/polgate ./go/cmd/polgate
go build -trimpath -ldflags="-s -w" -o /app/bin/replayctl ./go/cmd/replayctl
