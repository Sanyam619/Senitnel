#!/bin/bash
set -euo pipefail
emit_m() {
  local report="${SQ_REPORT:-/output/squid-seat.json}"
  mkdir -p "$(dirname "$report")"
  python3 - <<'PY'
import json, os, re
from pathlib import Path

etc = Path(os.environ.get("SQ_ETC", "/etc/squid"))
var = Path(os.environ.get("SQ_VAR", "/var/lib/squid"))
report = Path(os.environ.get("SQ_REPORT", "/output/squid-seat.json"))
site = Path("/app/config/site_standard.conf")
roster = [ln.strip() for ln in (etc / "roster.list").read_text().splitlines() if ln.strip()]
admitted = {ln.strip() for ln in (var / "state" / "admit.set").read_text().splitlines() if ln.strip()} if (var / "state" / "admit.set").exists() else set()
aborted = {ln.strip() for ln in (var / "state" / "abort.set").read_text().splitlines() if ln.strip()} if (var / "state" / "abort.set").exists() else set()
selected_set = {ln.strip() for ln in (var / "state" / "selected.set").read_text().splitlines() if ln.strip()} if (var / "state" / "selected.set").exists() else set()

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

site_kv = parse_kv(site.read_text())
live_path = etc / "conf.d" / "90-local.cfg"
live_kv = parse_kv(live_path.read_text()) if live_path.exists() else {}
abort_kv = parse_kv((var / "ops" / "abort.d" / "90-local.cfg").read_text())
acl_fold = parse_kv((var / "state" / "acl.fold").read_text()) if (var / "state" / "acl.fold").exists() else {}
mode = prefer_mode()
target = (var / "state" / "gen.target").read_text().strip()
bind = parse_kv((var / "ops" / "tip_bind.accept").read_text()) if (var / "ops" / "tip_bind.accept").exists() else {}
bind_ok = bind.get("gen") == target

peers = []
matrix_ok = True
for name in roster:
    tip_type = var / "state" / f"tip_{name}.type"
    tip_weight = var / "state" / f"tip_{name}.weight"
    tip_gen = var / "state" / f"tip_{name}.gen"
    if not (tip_type.exists() and tip_weight.exists() and tip_gen.exists()):
        matrix_ok = False
        peers.append({
            "name": name,
            "host": "0.0.0.0",
            "type": "sibling",
            "weight": 0,
            "generation": 0,
            "selected": False,
        })
        continue
    typ = tip_type.read_text().strip()
    weight = int(tip_weight.read_text().strip())
    gen = int(tip_gen.read_text().strip())
    floor = int((var / "floors" / f"{name}.floor").read_text().strip())
    host = (var / "peers" / f"{name}.host").read_text().strip()
    sheet_path = etc / "peers.d" / f"{name}.peer"
    sheet = parse_kv(sheet_path.read_text()) if sheet_path.exists() else {}
    expect_sel = (
        name in admitted
        and name not in aborted
        and gen >= floor
        and sheet.get("type") == typ
        and int(sheet.get("weight", "-1")) == weight
        and sheet.get("host") == host
    )
    selected = name in selected_set
    if selected != expect_sel:
        matrix_ok = False
    if sheet.get("type") != typ or int(sheet.get("weight", "-1")) != weight or sheet.get("host") != host:
        matrix_ok = False
    peers.append({
        "name": name,
        "host": host,
        "type": typ,
        "weight": weight,
        "generation": gen,
        "selected": selected,
    })

acls = []
for key in sorted({k for k in list(acl_fold) + [k.split(".",1)[1] for k in site_kv if k.startswith("acl.")]}):
    raw = acl_fold.get(key, site_kv.get(f"acl.{key}", "skip"))
    acls.append({"name": key, "matched": raw == "match"})

site_tokens_ok = all(live_kv.get(k) == v for k, v in site_kv.items())
abort_forensic = (
    abort_kv.get("tip_policy") == "prefer_abort"
    and abort_kv.get("weight.core") == "999"
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
    and site_tokens_ok
    and abort_forensic
    and receipt_ok
    and live_dropin_present
    and live_gen == target
    and live_kv.get("tip_policy") != "prefer_abort"
    and prefer_ok
    and bind_ok
)

out = {
    "schema_tag": "squid-seat-v1",
    "peers": peers,
    "acls": acls,
    "seat_ok": seat_ok,
}
report.write_text(json.dumps(out, separators=(",", ":")) + "\n")
PY
}
emit_m
