#!/bin/bash
# note_c — archive a shift-handover window memo.
set -euo pipefail
HOLD_D="${LVM_ROOT:-/var/lib/lvm}/holds"
MEMO=/var/log/lvm/window.memo
mkdir -p "$(dirname "$MEMO")"
ls -1 "$HOLD_D" 2>/dev/null | LC_ALL=C sort >"$MEMO" || true
