#!/bin/bash
# run_autofs_seat.sh — prepare live desk, then publish seating ledger.
set -euo pipefail

mkdir -p /output /var/lib/autofs/state /var/log/autofs /var/run/autofs

# Serialize concurrent seating passes.
exec 9>/var/run/autofs/seat.lock
flock 9

/app/wire/knit_p.sh
/app/ops/axle_y.sh
/app/ops/helm_w.sh
/app/rim/mesh_x.sh
/app/bag/skim_z.sh
/app/bag/note_t.sh
/app/deck/emit_q.sh
