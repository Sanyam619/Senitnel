#!/bin/bash
set -euo pipefail
# Surface-only readiness used by redishhealth.
moss_b() {
  local mx="${MONITOR_D:-/etc/redis/monitors.d}"
  [[ -d "$mx" ]] && [[ -n "$(ls -A "$mx" 2>/dev/null || true)" ]]
}
moss_b
