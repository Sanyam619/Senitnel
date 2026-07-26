#!/bin/bash
set -euo pipefail

cd /app

# Fix abort-window local drop-in so lexical fold matches site standard.
cat >/etc/fleet/reconcile.d/90-local.conf <<'EOF'
# Local operator override — aligned with site standard after cutover.
precedence_mode=seal_first
borrow_gate=live_and_clear
fragment_order=seal_ordinal
EOF
# Keep packaging seed in sync for operators who re-copy from /app/config.
cp -f /etc/fleet/reconcile.d/90-local.conf /app/config/reconcile.d/90-local.conf

cat >/app/ops/axle_p.sh <<'EOF'
#!/bin/bash
# axle_p.sh
set -euo pipefail

mkdir -p /var/lib/fleet/state /var/lib/fleet/ops
JOURNAL="${FLEET_JOURNAL:-/var/lib/fleet/ops/journal.jsonl}"
target=$(cat /var/lib/fleet/state/gen.target)

python3 - "$JOURNAL" "$target" <<'PY'
import json, sys
from pathlib import Path
journal, target = Path(sys.argv[1]), int(sys.argv[2])
rows = []
for line in journal.read_text().splitlines():
    line = line.strip()
    if not line:
        continue
    rows.append(json.loads(line))
# Sealed cutover for target gen is authoritative over rollback rows.
chosen = None
for r in rows:
    if r.get("tag") == "cutover" and r.get("mode") == "seal" and int(r.get("gen", -1)) == target:
        chosen = r
if chosen is None:
    raise SystemExit("axle_p: missing sealed cutover for target gen")
hold = chosen["hold"]
Path("/var/lib/fleet/state/gen.live").write_text(f"{target}\n")
# attach.intent carries the raw journal mode token.
Path("/var/lib/fleet/state/attach.intent").write_text("seal\n")
Path("/var/lib/fleet/state/hold.token").write_text(hold + "\n")
# Durable receipt suppresses abort rematerialize on fold_d.
Path("/var/lib/fleet/state/cutover.ok").write_text(
    f"gen={target}\nhold={hold}\nmode=seal\n"
)
env = Path("/etc/fleet/fleetd.env")
text = env.read_text() if env.is_file() else ""
lines = [
    ln
    for ln in text.splitlines()
    if not ln.startswith("HOLD_TOKEN=") and not ln.startswith("PAYLOAD_LINEAGE=")
]
# PAYLOAD_LINEAGE names the volume directory, not the journal mode token.
lines.append("PAYLOAD_LINEAGE=sealed")
lines.append(f"HOLD_TOKEN={hold}")
env.write_text("\n".join(lines) + "\n")
PY
EOF
chmod +x /app/ops/axle_p.sh

cat >/app/ops/fold_d.sh <<'EOF'
#!/bin/bash
# fold_d.sh
set -euo pipefail

mkdir -p /etc/fleet/reconcile.d /var/lib/fleet/ops/abort.d /var/lib/fleet/state
abort_pkg="/var/lib/fleet/ops/abort.d/90-local.conf"
live_dropin="/etc/fleet/reconcile.d/90-local.conf"
cutover_receipt="/var/lib/fleet/state/cutover.ok"
target_gen=$(cat /var/lib/fleet/state/gen.target)
hold_now=$(cat /var/lib/fleet/state/hold.token 2>/dev/null || true)

need_abort=1
if [[ -f "$cutover_receipt" ]]; then
  gen_ok=$(grep -E '^gen=' "$cutover_receipt" | head -n1 | cut -d= -f2- || true)
  hold_ok=$(grep -E '^hold=' "$cutover_receipt" | head -n1 | cut -d= -f2- || true)
  mode_ok=$(grep -E '^mode=' "$cutover_receipt" | head -n1 | cut -d= -f2- || true)
  if [[ "$gen_ok" == "$target_gen" && "$hold_ok" == "$hold_now" && "$mode_ok" == "seal" ]]; then
    need_abort=0
  fi
fi

if [[ "$need_abort" -eq 1 ]]; then
  if [[ -f "$abort_pkg" ]]; then
    cp -f "$abort_pkg" "$live_dropin"
  fi
  rm -f "$cutover_receipt"
fi
EOF
chmod +x /app/ops/fold_d.sh

cat >/app/ops/weave_k.sh <<'EOF'
#!/bin/bash
# weave_k.sh
set -euo pipefail

