#!/bin/bash
set -euo pipefail

cat >/app/wire/knit_p.sh <<'EOF'
#!/bin/bash
set -euo pipefail

ROOT="${BTRFS_ROOT:-/var/lib/btrfs}"
SEAL="${BTRFS_SEAL:-/etc/btrfs/pool.seal}"
ROSTER="${LANE_ROSTER:-/etc/btrfs/lane.roster}"
WAL="$ROOT/journal/send.wal"
RUNTIME="$ROOT/meta/runtime.tsv"
CRASH="$ROOT/meta/parents.crash.toml"
PARENTS="$ROOT/meta/parents.toml"

mkdir -p "$ROOT/meta"

if [[ -f "$CRASH" ]]; then
  cp -f "$CRASH" "$PARENTS"
fi

python3 - "$WAL" "$RUNTIME" "$PARENTS" "$SEAL" "$ROSTER" <<'PY'
import sys
from pathlib import Path

wal, runtime, parents, seal_path, roster_path = map(Path, sys.argv[1:])
cap = 0
for line in seal_path.read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#"):
        cap = int(line)
        break
allow = set()
for line in roster_path.read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#"):
        allow.add(line)

latest = {}
order = []
for line in wal.read_text().splitlines():
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    parts = line.split("|")
    if len(parts) < 8:
        continue
    gen = int(parts[0])
    if gen > cap:
        continue
    lane = parts[2]
    if lane not in allow:
        continue
    if lane not in latest:
        order.append(lane)
    latest[lane] = parts

lines = []
pmap = ["# tip map", "[parents]"]
for i, lane in enumerate(order, 1):
    p = latest[lane]
    lines.append(f"{i}\t{p[2]}\t{p[3]}\t{p[4]}\t{p[5]}\t{p[6]}\t{p[7]}")
    pmap.append(f'{lane} = "{p[3]}"')
runtime.write_text("\n".join(lines) + "\n")
parents.write_text("\n".join(pmap) + "\n")
PY
EOF
chmod +x /app/wire/knit_p.sh

cat >/app/rim/fold_q.sh <<'EOF'
#!/bin/bash
set -euo pipefail

ROOT="${BTRFS_ROOT:-/var/lib/btrfs}"
PREF_D="${BTRFS_PREF_D:-/etc/btrfs/pref.d}"
ARMED="$ROOT/meta/pref.armed"

mkdir -p "$ROOT/meta"

