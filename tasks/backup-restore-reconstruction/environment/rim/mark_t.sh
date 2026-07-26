#!/bin/bash
# mark_t.sh
set -euo pipefail

mkdir -p /var/run/fleet/gate /var/lib/fleet/state
target=$(cat /var/lib/fleet/state/gen.target 2>/dev/null || echo 0)
live=$(cat /var/lib/fleet/state/gen.live 2>/dev/null || echo 0)

rm -rf /var/run/fleet/gate/*
mkdir -p /var/run/fleet/gate/epsilon /var/run/fleet/gate/beta /var/run/fleet/gate/alpha

if [[ "$live" != "$target" ]]; then
  touch /var/run/fleet/gate/epsilon/cinder
  touch /var/run/fleet/gate/epsilon/mesa
  touch /var/run/fleet/gate/beta/ridge
  touch /var/run/fleet/gate/alpha/mesa
  exit 0
fi

for ep in alpha beta gamma delta epsilon; do
  mkdir -p "/var/run/fleet/gate/${ep}"
  qfile="/app/data/episodes/${ep}/quarantine.json"
  [[ -f "$qfile" ]] || continue
  python3 - "$qfile" "/var/run/fleet/gate/${ep}" <<'PY'
import json, sys
from pathlib import Path
qpath, gdir = Path(sys.argv[1]), Path(sys.argv[2])
peers = json.loads(qpath.read_text()).get("peers", {})
for peer, flagged in peers.items():
    if not flagged:
        (gdir / peer).write_text("")
PY
done
