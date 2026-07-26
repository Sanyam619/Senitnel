#!/bin/bash
set -euo pipefail

cd /app

# Resolve hold token from the desk journal (latest event=hold).
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

# Compound cutover gate: sealed + epoch at/above floor + journal hold token.
cat > /app/ops/nx/cut_n.toml <<EOF
soname_hint = "libr8.so"
cutover = "sealed"
epoch = ${FLOOR}
epoch_floor = ${FLOOR}
hold_token = "${HOLD_TOKEN}"
roster = "ship,fleet,field"
EOF

# Drop-in fold: live overlay uses non-draft sheets only.
cat > /app/ops/nx/fold_p.toml <<'EOF'
overlay = "live"
EOF

# Promote sheets applied when gate passes (live surfaces stay seed-wrong until then).
cat > /app/ops/nx/draft_q.toml <<'EOF'
[alias]
fleet = "fleet"
EOF

cat > /app/ops/nx/strand_q.toml <<'EOF'
[enable]
facet_x = true
facet_y = true

[notes]
strand = "strand_m"
source = "matrix"
EOF

cat > /app/ops/nx/width_q.toml <<'EOF'
name = "fleet"
pack_width = 4
notes = "fleet lane defaults"
EOF

# Packing prefer profile once gate is sealed.
cat > /app/ops/nx/pref_a.toml <<'EOF'
prefer = "profile"
mode = "live"
owner = "matrix"
EOF

# Hook mode probe: cmake honors -DPACK_WIDTH.
cat > /app/ops/nx/hook_q.toml <<'EOF'
mode = "probe"
EOF

# Release cells must keep declared facet_y.
cat > /app/ops/nx/rel_mask.toml <<'EOF'
strip_y_on_release = false
EOF

# Rebuild durable helpers under /app/bin (wire + fold + gate readers).
cd /app/g4
go build -o /app/bin/slotctl .

cmake -S /app/gen -B /tmp/genbuild_fix
cmake --build /tmp/genbuild_fix
cp /tmp/genbuild_fix/hdrgen /app/bin/hdrgen
chmod 0755 /app/bin/slotctl /app/bin/hdrgen

# Smoke: promote-on-resolve; wire retains facets with and without --release.
/app/bin/slotctl wire "facet_x,facet_y" | grep -q '^1 1$'
/app/bin/slotctl wire "facet_x,facet_y" --release | grep -q '^1 1$'
test "$(/app/bin/slotctl resolve fleet)" = "/app/config/profiles/fleet.toml"
grep -q 'cutover = "sealed"' /app/ops/nx/cut_n.toml
grep -q "hold_token = \"${HOLD_TOKEN}\"" /app/ops/nx/cut_n.toml
grep -q 'prefer = "profile"' /app/ops/nx/pref_a.toml
grep -q 'mode = "probe"' /app/ops/nx/hook_q.toml
grep -q 'pack_width = 4' /app/config/profiles/fleet.toml
grep -q 'facet_y = true' /app/config/strand_m.toml
grep -q 'overlay = "live"' /app/ops/nx/fold_p.toml
grep -q 'strip_y_on_release = false' /app/ops/nx/rel_mask.toml

# Cargo knit_w must observe sealed gate without rematerializing live surfaces.
FACET_X=1 FACET_Y=1 PACK_WIDTH=8 cargo build -p r8 --locked >/tmp/r8_oracle_build.log 2>&1 || {
  cat /tmp/r8_oracle_build.log
  exit 1
}
grep -q 'prefer = "profile"' /app/ops/nx/pref_a.toml
grep -q 'pack_width = 4' /app/config/profiles/fleet.toml
grep -q 'facet_y = true' /app/config/strand_m.toml
grep -q 'mode = "probe"' /app/ops/nx/hook_q.toml

echo "oracle: sealed cutover gate, nx promote sheets, live fold, prefer+hook+mask"
