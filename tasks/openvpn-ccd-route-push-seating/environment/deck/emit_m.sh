#!/bin/bash
set -euo pipefail
emit_m() {
  local report="${OV_REPORT:-/output/ovpn-seat.json}"
  mkdir -p "$(dirname "$report")"
  python3 - <<'PY'
import json, os, re
from pathlib import Path

etc = Path(os.environ.get("OV_ETC", "/etc/openvpn"))
var = Path(os.environ.get("OV_VAR", "/var/lib/openvpn"))
report = Path(os.environ.get("OV_REPORT", "/output/ovpn-seat.json"))
site = Path("/app/config/site_standard.conf")
roster = [ln.strip() for ln in (etc / "server" / "roster.list").read_text().splitlines() if ln.strip()]
admitted = {ln.strip() for ln in (var / "state" / "admit.set").read_text().splitlines() if ln.strip()} if (var / "state" / "admit.set").exists() else set()
aborted = {ln.strip() for ln in (var / "state" / "abort.set").read_text().splitlines() if ln.strip()} if (var / "state" / "abort.set").exists() else set()
pushed_set = {ln.strip() for ln in (var / "state" / "pushed.set").read_text().splitlines() if ln.strip()} if (var / "state" / "pushed.set").exists() else set()

def parse_kv(text: str) -> dict[str, str]:
    out = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out

def prefer_mode() -> str:
    pref = var / "ops" / "prefer.toml"
    if not pref.exists():
        return "live"
    m = re.search(r'^mode\s*=\s*"?([A-Za-z_]+)"?', pref.read_text(), re.M)
    return m.group(1) if m else "live"

def ccd_iroute(cn: str) -> str:
    path = etc / "ccd" / cn
    if not path.exists():
        return ""
    for raw in path.read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if line.startswith("iroute "):
            return line.split(None, 1)[1].strip()
    return ""

site_kv = parse_kv(site.read_text())
live_path = etc / "server" / "conf.d" / "90-local.conf"
live_kv = parse_kv(live_path.read_text()) if live_path.exists() else {}
abort_kv = parse_kv((var / "ops" / "abort.d" / "90-local.conf").read_text())
mode = prefer_mode()
target = (var / "state" / "gen.target").read_text().strip()
bind = parse_kv((var / "ops" / "tip_bind.accept").read_text()) if (var / "ops" / "tip_bind.accept").exists() else {}
bind_ok = bind.get("gen") == target

clients = []
matrix_ok = True
for cn in roster:
    tip_iroute = var / "state" / f"tip_{cn}.iroute"
    tip_gen = var / "state" / f"tip_{cn}.gen"
    if not (tip_iroute.exists() and tip_gen.exists()):
        matrix_ok = False
        clients.append({"cn": cn, "iroute": "0.0.0.0/32", "generation": 0, "pushed": False})
        continue
    iroute = tip_iroute.read_text().strip()
    gen = int(tip_gen.read_text().strip())
    floor = int((var / "floors" / f"{cn}.floor").read_text().strip())
    sheet_iroute = ccd_iroute(cn)
    expect_push = (
        cn in admitted
        and cn not in aborted
        and gen >= floor
        and sheet_iroute == iroute
    )
    pushed = cn in pushed_set
    if pushed != expect_push:
        matrix_ok = False
    if sheet_iroute != iroute:
        matrix_ok = False
    clients.append({
        "cn": cn,
        "iroute": iroute,
        "generation": gen,
        "pushed": pushed,
    })

pools = []
pool_ok = True
prefer_active = 0
for raw in (var / "state" / "pools.active").read_text().splitlines() if (var / "state" / "pools.active").exists() else []:
    if not raw.strip():
        continue
    name, cidr, flag = raw.strip().split("|", 2)
    active = flag == "1"
    if active:
        prefer_active += 1
    pools.append({"name": name, "cidr": cidr, "active": active})
if mode in {"durable", "authority"}:
    by_name = {p["name"]: p for p in pools}
    if not by_name.get("core", {}).get("active"):
        pool_ok = False
    if by_name.get("edge", {}).get("active"):
        pool_ok = False
    if by_name.get("lab", {}).get("active"):
        pool_ok = False
else:
    pool_ok = False

site_tokens_ok = all(live_kv.get(k) == v for k, v in site_kv.items())
abort_forensic = (
    abort_kv.get("pool_policy") == "prefer_abort"
    and "onyx" in abort_kv.get("abort", "")
)
receipt = var / "state" / "cutover.ok"
live_gen = (var / "state" / "gen.live").read_text().strip() if (var / "state" / "gen.live").exists() else ""
receipt_ok = False
if receipt.exists():
    rkv = parse_kv(receipt.read_text())
    receipt_ok = rkv.get("gen") == target and rkv.get("mode") == "seal"
live_dropin_present = live_path.is_file() and bool(live_path.read_text().strip())
prefer_ok = mode in {"durable", "authority"}

seat_ok = (
    matrix_ok
    and pool_ok
    and site_tokens_ok
    and abort_forensic
    and receipt_ok
    and live_dropin_present
    and live_gen == target
    and live_kv.get("pool_policy") != "prefer_abort"
    and prefer_ok
    and bind_ok
)

out = {
    "schema_tag": "ovpn-seat-v1",
    "clients": clients,
    "pools": pools,
    "seat_ok": seat_ok,
}
report.write_text(json.dumps(out, separators=(",", ":")) + "\n")
PY
}
emit_m