mode="strict-gt"
shopt -s nullglob
for f in $(ls -1 "$PREF_D"/*.conf 2>/dev/null | sort); do
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%%#*}"
    line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "$line" ]] && continue
    if [[ "$line" == mode=* ]]; then
      mode="${line#mode=}"
    fi
  done <"$f"
done
shopt -u nullglob

if [[ "$mode" != "equality-inclusive" ]]; then
  echo "fold_q: mode=$mode" >&2
  exit 1
fi
printf '%s\n' "$mode" >"$ARMED"
EOF
chmod +x /app/rim/fold_q.sh

cat >/app/ops/axle_j.sh <<'EOF'
#!/bin/bash
set -euo pipefail

ROOT="${BTRFS_ROOT:-/var/lib/btrfs}"
JOURNAL="${BTRFS_JOURNAL:-$ROOT/ops/journal.jsonl}"
STATE="$ROOT/meta"
ENV_FILE="${BTRFS_DESKD_ENV:-/etc/btrfs/deskd.env}"
TARGET=$(cat "$STATE/gen.target")

mkdir -p "$STATE" "$(dirname "$ENV_FILE")"

python3 - "$JOURNAL" "$TARGET" "$STATE" "$ENV_FILE" "$ROOT" <<'PY'
import json, sys
from pathlib import Path

journal, target, state, env_file, root = Path(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]), Path(sys.argv[5])
rows = []
for line in journal.read_text().splitlines():
    line = line.strip()
    if not line:
        continue
    rows.append(json.loads(line))
chosen = None
for r in rows:
    if r.get("tag") == "cutover" and r.get("mode") == "seal" and int(r.get("gen", -1)) == target:
        chosen = r
if chosen is None:
    raise SystemExit("axle_j: missing sealed cutover for target gen")
(state / "gen.live").write_text(f"{target}\n")
(state / "attach.intent").write_text("seal\n")
(state / "hold.token").write_text(chosen["hold"] + "\n")
env_file.write_text(
    "# deskd runtime environment\n"
    "PAYLOAD_LINEAGE=sealed\n"
    f"HOLD_TOKEN={chosen['hold']}\n"
    f"BTRFS_VOLUME_ROOT={root}/volumes\n"
    f"BTRFS_ATTACH_ROOT={root}/attach\n"
)
PY
EOF
chmod +x /app/ops/axle_j.sh

cat >/app/bag/slot_w.sh <<'EOF'
#!/bin/bash
set -euo pipefail

ROOT="${BTRFS_ROOT:-/var/lib/btrfs}"
SEAL="${BTRFS_SEAL:-/etc/btrfs/pool.seal}"
ARM="$ROOT/meta/seal_gen.arm"

mkdir -p "$ROOT/meta"
cap="0"
while IFS= read -r line || [[ -n "$line" ]]; do
  line="${line%%#*}"
  line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  [[ -z "$line" ]] && continue
  cap="$line"
  break
done <"$SEAL"
printf '%s\n' "$cap" >"$ARM"
EOF
chmod +x /app/bag/slot_w.sh

cat >/app/deck/hold_c.sh <<'EOF'
#!/bin/bash
set -euo pipefail

ROOT="${BTRFS_ROOT:-/var/lib/btrfs}"
LEASE_DIR="${LEASE_DIR:-/var/run/btrfs}"
live=$(cat "$ROOT/meta/gen.live")
target=$(cat "$ROOT/meta/gen.target")

if [[ "$live" != "$target" ]]; then
  echo "hold_c: generation not aligned ($live != $target)" >&2
  exit 1
fi

mkdir -p "$LEASE_DIR" "$ROOT/origins"
rm -f "$LEASE_DIR"/*.part "$ROOT/origins"/*.lease 2>/dev/null || true

if [[ -d "$ROOT/volumes" ]]; then
  for host in "$ROOT/volumes"/*/host; do
    [[ -d "$host" ]] || continue
    find "$host" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
  done
fi
EOF
chmod +x /app/deck/hold_c.sh

cat >/app/dock/link_v.sh <<'EOF'
#!/bin/bash
set -euo pipefail

ROOT="${BTRFS_ROOT:-/var/lib/btrfs}"
ROSTER="${LANE_ROSTER:-/etc/btrfs/lane.roster}"
ATTACH="$ROOT/attach"
HOLD=$(cat "$ROOT/meta/hold.token")

mkdir -p "$ATTACH"
find "$ATTACH" -mindepth 1 -type d -exec rm -rf {} + 2>/dev/null || true

while IFS= read -r lane || [[ -n "$lane" ]]; do
  lane="${lane%%#*}"
  lane="$(echo "$lane" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  [[ -z "$lane" ]] && continue
  src="$ROOT/volumes/$lane/sealed/payload.bin"
  dst="$ATTACH/${lane}.bin"
  src_id=$(stat -c '%d:%i' "$src")
  dst_id=$(stat -c '%d:%i' "$dst" 2>/dev/null || true)
  if [[ "$src_id" != "$dst_id" ]]; then
    rm -f "$dst"
    ln "$src" "$dst"
  fi
  printf '%s\n' "$HOLD" >"$ATTACH/.hold.$lane"
done <"$ROSTER"
EOF
chmod +x /app/dock/link_v.sh

chmod +x /app/ops/deskd /app/ops/run_cutover.sh

/app/ops/run_cutover.sh
