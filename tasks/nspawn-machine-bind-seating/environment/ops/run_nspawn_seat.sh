#!/bin/bash
# run_nspawn_seat.sh — prepare live desk, then publish seating ledger.
set -euo pipefail

mkdir -p /output /var/lib/machines/state /var/log/machines /var/run/machines

exec 9>/var/run/machines/seat.lock
flock 9

/app/wire/note_t.sh
/app/ops/axle_k.sh
/app/ops/helm_w.sh
/app/rim/mesh_p.sh
/app/bag/knit_v.sh
/app/bag/skim_z.sh
/app/deck/emit_q.sh
