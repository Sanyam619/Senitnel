#!/bin/bash
# weave_k.sh
set -euo pipefail

mkdir -p /etc/fleet
cp -f /app/config/reconcile.conf /etc/fleet/reconcile.conf

cat >/etc/fleet/fleetd.env <<'EOF'
PAYLOAD_LINEAGE=decoy
HOLD_TOKEN=lab-tmp
FLEET_VOLUME_ROOT=/var/lib/fleet/volumes
FLEET_RUNTIME_ROOT=/var/lib/fleet/runtime
EOF
