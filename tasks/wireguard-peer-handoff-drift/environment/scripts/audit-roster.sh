#!/bin/bash
set -euo pipefail
SCENARIO="${1:?scenario directory}"
TABLE="$SCENARIO/epoch_table.json"
LIVE="$SCENARIO/live_state.json"
PICK=$(python3 - <<'PY' "$LIVE"
import json, sys
live = json.load(open(sys.argv[1]))
print(live.get("epoch", 0))
PY
)
IDS=$(python3 - <<'PY' "$TABLE" "$PICK"
import json, sys
tab = json.load(open(sys.argv[1]))
pick = int(sys.argv[2])
ids = []
for row in tab["epochs"]:
    if row["epoch"] == pick:
        ids = [m["id"] for m in row["members"]]
print(json.dumps(ids))
PY
)
python3 - <<'PY' "$LIVE" "$IDS"
import json, sys
live = json.load(open(sys.argv[1]))
live["member_ids"] = json.loads(sys.argv[2])
json.dump(live, open(sys.argv[1], "w"), indent=2)
print()
PY