mkdir -p /etc/fleet/reconcile.d
# Fold live drop-ins in lexical order into effective reconcile.conf.
: >/etc/fleet/reconcile.conf
shopt -s nullglob
for f in /etc/fleet/reconcile.d/*.conf; do
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%%#*}"
    line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "$line" ]] && continue
    [[ "$line" != *=* ]] && continue
    key="${line%%=*}"
    val="${line#*=}"
    if grep -q "^${key}=" /etc/fleet/reconcile.conf 2>/dev/null; then
      grep -v "^${key}=" /etc/fleet/reconcile.conf > /tmp/reconcile.fold || true
      mv /tmp/reconcile.fold /etc/fleet/reconcile.conf
    fi
    echo "${key}=${val}" >> /etc/fleet/reconcile.conf
  done <"$f"
done
shopt -u nullglob

if ! grep -q '^precedence_mode=seal_first$' /etc/fleet/reconcile.conf; then
  echo "weave_k: effective precedence mismatch" >&2
  exit 1
fi
if grep -qE 'prefer_seal|live_or_clear|byte_offset' /etc/fleet/reconcile.conf; then
  echo "weave_k: synonym tokens present after fold" >&2
  exit 1
fi

# Preserve axle-armed HOLD_TOKEN / PAYLOAD_LINEAGE if present.
if [[ -f /etc/fleet/fleetd.env ]]; then
  hold=$(grep -E '^HOLD_TOKEN=' /etc/fleet/fleetd.env | head -n1 | cut -d= -f2- || true)
  lineage=$(grep -E '^PAYLOAD_LINEAGE=' /etc/fleet/fleetd.env | head -n1 | cut -d= -f2- || true)
else
  hold=""
  lineage=""
fi
[[ -z "$lineage" ]] && lineage=sealed
[[ -z "$hold" ]] && hold=$(cat /var/lib/fleet/state/hold.token 2>/dev/null || echo ridge-k4)

cat >/etc/fleet/fleetd.env <<ENV
PAYLOAD_LINEAGE=${lineage}
HOLD_TOKEN=${hold}
FLEET_VOLUME_ROOT=/var/lib/fleet/volumes
FLEET_RUNTIME_ROOT=/var/lib/fleet/runtime
ENV

{
  echo "# armed"
  grep -E '^(precedence_mode|borrow_gate|fragment_order)=' /etc/fleet/reconcile.conf
} >/etc/fleet/reconcile.armed
EOF
chmod +x /app/ops/weave_k.sh

cat >/app/bag/pull_m.sh <<'EOF'
#!/bin/bash
# pull_m.sh
set -euo pipefail

mkdir -p /var/lib/fleet/leases
target=$(cat /var/lib/fleet/state/gen.target)
live=$(cat /var/lib/fleet/state/gen.live)
if [[ "$live" != "$target" ]]; then
  echo "pull_m: generation not aligned ($live != $target)" >&2
  exit 1
fi

for ep in alpha beta gamma delta epsilon; do
  src="/app/data/episodes/${ep}/leases.json"
  if [[ ! -f "$src" ]]; then
    echo "pull_m: missing $ep" >&2
    exit 1
  fi
  cp -f "$src" "/var/lib/fleet/leases/${ep}.json"
  if ! grep -q '"claims"' "/var/lib/fleet/leases/${ep}.json"; then
    echo "pull_m: empty claims $ep" >&2
    exit 1
  fi
done
EOF
chmod +x /app/bag/pull_m.sh

cat >/app/rim/mark_t.sh <<'EOF'
#!/bin/bash
# mark_t.sh
set -euo pipefail

mkdir -p /var/run/fleet/gate
target=$(cat /var/lib/fleet/state/gen.target)
live=$(cat /var/lib/fleet/state/gen.live)
if [[ "$live" != "$target" ]]; then
  echo "mark_t: generation not aligned ($live != $target)" >&2
  exit 1
fi

rm -rf /var/run/fleet/gate/*
for ep in alpha beta gamma delta epsilon; do
  mkdir -p "/var/run/fleet/gate/${ep}"
  qfile="/app/data/episodes/${ep}/quarantine.json"
  [[ -f "$qfile" ]] || continue
  python3 - "$qfile" "/var/run/fleet/gate/${ep}" <<'PY'
import json, sys
from pathlib import Path
qpath, gdir = Path(sys.argv[1]), Path(sys.argv[2])
gdir.mkdir(parents=True, exist_ok=True)
peers = json.loads(qpath.read_text()).get("peers", {})
for peer, flagged in peers.items():
    if flagged:
        (gdir / peer).write_text("")
PY
done
if [[ ! -f /var/run/fleet/gate/epsilon/ridge ]]; then
  echo "mark_t: missing epsilon/ridge" >&2
  exit 1
fi
if [[ -f /var/run/fleet/gate/epsilon/cinder ]]; then
  echo "mark_t: unexpected epsilon/cinder" >&2
  exit 1
fi
if [[ -f /var/run/fleet/gate/beta/ridge ]]; then
  echo "mark_t: unexpected beta/ridge" >&2
  exit 1
fi
EOF
chmod +x /app/rim/mark_t.sh

cat >/app/deck/bind_v.sh <<'EOF'
#!/bin/bash
# bind_v.sh
set -euo pipefail

# shellcheck disable=SC1091
if [[ -f /etc/fleet/fleetd.env ]]; then
  set -a
  # shellcheck disable=SC1090
  source /etc/fleet/fleetd.env
  set +a
fi

vol_root="${FLEET_VOLUME_ROOT:-/var/lib/fleet/volumes}"
rt_root="${FLEET_RUNTIME_ROOT:-/var/lib/fleet/runtime}"
hold=$(cat /var/lib/fleet/state/hold.token 2>/dev/null || echo "${HOLD_TOKEN:-}")
intent=$(cat /var/lib/fleet/state/attach.intent 2>/dev/null || echo seal)
lineage="${PAYLOAD_LINEAGE:-}"
if [[ "$intent" != "seal" ]]; then
  echo "bind_v: attach intent is not seal" >&2
  exit 1
fi
if [[ "$lineage" != "sealed" ]]; then
  echo "bind_v: PAYLOAD_LINEAGE must be volume dir sealed (not journal mode seal)" >&2
  exit 1
fi
if [[ -z "$hold" ]]; then
  echo "bind_v: missing hold token" >&2
  exit 1
fi

for ep in alpha beta gamma delta epsilon; do
  src="$vol_root/$ep/sealed/payload.bin"
  dst_dir="$rt_root/$ep"
  dst="$dst_dir/payload.bin"
  if [[ ! -f "$src" ]]; then
    echo "bind_v: missing sealed payload for $ep" >&2
    exit 1
  fi
  mkdir -p "$dst_dir"
  rm -f "$dst"
  ln -f "$src" "$dst"
  src_ino=$(stat -c '%i' "$src")
  dst_ino=$(stat -c '%i' "$dst")
  if [[ "$src_ino" != "$dst_ino" ]]; then
    echo "bind_v: inode mismatch for $ep" >&2
    exit 1
  fi
  decoy="$vol_root/$ep/decoy/payload.bin"
  if [[ -f "$decoy" && "$(stat -c '%i' "$decoy")" == "$dst_ino" ]]; then
    echo "bind_v: decoy attached for $ep" >&2
    exit 1
  fi
  printf '%s\n' "$hold" >"$dst_dir/.hold"
done
EOF
chmod +x /app/deck/bind_v.sh

for b in fleetctl yarder fleetpeek; do
  if [[ ! -x "/app/bin/$b" && -x "/usr/lib/fleet/bin/$b" ]]; then
    cp -f "/usr/lib/fleet/bin/$b" "/app/bin/$b"
    chmod +x "/app/bin/$b"
  fi
done

bash /app/ops/fleethealth >/dev/null || true
bash /app/ops/run_recovery.sh

for ep in alpha beta gamma delta epsilon; do
  dst="/var/lib/fleet/runtime/$ep/payload.bin"
  src="/var/lib/fleet/volumes/$ep/sealed/payload.bin"
  if [[ "$(stat -c '%i' "$dst")" != "$(stat -c '%i' "$src")" ]]; then
    echo "oracle: sealed volume not attached for $ep" >&2
    exit 1
  fi
  test "$(cat /var/lib/fleet/runtime/$ep/.hold)" = "ridge-k4"
done

test "$(cat /var/lib/fleet/state/gen.live)" = "7"
test "$(cat /var/lib/fleet/state/attach.intent)" = "seal"
test -f /var/lib/fleet/state/cutover.ok
grep -q '^gen=7$' /var/lib/fleet/state/cutover.ok
grep -q '^hold=ridge-k4$' /var/lib/fleet/state/cutover.ok
grep -q '^mode=seal$' /var/lib/fleet/state/cutover.ok
test -f /output/reconciliation.json
test -f /output/meta/run.stamp
grep -q seal_first /output/meta/run.stamp
grep -q live_and_clear /output/meta/run.stamp
grep -q seal_ordinal /output/meta/run.stamp

grep -q '^precedence_mode=seal_first$' /etc/fleet/reconcile.conf
grep -q '^borrow_gate=live_and_clear$' /etc/fleet/reconcile.conf
grep -q '^fragment_order=seal_ordinal$' /etc/fleet/reconcile.conf
grep -q '^PAYLOAD_LINEAGE=sealed$' /etc/fleet/fleetd.env
grep -q '^HOLD_TOKEN=ridge-k4$' /etc/fleet/fleetd.env
# Abort residue must not have overwritten the live drop-in after receipt.
grep -q '^precedence_mode=seal_first$' /etc/fleet/reconcile.d/90-local.conf
! grep -q prefer_seal /etc/fleet/reconcile.d/90-local.conf
# Abort package itself stays on abort-window synonyms.
grep -q '^precedence_mode=prefer_seal$' /var/lib/fleet/ops/abort.d/90-local.conf
grep -q '^borrow_gate=live_or_clear$' /var/lib/fleet/ops/abort.d/90-local.conf
grep -q '^fragment_order=byte_offset$' /var/lib/fleet/ops/abort.d/90-local.conf
test -f /var/run/fleet/gate/epsilon/ridge
test ! -f /var/run/fleet/gate/epsilon/cinder
test ! -f /var/run/fleet/gate/beta/ridge

echo "oracle: fleet admin reconcile complete"
