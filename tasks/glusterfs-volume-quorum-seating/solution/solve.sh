#!/bin/bash
# Oracle: bring the Gluster volume seating desk to the durable end-state.
set -euo pipefail

SV=/var/lib/glusterd
SD=/etc/glusterfs/glusterd.d

cat >"$SD/90-local.conf" <<'EOF'
tip_policy=durable_authority
bind_order=lexical
abort=none
EOF

mkdir -p "$SV/ops/state"
target=$(tr -d '[:space:]' <"$SV/state/gen.target")
cat >"$SV/ops/state/apply.ok" <<EOF
gen=${target}
mode=seal
EOF

sed -i 's/^plane *= *"surface"/plane = "durable"/' "$SV/ops/prefer.toml"

cat >/app/ops/reef_t.sh <<'EOS'
#!/bin/bash
set -euo pipefail
reef_t() {
  local bx="${BRICK_D:-/etc/glusterfs/bricks.d}"
  local sd="${DROPIN_D:-/etc/glusterfs/glusterd.d}"
  local sv="${GLUSTER_ROOT:-/var/lib/glusterd}"
  local plane aim rg rmode ok=0
  mkdir -p "$bx" "$sd" "$sv/ops/state"
  plane=$(sed -n 's/^plane *= *"\([a-z]*\)".*/\1/p' "$sv/ops/prefer.toml" | head -n1)
  aim=$(tr -d '[:space:]' <"$sv/state/gen.target")
  if [[ "$plane" == "durable" && -f "$sv/ops/state/apply.ok" ]]; then
    rg=$(sed -n 's/^gen=\([0-9]*\)$/\1/p' "$sv/ops/state/apply.ok" | head -n1)
    rmode=$(sed -n 's/^mode=\(.*\)$/\1/p' "$sv/ops/state/apply.ok" | head -n1)
    if [[ "$rg" == "$aim" && "$rmode" == "seal" ]]; then
      ok=1
    fi
  fi
  if [[ "$ok" -eq 1 ]]; then
    python3 - "$sv/ops/brick_journal.jsonl" "$aim" "$bx" <<'PY'
import json
import sys
from pathlib import Path

journal, aim_s, brick_d = sys.argv[1:]
aim = int(aim_s)
row = {}
for line in Path(journal).read_text().splitlines():
    line = line.strip()
    if not line:
        continue
    cand = json.loads(line)
    if (
        cand.get("kind") == "cutover"
        and int(cand.get("gen", -1)) == aim
        and cand.get("mode") == "seal"
    ):
        row = cand
target = Path(brick_d)
target.mkdir(parents=True, exist_ok=True)
for name, bricks in sorted(row.get("bricks", {}).items()):
    (target / (name + ".bricks")).write_text(
        "".join(b + "\n" for b in bricks)
    )
PY
  else
    local row a b
    while IFS= read -r row || [[ -n "${row:-}" ]]; do
      [[ -z "${row:-}" || "$row" =~ ^# ]] && continue
      a=$(sed -n 's/.*vol=\([a-z]*\).*/\1/p' <<<"$row")
      b=$(sed -n 's/.*bricks=\([^ ]*\).*/\1/p' <<<"$row")
      [[ -z "${a:-}" ]] && continue
      tr ',' '\n' <<<"$b" >"$bx/${a}.bricks"
    done <"$sv/ops/surface.bricks"
    if [[ -f "$sv/ops/abort.d/90-local.conf" ]]; then
      cp -f "$sv/ops/abort.d/90-local.conf" "$sd/90-local.conf"
    fi
    rm -f "$sv/ops/state/apply.ok"
  fi
}
reef_t
EOS

cat >/app/ops/barn_w.sh <<'EOS'
#!/bin/bash
set -euo pipefail
barn_w() {
  local sv="${GLUSTER_ROOT:-/var/lib/glusterd}"
  local rl="${ROSTER:-/etc/glusterfs/roster.list}"
  local aim
  aim=$(tr -d '[:space:]' <"$sv/state/gen.target")
  mkdir -p "$sv/state"
  python3 - "$sv/ops/brick_journal.jsonl" "$sv/state" "$aim" "$rl" "$sv/floors" <<'PY'
import json
import sys
from pathlib import Path

journal, state_s, aim_s, roster, floor_s = sys.argv[1:]
state = Path(state_s)
floor_d = Path(floor_s)
aim = int(aim_s)
row = {}
for line in Path(journal).read_text().splitlines():
    line = line.strip()
    if not line:
        continue
    cand = json.loads(line)
    if (
        cand.get("kind") == "cutover"
        and int(cand.get("gen", -1)) == aim
        and cand.get("mode") == "seal"
    ):
        row = cand
tips = {k: int(v) for k, v in row.get("tips", {}).items()}
bricks = {k: list(v) for k, v in row.get("bricks", {}).items()}
quorum = {k: int(v) for k, v in row.get("quorum", {}).items()}
names = [
    ln.strip()
    for ln in Path(roster).read_text().splitlines()
    if ln.strip() and not ln.strip().startswith("#")
]
for name in names:
    tip = int(tips.get(name, 0))
    (state / ("tip_" + name + ".gen")).write_text("%d\n" % tip)
    (state / ("pub_" + name + ".gen")).write_text("%d\n" % tip)
    blist = bricks.get(name, [])
    (state / ("tip_bricks_" + name)).write_text(
        "".join(b + "\n" for b in blist)
    )
    q = int(quorum.get(name, 0))
    (state / ("tip_quorum_" + name)).write_text("%d\n" % q)
    fp = floor_d / (name + ".floor")
    bar = int(fp.read_text().strip()) if fp.exists() else 0
    (state / ("elig_" + name)).write_text("1\n" if tip >= bar else "0\n")
    (state / ("quorum_" + name)).write_text("1\n" if tip >= bar else "0\n")
(state / "gen.live").write_text("%d\n" % aim)
PY
}
barn_w
EOS

cat >/app/rim/clay_m.sh <<'EOS'
#!/bin/bash
set -euo pipefail
clay_m() {
  local pd="${DROPIN_D:-/etc/glusterfs/glusterd.d}"
  local out="${EFF_POLICY:-/etc/glusterfs/effective.conf}"
  local f line a b
  mkdir -p "$(dirname "$out")"
  declare -A kv=()
  shopt -s nullglob
  for f in $(ls -1 "$pd"/*.conf 2>/dev/null | LC_ALL=C sort); do
    while IFS= read -r line || [[ -n "$line" ]]; do
      line="${line%%#*}"
      line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
      [[ -z "$line" ]] && continue
      [[ "$line" != *=* ]] && continue
      a="${line%%=*}"
      b="${line#*=}"
      kv["$a"]="$b"
    done <"$f"
  done
  shopt -u nullglob
  {
    for a in $(printf '%s\n' "${!kv[@]}" | LC_ALL=C sort); do
      printf '%s=%s\n' "$a" "${kv[$a]}"
    done
  } >"$out"
}
clay_m
EOS

cat >/app/bag/flint_k.sh <<'EOS'
#!/bin/bash
set -euo pipefail
flint_k() {
  local sv="${GLUSTER_ROOT:-/var/lib/glusterd}"
  local hd="$sv/holds"
  local st="$sv/state"
  local now f a b c line
  now=$(tr -d '[:space:]' <"$st/clock.epoch")
  mkdir -p "$st"
  : >"$st/holds.tsv"
  shopt -s nullglob
  for f in $(ls -1 "$hd"/*.hold 2>/dev/null | LC_ALL=C sort); do
    [[ -f "$f" ]] || continue
    a=$(basename "$f" .hold)
    b=""
    c=0
    while IFS= read -r line || [[ -n "$line" ]]; do
      line="${line%%#*}"
      line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
      [[ "$line" == brick=* ]] && b="${line#brick=}"
      [[ "$line" == until_epoch=* ]] && c="${line#until_epoch=}"
    done <"$f"
    printf '%s\t%s\t%s\n' "$a" "$b" "$c" >>"$st/holds.tsv"
    if (( c > now )); then
      printf '1\n' >"$st/hold_block_${a}"
    else
      printf '0\n' >"$st/hold_block_${a}"
    fi
  done
  shopt -u nullglob

  local rl="${ROSTER:-/etc/glusterfs/roster.list}"
  python3 - "$st" "$rl" <<'PY'
import sys
from pathlib import Path

state = Path(sys.argv[1])
roster = Path(sys.argv[2])
held = set()
tsv = state / "holds.tsv"
if tsv.exists():
    for line in tsv.read_text().splitlines():
        parts = line.split("\t")
        if len(parts) >= 3:
            hid, bpath = parts[0], parts[1]
            if (state / f"hold_block_{hid}").read_text().strip() == "1":
                held.add(bpath)
names = [
    ln.strip()
    for ln in roster.read_text().splitlines()
    if ln.strip() and not ln.strip().startswith("#")
]
for name in names:
    bricks_p = state / f"tip_bricks_{name}"
    bricks = [
        ln.strip()
        for ln in bricks_p.read_text().splitlines()
        if ln.strip()
    ] if bricks_p.exists() else []
    try:
        need = int((state / f"tip_quorum_{name}").read_text().strip())
    except Exception:
        need = 0
    free = [b for b in bricks if b not in held]
    ok = len(free) >= need and need > 0
    (state / f"quorum_{name}").write_text("1\n" if ok else "0\n")
PY
}
flint_k
EOS

cat >/app/bag/peat_x.sh <<'EOS'
#!/bin/bash
set -euo pipefail
peat_x() {
  local sv="${GLUSTER_ROOT:-/var/lib/glusterd}"
  local rl="${ROSTER:-/etc/glusterfs/roster.list}"
  local st="$sv/state"
  mkdir -p "$st"
  python3 - "$st" "$rl" <<'PY'
import sys
from pathlib import Path

state = Path(sys.argv[1])
roster = Path(sys.argv[2])
held = set()
tsv = state / "holds.tsv"
if tsv.exists():
    for line in tsv.read_text().splitlines():
        parts = line.split("\t")
        if len(parts) >= 3:
            hid, bpath = parts[0], parts[1]
            if (state / f"hold_block_{hid}").read_text().strip() == "1":
                held.add(bpath)
names = [
    ln.strip()
    for ln in roster.read_text().splitlines()
    if ln.strip() and not ln.strip().startswith("#")
]
lines = []
for name in names:
    bricks_p = state / f"tip_bricks_{name}"
    bricks = [
        ln.strip()
        for ln in bricks_p.read_text().splitlines()
        if ln.strip()
    ] if bricks_p.exists() else []
    pending = sum(1 for b in bricks if b in held)
    lines.append("%s\t%d\n" % (name, pending))
(state / "heals.tsv").write_text("".join(lines))
PY
}
peat_x
EOS

cat >/app/deck/slate_j.sh <<'EOS'
#!/bin/bash
set -euo pipefail
exec /app/bin/glusterseat
EOS

chmod 755 /app/ops/reef_t.sh /app/ops/barn_w.sh /app/rim/clay_m.sh \
  /app/bag/flint_k.sh /app/bag/peat_x.sh /app/deck/slate_j.sh

bash /app/ops/run_gluster_seat.sh
cp /output/gluster-seat.json /tmp/pass1.json
bash /app/ops/run_gluster_seat.sh

if ! cmp -s /tmp/pass1.json /output/gluster-seat.json; then
  echo "oracle: passes differ" >&2
  exit 1
fi
if ! grep -q '"seat_ok": true' /output/gluster-seat.json; then
  echo "oracle: desk did not settle" >&2
  exit 1
fi
if ! grep -q '^gen=' "$SV/ops/state/apply.ok"; then
  echo "oracle: receipt missing" >&2
  exit 1
fi
rm -f /tmp/pass1.json
echo "oracle: desk seated"
