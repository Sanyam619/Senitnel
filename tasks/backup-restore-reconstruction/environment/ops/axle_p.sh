#!/bin/bash
# axle_p.sh
set -euo pipefail

mkdir -p /var/lib/fleet/state /var/lib/fleet/ops
JOURNAL="${FLEET_JOURNAL:-/var/lib/fleet/ops/journal.jsonl}"

if [[ ! -f "$JOURNAL" ]]; then
  echo "axle_p: missing journal" >&2
  exit 1
fi
line=$(tail -n 1 "$JOURNAL")
mode=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1]).get("mode",""))' "$line")
gen=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1]).get("gen",0))' "$line")
hold=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1]).get("hold",""))' "$line")

printf '%s\n' "$gen" >/var/lib/fleet/state/gen.live
printf '%s\n' "$mode" >/var/lib/fleet/state/attach.intent
printf '%s\n' "$hold" >/var/lib/fleet/state/hold.token
rm -f /var/lib/fleet/state/cutover.ok

if [[ -f /etc/fleet/fleetd.env ]]; then
  grep -v '^HOLD_TOKEN=' /etc/fleet/fleetd.env | grep -v '^PAYLOAD_LINEAGE=' > /tmp/fleetd.env.axle || true
  echo "HOLD_TOKEN=$hold" >> /tmp/fleetd.env.axle
  echo "PAYLOAD_LINEAGE=$mode" >> /tmp/fleetd.env.axle
  mv /tmp/fleetd.env.axle /etc/fleet/fleetd.env
fi
