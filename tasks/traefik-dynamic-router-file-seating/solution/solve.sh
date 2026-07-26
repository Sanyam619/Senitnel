#!/bin/bash
set -euo pipefail

cd /app

cat >/var/lib/traefik/ops/prefer.toml <<'EOF'
[selection]
source = "durable"
mode = "authority"
EOF

TIP_ID=$(python3 - <<'PY'
import json
from pathlib import Path
var = Path("/var/lib/traefik")
retired = set()
for line in (var / "ops" / "retired_tips.jsonl").read_text().splitlines():
    if not line.strip():
        continue
    retired.add(json.loads(line)["tip"])
last = None
for line in (var / "ops" / "journal.jsonl").read_text().splitlines():
    if not line.strip():
        continue
    row = json.loads(line)
    if row.get("tag") != "tip":
        continue
    if row.get("kind") != "durable":
        continue
    if row.get("tip") in retired:
        continue
    last = row.get("tip")
print(last or "")
PY
)
printf '%s\n' "$TIP_ID" >/var/lib/traefik/ops/tip_bind.accept

cat >/app/ops/helm_r.sh <<'EOF'
#!/bin/bash
set -euo pipefail
helm_r() {
  local trf_x="${TRF_ETC:-/etc/traefik}"
  local trf_y="${TRF_VAR:-/var/lib/traefik}"
  local abort_pkg="$trf_y/ops/abort.d/90-abort.yml"
  local live_dropin="$trf_x/dynamic/90-local.yml"
  local cutover_receipt="$trf_y/ops/state/cutover.ok"
  local sheet_z="/app/config/site_standard.yml"
  local target_gen gen_ok mode_ok need_abort
  target_gen=$(tr -d ' \t\r\n' <"$trf_y/ops/state/gen.target")
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
  local trf_x="${TRF_ETC:-/etc/traefik}"
  local trf_y="${TRF_VAR:-/var/lib/traefik}"
  local sheet_z="/app/config/site_standard.yml"
  mkdir -p "$trf_y/ops/state" "$trf_x/dynamic"
  python3 - <<'PY'
import json
import os
from pathlib import Path

var = Path(os.environ.get("TRF_VAR", "/var/lib/traefik"))
etc = Path(os.environ.get("TRF_ETC", "/etc/traefik"))
target = (var / "ops" / "state" / "gen.target").read_text().strip()
retired = set()
for line in (var / "ops" / "retired_tips.jsonl").read_text().splitlines():
    if not line.strip():
        continue
    retired.add(json.loads(line)["tip"])
tips = {}
tip_id = None
seal_ok = False
for line in (var / "ops" / "journal.jsonl").read_text().splitlines():
    if not line.strip():
        continue
    row = json.loads(line)
    if row.get("tag") == "seal" and str(row.get("gen")) == target:
        seal_ok = True
    if row.get("tag") != "tip":
        continue
    if row.get("kind") != "durable":
        continue
    if row.get("tip") in retired:
        continue
    tip_id = row.get("tip")
    tips[str(row["name"])] = {
        "rule": row["rule"],
        "service": row["service"],
        "generation": int(row["generation"]),
        "tip": tip_id,
    }
if not seal_ok:
    raise SystemExit("axle_n: missing sealed journal row for gen.target")
if not tip_id:
    raise SystemExit("axle_n: no durable tip")
for name, meta in tips.items():
    (var / "ops" / "state" / f"tip_{name}.gen").write_text(f"{meta['generation']}\n")
    (var / "ops" / "state" / f"tip_{name}.rule").write_text(f"{meta['rule']}\n")
    (var / "ops" / "state" / f"tip_{name}.service").write_text(f"{meta['service']}\n")
(var / "ops" / "state" / "serving.tip").write_text(f"{tip_id}\n")
(var / "ops" / "state" / "gen.live").write_text(f"{target}\n")
PY
  local target_gen
  target_gen=$(tr -d ' \t\r\n' <"$trf_y/ops/state/gen.target")
  cp -f "$sheet_z" "$trf_x/dynamic/90-local.yml"
  {
    echo "gen=${target_gen}"
    echo "mode=seal"
  } >"$trf_y/ops/state/cutover.ok"
}
axle_n
EOF
chmod +x /app/ops/axle_n.sh

