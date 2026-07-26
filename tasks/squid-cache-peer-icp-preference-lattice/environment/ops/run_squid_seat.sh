#!/bin/bash
set -euo pipefail

export SQ_ETC="${SQ_ETC:-/etc/squid}"
export SQ_VAR="${SQ_VAR:-/var/lib/squid}"
export SQ_RUN="${SQ_RUN:-/var/run/squid}"
export SQ_REPORT="${SQ_REPORT:-/output/squid-seat.json}"

mkdir -p "$SQ_ETC/conf.d" "$SQ_ETC/peers.d" "$SQ_VAR/state" "$SQ_RUN" /output /var/log/squid

exec 9>/var/run/squid/seat.lock
flock 9

/app/ops/helm_r.sh
/app/ops/axle_n.sh
/app/rim/mesh_k.sh
/app/bag/skim_p.sh
/app/wire/sock_v.sh
/app/wire/knit_q.sh
/app/deck/emit_m.sh
