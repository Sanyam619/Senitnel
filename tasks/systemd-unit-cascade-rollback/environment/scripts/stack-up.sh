#!/usr/bin/env bash
set -euo pipefail
/app/scripts/merge-overrides.sh journal.service
/app/scripts/merge-overrides.sh store.service
/app/scripts/merge-overrides.sh cache.service
/app/scripts/merge-overrides.sh ingress.service
/app/scripts/merge-overrides.sh stack.target
if ! /app/bin/arm_b \
    --units-root /data/stack/units \
    --runtime-root /data/stack/runtime \
    --target stack.target; then
  echo "stackarm activation failed" >&2
  exit 1
fi
