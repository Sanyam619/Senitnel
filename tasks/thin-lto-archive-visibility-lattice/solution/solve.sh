#!/bin/bash
set -euo pipefail

cd /app

HOLD_TOKEN="$(python3 - <<'PY'
import json
token = ""
with open("/app/data/fixtures/desk_journal.jsonl") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        if row.get("event") == "hold":
            token = str(row.get("token", ""))
print(token)
PY
)"
test -n "$HOLD_TOKEN"

FLOOR="$(python3 - <<'PY'
import re
text = open("/app/ops/nx/cut_n.toml").read()
m = re.search(r"epoch_floor\s*=\s*(\d+)", text)
print(m.group(1) if m else "3")
PY
)"

mkdir -p /app/ops/nx

cat > /app/ops/nx/cut_n.toml <<EOF
soname_hint = "libr7.so"
cutover = "sealed"
epoch = ${FLOOR}
epoch_floor = ${FLOOR}
hold_token = "${HOLD_TOKEN}"
roster = "ship,fleet,craft,field"
desk_lane = "nx"
promote = "live"
EOF

cat > /app/ops/nx/fold_p.toml <<'EOF'
overlay = "live"
EOF

cat > /app/ops/nx/draft_q.toml <<'EOF'
[alias]
fleet = "fleet"

[meta]
overlay_target = "lane.d"
sheet = "50-draft"
EOF

cat > /app/ops/nx/strand_q.toml <<'EOF'
name = "craft"
bitcode_epoch = 5
archive_members = 5
notes = "craft lane live"
lane = "craft"
source = "matrix"
epoch_kind = "bitcode"
EOF

cat > /app/ops/nx/width_q.toml <<'EOF'
name = "fleet"
bitcode_epoch = 7
archive_members = 6
notes = "fleet lane live"
lane = "fleet"
source = "matrix"
width_kind = "archive_members"
EOF

cat > /app/ops/nx/pref_a.toml <<'EOF'
prefer = "profile"
mode = "live"
owner = "matrix"
EOF

cat > /app/ops/nx/rel_mask.toml <<'EOF'
strip_b_on_release = false
EOF

python3 - <<'PY'
import json
import re
from pathlib import Path

cut = Path("/app/ops/nx/cut_n.toml").read_text()
assert 'cutover = "sealed"' in cut
assert re.search(r"hold_token\s*=\s*\"q7m3\"", cut), cut
assert Path("/app/ops/nx/pref_a.toml").read_text().strip().startswith('prefer = "profile"')
assert 'overlay = "live"' in Path("/app/ops/nx/fold_p.toml").read_text()
assert "strip_b_on_release = false" in Path("/app/ops/nx/rel_mask.toml").read_text()
PY

cd /app/g5
go build -o /app/bin/archctl .

cmake -S /app/vis -B /tmp/visbuild_fix
cmake --build /tmp/visbuild_fix
cp /tmp/visbuild_fix/visgen /app/bin/visgen
chmod 0755 /app/bin/archctl /app/bin/visgen

test "$(/app/bin/archctl resolve fleet)" = "/app/config/profiles/fleet.toml"
test "$(/app/bin/archctl members 1 1 6)" = "6"
test "$(/app/bin/archctl digest 1 1 7 6)" = "43497"

rm -f /output/lattice-report.json
/app/bin/lattice_probe >/tmp/lattice_oracle_probe.log 2>&1
test -s /output/lattice-report.json

python3 - <<'PY'
import json
from pathlib import Path

report = json.loads(Path("/output/lattice-report.json").read_text())
for key in ("alpha", "beta", "gamma", "epsilon"):
    cell = report["cells"][key]
    assert cell.get("status") == "ok", cell
fleet = Path("/app/config/profiles/fleet.toml").read_text()
assert "bitcode_epoch = 7" in fleet
craft = Path("/app/config/profiles/craft.toml").read_text()
assert "bitcode_epoch = 5" in craft
PY

echo "oracle: sealed nx cutover, promote sheets, prefer profile, live fold"
