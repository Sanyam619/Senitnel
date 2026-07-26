#!/usr/bin/env bash
set -euo pipefail
echo "== coredump =="
cat /app/data/coredump/partial.json
echo
echo "== warmup.log =="
cat /app/data/logs/warmup.log
