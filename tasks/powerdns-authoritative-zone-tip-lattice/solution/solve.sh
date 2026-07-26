#!/bin/bash
set -euo pipefail

cd /app

cat >/var/lib/powerdns/ops/prefer.toml <<'EOF'
mode = "durable"
tag_path = "authority"
EOF

cat >/app/ops/crib_j.sh <<'EOF'
#!/bin/bash
set -euo pipefail
crib_j() {
  local pd_x="${PD_ETC:-/etc/powerdns}"
  local pd_y="${PD_VAR:-/var/lib/powerdns}"
  local abort_pkg="$pd_y/ops/abort.d/90-local.conf"
  local live_dropin="$pd_x/pdns.d/90-local.conf"
  local receipt="$pd_y/state/cutover.ok"
  local target_gen gen_ok mode_ok need_abort
  target_gen=$(tr -d ' \t\r\n' <"$pd_y/state/gen.target")
  need_abort=1
  if [[ -f "$receipt" ]]; then
    gen_ok=$(grep -E '^gen=' "$receipt" | head -n1 | cut -d= -f2- || true)
    mode_ok=$(grep -E '^mode=' "$receipt" | head -n1 | cut -d= -f2- || true)
    if [[ "$gen_ok" == "$target_gen" && "$mode_ok" == "seal" ]]; then
      need_abort=0
    fi
  fi
  if [[ "$need_abort" -eq 1 ]]; then
    if [[ -f "$abort_pkg" ]]; then
      cp -f "$abort_pkg" "$live_dropin"
    fi
  fi
}
crib_j
EOF
chmod +x /app/ops/crib_j.sh

cat >/app/ops/lath_p.sh <<'EOF'
#!/bin/bash
set -euo pipefail
lath_p() {
  local pd_x="${PD_ETC:-/etc/powerdns}"
  local pd_y="${PD_VAR:-/var/lib/powerdns}"
  local sheet_z="/app/config/site_standard.conf"
  local target_gen
  mkdir -p "$pd_y/state" "$pd_x/pdns.d" "$pd_x/zones.d" "$pd_y/ops"
  target_gen=$(tr -d ' \t\r\n' <"$pd_y/state/gen.target")
  python3 - <<'PY'
import json
import os
from pathlib import Path
var = Path(os.environ.get("PD_VAR", "/var/lib/powerdns"))
target = (var / "state" / "gen.target").read_text().strip()
batches = []
seal_ok = False
for line in (var / "ops" / "zone_journal.jsonl").read_text().splitlines():
    if not line.strip():
        continue
    row = json.loads(line)
    if row.get("tag") == "seal" and str(row.get("gen")) == target:
        seal_ok = True
    if row.get("tag") == "batch":
        batches.append(row)
if not seal_ok:
    raise SystemExit("lath_p: missing seal for gen.target")
chosen = None
for batch in batches:
    if str(batch.get("gen")) != target:
        continue
    if batch.get("sealed") is True and batch.get("complete") is True:
        chosen = batch
if chosen is None:
    raise SystemExit("lath_p: no sealed complete batch for gen.target")
tip_dir = var / "state"
for row in chosen.get("zones", []):
    name = row["name"]
    (tip_dir / f"tip_{name}.serial").write_text(f'{int(row["serial"])}\n')
    (tip_dir / f"tip_{name}.gen").write_text(f"{target}\n")
    (tip_dir / f"tip_{name}.records").write_text(
        json.dumps(row.get("records", [])) + "\n"
    )
(tip_dir / "gen.live").write_text(f"{target}\n")
(tip_dir / "tip.batch").write_text(json.dumps(chosen) + "\n")
(var / "ops" / "tip_bind.accept").write_text(f"gen={target}\ntip=journal\n")
PY
  cp -f "$sheet_z" "$pd_x/pdns.d/90-local.conf"
  {
    echo "gen=${target_gen}"
    echo "mode=seal"
  } >"$pd_y/state/cutover.ok"
}
lath_p
EOF
chmod +x /app/ops/lath_p.sh

cat >/app/rig/gaff_s.sh <<'EOF'
#!/bin/bash
set -euo pipefail
# gaff_s
gaff_s() {
  local pd_y="${PD_VAR:-/var/lib/powerdns}"
  mkdir -p "$pd_y/state"
  python3 - <<'PY'
import json
import os
from pathlib import Path
var = Path(os.environ.get("PD_VAR", "/var/lib/powerdns"))
retired = set()
retired_path = var / "ops" / "retired_stores.jsonl"
if retired_path.exists():
    for line in retired_path.read_text().splitlines():
        if line.strip():
            retired.add(str(json.loads(line).get("store", "")))
best = None
for line in (var / "ops" / "store_registry.jsonl").read_text().splitlines():
    if not line.strip():
        continue
    row = json.loads(line)
    if row.get("tag") != "bind":
        continue
    if str(row.get("store", "")) in retired:
        continue
    if best is None or int(row.get("epoch", -1)) > int(best.get("epoch", -1)):
        best = row
if best is None:
    raise SystemExit("gaff_s: no eligible registry rows")
(var / "state" / "store.sel").write_text(f'{best["store"]}\n')
PY
}
gaff_s
EOF
chmod +x /app/rig/gaff_s.sh

