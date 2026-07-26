#!/usr/bin/env bash
set -euo pipefail
/app/ops/fold_u.sh
/app/ops/lease_w.sh
/app/mesh/skim_v.sh
/app/mesh/pref_q.sh
/app/seat/seat_m.sh
/app/arm/arm_h.sh
/app/rim/hold_r.sh
/app/bin/ringfan
/app/bin/preflight
