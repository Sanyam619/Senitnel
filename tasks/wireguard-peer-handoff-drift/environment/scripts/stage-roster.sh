#!/bin/bash
set -euo pipefail
SCENARIO="${1:?scenario directory}"
LIVE="$SCENARIO/live_state.json"
PENDING="$SCENARIO/pending.json"
python3 - <<'PY' "$LIVE" "$PENDING"
import json, sys
live = json.load(open(sys.argv[1]))
pending = json.load(open(sys.argv[2]))
merged = sorted(set(live.get("member_ids", [])) | set(pending.get("member_ids", [])))
live["member_ids"] = merged
json.dump(live, open(sys.argv[1], "w"), indent=2)
print()
PY
