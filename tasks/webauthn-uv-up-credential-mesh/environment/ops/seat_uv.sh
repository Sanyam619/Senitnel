#!/bin/bash
# seat_uv.sh — seat UV/UP policy into live ceremony state.
set -euo pipefail

mkdir -p /var/lib/ceremony/state
cat >/var/lib/ceremony/state/uv_policy.conf <<'EOF'
fleet_a_uv=0
fleet_a_up=0
fleet_b_uv=0
fleet_b_up=0
EOF
