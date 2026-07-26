#!/bin/bash
set -euo pipefail
emit_m() {
  local report="${PF_REPORT:-/output/postfix-seat.json}"
  mkdir -p "$(dirname "$report")"
  python3 - <<'PY'
import json, os, re
from pathlib import Path

etc = Path(os.environ.get("PF_ETC", "/etc/postfix"))
var = Path(os.environ.get("PF_VAR", "/var/lib/postfix"))
report = Path(os.environ.get("PF_REPORT", "/output/postfix-seat.json"))
site = Path("/app/config/site_standard.conf")
roster = [ln.strip() for ln in (etc / "roster.list").read_text().splitlines() if ln.strip()]
admitted = {ln.strip() for ln in (var / "state" / "admit.set").read_text().splitlines() if ln.strip()} if (var / "state" / "admit.set").exists() else set()
active_set = {ln.strip() for ln in (var / "state" / "active.set").read_text().splitlines() if ln.strip()} if (var / "state" / "active.set").exists() else set()

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

def parse_main(path: Path) -> dict[str, str]:
    out = {}
    if not path.exists():
        return out
    for raw in path.read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out

site_kv = parse_kv(site.read_text())
live_path = etc / "master.d" / "90-local.cf"
live_kv = parse_kv(live_path.read_text()) if live_path.exists() else {}
abort_kv = parse_kv((var / "ops" / "abort.d" / "90-local.cf").read_text())
mode = prefer_mode()
target = (var / "state" / "gen.target").read_text().strip()
bind = parse_kv((var / "ops" / "tip_bind.accept").read_text()) if (var / "ops" / "tip_bind.accept").exists() else {}
bind_ok = bind.get("gen") == target
prefer_map = "hash:/var/lib/postfix/ops/maps/nexthop.prefer"

instances = []
matrix_ok = True
for name in roster:
    tip_queue = var / "state" / f"tip_{name}.queue"
    tip_gen = var / "state" / f"tip_{name}.gen"
    if not (tip_queue.exists() and tip_gen.exists()):
        matrix_ok = False
        instances.append({
            "name": name,
            "queue_dir": "/var/spool/missing",
            "generation": 0,
            "active": False,
        })
        continue
    queue_dir = tip_queue.read_text().strip()
    gen = int(tip_gen.read_text().strip())
    floor = int((var / "floors" / f"{name}.floor").read_text().strip())
    main = parse_main(Path(f"/etc/postfix-{name}/main.cf"))
    live_qd = main.get("queue_directory", "")
    live_tm = main.get("transport_maps", "")
    expect_active = (
        name in admitted
        and gen >= floor
        and live_qd == queue_dir
        and live_tm == prefer_map
        and not queue_dir.endswith("-decoy")
        and not queue_dir.endswith("-surface")
        and not queue_dir.endswith("-wrong")
        and not queue_dir.endswith("-old")
    )
    active = name in active_set
    if active != expect_active:
        matrix_ok = False
    if live_qd != queue_dir or live_tm != prefer_map:
        matrix_ok = False
    instances.append({
        "name": name,
        "queue_dir": queue_dir,
        "generation": gen,
        "active": active,
    })

transports = []
honor_map = {}
if (var / "state" / "honor.set").exists():
    for line in (var / "state" / "honor.set").read_text().splitlines():
        if "=" not in line:
            continue
        p, flag = line.split("=", 1)
        honor_map[p.strip()] = flag.strip() == "1"
fold_ok = True
if (var / "state" / "transport.fold").exists():
    for raw in (var / "state" / "transport.fold").read_text().splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            fold_ok = False
            continue
        pattern, nexthop = parts
        honored = honor_map.get(pattern, True)
        if "decoy" in nexthop or "surface" in nexthop or "bait" in nexthop:
            fold_ok = False
        transports.append({
            "pattern": pattern,
            "nexthop": nexthop,
            "honored": honored,
        })
else:
    fold_ok = False

# collide.lab must be present and unhonored when abort fragment lists it
by_pat = {t["pattern"]: t for t in transports}
if "collide.lab" in by_pat and by_pat["collide.lab"]["honored"] is not False:
    fold_ok = False
if ".example.com" in by_pat and "prefer" not in by_pat[".example.com"]["nexthop"]:
    fold_ok = False

site_tokens_ok = all(live_kv.get(k) == v for k, v in site_kv.items())
abort_forensic = (
    abort_kv.get("mail_policy") == "prefer_abort"
    and "collide.lab" in (var / "ops" / "abort.d" / "90-local.cf").read_text()
)
receipt = var / "state" / "cutover.ok"
live_gen = (var / "state" / "gen.live").read_text().strip() if (var / "state" / "gen.live").exists() else ""
receipt_ok = False
if receipt.exists():
    rkv = parse_kv(receipt.read_text())
    receipt_ok = rkv.get("gen") == target and rkv.get("mode") == "seal"
live_dropin_present = live_path.is_file() and bool(live_path.read_text().strip())
prefer_ok = mode in {"durable", "authority"}
prefer_map_file = (var / "ops" / "maps" / "nexthop.prefer").read_text() if (var / "ops" / "maps" / "nexthop.prefer").exists() else ""
map_ok = "mx.prefer.internal" in prefer_map_file and "mx.surface.decoy" not in prefer_map_file

seat_ok = (
    matrix_ok
    and fold_ok
    and site_tokens_ok
    and abort_forensic
    and receipt_ok
    and live_dropin_present
    and live_gen == target
    and live_kv.get("mail_policy") != "prefer_abort"
    and prefer_ok
    and bind_ok
    and map_ok
)

out = {
    "schema_tag": "postfix-seat-v1",
    "instances": instances,
    "transports": transports,
    "seat_ok": seat_ok,
}
report.write_text(json.dumps(out, separators=(",", ":")) + "\n")
PY
}
emit_m
