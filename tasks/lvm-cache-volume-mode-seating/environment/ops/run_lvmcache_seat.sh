#!/bin/bash
# run_lvmcache_seat.sh — prepare the live desk, then publish the seating ledger.
set -euo pipefail

mkdir -p /output /var/lib/lvm/state /var/lib/lvm/ops/state /var/log/lvm /var/run/lvm

# Serialize concurrent seating passes.
exec 9>/var/run/lvm/seat.lock
flock 9

/app/wire/knit_s.sh
/app/ops/kelp_n.sh
/app/ops/axle_r.sh
/app/rim/mesh_p.sh
/app/bag/skim_w.sh
/app/bag/note_c.sh
/app/deck/emit_j.sh
