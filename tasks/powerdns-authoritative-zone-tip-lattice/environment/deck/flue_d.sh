#!/bin/bash
set -euo pipefail
flue_d() {
  local report="${PD_REPORT:-/output/pdns-seat.json}"
  mkdir -p "$(dirname "$report")"
  python3 - <<'PY'
import json
import os
import re
from pathlib import Path

etc = Path(os.environ.get("PD_ETC", "/etc/powerdns"))
var = Path(os.environ.get("PD_VAR", "/var/lib/powerdns"))
report = Path(os.environ.get("PD_REPORT", "/output/pdns-seat.json"))
site = Path("/app/config/site_standard.conf")
roster = [ln.strip() for ln in (etc / "zone.roster").read_text().splitlines() if ln.strip()]


def parse_kv(text: str) -> dict[str, str]:
    out = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def read_set(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {ln.strip() for ln in path.read_text().splitlines() if ln.strip()}


def prefer_mode() -> str:
    pref = var / "ops" / "prefer.toml"
    if not pref.exists():
        return "live"
    m = re.search(r'^mode\s*=\s*"?([A-Za-z_]+)"?', pref.read_text(), re.M)
    return m.group(1) if m else "live"


def rec_sheet(name: str) -> dict[tuple[str, str], str]:
    sheet = etc / "zones.d" / f"{name}.rec"
    out: dict[tuple[str, str], str] = {}
    if not sheet.exists():
        return out
    for raw in sheet.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("@"):
            continue
        parts = line.split(None, 2)
        if len(parts) < 3:
            continue
        out[(parts[0], parts[1])] = parts[2]
    return out


site_kv = parse_kv(site.read_text())
live_path = etc / "pdns.d" / "90-local.conf"
live_kv = parse_kv(live_path.read_text()) if live_path.exists() else {}
abort_kv = parse_kv((var / "ops" / "abort.d" / "90-local.conf").read_text())
mode = prefer_mode()
target = (var / "state" / "gen.target").read_text().strip()
bind_path = var / "ops" / "tip_bind.accept"
bind = parse_kv(bind_path.read_text()) if bind_path.exists() else {}
bind_ok = bind.get("gen") == target

retired = set()
retired_path = var / "ops" / "retired_stores.jsonl"
if retired_path.exists():
    for line in retired_path.read_text().splitlines():
        if line.strip():
            retired.add(str(json.loads(line).get("store", "")))
sel_path = var / "state" / "store.sel"
store_sel = sel_path.read_text().strip() if sel_path.exists() else ""
store_ok = bool(store_sel) and store_sel not in retired

aborted = read_set(var / "state" / "abort.set")
publish = read_set(var / "state" / "publish.set")
honor = read_set(var / "state" / "honor.set")

holds: dict[tuple[str, str, str], str] = {}
holds_path = var / "ops" / "holds.jsonl"
if holds_path.exists():
    for line in holds_path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        holds[(row["zone"], row["name"], row["type"])] = row["content"]

zones = []
records = []
matrix_ok = True
for name in roster:
    serial_p = var / "state" / f"tip_{name}.serial"
    gen_p = var / "state" / f"tip_{name}.gen"
    serial = int(serial_p.read_text().strip()) if serial_p.exists() else 0
    gen = int(gen_p.read_text().strip()) if gen_p.exists() else 0
    if not (serial_p.exists() and gen_p.exists()):
        matrix_ok = False
    floor = int((var / "floors" / f"{name}.floor").read_text().strip())
    live_serial_p = etc / "serials" / f"{name}.serial"
    live_serial = live_serial_p.read_text().strip() if live_serial_p.exists() else ""
    store_p = etc / "zones.d" / f"{name}.store"
    live_store = store_p.read_text().strip() if store_p.exists() else ""
    expect_pub = (
        serial > 0
        and live_serial == str(serial)
        and gen >= floor
        and store_ok
        and live_store == store_sel
        and name not in aborted
    )
    published = name in publish
    if published != expect_pub:
        matrix_ok = False
    if live_store != store_sel:
        matrix_ok = False
    zones.append(
        {
            "name": name,
            "serial": serial,
            "backend": live_store,
            "generation": gen,
            "published": published,
        }
    )
    tip_rec_p = var / "state" / f"tip_{name}.records"
    if not tip_rec_p.exists():
        matrix_ok = False
        continue
    sheet = rec_sheet(name)
    for row in json.loads(tip_rec_p.read_text()):
        rname, rtype, tip_content = row["name"], row["type"], row["content"]
        held = holds.get((name, rname, rtype))
        expected_content = held if held is not None else tip_content
        live_content = sheet.get((rname, rtype), "")
        honored_flag = f"{name}|{rname}|{rtype}" in honor
        expect_honored = bool(live_content) and live_content == tip_content
        if honored_flag != expect_honored:
            matrix_ok = False
        if live_content != expected_content:
            matrix_ok = False
        records.append(
            {
                "zone": name,
                "name": rname,
                "type": rtype,
                "content": live_content,
                "honored": honored_flag,
            }
        )

site_tokens_ok = all(live_kv.get(k) == v for k, v in site_kv.items())
abort_forensic = (
    abort_kv.get("zone_policy") == "prefer_abort"
    and abort_kv.get("serial.crest.example") == "1111111111"
)
receipt = var / "state" / "cutover.ok"
live_gen_p = var / "state" / "gen.live"
live_gen = live_gen_p.read_text().strip() if live_gen_p.exists() else ""
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
    and live_kv.get("zone_policy") != "prefer_abort"
    and prefer_ok
    and bind_ok
    and store_ok
)

out = {
    "schema_tag": "pdns-seat-v1",
    "zones": zones,
    "records": records,
    "seat_ok": seat_ok,
}
report.write_text(json.dumps(out, separators=(",", ":")) + "\n")
PY
}
flue_d
