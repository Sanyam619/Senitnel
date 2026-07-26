#!/usr/bin/env bash
set -euo pipefail
exec /app/bin/chk_a \
  --units-root /data/stack/units \
  --runtime-root /data/stack/runtime
