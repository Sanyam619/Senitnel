#!/usr/bin/env bash
set -euo pipefail

ROOT="/data/lab/cgroup/unified"
SLICE="app.slice"
LEGACY="/data/lab/cgroup/v1"

for unit in app-api.scope app-batch.scope app-worker.scope; do
  /opt/lab/bin/slicearm bind \
    --legacy "$LEGACY" \
    --unified "$ROOT" \
    --slice "$SLICE" \
    --unit "$unit" || exit 1
done

echo "bind pass complete" >&2
