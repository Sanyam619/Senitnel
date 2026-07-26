#!/bin/bash
# run_nft_seat.sh — prepare live desk, then publish seating ledger.
set -euo pipefail

mkdir -p /output /var/lib/nft/state /var/log/nft /var/run/nft

exec 9>/var/run/nft/seat.lock
flock 9

/app/wire/knit_p.sh
/app/ops/helm_w.sh
/app/rim/fold_k.sh
/app/ops/pin_m.sh
/app/bag/swap_r.sh
/app/ops/echo_t.sh
/app/bag/note_t.sh
/app/deck/card_w.sh
