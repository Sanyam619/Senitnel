#!/bin/bash
# run_time_seat.sh — seat the time desk and emit /output/time-seat.json
set -euo pipefail

APP=/app
mkdir -p /output /var/lib/time/ops /var/lib/chrony \
  /etc/chrony/sources.d /etc/systemd/timesyncd.conf.d

bash "$APP/ops/axle_p.sh"
bash "$APP/ops/knit_w.sh"
bash "$APP/ops/pull_m.sh"
bash "$APP/ops/bind_v.sh"
bash "$APP/rim/mark_t.sh"
bash "$APP/ops/emit_q.sh"

test -f /output/time-seat.json
