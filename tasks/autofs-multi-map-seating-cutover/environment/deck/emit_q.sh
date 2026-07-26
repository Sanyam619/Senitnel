#!/bin/bash
emit_q() {
  set -euo pipefail

  OUT="${SEAT_OUT:-/output/autofs-seat.json}"
  ROSTER="${ROSTER:-/etc/autofs/roster.list}"
  STATE="${AUTO_ROOT:-/var/lib/autofs}/state"
  EFF="${EFF_POLICY:-/etc/autofs/effective.conf}"

  mkdir -p "$(dirname "$OUT")"

  python3 - "$OUT" "$ROSTER" "$STATE" "$EFF" <<'PY'
  import json, sys
  from pathlib import Path

  out, roster, state, eff = map(Path, sys.argv[1:])
  names = [ln.strip() for ln in roster.read_text().splitlines() if ln.strip() and not ln.strip().startswith("#")]
  abort = "none"
  if eff.exists():
      for line in eff.read_text().splitlines():
          line = line.strip()
          if line.startswith("abort="):
              abort = line.split("=", 1)[1]

  maps = []
  for name in names:
      gen_p = state / f"pub_{name}.gen"
      gen = int(gen_p.read_text().strip()) if gen_p.exists() else 0
      elig_p = state / f"elig_{name}"
      elig = elig_p.read_text().strip() == "1" if elig_p.exists() else False
      active = elig
      maps.append({
          "name": name,
          "mountpoint": f"/mnt/{name}",
          "generation": gen,
          "source": f"/etc/autofs/maps/{name}.map",
          "active": active,
      })

  holds = []
  holds_tsv = state / "holds.tsv"
  if holds_tsv.exists():
      for line in holds_tsv.read_text().splitlines():
          parts = line.split("\t")
          if len(parts) >= 2:
              holds.append({"key": parts[0], "until_epoch": int(parts[1])})

  doc = {
      "schema_tag": "seat-draft",
      "maps": maps,
      "holds": holds,
      "seating_ok": True,
  }
  out.write_text(json.dumps(doc, indent=2) + "\n")
  PY
}
emit_q