cat >/app/wire/knit_q.sh <<'EOF'
#!/bin/bash
set -euo pipefail
knit_q() {
  local trf_x="${TRF_ETC:-/etc/traefik}"
  local trf_y="${TRF_VAR:-/var/lib/traefik}"
  mkdir -p "$trf_x/dynamic"
  python3 - <<'PY'
import os
import re
from pathlib import Path

var = Path(os.environ.get("TRF_VAR", "/var/lib/traefik"))
etc = Path(os.environ.get("TRF_ETC", "/etc/traefik"))
prefer = (var / "ops" / "prefer.toml").read_text()
bind = (var / "ops" / "tip_bind.accept").read_text().strip()
serving = ""
sp = var / "ops" / "state" / "serving.tip"
if sp.exists():
    serving = sp.read_text().strip()
src_ok = bool(re.search(r'^\s*source\s*=\s*"durable"', prefer, re.M))
mode_ok = bool(re.search(r'^\s*mode\s*=\s*"authority"', prefer, re.M))
gate_ok = src_ok and mode_ok and bind == serving and serving != ""
seed = var / "ops" / "seeds" / "10-routers.yml"
live = etc / "dynamic" / "10-routers.yml"
if not gate_ok:
    if seed.exists():
        live.write_text(seed.read_text())
    raise SystemExit(0)
roster = [ln.strip() for ln in (etc / "roster.list").read_text().splitlines() if ln.strip()]
lines = ["http:", "  routers:"]
for name in roster:
    rule = (var / "ops" / "state" / f"tip_{name}.rule").read_text().strip()
    service = (var / "ops" / "state" / f"tip_{name}.service").read_text().strip()
    lines.append(f"    {name}:")
    lines.append(f'      rule: "{rule}"')
    lines.append(f"      service: {service}")
live.write_text("\n".join(lines) + "\n")
PY
}
knit_q
EOF
chmod +x /app/wire/knit_q.sh

cat >/app/rim/mesh_k.sh <<'EOF'
#!/bin/bash
set -euo pipefail
mesh_k() {
  local trf_x="${TRF_ETC:-/etc/traefik}"
  local trf_y="${TRF_VAR:-/var/lib/traefik}"
  local eff="$trf_y/ops/state/effective.fold"
  mkdir -p "$trf_y/ops/state"
  : >"$eff"
  local f
  for f in $(find "$trf_x/dynamic" -type f -name '*.yml' | sort); do
    echo "# fold $(basename "$f")" >>"$eff"
    cat "$f" >>"$eff"
    echo >>"$eff"
  done
  local name
  for name in alpha beta gamma delta epsilon; do
    rm -f "$trf_y/ops/state/flag_${name}"
  done
}
mesh_k
EOF
chmod +x /app/rim/mesh_k.sh

cat >/app/bag/skim_p.sh <<'EOF'
#!/bin/bash
set -euo pipefail
skim_p() {
  local trf_y="${TRF_VAR:-/var/lib/traefik}"
  local trf_x="${TRF_ETC:-/etc/traefik}"
  mkdir -p "$trf_y/ops/state"
  python3 - <<'PY'
from pathlib import Path
import os

etc = Path(os.environ.get("TRF_ETC", "/etc/traefik"))
var = Path(os.environ.get("TRF_VAR", "/var/lib/traefik"))
prefer = (var / "ops" / "mw_prefer.toml").read_text()
kv = {}
for line in prefer.splitlines():
    line = line.split("#", 1)[0].strip()
    if not line or "=" not in line:
        continue
    k, v = line.split("=", 1)
    kv[k.strip()] = v.strip()
names = [ln.strip() for ln in (etc / "mw.list").read_text().splitlines() if ln.strip()]
lines = []
for name in names:
    attached = kv.get(f"attach.{name}", "false")
    typ = kv.get(f"type.{name}", name)
    lines.append(f"{name}|{typ}|{attached}")
(var / "ops" / "state" / "mw.attach").write_text("\n".join(lines) + ("\n" if lines else ""))
PY
}
skim_p
EOF
chmod +x /app/bag/skim_p.sh

