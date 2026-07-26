#!/bin/bash
set -euo pipefail
# Bookkeeping stamp; no seating decisions.
note_c() {
  local sv="${REDIS_ROOT:-/var/lib/redis}"
  date -u +%Y%m%dT%H%M%SZ >"$sv/state/note.stamp" 2>/dev/null || printf 'stamp\n' >"$sv/state/note.stamp"
}
note_c
