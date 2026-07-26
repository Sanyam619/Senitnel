#!/bin/bash
# run_ldap_seat.sh — prepare live desk, then publish seating ledger.
set -euo pipefail

mkdir -p /output /var/lib/ldap/state /var/log/ldap /var/run/ldap

exec 9>/var/run/ldap/seat.lock
flock 9

/app/wire/knit_p.sh
/app/ops/axle_y.sh
/app/rim/mesh_x.sh
/app/bag/skim_z.sh
/app/ops/helm_w.sh
/app/bag/note_t.sh
/app/deck/emit_q.sh
