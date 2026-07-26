#!/bin/bash
set -euo pipefail

cd /app

cat >/app/ops/helm_r.sh <<'EOF'
#!/bin/bash
set -euo pipefail
helm_r() {
  local hap_x="${HAP_ETC:-/etc/haproxy}"
  local hap_y="${HAP_VAR:-/var/lib/haproxy}"
  local abort_pkg="$hap_y/ops/abort.d/90-local.cfg"
  local live_dropin="$hap_x/conf.d/90-local.cfg"
  local cutover_receipt="$hap_y/state/cutover.ok"
  local target_gen gen_ok mode_ok need_abort
  target_gen=$(tr -d ' \t\r\n' <"$hap_y/state/gen.target")
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
  local hap_x="${HAP_ETC:-/etc/haproxy}"
  local hap_y="${HAP_VAR:-/var/lib/haproxy}"
  local sheet_z="/app/config/site_standard.conf"
  local target_gen
  mkdir -p "$hap_y/state" "$hap_x/conf.d"
  target_gen=$(tr -d ' \t\r\n' <"$hap_y/state/gen.target")
  python3 - <<'PY'
import json, os
from pathlib import Path
var = Path(os.environ.get("HAP_VAR", "/var/lib/haproxy"))
target = (var / "state" / "gen.target").read_text().strip()
journal = var / "ops" / "journal.jsonl"
tips = {}
seal_ok = False
for line in journal.read_text().splitlines():
    if not line.strip():
        continue
    row = json.loads(line)
    if row.get("tag") == "seal" and str(row.get("gen")) == target:
        seal_ok = True
    if row.get("tag") == "tip" and "name" in row:
        tips[row["name"]] = int(row["generation"])
if not seal_ok:
    raise SystemExit("axle_n: missing sealed journal row for gen.target")
for name, gen in tips.items():
    (var / "state" / f"tip_{name}.gen").write_text(f"{gen}\n")
(var / "state" / "gen.live").write_text(f"{target}\n")
PY
  cp -f "$sheet_z" "$hap_x/conf.d/90-local.cfg"
  {
    echo "gen=${target_gen}"
    echo "mode=seal"
  } >"$hap_y/state/cutover.ok"
}
axle_n
EOF
chmod +x /app/ops/axle_n.sh

