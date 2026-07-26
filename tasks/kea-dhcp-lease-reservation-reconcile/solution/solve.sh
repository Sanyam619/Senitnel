#!/bin/bash
set -euo pipefail

cd /app

cat >/app/ops/helm_r.sh <<'EOF'
#!/bin/bash
set -euo pipefail
helm_r() {
  local kea_x="${KEA_ETC:-/etc/kea}"
  local kea_y="${KEA_VAR:-/var/lib/kea}"
  local abort_pkg="$kea_y/ops/abort.d/90-local.conf"
  local live_dropin="$kea_x/kea-dhcp4.d/90-local.conf"
  local cutover_receipt="$kea_y/state/cutover.ok"
  local target_gen gen_ok mode_ok need_abort
  target_gen=$(tr -d ' \t\r\n' <"$kea_y/state/gen.target")
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
  local kea_x="${KEA_ETC:-/etc/kea}"
  local kea_y="${KEA_VAR:-/var/lib/kea}"
  local sheet_z="/app/config/site_standard.conf"
  local target_gen
  mkdir -p "$kea_y/state" "$kea_x/kea-dhcp4.d"
  target_gen=$(tr -d ' \t\r\n' <"$kea_y/state/gen.target")
  python3 - <<'PY'
import json, os
from pathlib import Path
var = Path(os.environ.get("KEA_VAR", "/var/lib/kea"))
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
    if row.get("tag") == "tip" and "id" in row:
        tips[str(row["id"])] = int(row["generation"])
if not seal_ok:
    raise SystemExit("axle_n: missing sealed journal row for gen.target")
for sid, gen in tips.items():
    (var / "state" / f"tip_{sid}.gen").write_text(f"{gen}\n")
(var / "state" / "gen.live").write_text(f"{target}\n")
(var / "ops" / "prefer.toml").write_text("pool_root=durable\n")
PY
  cp -f "$sheet_z" "$kea_x/kea-dhcp4.d/90-local.conf"
  {
    echo "gen=${target_gen}"
    echo "mode=seal"
  } >"$kea_y/state/cutover.ok"
}
axle_n
EOF
chmod +x /app/ops/axle_n.sh

cat >/app/rim/mesh_k.sh <<'EOF'
#!/bin/bash
set -euo pipefail
mesh_k() {
  local kea_x="${KEA_ETC:-/etc/kea}"
  local kea_y="${KEA_VAR:-/var/lib/kea}"
  local eff="$kea_y/state/effective.conf"
  local shadow="$kea_y/state/shadowed.ips"
  mkdir -p "$kea_y/state"
  : >"$eff"
  : >"$shadow"
  python3 - <<'PY'
import os
from pathlib import Path

etc = Path(os.environ.get("KEA_ETC", "/etc/kea"))
var = Path(os.environ.get("KEA_VAR", "/var/lib/kea"))
eff = var / "state" / "effective.conf"
shadow = var / "state" / "shadowed.ips"

kv: dict[str, str] = {}
seen_hw: dict[str, str] = {}
shadowed: list[str] = []

files = sorted((etc / "kea-dhcp4.d").glob("*.conf"))
for f in files:
    for raw in f.read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip()
        if k.startswith("reserve."):
            hw = k[len("reserve."):]
            ip = v.split(":", 1)[0]
            if hw in seen_hw and seen_hw[hw] != ip:
                shadowed.append(seen_hw[hw])
            seen_hw[hw] = ip
        kv[k] = v

eff.write_text("".join(f"{k}={kv[k]}\n" for k in sorted(kv)))
shadow.write_text("\n".join(shadowed) + ("\n" if shadowed else ""))
PY
}
mesh_k
EOF
chmod +x /app/rim/mesh_k.sh

