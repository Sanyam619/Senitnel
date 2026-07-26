#!/bin/bash
set -euo pipefail

export SD_ETC="${SD_ETC:-/etc/ceph}"
export SD_VAR="${SD_VAR:-/var/lib/ceph/ops}"
export SD_RUN="${SD_RUN:-/var/run/ceph}"
export SD_REPORT="${SD_REPORT:-/output/crush-seat.json}"

mkdir -p "$SD_ETC/reweight.d" "$SD_ETC/pools.d" "$SD_VAR/state" "$SD_RUN" \
  /output /var/log/ceph

exec 9>"$SD_RUN/seat.lock"
flock 9

/app/ops/kelp_v.sh
/app/ops/gorse_t.sh
/app/lane/moss_q.sh
/app/lane/brome_j.sh
/app/mast/fern_h.sh
/app/mast/vetch_r.sh
/app/deck/tarn_e.sh
/app/deck/sedge_w.sh