cat >/app/deck/emit_m.sh <<'EOF'
#!/bin/bash
set -euo pipefail
emit_m() {
  local report="${TRF_REPORT:-/output/traefik-seat.json}"
  mkdir -p "$(dirname "$report")"
  python3 - <<'PY'
import json
import os
import re
from pathlib import Path

etc = Path(os.environ.get("TRF_ETC", "/etc/traefik"))
var = Path(os.environ.get("TRF_VAR", "/var/lib/traefik"))
report = Path(os.environ.get("TRF_REPORT", "/output/traefik-seat.json"))
roster = [ln.strip() for ln in (etc / "roster.list").read_text().splitlines() if ln.strip()]

def parse_kv(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out

dyn = (etc / "dynamic" / "10-routers.yml").read_text()
routers = []
ok_rows = True
for name in roster:
    rule_m = re.search(rf"{name}:\s*\n\s*rule:\s*\"([^\"]+)\"", dyn)
    svc_m = re.search(rf"{name}:\s*\n(?:.*\n)*?\s*service:\s*(\S+)", dyn)
    tip_rule = (var / "ops" / "state" / f"tip_{name}.rule").read_text().strip()
    tip_svc = (var / "ops" / "state" / f"tip_{name}.service").read_text().strip()
    gen = int((var / "ops" / "state" / f"tip_{name}.gen").read_text().strip())
    floor = int((var / "ops" / "floors" / f"{name}.floor").read_text().strip())
    rule = rule_m.group(1) if rule_m else ""
    service = svc_m.group(1) if svc_m else ""
    match = rule == tip_rule and service == tip_svc
    active = match and gen >= floor
    if not match or gen != int((var / "ops" / "state" / f"tip_{name}.gen").read_text().strip()):
        ok_rows = False
    if rule != tip_rule or service != tip_svc:
        ok_rows = False
    routers.append({
        "name": name,
        "rule": rule,
        "service": service,
        "generation": gen,
        "active": active,
    })

middlewares = []
mw_path = var / "ops" / "state" / "mw.attach"
prefer = parse_kv((var / "ops" / "mw_prefer.toml").read_text())
for line in mw_path.read_text().splitlines():
    if not line.strip():
        continue
    name, typ, attached = line.split("|", 2)
    want_att = prefer.get(f"attach.{name}", "false") == "true"
    want_typ = prefer.get(f"type.{name}", name)
    got_att = attached == "true"
    if got_att != want_att or typ != want_typ:
        ok_rows = False
    middlewares.append({"name": name, "type": typ, "attached": got_att})

# Cutover / live drop-in agreement
receipt = var / "ops" / "state" / "cutover.ok"
target = (var / "ops" / "state" / "gen.target").read_text().strip()
rkv = parse_kv(receipt.read_text()) if receipt.exists() else {}
live = (etc / "dynamic" / "90-local.yml").read_text()
site = Path("/app/config/site_standard.yml").read_text()
abort = (var / "ops" / "abort.d" / "90-abort.yml").read_text()
cutover_ok = rkv.get("gen") == target and rkv.get("mode") == "seal"
live_ok = "tip_policy=durable_authority" in live and "revoke.alpha=true" not in live
abort_ok = "prefer_abort" in abort
gen_live_ok = (var / "ops" / "state" / "gen.live").read_text().strip() == target
seat_ok = ok_rows and cutover_ok and live_ok and abort_ok and gen_live_ok

out = {
    "schema_tag": "traefik-seat-v1",
    "routers": routers,
    "middlewares": middlewares,
    "seat_ok": seat_ok,
}
report.write_text(json.dumps(out, separators=(",", ":")) + "\n")
PY
}
emit_m
EOF
chmod +x /app/deck/emit_m.sh

/bin/bash /app/ops/run_traefik_seat.sh
/bin/bash /app/ops/run_traefik_seat.sh
