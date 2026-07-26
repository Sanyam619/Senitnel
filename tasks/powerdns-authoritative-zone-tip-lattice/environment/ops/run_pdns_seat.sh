#!/bin/bash
set -euo pipefail

export PD_ETC="${PD_ETC:-/etc/powerdns}"
export PD_VAR="${PD_VAR:-/var/lib/powerdns}"
export PD_RUN="${PD_RUN:-/var/run/powerdns}"
export PD_REPORT="${PD_REPORT:-/output/pdns-seat.json}"

mkdir -p "$PD_ETC/pdns.d" "$PD_ETC/zones.d" "$PD_ETC/serials" \
  "$PD_VAR/state" "$PD_RUN" /output /var/log/powerdns

exec 9>/var/run/powerdns/seat.lock
flock 9

/app/ops/crib_j.sh
/app/ops/lath_p.sh
/app/rig/vane_t.sh
/app/rig/gaff_s.sh
/app/span/moor_w.sh
/app/wire/keel_x.sh
/app/deck/flue_d.sh
