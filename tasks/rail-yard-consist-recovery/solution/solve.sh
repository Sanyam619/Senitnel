#!/bin/bash
set -euo pipefail

export PATH="/app/bin:${PATH}"

test -d /app/config/l7
test -x /app/bin/yardctl
test -x /app/bin/lane
mkdir -p /output /app/ops/staging

read -r HEAD < <(
python3 <<'PY'
import json
from pathlib import Path

head = 0
tiers = {}
for path in sorted(Path("/app/data/movements").glob("tier_*.jsonl")):
    tier_head = 0
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        seq = int(rec["seq"])
        head = max(head, seq)
        tier_head = max(tier_head, seq)
    tiers[path.stem] = tier_head
if head == 0:
    raise SystemExit("could not derive movement head")
if max(tiers.values()) != head:
    raise SystemExit("tier head map inconsistent with promoted head")
print(head)
PY
)

cat > /app/config/l7/k9.toml <<EOF
journal_pin = ${HEAD}
seq_floor = ${HEAD}
yard_ready = true
audit_stamp = "applied"
anchor_mode = "promoted"
EOF

cat > /app/config/l7/m2.toml <<EOF
tier_reducer = "max"
replay_gate = 0
barrier_live = true
window_scan = true
EOF

cat > /app/config/l7/p7.toml <<EOF
phases = ["scan", "bind", "emit"]
strict_chain = true
allow_batch = false
workflow_note = "promoted"
EOF

cat > /app/config/l7/n3.toml <<EOF
track_cap = 8
probe_stride = 1
hold_back = false
EOF

cat > /app/config/l7/r8.toml <<EOF
audit_mode = "promoted"
emit_lane = "primary"
retry_ms = 100
EOF

cat > /app/data/state/runtime.json <<EOF
{
  "active_seq": ${HEAD},
  "last_replay_seq": ${HEAD},
  "movement_head": ${HEAD},
  "partial_cutoff": 0
}
EOF

python3 <<'PY'
import json
from pathlib import Path

rows = []
for path in sorted(Path("/app/data/movements").glob("tier_*.jsonl")):
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        rows.append(
            {
                "tier": rec.get("tier", path.stem.replace("tier_", "")),
                "seq": int(rec["seq"]),
                "stamp": rec.get("stamp", ""),
            }
        )
rows.sort(key=lambda r: (r["seq"], r["tier"]))
Path("/app/data/sidecars/movements.idx").write_text(
    "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows)
)
PY

python3 <<PY
import json
import subprocess
from pathlib import Path

head = int("${HEAD}")
probe = subprocess.run(
    ["python3", "/app/ops/scripts/consist_lab.py", str(head)],
    check=True,
    capture_output=True,
    text=True,
)
expected = json.loads(probe.stdout)
for track in ("T1", "T2", "T3"):
    if track not in expected["tracks"]:
        raise SystemExit(f"missing expected track {track}")
if len(expected["tracks"]["T1"]) < 3:
    raise SystemExit("promoted T1 window too short")
if "C103" in expected["tracks"].get("T2", []):
    raise SystemExit("reference probe still ghosts tank on departure spur")

runtime = json.loads(Path("/app/data/state/runtime.json").read_text())
if runtime["active_seq"] != head:
    raise SystemExit("runtime active_seq not promoted")
PY

/app/bin/yardctl report --out /output/consist-report.json

lane_seq=$(/app/bin/lane probe)
report_seq=$(python3 -c "import json; print(json.load(open('/output/consist-report.json'))['replay_seq'])")
test "${lane_seq}" -eq "${report_seq}"
test "${report_seq}" -eq "${HEAD}"

probe=$(python3 /app/ops/scripts/consist_lab.py "${HEAD}")
report_digest=$(python3 -c "import json; print(json.load(open('/output/consist-report.json'))['audit_digest'])")
expected_digest=$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['audit_digest'])" "${probe}")
test "${report_digest}" = "${expected_digest}"

python3 <<PY
import json
from pathlib import Path

head = int("${HEAD}")
report = json.loads(Path("/output/consist-report.json").read_text())
assert report["replay_seq"] == head
assert isinstance(report["audit_digest"], str) and int(report["audit_digest"], 16) >= 0
assert "T3" in report["tracks"]
print(json.dumps({"promoted_head": head, "tracks": sorted(report["tracks"])}, sort_keys=True))
PY

echo "complete" > /app/ops/staging/workflow.complete
