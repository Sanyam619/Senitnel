#!/usr/bin/env bash
set -uo pipefail

if [ ! -x /opt/lab/bin/walscope ] || [ ! -x /opt/lab/bin/sidealign ] || [ ! -x /opt/lab/bin/mkstandalone ]; then
  echo "missing lab tools" >&2
  exit 1
fi

cat > config/elevation_runbook.toml <<'RUNBOOK'
# elevation runbook — operator notes
phase = "inspect"
tooling = ["walscope", "sidealign", "mkstandalone", "sizecheck"]
replica_path = "/data/standby/replica.db"
wal_path = "/data/standby/replica.db-wal"
shm_path = "/data/standby/replica.db-shm"
live_path = "/data/standby/live.db"
trace_path = "/data/standby/elevation_audit.json"
snapshot_path = "/data/fixtures/snapshot/source.db"

[inspect]
command = "walscope --json"
notes = "read last_valid_index and salt before trimming"

[trim]
command = "walscope --truncate-at"
notes = "never trim at EOF when tail garbage is present"

[align]
command = "sidealign --shm --salt"
notes = "rewrite shm header after wal trim"

[materialize]
command = "mkstandalone --src --dst"
notes = "run only after align reports success"

[verify]
user_version = 42
min_rows = 5
trace_version = 1
required_tools = ["walscope", "sidealign", "mkstandalone"]

[ordering]
first = "walscope"
second = "sidealign"
third = "mkstandalone"

[guardrails]
preserve_snapshot = true
avoid_repeat_materialize = true
RUNBOOK

rm -f /data/standby/live.db /data/standby/elevation_audit.json

JSON=$(/opt/lab/bin/walscope --file /data/standby/replica.db-wal --shm /data/standby/replica.db-shm --json)
IDX=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["last_valid_index"])' <<<"$JSON")
SALT=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["salt"])' <<<"$JSON")

python3 -c '
import json, pathlib
path = pathlib.Path("/data/standby/elevation_audit.json")
path.write_text(json.dumps({"version": 1, "steps": [{"tool": "walscope", "action": "inspect"}]}, indent=2))
'

/opt/lab/bin/walscope --file /data/standby/replica.db-wal --truncate-at "$IDX"
python3 -c '
import json, pathlib
p = pathlib.Path("/data/standby/elevation_audit.json")
d = json.loads(p.read_text())
d["steps"].append({"tool": "walscope", "action": "trim"})
p.write_text(json.dumps(d, indent=2))
'

/opt/lab/bin/sidealign --shm /data/standby/replica.db-shm --salt "$SALT"
python3 -c '
import json, pathlib
p = pathlib.Path("/data/standby/elevation_audit.json")
d = json.loads(p.read_text())
d["steps"].append({"tool": "sidealign", "action": "align"})
p.write_text(json.dumps(d, indent=2))
'

/opt/lab/bin/mkstandalone --src /data/standby/replica.db --dst /data/standby/live.db
python3 -c '
import json, pathlib
p = pathlib.Path("/data/standby/elevation_audit.json")
d = json.loads(p.read_text())
d["steps"].append({"tool": "mkstandalone", "action": "materialize"})
p.write_text(json.dumps(d, indent=2))
'

if [ ! -f /data/standby/live.db ]; then
  echo "live db not created" >&2
  exit 1
fi

if ! sqlite3 /data/standby/live.db "PRAGMA user_version;" | grep -q '^42$'; then
  echo "user_version mismatch" >&2
  exit 1
fi

if [ "$(sqlite3 /data/standby/live.db "SELECT COUNT(*) FROM inventory;")" -lt 5 ]; then
  echo "unexpected row count" >&2
  exit 1
fi

echo "elevation complete"
