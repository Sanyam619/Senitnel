#!/bin/bash
set -euo pipefail
SCENARIO="${1:?scenario directory}"
TABLE="$SCENARIO/epoch_table.json"
LIVE="$SCENARIO/live_state.json"
python3 - <<'PY' "$TABLE" "$LIVE"
import json, sys
tab = json.load(open(sys.argv[1]))
live = json.load(open(sys.argv[2]))
tab["current_epoch"] = live["epoch"]
json.dump(tab, open(sys.argv[1], "w"), indent=2)
print()
PY
