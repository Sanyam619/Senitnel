#!/bin/bash
set -euo pipefail

export HAP_ETC="${HAP_ETC:-/etc/haproxy}"
export HAP_VAR="${HAP_VAR:-/var/lib/haproxy}"
export HAP_RUN="${HAP_RUN:-/var/run/haproxy}"
export HAP_REPORT="${HAP_REPORT:-/output/proxy-seat.json}"

mkdir -p "$HAP_ETC/conf.d" "$HAP_VAR/state" "$HAP_RUN" /output /var/log/haproxy

exec 9>/var/run/haproxy/seat.lock
flock 9

/app/ops/helm_r.sh
/app/ops/axle_n.sh
/app/rim/mesh_k.sh
/app/bag/skim_p.sh
/app/wire/sock_v.sh
/app/deck/emit_m.sh
