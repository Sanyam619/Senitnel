#!/bin/bash
set -euo pipefail

export PF_ETC="${PF_ETC:-/etc/postfix}"
export PF_VAR="${PF_VAR:-/var/lib/postfix}"
export PF_RUN="${PF_RUN:-/var/run/postfix}"
export PF_REPORT="${PF_REPORT:-/output/postfix-seat.json}"

mkdir -p "$PF_ETC/master.d" "$PF_ETC/maps" "$PF_VAR/state" "$PF_RUN" /output /var/log/postfix

exec 9>/var/run/postfix/seat.lock
flock 9

/app/ops/helm_r.sh
/app/ops/axle_n.sh
/app/bag/skim_p.sh
/app/wire/sock_v.sh
/app/wire/knit_q.sh
/app/rim/mesh_k.sh
/app/deck/emit_m.sh
