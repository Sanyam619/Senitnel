#!/bin/bash
set -euo pipefail

export TRF_ETC="${TRF_ETC:-/etc/traefik}"
export TRF_VAR="${TRF_VAR:-/var/lib/traefik}"
export TRF_REPORT="${TRF_REPORT:-/output/traefik-seat.json}"

mkdir -p "$TRF_ETC/dynamic" "$TRF_VAR/ops/state" /output /var/log/traefik /var/run/traefik

exec 9>/var/run/traefik/seat.lock
flock 9

/app/ops/helm_r.sh
/app/ops/axle_n.sh
/app/wire/knit_q.sh
/app/rim/mesh_k.sh
/app/bag/skim_p.sh
/app/deck/emit_m.sh
