#!/bin/bash
set -euo pipefail

SCENARIOS="${1:-/app/scenarios}"
OUTPUT="${2:-/app/output}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

python3 /app/k7/k7.py "$SCENARIOS" "$WORK/stage1.json"
python3 /app/m3/m3.py "$WORK/stage1.json" "$WORK/stage2.json"
python3 /app/r9/r9.py "$WORK/stage2.json" "$WORK/stage3.json"
python3 /app/w2/w2.py "$WORK/stage3.json" "$WORK/stage4.json"

python3 - "$WORK/stage4.json" "$OUTPUT" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
out = Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
decisions = {"scenarios": {}}
compensations = {"scenarios": {}}
for name, bundle in sorted(payload["scenarios"].items()):
    decisions["scenarios"][name] = {
        "transactions": {
            txid: {"decision": value}
            for txid, value in sorted(bundle["decisions"].items())
        }
    }
    compensations["scenarios"][name] = {
        "sagas": {
            group: {"actions": labels}
            for group, labels in sorted(bundle["sagas"].items())
        }
    }
(out / "decisions.json").write_text(json.dumps(decisions) + "\n", encoding="utf-8")
(out / "compensations.json").write_text(json.dumps(compensations) + "\n", encoding="utf-8")
PY
