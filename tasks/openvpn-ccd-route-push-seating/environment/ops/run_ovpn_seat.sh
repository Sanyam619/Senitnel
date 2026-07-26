#!/bin/bash
set -euo pipefail

export OV_ETC="${OV_ETC:-/etc/openvpn}"
export OV_VAR="${OV_VAR:-/var/lib/openvpn}"
export OV_RUN="${OV_RUN:-/var/run/openvpn}"
export OV_REPORT="${OV_REPORT:-/output/ovpn-seat.json}"

mkdir -p "$OV_ETC/server/conf.d" "$OV_ETC/ccd" "$OV_VAR/state" "$OV_RUN" /output /var/log/openvpn

exec 9>/var/run/openvpn/seat.lock
flock 9

/app/ops/helm_r.sh
/app/ops/axle_n.sh
/app/rim/mesh_k.sh
/app/bag/skim_p.sh
/app/wire/sock_v.sh
/app/wire/knit_q.sh
/app/deck/emit_m.sh
