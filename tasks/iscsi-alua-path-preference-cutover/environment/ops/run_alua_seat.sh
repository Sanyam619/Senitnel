#!/bin/bash
# run_alua_seat.sh — seat the SAN multipath desk and emit /output/alua-seat.json
set -euo pipefail

APP=/app
mkdir -p /output \
  /var/lib/multipath/ops \
  /var/lib/multipath/candidates \
  /etc/multipath/conf.d

bash "$APP/ops/weld_p.sh"
bash "$APP/ops/stitch_r.sh"
bash "$APP/ops/latch_m.sh"
bash "$APP/ops/graft_k.sh"
bash "$APP/rim/tally_t.sh"
bash "$APP/ops/emit_z.sh"

test -f /output/alua-seat.json
