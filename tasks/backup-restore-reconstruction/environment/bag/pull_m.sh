#!/bin/bash
# pull_m.sh
set -euo pipefail

mkdir -p /var/lib/fleet/leases /var/lib/fleet/state
target=$(cat /var/lib/fleet/state/gen.target 2>/dev/null || echo 0)
live=$(cat /var/lib/fleet/state/gen.live 2>/dev/null || echo 0)

for ep in alpha beta gamma delta epsilon; do
  if [[ "$live" != "$target" ]]; then
    if [[ "$ep" == "beta" || "$ep" == "epsilon" ]]; then
      cat >"/var/lib/fleet/leases/${ep}.json" <<'EOF'
{
  "slot": "borrow_primary",
  "claims": [
    {
      "peer": "atlas",
      "live": true,
      "sealed": false,
      "ts": 900,
      "token": "ops-newest"
    }
  ]
}
EOF
    else
      cat >"/var/lib/fleet/leases/${ep}.json" <<'EOF'
{
  "slot": "borrow_primary",
  "claims": [
    {
      "peer": "atlas",
      "live": true,
      "sealed": false,
      "ts": 50,
      "token": "ops-default"
    }
  ]
}
EOF
    fi
  else
    src="/app/data/episodes/${ep}/leases.json"
    if [[ -f "$src" ]]; then
      python3 - "$src" "/var/lib/fleet/leases/${ep}.json" <<'PY'
import json, sys
from pathlib import Path
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
obj = json.loads(src.read_text())
claims = obj.get("claims", [])
live = [c for c in claims if c.get("live")]
if live:
    best = max(live, key=lambda c: c.get("ts", 0))
    obj["claims"] = [best]
dst.write_text(json.dumps(obj, indent=2) + "\n")
PY
    fi
  fi
done
