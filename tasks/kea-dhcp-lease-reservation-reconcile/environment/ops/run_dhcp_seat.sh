#!/bin/bash
set -euo pipefail

export KEA_ETC="${KEA_ETC:-/etc/kea}"
export KEA_VAR="${KEA_VAR:-/var/lib/kea}"
export KEA_RUN="${KEA_RUN:-/var/run/kea}"
export KEA_REPORT="${KEA_REPORT:-/output/dhcp-seat.json}"

mkdir -p "$KEA_ETC/kea-dhcp4.d" "$KEA_VAR/state" "$KEA_RUN" /output /var/log/kea

exec 9>/var/run/kea/seat.lock
flock 9

/app/ops/helm_r.sh
/app/ops/axle_n.sh
/app/rim/mesh_k.sh
/app/bag/skim_p.sh
/app/wire/bind_v.sh
/app/deck/emit_m.sh
