#!/bin/bash
set -euo pipefail
cd /opt/wghandoff
go build -o bin/reconcile ./cmd/reconcile
bin/reconcile --policy data/policy.toml --scenarios data/scenarios --out /tmp/wg-smoke-out
test -s /tmp/wg-smoke-out/handoff_report.json
