#!/bin/bash
emit_q() {
  set -euo pipefail

  OUT="${SEAT_OUT:-/output/ldap-seat.json}"
  ROSTER="${ROSTER:-/etc/ldap/roster.list}"
  STATE="${LDAP_ROOT:-/var/lib/ldap}/state"
  EFF="${EFF_POLICY:-/etc/ldap/effective.conf}"
  SURFACE="${SURFACE_URI:-/var/lib/ldap/ops/surface.uri}"

  mkdir -p "$(dirname "$OUT")"

  python3 - "$OUT" "$ROSTER" "$STATE" "$EFF" "$SURFACE" <<'PY'
import json, sys
from pathlib import Path

out, roster, state, eff, surface = map(Path, sys.argv[1:])
names = []
for ln in roster.read_text().splitlines():
    ln = ln.strip()
    if not ln or ln.startswith("#"):
        continue
    parts = ln.split("\t")
    names.append((parts[0], parts[1] if len(parts) > 1 else f"dc={parts[0]},dc=lab"))

prov = surface.read_text().strip() if surface.exists() else "ldap://missing"
if eff.exists():
    for line in eff.read_text().splitlines():
        line = line.strip()
        if line.startswith("providerURI="):
            prov = line.split("=", 1)[1]

consumers = []
for name, suffix in names:
    gen_p = state / f"pub_{name}.gen"
    gen = int(gen_p.read_text().strip()) if gen_p.exists() else 0
    csn_p = state / f"pub_{name}.csn"
    csn = csn_p.read_text().strip() if csn_p.exists() else ""
    elig_p = state / f"elig_{name}"
    elig = elig_p.read_text().strip() == "1" if elig_p.exists() else False
    consumers.append({
        "name": name,
        "provider": prov,
        "contextCSN": csn,
        "generation": gen,
        "bound": elig,
    })

holds = []
holds_tsv = state / "holds.tsv"
if holds_tsv.exists():
    for line in holds_tsv.read_text().splitlines():
        parts = line.split("\t")
        if len(parts) >= 3:
            holds.append({"suffix": parts[1], "until_epoch": int(parts[2])})

doc = {
    "schema_tag": "seat-draft",
    "consumers": consumers,
    "holds": holds,
    "sync_ok": True,
}
out.write_text(json.dumps(doc, indent=2) + "\n")
PY
}
emit_q
