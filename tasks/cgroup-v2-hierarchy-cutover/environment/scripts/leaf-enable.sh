#!/usr/bin/env bash
set -euo pipefail

SLICE="/data/lab/cgroup/unified/app.slice"

for unit in app-api.scope app-batch.scope app-worker.scope; do
  /opt/lab/bin/slicearm arm --parent "$SLICE/$unit" --add io,memory || exit 1
done

echo "leaf arm complete" >&2