cat >/app/rim/mesh_k.sh <<'EOF'
#!/bin/bash
set -euo pipefail
mesh_k() {
  local hap_x="${HAP_ETC:-/etc/haproxy}"
  local hap_y="${HAP_VAR:-/var/lib/haproxy}"
  local eff="$hap_y/state/effective.conf"
  local f line k v
  mkdir -p "$hap_y/state"
  : >"$eff"
  declare -A kv=()
  while IFS= read -r f; do
    [[ -f "$f" ]] || continue
    while IFS= read -r line || [[ -n "${line:-}" ]]; do
      line=${line%%#*}
      line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
      [[ -z "$line" ]] && continue
      [[ "$line" != *=* ]] && continue
      k=${line%%=*}
      v=${line#*=}
      kv["$k"]="$v"
    done <"$f"
  done < <(find "$hap_x/conf.d" -type f -name '*.cfg' | sort)
  for k in $(printf '%s\n' "${!kv[@]}" | sort); do
    printf '%s=%s\n' "$k" "${kv[$k]}"
  done >"$eff"
}
mesh_k
EOF
chmod +x /app/rim/mesh_k.sh

cat >/app/bag/skim_p.sh <<'EOF'
#!/bin/bash
set -euo pipefail
skim_p() {
  local hap_y="${HAP_VAR:-/var/lib/haproxy}"
  local drain_dir="$hap_y/state/drain"
  local clock name lease until_epoch drained
  mkdir -p "$drain_dir"
  rm -f "$drain_dir"/*
  clock=$(tr -d ' \t\r\n' <"$hap_y/state/clock.epoch" 2>/dev/null || echo 0)
  while IFS= read -r name || [[ -n "${name:-}" ]]; do
    [[ -z "${name:-}" ]] && continue
    lease="$hap_y/leases/${name}.lease"
    drained=0
    if [[ -f "$lease" ]]; then
      until_epoch=$(grep -E '^until_epoch=' "$lease" | head -n1 | cut -d= -f2- || echo 0)
      if [[ "$until_epoch" -gt "$clock" ]]; then
        drained=1
      fi
    fi
    printf 'drained=%s\n' "$drained" >"$drain_dir/${name}.flag"
  done </etc/haproxy/roster.list
}
skim_p
EOF
chmod +x /app/bag/skim_p.sh

cat >/app/wire/sock_v.sh <<'EOF'
#!/bin/bash
set -euo pipefail
sock_v() {
  local hap_x="${HAP_ETC:-/etc/haproxy}"
  local hap_y="${HAP_VAR:-/var/lib/haproxy}"
  local hap_z="${HAP_RUN:-/var/run/haproxy}"
  local eff="$hap_y/state/effective.conf"
  local drain_dir="$hap_y/state/drain"
  local map="$hap_z/runtime.map"
  local name w d
  mkdir -p "$hap_z"
  : >"$map"
  while IFS= read -r name || [[ -n "${name:-}" ]]; do
    [[ -z "${name:-}" ]] && continue
    w=$(grep -E "^weight\.${name}=" "$eff" | tail -n1 | cut -d= -f2- || echo 0)
    d=0
    if [[ -f "$drain_dir/${name}.flag" ]]; then
      d=$(grep -E '^drained=' "$drain_dir/${name}.flag" | head -n1 | cut -d= -f2- || echo 0)
    fi
    printf '%s %s %s\n' "$name" "$w" "$d" >>"$map"
  done <"$hap_x/roster.list"
  printf '1\n' >"$hap_z/socket.applied"
}
sock_v
EOF
chmod +x /app/wire/sock_v.sh

cat >/app/deck/emit_m.sh <<'EOF'
#!/bin/bash
set -euo pipefail
emit_m() {
  local out_path="${HAP_REPORT:-/output/proxy-seat.json}"
  mkdir -p "$(dirname "$out_path")"
  python3 - <<'PY'
import json
import os
from pathlib import Path

etc = Path(os.environ.get("HAP_ETC", "/etc/haproxy"))
var = Path(os.environ.get("HAP_VAR", "/var/lib/haproxy"))
run = Path(os.environ.get("HAP_RUN", "/var/run/haproxy"))
report = Path(os.environ.get("HAP_REPORT", "/output/proxy-seat.json"))
std = Path("/app/config/site_standard.conf")

def parse_kv(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out

roster = [ln.strip() for ln in (etc / "roster.list").read_text().splitlines() if ln.strip()]
eff = parse_kv((var / "state" / "effective.conf").read_text())
std_kv = parse_kv(std.read_text())
runtime_lines = {}
if (run / "runtime.map").exists():
    for line in (run / "runtime.map").read_text().splitlines():
        parts = line.split()
        if len(parts) >= 3:
            runtime_lines[parts[0]] = (int(parts[1]), int(parts[2]))

backends = []
ok = True
socket_ok = (run / "socket.applied").exists() and (run / "socket.applied").read_text().strip() == "1"

for name in roster:
    addr_path = var / "backends" / f"{name}.addr"
    server = addr_path.read_text().strip() if addr_path.exists() else ""
    weight = int(eff.get(f"weight.{name}", "0"))
    expected_w = int(std_kv.get(f"weight.{name}", "0"))
    flag = var / "state" / "drain" / f"{name}.flag"
    drained = False
    if flag.exists():
        drained = parse_kv(flag.read_text()).get("drained", "0") == "1"
    gen = int((var / "state" / f"tip_{name}.gen").read_text().strip())
    backends.append({
        "name": name,
        "server": server,
        "weight": weight,
        "drained": drained,
        "generation": gen,
    })
    if weight != expected_w:
        ok = False
    if not server or server.startswith("127.0.0.1"):
        ok = False
    lease = var / "leases" / f"{name}.lease"
    clock = int((var / "state" / "clock.epoch").read_text().strip())
    expect_drain = False
    if lease.exists():
        until_epoch = int(parse_kv(lease.read_text()).get("until_epoch", "0"))
        expect_drain = until_epoch > clock
    if drained != expect_drain:
        ok = False
    if name not in runtime_lines or runtime_lines[name] != (weight, 1 if drained else 0):
        socket_ok = False
        ok = False

if std_kv.get("tip_policy") != eff.get("tip_policy"):
    ok = False
if std_kv.get("bind_order") != eff.get("bind_order"):
    ok = False

live_local = etc / "conf.d" / "90-local.cfg"
if not live_local.exists():
    ok = False
else:
    live_kv = parse_kv(live_local.read_text())
    for key in ("tip_policy", "bind_order"):
        if live_kv.get(key) != std_kv.get(key):
            ok = False
    for name in roster:
        if live_kv.get(f"weight.{name}") != std_kv.get(f"weight.{name}"):
            ok = False

abort_pkg = var / "ops" / "abort.d" / "90-local.cfg"
if abort_pkg.exists():
    abort_kv = parse_kv(abort_pkg.read_text())
    if abort_kv.get("tip_policy") != "prefer_abort":
        ok = False

receipt = var / "state" / "cutover.ok"
target = (var / "state" / "gen.target").read_text().strip()
if not receipt.exists():
    ok = False
else:
    rkv = parse_kv(receipt.read_text())
    if rkv.get("gen") != target or rkv.get("mode") != "seal":
        ok = False

gen_live = (var / "state" / "gen.live").read_text().strip()
if gen_live != target:
    ok = False

out = {
    "schema_tag": "proxy-seat-v1",
    "backends": backends,
    "socket_applied": bool(socket_ok),
    "seat_ok": bool(ok and socket_ok),
}
report.write_text(json.dumps(out, separators=(",", ":"), sort_keys=False) + "\n")
PY
}
emit_m
EOF
chmod +x /app/deck/emit_m.sh

/app/ops/run_proxy_seat.sh
/app/ops/run_proxy_seat.sh
