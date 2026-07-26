#!/bin/bash
# note_c — archive a shift-handover hold memo.
set -euo pipefail
HOLD_D="${GLUSTER_ROOT:-/var/lib/glusterd}/holds"
MEMO=/var/log/gluster/hold.memo
mkdir -p "$(dirname "$MEMO")"
ls -1 "$HOLD_D" 2>/dev/null | LC_ALL=C sort >"$MEMO" || true
