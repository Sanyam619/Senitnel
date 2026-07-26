#!/bin/bash
# run_crm_seat.sh — prepare live desk, then publish seating ledger.
set -euo pipefail

mkdir -p /output /var/lib/pacemaker/state /var/lib/cluster/ops/state \
  /var/log/cluster /var/run/cluster

exec 9>/var/run/cluster/seat.lock
flock 9

/app/wire/knit_q.sh
/app/ops/axle_n.sh
/app/ops/helm_r.sh
/app/rim/mesh_k.sh
/app/bag/skim_p.sh
/app/bag/note_u.sh
/app/rim/scan_t.sh
/app/deck/emit_v.sh
