#!/bin/bash
# run_gluster_seat.sh — prepare the live desk, then publish the seating ledger.
set -euo pipefail

mkdir -p /output /var/lib/glusterd/state /var/lib/glusterd/ops/state \
  /var/log/gluster /var/run/gluster

exec 9>/var/run/gluster/seat.lock
flock 9

/app/wire/dune_p.sh
/app/ops/reef_t.sh
/app/ops/barn_w.sh
/app/rim/clay_m.sh
/app/bag/flint_k.sh
/app/bag/peat_x.sh
/app/bag/note_c.sh
/app/deck/slate_j.sh
