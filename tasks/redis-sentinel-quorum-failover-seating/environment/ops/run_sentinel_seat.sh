#!/bin/bash
# run_sentinel_seat.sh — prepare the live desk, then publish the seating ledger.
set -euo pipefail

mkdir -p /output /var/lib/redis/state /var/lib/redis/ops/state \
  /var/log/redis /var/run/redis

exec 9>/var/run/redis/seat.lock
flock 9

/app/wire/dune_p.sh
/app/ops/helm_r.sh
/app/ops/axle_n.sh
/app/rim/mesh_k.sh
/app/bag/skim_p.sh
/app/bag/sock_v.sh
/app/bag/note_c.sh
/app/deck/slate_j.sh