cat >/app/bag/skim_p.sh <<'EOF'
#!/bin/bash
set -euo pipefail
skim_p() {
  local kea_y="${KEA_VAR:-/var/lib/kea}"
  local out="$kea_y/state/lease_hits.tsv"
  mkdir -p "$kea_y/state"
  python3 - <<'PY'
import os
from pathlib import Path

var = Path(os.environ.get("KEA_VAR", "/var/lib/kea"))
mem = var / "ops" / "memfile.csv"
out = var / "state" / "lease_hits.tsv"
rows = []
if mem.exists():
    for i, line in enumerate(mem.read_text().splitlines()):
        if i == 0 and line.lower().startswith("ip,"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 3:
            continue
        ip, hw, state = parts[0], parts[1].lower(), parts[2].lower()
        if state == "active":
            rows.append(f"{ip}\t{hw}")
out.write_text("\n".join(rows) + ("\n" if rows else ""))
PY
}
skim_p
EOF
chmod +x /app/bag/skim_p.sh

cat >/app/wire/bind_v.sh <<'EOF'
#!/bin/bash
set -euo pipefail
bind_v() {
  local kea_x="${KEA_ETC:-/etc/kea}"
  local kea_y="${KEA_VAR:-/var/lib/kea}"
  local kea_z="${KEA_RUN:-/var/run/kea}"
  mkdir -p "$kea_z" "$kea_y/state/pool_ok"
  rm -f "$kea_y/state/pool_ok"/*
  python3 - <<'PY'
import os
from pathlib import Path

etc = Path(os.environ.get("KEA_ETC", "/etc/kea"))
var = Path(os.environ.get("KEA_VAR", "/var/lib/kea"))
run = Path(os.environ.get("KEA_RUN", "/var/run/kea"))
prefer = {}
for line in (var / "ops" / "prefer.toml").read_text().splitlines():
    line = line.split("#", 1)[0].strip()
    if not line or "=" not in line:
        continue
    k, v = line.split("=", 1)
    prefer[k.strip()] = v.strip()
root = prefer.get("pool_root", "live")
roster = [ln.strip() for ln in (etc / "roster.list").read_text().splitlines() if ln.strip()]
pool_dir = var / "pools" if root == "durable" else etc / "pools"
ok_dir = var / "state" / "pool_ok"
ok_dir.mkdir(parents=True, exist_ok=True)
for sid in roster:
    src = pool_dir / f"{sid}.pool"
    cidr = src.read_text().strip() if src.exists() else ""
    (ok_dir / f"{sid}.cidr").write_text(cidr + "\n")
(run / "prefer.applied").write_text("1\n" if root == "durable" else "0\n")
PY
}
bind_v
EOF
chmod +x /app/wire/bind_v.sh

cat >/app/deck/emit_m.sh <<'EOF'
#!/bin/bash
set -euo pipefail
emit_m() {
  local out_path="${KEA_REPORT:-/output/dhcp-seat.json}"
  mkdir -p "$(dirname "$out_path")"
  python3 - <<'PY'
import json
import os
from pathlib import Path

etc = Path(os.environ.get("KEA_ETC", "/etc/kea"))
var = Path(os.environ.get("KEA_VAR", "/var/lib/kea"))
run = Path(os.environ.get("KEA_RUN", "/var/run/kea"))
report = Path(os.environ.get("KEA_REPORT", "/output/dhcp-seat.json"))
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


def in_cidr(ip: str, cidr: str) -> bool:
    try:
        addr = tuple(int(x) for x in ip.split("."))
        net_s, pref_s = cidr.split("/", 1)
        net = tuple(int(x) for x in net_s.split("."))
        pref = int(pref_s)
    except ValueError:
        return False
    if len(addr) != 4 or len(net) != 4 or not 0 <= pref <= 32:
        return False
    a = (addr[0] << 24) | (addr[1] << 16) | (addr[2] << 8) | addr[3]
    n = (net[0] << 24) | (net[1] << 16) | (net[2] << 8) | net[3]
    mask = (0xFFFFFFFF << (32 - pref)) & 0xFFFFFFFF if pref else 0
    return (a & mask) == (n & mask)


roster = [ln.strip() for ln in (etc / "roster.list").read_text().splitlines() if ln.strip()]
eff = parse_kv((var / "state" / "effective.conf").read_text())
std_kv = parse_kv(std.read_text())
shadowed = {
    ln.strip()
    for ln in (var / "state" / "shadowed.ips").read_text().splitlines()
    if ln.strip()
}
leases: dict[str, str] = {}
hits = var / "state" / "lease_hits.tsv"
if hits.exists():
    for line in hits.read_text().splitlines():
        if not line.strip():
            continue
        ip, hw = line.split("\t", 1)
        leases[ip] = hw.lower()

subnets = []
for sid in roster:
    gen = int((var / "state" / f"tip_{sid}.gen").read_text().strip())
    cidr = (var / "state" / "pool_ok" / f"{sid}.cidr").read_text().strip()
    subnets.append({"id": int(sid), "pool": cidr, "generation": gen})

# Folded reservations in stable hw order from effective.conf
reserves = []
for k, v in sorted(eff.items()):
    if not k.startswith("reserve."):
        continue
    hw = k[len("reserve.") :]
    ip, sid_s = v.split(":", 1)
    reserves.append({"hw": hw, "ip": ip, "subnet": int(sid_s)})

# Duplicate IP detection
ip_counts: dict[str, int] = {}
for r in reserves:
    ip_counts[r["ip"]] = ip_counts.get(r["ip"], 0) + 1

floors = {
    sid: int((var / "floors" / f"{sid}.floor").read_text().strip()) for sid in roster
}
pools = {
    sid: (var / "state" / "pool_ok" / f"{sid}.cidr").read_text().strip() for sid in roster
}
gens = {sid: int((var / "state" / f"tip_{sid}.gen").read_text().strip()) for sid in roster}

conflicts: list[dict] = []
seen_conflict: set[tuple[str, str]] = set()


def add_conflict(ip: str, reason: str) -> None:
    key = (ip, reason)
    if key in seen_conflict:
        return
    seen_conflict.add(key)
    conflicts.append({"ip": ip, "reason": reason})


reservations = []
for r in reserves:
    sid = str(r["subnet"])
    honored = True
    if r["ip"] in shadowed:
        honored = False
        add_conflict(r["ip"], "shadowed")
    if ip_counts.get(r["ip"], 0) > 1:
        honored = False
        add_conflict(r["ip"], "duplicate_ip")
    if r["ip"] in leases and leases[r["ip"]] != r["hw"].lower():
        honored = False
        add_conflict(r["ip"], "lease_collision")
    if gens.get(sid, 0) < floors.get(sid, 0):
        honored = False
        add_conflict(r["ip"], "generation_floor")
    cidr = pools.get(sid, "")
    if not cidr or not in_cidr(r["ip"], cidr):
        honored = False
        add_conflict(r["ip"], "pool_miss")
    # Shadowed earlier IP may not be a current reservation row; still listed via shadowed set
    reservations.append(
        {
            "hw": r["hw"],
            "ip": r["ip"],
            "subnet": r["subnet"],
            "honored": honored,
        }
    )

for ip in sorted(shadowed):
    # Ensure shadowed IPs that are no longer the active reserve still conflict
    if not any(c["ip"] == ip and c["reason"] == "shadowed" for c in conflicts):
        add_conflict(ip, "shadowed")

ok = True
prefer_ok = (run / "prefer.applied").exists() and (run / "prefer.applied").read_text().strip() == "1"
if not prefer_ok:
    ok = False

live_local = etc / "kea-dhcp4.d" / "90-local.conf"
if not live_local.exists():
    ok = False
else:
    live_kv = parse_kv(live_local.read_text())
    for key in ("tip_policy", "bind_order"):
        if live_kv.get(key) != std_kv.get(key):
            ok = False
    for k, v in std_kv.items():
        if k.startswith("reserve.") and live_kv.get(k) != v:
            ok = False

abort_pkg = var / "ops" / "abort.d" / "90-local.conf"
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

# Expected honor matrix must match recomputation
if any(r["honored"] for r in reservations if ip_counts.get(r["ip"], 0) > 1):
    ok = False
if not any(r["honored"] for r in reservations):
    ok = False
if not any(not r["honored"] for r in reservations):
    ok = False

# Durable pools must be present in subnet rows
for s in subnets:
    durable = (var / "pools" / f"{s['id']}.pool").read_text().strip()
    if s["pool"] != durable:
        ok = False

out = {
    "schema_tag": "dhcp-seat-v1",
    "subnets": subnets,
    "reservations": reservations,
    "conflicts": sorted(conflicts, key=lambda c: (c["ip"], c["reason"])),
    "seat_ok": bool(ok and prefer_ok),
}
report.write_text(json.dumps(out, separators=(",", ":"), sort_keys=False) + "\n")
PY
}
emit_m
EOF
chmod +x /app/deck/emit_m.sh

/app/ops/run_dhcp_seat.sh
/app/ops/run_dhcp_seat.sh