cat >/app/span/moor_w.sh <<'EOF'
#!/bin/bash
set -euo pipefail
moor_w() {
  local pd_x="${PD_ETC:-/etc/powerdns}"
  local pd_y="${PD_VAR:-/var/lib/powerdns}"
  mkdir -p "$pd_y/state" "$pd_x/zones.d" "$pd_x/serials"
  python3 - <<'PY'
import json
import os
from pathlib import Path
etc = Path(os.environ.get("PD_ETC", "/etc/powerdns"))
var = Path(os.environ.get("PD_VAR", "/var/lib/powerdns"))
roster = [
    ln.strip()
    for ln in (etc / "zone.roster").read_text().splitlines()
    if ln.strip()
]
sel_path = var / "state" / "store.sel"
store_sel = sel_path.read_text().strip() if sel_path.exists() else ""
abort_path = var / "state" / "abort.set"
aborted = (
    {ln.strip() for ln in abort_path.read_text().splitlines() if ln.strip()}
    if abort_path.exists()
    else set()
)
holds = {}
holds_path = var / "ops" / "holds.jsonl"
if holds_path.exists():
    for line in holds_path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        holds[(row["zone"], row["name"], row["type"])] = row["content"]
publish = []
honor = []
for name in roster:
    serial = int((var / "state" / f"tip_{name}.serial").read_text().strip())
    gen = int((var / "state" / f"tip_{name}.gen").read_text().strip())
    floor = int((var / "floors" / f"{name}.floor").read_text().strip())
    apex = (var / "zones" / f"{name}.ns").read_text().strip()
    rows = json.loads((var / "state" / f"tip_{name}.records").read_text())
    lines = [f"@ NS {apex}"]
    for row in rows:
        content = holds.get((name, row["name"], row["type"]), row["content"])
        lines.append(f'{row["name"]} {row["type"]} {content}')
        if content == row["content"]:
            honor.append(f'{name}|{row["name"]}|{row["type"]}')
    (etc / "zones.d" / f"{name}.rec").write_text(
        "".join(f"{ln}\n" for ln in lines)
    )
    (etc / "zones.d" / f"{name}.store").write_text(f"{store_sel}\n")
    (etc / "serials" / f"{name}.serial").write_text(f"{serial}\n")
    ok = serial > 0 and gen >= floor and bool(store_sel) and name not in aborted
    if ok:
        publish.append(name)
(var / "state" / "publish.set").write_text("".join(f"{n}\n" for n in publish))
(var / "state" / "honor.set").write_text("".join(f"{r}\n" for r in honor))
(var / "state" / "seated.stamp").write_text("1\n")
PY
}
moor_w
EOF
chmod +x /app/span/moor_w.sh

cat >/app/wire/keel_x.sh <<'EOF'
#!/bin/bash
# keel_x — surface rematerialize gated on preference + tip bind
set -euo pipefail
keel_x() {
  local pd_x="${PD_ETC:-/etc/powerdns}"
  local pd_y="${PD_VAR:-/var/lib/powerdns}"
  local surf="$pd_y/surface"
  local pref="$pd_y/ops/prefer.toml"
  local bind="$pd_y/ops/tip_bind.accept"
  local mode="live"
  local target_gen gen_ok need_surface=1
  mkdir -p "$pd_x/zones.d" "$pd_x/serials" "$pd_y/state"
  target_gen=$(tr -d ' \t\r\n' <"$pd_y/state/gen.target")
  if [[ -f "$pref" ]]; then
    mode=$(grep -E '^mode[[:space:]]*=' "$pref" | head -1 \
      | sed 's/.*=[[:space:]]*//;s/"//g;s/[[:space:]]*$//' | tr -d ' ')
  fi
  gen_ok=""
  if [[ -f "$bind" ]]; then
    gen_ok=$(grep -E '^gen=' "$bind" | head -n1 | cut -d= -f2- || true)
  fi
  case "$mode" in
    durable|authority)
      if [[ "$gen_ok" == "$target_gen" ]]; then
        need_surface=0
      fi
      ;;
  esac
  if [[ "$need_surface" -eq 1 ]]; then
    if [[ -d "$surf/zones.d" ]]; then
      cp -a "$surf/zones.d/." "$pd_x/zones.d/"
    fi
    if [[ -d "$surf/tips" ]]; then
      cp -a "$surf/tips/." "$pd_y/state/"
    fi
    if [[ -d "$surf/serials" ]]; then
      cp -a "$surf/serials/." "$pd_x/serials/"
    fi
  fi
  date +%s >"$pd_y/state/probe.stamp"
  printf '%s\n' "$mode" >"$pd_y/state/mode.active"
}
keel_x
EOF
chmod +x /app/wire/keel_x.sh

/app/ops/run_pdns_seat.sh
/app/ops/run_pdns_seat.sh
