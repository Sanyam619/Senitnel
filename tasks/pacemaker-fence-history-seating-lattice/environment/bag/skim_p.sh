#!/bin/bash
skim_p() {
  set -euo pipefail

  ROOT="${CLUSTER_OPS:-/var/lib/cluster/ops}"
  STATE="${PCM_ROOT:-/var/lib/pacemaker}/state"
  JOURNAL="$ROOT/fence_journal.jsonl"

  mkdir -p "$STATE"
  : >"$STATE/fences.tsv"

  if [[ -f "$JOURNAL" ]]; then
    python3 - "$JOURNAL" "$STATE" <<'PY'
import json, sys
from pathlib import Path
journal, state = map(Path, sys.argv[1:])
targets = set()
for line in journal.read_text().splitlines():
    line = line.strip()
    if not line:
        continue
    row = json.loads(line)
    targets.add(row.get("target", ""))
for t in sorted(targets):
    if not t:
        continue
    (state / f"fence_clear_{t}").write_text("1\n")
(state / "fences.tsv").write_text("")
PY
  fi
}
skim_p
