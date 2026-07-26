#!/bin/bash
# run_ipa_seat.sh — prepare live client desk, then publish enrollment ledger.
set -euo pipefail

mkdir -p /output /var/lib/ipa/state /var/log/ipa /var/run/ipa

exec 9>/var/run/ipa/seat.lock
flock 9

/app/pre/warp_h.sh
/app/ops/tag_r.sh
/app/ridge/fold_c.sh
/app/span/dom_k.sh
/app/ops/bind_v.sh
/app/span/memo_s.sh
/app/deck/emit_x.sh
