#!/bin/bash
# note_t — decoy: archive a non-graded hold memo.
set -euo pipefail
HOLD_D="${AUTO_ROOT:-/var/lib/autofs}/holds"
MEMO=/var/log/autofs/hold.memo
mkdir -p "$(dirname "$MEMO")"
ls -1 "$HOLD_D" 2>/dev/null | sort >"$MEMO" || true
