#!/bin/bash
set -euo pipefail

# Rewrite live drop-in to site-standard tokens (abort package stays forensic).
cat >/etc/auto.master.d/90-local.conf <<'EOF'
tip_policy=equality_inclusive
bind_order=lexical
abort=none
EOF

# Durable cutover receipt matching gen.target.
target=$(tr -d '[:space:]' </var/lib/autofs/state/gen.target)
cat >/var/lib/autofs/state/cutover.ok <<EOF
gen=${target}
mode=seal
EOF

cat >/app/rim/mesh_x.sh <<'EOF'
#!/bin/bash
set -euo pipefail

PREF_D="/etc/auto.master.d"
OUT="/etc/autofs/effective.conf"

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
EOF
chmod +x /app/rim/mesh_x.sh

cat >/app/ops/axle_y.sh <<'EOF'
#!/bin/bash
set -euo pipefail

ROOT="/var/lib/autofs"
FLOOR_D="$ROOT/floors"
ROSTER="/etc/autofs/roster.list"
STATE="$ROOT/state"
JOURNAL="$ROOT/ops/journal.jsonl"
TARGET=$(tr -d '[:space:]' <"$STATE/gen.target")

mkdir -p "$STATE"

python3 - "$JOURNAL" "$STATE" "$TARGET" "$ROSTER" "$FLOOR_D" <<'PY'
import json
import sys
from pathlib import Path

journal, state, target_s, roster, floor_d = sys.argv[1:]
state = Path(state)
floor_d = Path(floor_d)
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
    elig = 1 if tip >= floor else 0
    (state / f"elig_{name}").write_text(f"{elig}\n")

(state / "gen.live").write_text(f"{target}\n")
PY
EOF
chmod +x /app/ops/axle_y.sh

cat >/app/bag/skim_z.sh <<'EOF'
#!/bin/bash
set -euo pipefail

ROOT="/var/lib/autofs"
HOLD_D="$ROOT/holds"
STATE="$ROOT/state"
CLOCK=$(tr -d '[:space:]' <"$STATE/clock.epoch")

mkdir -p "$STATE"
: >"$STATE/holds.tsv"

shopt -s nullglob
for f in $(ls -1 "$HOLD_D"/*.hold 2>/dev/null | sort); do
  [[ -f "$f" ]] || continue
  key=$(basename "$f" .hold)
  until_epoch=0
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%%#*}"
    line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ "$line" == until_epoch=* ]] && until_epoch="${line#until_epoch=}"
  done <"$f"
  printf '%s\t%s\n' "$key" "$until_epoch" >>"$STATE/holds.tsv"
  if (( until_epoch > CLOCK )); then
    printf '0\n' >"$STATE/hold_block_${key}"
  else
    printf '1\n' >"$STATE/hold_block_${key}"
  fi
done
shopt -u nullglob
EOF
chmod +x /app/bag/skim_z.sh

cat >/app/ops/helm_w.sh <<'EOF'
#!/bin/bash
set -euo pipefail

ABORT_D="/var/lib/autofs/ops/abort.d"
LIVE_D="/etc/auto.master.d"
STATE="/var/lib/autofs/state"
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
EOF
chmod +x /app/ops/helm_w.sh

cat >/app/deck/emit_q.sh <<'EOF'
#!/bin/bash
set -euo pipefail
exec /app/bin/seatctl
EOF
chmod +x /app/deck/emit_q.sh

/app/ops/run_autofs_seat.sh
/app/ops/run_autofs_seat.sh
