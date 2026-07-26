#!/bin/bash
emit_x() {
  set -euo pipefail

  OUT="${SEAT_OUT:-/output/ipa-seat.json}"
  HOSTS="${HOSTS:-/etc/ipa/hosts.list}"
  SERVICES="${SERVICES:-/etc/ipa/services.list}"
  STATE="${IPA_ROOT:-/var/lib/ipa}/state"
  EFF="${EFF_POLICY:-/etc/ipa/effective.conf}"
  SURFACE="${SURFACE_REALM:-/var/lib/ipa/ops/surface.realm}"

  mkdir -p "$(dirname "$OUT")"

  python3 - "$OUT" "$HOSTS" "$SERVICES" "$STATE" "$EFF" "$SURFACE" <<'PY'
import json, sys
from pathlib import Path

out, hosts, services, state, eff, surface = map(Path, sys.argv[1:])

names = []
for ln in hosts.read_text().splitlines():
    ln = ln.strip()
    if not ln or ln.startswith("#"):
        continue
    parts = ln.split("\t")
    names.append(parts[0])

realm = surface.read_text().strip() if surface.exists() else "MISSING"
if eff.exists():
    for line in eff.read_text().splitlines():
        line = line.strip()
        if line.startswith("realm="):
            realm = line.split("=", 1)[1]

enrolled = {}
host_rows = []
for name in names:
    gen_p = state / f"pub_{name}.gen"
    gen = int(gen_p.read_text().strip()) if gen_p.exists() else 0
    fpr_p = state / f"pub_{name}.fpr"
    fpr = fpr_p.read_text().strip() if fpr_p.exists() else ""
    elig_p = state / f"elig_{name}"
    elig = elig_p.read_text().strip() == "1" if elig_p.exists() else False
    enrolled[name] = elig
    host_rows.append({
        "name": name,
        "realm": realm,
        "keytab": fpr,
        "generation": gen,
        "enrolled": elig,
    })

svc_rows = []
for ln in services.read_text().splitlines():
    ln = ln.strip()
    if not ln or ln.startswith("#"):
        continue
    parts = ln.split("\t")
    principal = parts[0]
    host = parts[1] if len(parts) > 1 else ""
    svc_rows.append({"principal": principal, "bound": enrolled.get(host, False)})

doc = {
    "schema_tag": "seat-draft",
    "hosts": host_rows,
    "services": svc_rows,
    "seat_ok": True,
}
out.write_text(json.dumps(doc, indent=2) + "\n")
PY
}
emit_x
