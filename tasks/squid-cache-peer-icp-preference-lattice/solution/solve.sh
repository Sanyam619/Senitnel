#!/bin/bash
set -euo pipefail

cd /app

cat >/var/lib/squid/ops/prefer.toml <<'EOF'
mode = "durable"
tag_path = "authority"
EOF

cat >/app/ops/helm_r.sh <<'EOF'
#!/bin/bash
set -euo pipefail
helm_r() {
  local sq_x="${SQ_ETC:-/etc/squid}"
  local sq_y="${SQ_VAR:-/var/lib/squid}"
  local abort_pkg="$sq_y/ops/abort.d/90-local.cfg"
  local live_dropin="$sq_x/conf.d/90-local.cfg"
  local cutover_receipt="$sq_y/state/cutover.ok"
  local target_gen gen_ok mode_ok need_abort
  target_gen=$(tr -d ' \t\r\n' <"$sq_y/state/gen.target")
  need_abort=1
  if [[ -f "$cutover_receipt" ]]; then
    gen_ok=$(grep -E '^gen=' "$cutover_receipt" | head -n1 | cut -d= -f2- || true)
    mode_ok=$(grep -E '^mode=' "$cutover_receipt" | head -n1 | cut -d= -f2- || true)
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
helm_r
EOF
chmod +x /app/ops/helm_r.sh

cat >/app/ops/axle_n.sh <<'EOF'
#!/bin/bash
set -euo pipefail
axle_n() {
  local sq_x="${SQ_ETC:-/etc/squid}"
  local sq_y="${SQ_VAR:-/var/lib/squid}"
  local sheet_z="/app/config/site_standard.conf"
  local target_gen
  mkdir -p "$sq_y/state" "$sq_x/conf.d" "$sq_x/peers.d" "$sq_y/ops"
  target_gen=$(tr -d ' \t\r\n' <"$sq_y/state/gen.target")
  python3 - <<'PY'
import json, os
from pathlib import Path
var = Path(os.environ.get("SQ_VAR", "/var/lib/squid"))
target = (var / "state" / "gen.target").read_text().strip()
prefer = var / "ops" / "prefer.jsonl"
batches = []
seal_ok = False
for line in prefer.read_text().splitlines():
    if not line.strip():
        continue
    row = json.loads(line)
    if row.get("tag") == "seal" and str(row.get("gen")) == target:
        seal_ok = True
    if row.get("tag") == "batch":
        batches.append(row)
if not seal_ok:
    raise SystemExit("axle_n: missing seal for gen.target")
chosen = None
for batch in batches:
    if str(batch.get("gen")) != target:
        continue
    if batch.get("sealed") is True and batch.get("complete") is True:
        chosen = batch
if chosen is None:
    raise SystemExit("axle_n: no sealed complete batch for gen.target")
tip_dir = var / "state"
for row in chosen.get("rows", []):
    name = row["name"]
    (tip_dir / f"tip_{name}.gen").write_text(f"{target}\n")
    (tip_dir / f"tip_{name}.type").write_text(f'{row["type"]}\n')
    (tip_dir / f"tip_{name}.weight").write_text(f'{int(row["weight"])}\n')
(tip_dir / "gen.live").write_text(f"{target}\n")
(tip_dir / "tip.batch").write_text(json.dumps(chosen) + "\n")
(var / "ops" / "tip_bind.accept").write_text(f"gen={target}\ntip=prefer\n")
PY
  cp -f "$sheet_z" "$sq_x/conf.d/90-local.cfg"
  {
    echo "gen=${target_gen}"
    echo "mode=seal"
  } >"$sq_y/state/cutover.ok"
}
axle_n
EOF
chmod +x /app/ops/axle_n.sh

cat >/app/wire/sock_v.sh <<'EOF'
#!/bin/bash
set -euo pipefail
sock_v() {
  local sq_x="${SQ_ETC:-/etc/squid}"
  local sq_y="${SQ_VAR:-/var/lib/squid}"
  mkdir -p "$sq_y/state" "$sq_x/peers.d"
  python3 - <<'PY'
import os
from pathlib import Path
etc = Path(os.environ.get("SQ_ETC", "/etc/squid"))
var = Path(os.environ.get("SQ_VAR", "/var/lib/squid"))
roster = [ln.strip() for ln in (etc / "roster.list").read_text().splitlines() if ln.strip()]
admitted = {ln.strip() for ln in (var / "state" / "admit.set").read_text().splitlines() if ln.strip()}
aborted = {ln.strip() for ln in (var / "state" / "abort.set").read_text().splitlines() if ln.strip()}
selected = []
for name in roster:
    typ = (var / "state" / f"tip_{name}.type").read_text().strip()
    weight = int((var / "state" / f"tip_{name}.weight").read_text().strip())
    gen = int((var / "state" / f"tip_{name}.gen").read_text().strip())
    floor = int((var / "floors" / f"{name}.floor").read_text().strip())
    host = (var / "peers" / f"{name}.host").read_text().strip()
    sheet = etc / "peers.d" / f"{name}.peer"
    sheet.write_text(f"type={typ}\nweight={weight}\nhost={host}\n")
    ok = (
        name in admitted
        and name not in aborted
        and gen >= floor
    )
    if ok:
        selected.append(name)
(var / "state" / "selected.set").write_text("".join(f"{n}\n" for n in selected))
(var / "state" / "socket.applied").write_text("1\n")
PY
}
sock_v
EOF
chmod +x /app/wire/sock_v.sh

cat >/app/wire/knit_q.sh <<'EOF'
#!/bin/bash
# knit_q — surface rematerialize gated on preference + tip bind
set -euo pipefail
knit_q() {
  local sq_x="${SQ_ETC:-/etc/squid}"
  local sq_y="${SQ_VAR:-/var/lib/squid}"
  local surf="$sq_y/surface"
  local pref="$sq_y/ops/prefer.toml"
  local bind="$sq_y/ops/tip_bind.accept"
  local mode="live"
  local target_gen gen_ok need_surface=1
  mkdir -p "$sq_x/peers.d" "$sq_y/state"
  target_gen=$(tr -d ' \t\r\n' <"$sq_y/state/gen.target")
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
    if [[ -d "$surf/peers.d" ]]; then
      cp -a "$surf/peers.d/." "$sq_x/peers.d/"
    fi
    if [[ -d "$surf/tips" ]]; then
      cp -a "$surf/tips/." "$sq_y/state/"
    fi
  fi
  date +%s >"$sq_y/state/probe.stamp"
  printf '%s\n' "$mode" >"$sq_y/state/mode.active"
}
knit_q
EOF
chmod +x /app/wire/knit_q.sh

/app/ops/run_squid_seat.sh
/app/ops/run_squid_seat.sh
