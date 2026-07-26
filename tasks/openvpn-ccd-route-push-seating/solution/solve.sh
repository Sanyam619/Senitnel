#!/bin/bash
set -euo pipefail

cd /app

cat >/var/lib/openvpn/ops/prefer.toml <<'EOF'
mode = "durable"
tag_path = "authority"
EOF

cat >/app/ops/helm_r.sh <<'EOF'
#!/bin/bash
set -euo pipefail
helm_r() {
  local ov_x="${OV_ETC:-/etc/openvpn}"
  local ov_y="${OV_VAR:-/var/lib/openvpn}"
  local abort_pkg="$ov_y/ops/abort.d/90-local.conf"
  local live_dropin="$ov_x/server/conf.d/90-local.conf"
  local cutover_receipt="$ov_y/state/cutover.ok"
  local target_gen gen_ok mode_ok need_abort
  target_gen=$(tr -d ' \t\r\n' <"$ov_y/state/gen.target")
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
  local ov_x="${OV_ETC:-/etc/openvpn}"
  local ov_y="${OV_VAR:-/var/lib/openvpn}"
  local sheet_z="/app/config/site_standard.conf"
  local target_gen
  mkdir -p "$ov_y/state" "$ov_x/server/conf.d" "$ov_x/ccd" "$ov_y/ops"
  target_gen=$(tr -d ' \t\r\n' <"$ov_y/state/gen.target")
  python3 - <<'PY'
import json, os
from pathlib import Path
var = Path(os.environ.get("OV_VAR", "/var/lib/openvpn"))
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
    cn = row["cn"]
    (tip_dir / f"tip_{cn}.gen").write_text(f"{target}\n")
    (tip_dir / f"tip_{cn}.iroute").write_text(f'{row["iroute"]}\n')
(tip_dir / "gen.live").write_text(f"{target}\n")
(tip_dir / "tip.batch").write_text(json.dumps(chosen) + "\n")
(var / "ops" / "tip_bind.accept").write_text(f"gen={target}\ntip=prefer\n")
PY
  cp -f "$sheet_z" "$ov_x/server/conf.d/90-local.conf"
  {
    echo "gen=${target_gen}"
    echo "mode=seal"
  } >"$ov_y/state/cutover.ok"
}
axle_n
EOF
chmod +x /app/ops/axle_n.sh

cat >/app/wire/sock_v.sh <<'EOF'
#!/bin/bash
set -euo pipefail
sock_v() {
  local ov_x="${OV_ETC:-/etc/openvpn}"
  local ov_y="${OV_VAR:-/var/lib/openvpn}"
  mkdir -p "$ov_y/state" "$ov_x/ccd"
  python3 - <<'PY'
import os
from pathlib import Path
etc = Path(os.environ.get("OV_ETC", "/etc/openvpn"))
var = Path(os.environ.get("OV_VAR", "/var/lib/openvpn"))
roster = [ln.strip() for ln in (etc / "server" / "roster.list").read_text().splitlines() if ln.strip()]
admitted = {ln.strip() for ln in (var / "state" / "admit.set").read_text().splitlines() if ln.strip()}
aborted = {ln.strip() for ln in (var / "state" / "abort.set").read_text().splitlines() if ln.strip()}
pushed = []
for cn in roster:
    iroute = (var / "state" / f"tip_{cn}.iroute").read_text().strip()
    gen = int((var / "state" / f"tip_{cn}.gen").read_text().strip())
    floor = int((var / "floors" / f"{cn}.floor").read_text().strip())
    sheet = etc / "ccd" / cn
    sheet.write_text(f"iroute {iroute}\n")
    ok = (
        cn in admitted
        and cn not in aborted
        and gen >= floor
    )
    if ok:
        pushed.append(cn)
(var / "state" / "pushed.set").write_text("".join(f"{n}\n" for n in pushed))
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
  local ov_x="${OV_ETC:-/etc/openvpn}"
  local ov_y="${OV_VAR:-/var/lib/openvpn}"
  local surf="$ov_y/surface"
  local pref="$ov_y/ops/prefer.toml"
  local bind="$ov_y/ops/tip_bind.accept"
  local mode="live"
  local target_gen gen_ok need_surface=1
  mkdir -p "$ov_x/ccd" "$ov_y/state"
  target_gen=$(tr -d ' \t\r\n' <"$ov_y/state/gen.target")
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
    if [[ -d "$surf/ccd" ]]; then
      cp -a "$surf/ccd/." "$ov_x/ccd/"
    fi
    if [[ -d "$surf/tips" ]]; then
      cp -a "$surf/tips/." "$ov_y/state/"
    fi
  fi
  date +%s >"$ov_y/state/probe.stamp"
  printf '%s\n' "$mode" >"$ov_y/state/mode.active"
}
knit_q
EOF
chmod +x /app/wire/knit_q.sh

/app/ops/run_ovpn_seat.sh
/app/ops/run_ovpn_seat.sh
