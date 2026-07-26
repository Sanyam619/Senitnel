#!/bin/bash
set -euo pipefail

# Rewrite live drop-in to site-standard tokens (abort package stays forensic).
cat >/etc/systemd/system/machines.target.wants/90-local.conf <<'EOF'
tip_policy=durable
bind_order=inode
abort=none
EOF

# Durable cutover receipt matching gen.target.
target=$(tr -d '[:space:]' </var/lib/machines/state/gen.target)
cat >/var/lib/machines/state/cutover.ok <<EOF
gen=${target}
mode=seal
EOF

cat >/app/rim/mesh_p.sh <<'EOF'
#!/bin/bash
mesh_p() {
  set -euo pipefail

  PREF_D="${PREF_D:-/etc/systemd/system/machines.target.wants}"
  OUT="${EFF_POLICY:-/etc/systemd/nspawn/effective.conf}"
  MARK="${EFF_MARK:-/var/lib/machines/state/fold.mark}"

  mkdir -p "$(dirname "$OUT")" "$(dirname "$MARK")"
  declare -A kv=()
  declare -a seen=()
  shopt -s nullglob
  for f in $(ls -1 "$PREF_D"/*.conf 2>/dev/null | sort); do
    seen+=("$(basename "$f")")
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
  printf '%s\n' "${seen[@]}" >"$MARK"
}
mesh_p
EOF
chmod +x /app/rim/mesh_p.sh

cat >/app/ops/axle_k.sh <<'EOF'
#!/bin/bash
axle_k() {
  set -euo pipefail

  ROOT="${MACH_ROOT:-/var/lib/machines}"
  FLOOR_D="$ROOT/floors"
  ROSTER="${ROSTER:-/etc/systemd/nspawn/roster.list}"
  STATE="$ROOT/state"
  JOURNAL="$ROOT/ops/journal.jsonl"
  NSP="/etc/systemd/nspawn"
  TARGET=$(tr -d '[:space:]' <"$STATE/gen.target")

  mkdir -p "$STATE"

  python3 - "$JOURNAL" "$STATE" "$TARGET" "$ROSTER" "$FLOOR_D" "$NSP" "$ROOT" <<'PY'
import json
import sys
from pathlib import Path

journal, state, target_s, roster, floor_d, nsp, root = sys.argv[1:]
state = Path(state)
floor_d = Path(floor_d)
nsp = Path(nsp)
root = Path(root)
target = int(target_s)

tips = {}
sealed = None
for line in Path(journal).read_text().splitlines():
    line = line.strip()
    if not line:
        continue
    row = json.loads(line)
    if (
        row.get("kind") == "cutover"
        and int(row.get("gen", -1)) == target
        and row.get("mode") == "seal"
    ):
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
    durable = root / "images" / name / "root"
    (state / f"root_{name}").write_text(f"{durable}\n")
    unit = nsp / f"{name}.nspawn"
    if unit.exists():
        lines = []
        for line in unit.read_text().splitlines():
            if line.startswith("Directory="):
                lines.append(f"Directory={durable}")
            else:
                lines.append(line)
        unit.write_text("\n".join(lines) + "\n")

(state / "gen.live").write_text(f"{target}\n")
PY
}
axle_k
EOF
chmod +x /app/ops/axle_k.sh

cat >/app/bag/knit_v.sh <<'EOF'
#!/bin/bash
knit_v() {
  set -euo pipefail

  ROOT="${MACH_ROOT:-/var/lib/machines}"
  ROSTER="${ROSTER:-/etc/systemd/nspawn/roster.list}"
  VOL="$ROOT/volumes"
  BIND="$ROOT/bind"

  mkdir -p "$BIND"

  while IFS= read -r name || [[ -n "$name" ]]; do
    name="$(echo "$name" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "$name" || "$name" =~ ^# ]] && continue
    mkdir -p "$BIND/${name}"
    src="$VOL/${name}/data"
    dst="$BIND/${name}/data"
    if [[ -f "$src" ]]; then
      rm -f "$dst"
      ln "$src" "$dst"
    fi
  done <"$ROSTER"
}
knit_v
EOF
chmod +x /app/bag/knit_v.sh

cat >/app/ops/helm_w.sh <<'EOF'
#!/bin/bash
helm_w() {
  set -euo pipefail

  ABORT_D="${ABORT_D:-/var/lib/machines/ops/abort.d}"
  LIVE_D="${LIVE_D:-/etc/systemd/system/machines.target.wants}"
  STATE="/var/lib/machines/state"
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
      [[ -z "$line" || "$line" != *=* ]] && continue
      k="${line%%=*}"
      v="${line#*=}"
      [[ "$k" == "gen" ]] && got_gen="$v"
      [[ "$k" == "mode" ]] && got_mode="$v"
    done <"$RECEIPT"
    if [[ "$got_gen" == "$TARGET" && "$got_mode" == "seal" ]]; then
      skip=1
    fi
  fi

  if [[ "$skip" -eq 0 && -f "$ABORT_D/90-local.conf" ]]; then
    cp -f "$ABORT_D/90-local.conf" "$LIVE_D/90-local.conf"
  fi
}
helm_w
EOF
chmod +x /app/ops/helm_w.sh

cat >/app/bag/skim_z.sh <<'EOF'
#!/bin/bash
skim_z() {
  set -euo pipefail

  STATE="${MACH_ROOT:-/var/lib/machines}/state"
  DUR_PORTS="${DUR_PORTS:-/var/lib/machines/ops/ports.toml}"

  mkdir -p "$STATE"
  : >"$STATE/ports.tsv"

  if [[ -f "$DUR_PORTS" ]]; then
    while IFS='=' read -r k v || [[ -n "$k" ]]; do
      [[ -z "${k:-}" || "$k" =~ ^# ]] && continue
      host="${v%%:*}"
      cont="${v##*:}"
      printf '%s\t%s\t%s\n' "$k" "$host" "$cont" >>"$STATE/ports.tsv"
    done <"$DUR_PORTS"
  fi
}
skim_z
EOF
chmod +x /app/bag/skim_z.sh

cat >/app/deck/emit_q.sh <<'EOF'
#!/bin/bash
emit_q() {
  set -euo pipefail

  OUT="${SEAT_OUT:-/output/nspawn-seat.json}"
  ROSTER="${ROSTER:-/etc/systemd/nspawn/roster.list}"
  ROOT="${MACH_ROOT:-/var/lib/machines}"
  STATE="$ROOT/state"
  EFF="${EFF_POLICY:-/etc/systemd/nspawn/effective.conf}"
  NSP="/etc/systemd/nspawn"
  VOL="$ROOT/volumes"

  mkdir -p "$(dirname "$OUT")"

  python3 - "$OUT" "$ROSTER" "$STATE" "$EFF" "$NSP" "$ROOT" "$VOL" <<'PY'
import json
import os
import sys
from pathlib import Path

out, roster, state, eff, nsp, root, vol = map(Path, sys.argv[1:])
names = [
    ln.strip()
    for ln in roster.read_text().splitlines()
    if ln.strip() and not ln.strip().startswith("#")
]
abort = "none"
if eff.exists():
    for line in eff.read_text().splitlines():
        line = line.strip()
        if line.startswith("abort="):
            abort = line.split("=", 1)[1]

def same_inode(a: Path, b: Path) -> bool:
    if not a.exists() or not b.exists():
        return False
    sa = os.stat(a)
    sb = os.stat(b)
    return sa.st_ino == sb.st_ino and sa.st_dev == sb.st_dev

machines = []
agree = True
for name in names:
    gen_p = state / f"pub_{name}.gen"
    gen = int(gen_p.read_text().strip()) if gen_p.exists() else 0
    elig_p = state / f"elig_{name}"
    elig = elig_p.read_text().strip() == "1" if elig_p.exists() else False
    durable = root / "images" / name / "root"
    unit_root = str(durable)
    bind = []
    unit = nsp / f"{name}.nspawn"
    if unit.exists():
        for line in unit.read_text().splitlines():
            line = line.strip()
            if line.startswith("Bind="):
                bind.append(line.split("=", 1)[1])
            if line.startswith("Directory="):
                unit_root = line.split("=", 1)[1]
    sealed = vol / name / "data"
    binds_ok = all(same_inode(Path(bp), sealed) for bp in bind) if bind else False
    tip_ok = Path(unit_root).resolve() == durable.resolve()
    active = bool(elig and abort != name and tip_ok and binds_ok)
    if not tip_ok or not binds_ok:
        agree = False
    machines.append(
        {
            "name": name,
            "root": str(durable),
            "bind": bind,
            "generation": gen,
            "active": active,
        }
    )

ports = []
ports_tsv = state / "ports.tsv"
if ports_tsv.exists():
    for line in ports_tsv.read_text().splitlines():
        parts = line.split("\t")
        if len(parts) >= 3:
            ports.append(
                {
                    "machine": parts[0],
                    "host": int(parts[1]),
                    "container": int(parts[2]),
                }
            )
if not ports:
    agree = False

doc = {
    "schema_tag": "nspawn-seat-v1",
    "machines": machines,
    "ports": ports,
    "seat_ok": bool(agree and abort == "none"),
}
out.write_text(json.dumps(doc, indent=2) + "\n")
PY
}
emit_q
EOF
chmod +x /app/deck/emit_q.sh

/app/ops/run_nspawn_seat.sh
