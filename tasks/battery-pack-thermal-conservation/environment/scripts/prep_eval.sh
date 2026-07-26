#!/bin/bash
set -euo pipefail
# Evaluation prep: compile thermal advance sources and rematerialize unaccepted trial prefs.
APP_ROOT="${APP_ROOT:-/app}"
POLICY="$APP_ROOT/data/policy"

python3 -m py_compile "$APP_ROOT/solver/core/step.py" \
  "$APP_ROOT/knit_x/op_a.py" \
  "$APP_ROOT/fold_y/op_b.py" \
  "$APP_ROOT/slot_z/op_c.py"

if [[ -f "$POLICY/handoff.accept" ]]; then
  rm -f "$POLICY/trial_pref.live"
else
  cp "$POLICY/trial_pref.seed" "$POLICY/trial_pref.live"
fi

echo "prep ok"
