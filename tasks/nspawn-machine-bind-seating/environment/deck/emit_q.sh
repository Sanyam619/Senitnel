#!/bin/bash
emit_q() {
  set -euo pipefail

  OUT="${SEAT_OUT:-/output/nspawn-seat.json}"
  ROSTER="${ROSTER:-/etc/systemd/nspawn/roster.list}"
  STATE="${MACH_ROOT:-/var/lib/machines}/state"
  EFF="${EFF_POLICY:-/etc/systemd/nspawn/effective.conf}"
  NSP="/etc/systemd/nspawn"

  mkdir -p "$(dirname "$OUT")"

  python3 - "$OUT" "$ROSTER" "$STATE" "$EFF" "$NSP" <<'PY'
import json
import sys
from pathlib import Path

out, roster, state, eff, nsp = map(Path, sys.argv[1:])
names = [
    ln.strip()
    for ln in roster.read_text().splitlines()
    if ln.strip() and not ln.strip().startswith("#")
]
abort = "none"
if eff.exists():
    for line in eff.read_text().splitlines():
        line = line.strip()
        if line.startswith("abort="):
            abort = line.split("=", 1)[1]

machines = []
for name in names:
    gen_p = state / f"pub_{name}.gen"
    gen = int(gen_p.read_text().strip()) if gen_p.exists() else 0
    elig_p = state / f"elig_{name}"
    elig = elig_p.read_text().strip() == "1" if elig_p.exists() else False
    root_p = state / f"root_{name}"
    root = root_p.read_text().strip() if root_p.exists() else f"/var/lib/machines/live/{name}/root"
    bind = []
    unit = nsp / f"{name}.nspawn"
    if unit.exists():
        for line in unit.read_text().splitlines():
            line = line.strip()
            if line.startswith("Bind="):
                bind.append(line.split("=", 1)[1])
    active = bool(elig and abort != name)
    machines.append(
        {
            "name": name,
            "root": root,
            "bind": bind,
            "generation": gen,
            "active": active,
        }
    )

ports = []
ports_tsv = state / "ports.tsv"
if ports_tsv.exists():
    for line in ports_tsv.read_text().splitlines():
        parts = line.split("\t")
        if len(parts) >= 3:
            ports.append(
                {
                    "machine": parts[0],
                    "host": int(parts[1]),
                    "container": int(parts[2]),
                }
            )

doc = {
    "schema_tag": "seat-draft",
    "machines": machines,
    "ports": ports,
    "seat_ok": True,
}
out.write_text(json.dumps(doc, indent=2) + "\n")
PY
}
emit_q
