#!/bin/bash
set -euo pipefail

# Rewrite live drop-in to site-standard tokens (abort package stays forensic).
cat >/etc/pacemaker/cib.d/90-local.conf <<'EOF'
default_stickiness=200
bind_order=lexical
location_policy=site_standard
EOF

# Durable cutover receipt matching gen.target.
target=$(tr -d '[:space:]' </var/lib/cluster/ops/state/gen.target)
cat >/var/lib/cluster/ops/state/cutover.ok <<EOF
gen=${target}
mode=seal
EOF

cat >/app/rim/mesh_k.sh <<'EOF'
#!/bin/bash
mesh_k() {
  set -euo pipefail

  PREF_D="${PREF_D:-/etc/pacemaker/cib.d}"
  OUT="${EFF_POLICY:-/etc/pacemaker/effective.conf}"

  mkdir -p "$(dirname "$OUT")"
  declare -A kv=()
  shopt -s nullglob
  for f in $(ls -1 "$PREF_D"/*.conf 2>/dev/null | sort); do
    while IFS= read -r line || [[ -n "$line" ]]; do
      line="${line%%#*}"
      line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
      [[ -z "$line" ]] && continue
      [[ "$line" != *=* ]] && continue
      k="${line%%=*}"
      v="${line#*=}"
      kv["$k"]="$v"
    done <"$f"
  done
  shopt -u nullglob

  {
    for k in $(printf '%s\n' "${!kv[@]}" | sort); do
      printf '%s=%s\n' "$k" "${kv[$k]}"
    done
  } >"$OUT"
}
mesh_k
EOF
chmod +x /app/rim/mesh_k.sh

cat >/app/ops/axle_n.sh <<'EOF'
#!/bin/bash
axle_n() {
  set -euo pipefail

  ROOT="${PCM_ROOT:-/var/lib/pacemaker}"
  FLOOR_D="$ROOT/floors"
  ROSTER="${NODE_ROSTER:-/var/lib/pacemaker/nodes.roster}"
  STATE="$ROOT/state"
  OPS="${CLUSTER_OPS:-/var/lib/cluster/ops}"
  JOURNAL="$OPS/prefer_journal.jsonl"
  TARGET=$(tr -d '[:space:]' <"$OPS/state/gen.target")

  mkdir -p "$STATE" "$OPS/state"

  python3 - "$JOURNAL" "$STATE" "$TARGET" "$ROSTER" "$FLOOR_D" "$OPS/state" <<'PY'
import json
import sys
from pathlib import Path

journal, state, target_s, roster, floor_d, ops_state = sys.argv[1:]
state = Path(state)
floor_d = Path(floor_d)
ops_state = Path(ops_state)
target = int(target_s)

tips = {}
sealed = None
for line in Path(journal).read_text().splitlines():
    line = line.strip()
    if not line:
        continue
    row = json.loads(line)
    if row.get("kind") == "cutover" and int(row.get("gen", -1)) == target and row.get("mode") == "seal":
        sealed = row
if sealed and isinstance(sealed.get("tips"), dict):
    tips = {k: int(v) for k, v in sealed["tips"].items()}

names = [
    ln.strip()
    for ln in Path(roster).read_text().splitlines()
    if ln.strip() and not ln.strip().startswith("#")
]
for name in names:
    tip = int(tips.get(name, 0))
    (state / f"tip_{name}.gen").write_text(f"{tip}\n")
    (state / f"pub_{name}.gen").write_text(f"{tip}\n")
    floor_p = floor_d / f"{name}.floor"
    floor = int(floor_p.read_text().strip()) if floor_p.exists() else 0
    online = 1 if tip >= floor else 0
    (state / f"online_{name}").write_text(f"{online}\n")

(ops_state / "gen.live").write_text(f"{target}\n")
PY
}
axle_n
EOF
chmod +x /app/ops/axle_n.sh

cat >/app/bag/skim_p.sh <<'EOF'
#!/bin/bash
skim_p() {
  set -euo pipefail

  ROOT="${CLUSTER_OPS:-/var/lib/cluster/ops}"
  STATE="${PCM_ROOT:-/var/lib/pacemaker}/state"
  JOURNAL="$ROOT/fence_journal.jsonl"

  mkdir -p "$STATE"

  python3 - "$JOURNAL" "$STATE" <<'PY'
import json
import sys
from pathlib import Path

journal, state = map(Path, sys.argv[1:])
# last status per target by epoch order
latest = {}
for line in journal.read_text().splitlines():
    line = line.strip()
    if not line:
        continue
    row = json.loads(line)
    t = row.get("target")
    if not t:
        continue
    ep = int(row.get("epoch", 0))
    st = row.get("status", "")
    prev = latest.get(t)
    if prev is None or ep >= prev[0]:
        latest[t] = (ep, st)

lines = []
for t, (ep, st) in sorted(latest.items()):
    clear_p = state / f"fence_clear_{t}"
    if st == "fenced":
        clear_p.write_text("0\n")
        lines.append(f"{t}\t{ep}")
    else:
        clear_p.write_text("1\n")
(state / "fences.tsv").write_text("\n".join(lines) + ("\n" if lines else ""))
PY
}
skim_p
EOF
chmod +x /app/bag/skim_p.sh

cat >/app/ops/helm_r.sh <<'EOF'
#!/bin/bash
helm_r() {
  set -euo pipefail

  ABORT_D="${ABORT_D:-/var/lib/cluster/ops/abort.d}"
  LIVE_D="${LIVE_D:-/etc/pacemaker/cib.d}"
  STATE="/var/lib/cluster/ops/state"
  RECEIPT="$STATE/cutover.ok"
  TARGET=$(tr -d '[:space:]' <"$STATE/gen.target")

  mkdir -p "$LIVE_D" "$STATE"

  skip=0
  if [[ -f "$RECEIPT" ]]; then
    got_gen=""
    got_mode=""
    while IFS= read -r line || [[ -n "$line" ]]; do
      line="${line%%#*}"
      line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
      [[ -z "$line" ]] && continue
      case "$line" in
        gen=*) got_gen="${line#gen=}" ;;
        mode=*) got_mode="${line#mode=}" ;;
      esac
    done <"$RECEIPT"
    if [[ "$got_gen" == "$TARGET" && "$got_mode" == "seal" ]]; then
      skip=1
    fi
  fi

  if [[ "$skip" -eq 0 ]]; then
    if [[ -f "$ABORT_D/90-local.conf" ]]; then
      cp -f "$ABORT_D/90-local.conf" "$LIVE_D/90-local.conf"
    fi
  fi
}
helm_r
EOF
chmod +x /app/ops/helm_r.sh

cat >/app/deck/emit_v.sh <<'EOF'
#!/bin/bash
emit_v() {
  set -euo pipefail
  exec /app/bin/seatctl
}
emit_v
EOF
chmod +x /app/deck/emit_v.sh

/app/ops/run_crm_seat.sh
/app/ops/run_crm_seat.sh
