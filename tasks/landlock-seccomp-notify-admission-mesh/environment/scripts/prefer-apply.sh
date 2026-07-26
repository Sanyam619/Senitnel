#!/bin/bash
# Rematerialize surface seating / notify stubs while prefer still binds live surface.
set -euo pipefail

PREF=/app/ops/prefer.toml
ROOT=""
BIND=""
if [[ -f "$PREF" ]]; then
  ROOT=$(awk -F= '/^root/{gsub(/[" ]/,"",$2); print $2}' "$PREF")
  BIND=$(awk -F= '/^bind/{gsub(/[" ]/,"",$2); print $2}' "$PREF")
fi

if [[ "$ROOT" == "durable" && "$BIND" == "authority" ]]; then
  exit 0
fi

WIN=/app/data/revoke/window.toml
SURF_BIND=/app/data/surface/binder.toml
LO=$(awk -F= '/^lo/{gsub(/ /,"",$2); print $2}' "$WIN")
HI=$(awk -F= '/^hi/{gsub(/ /,"",$2); print $2}' "$WIN")
MODE=$(awk -F= '/^mode/{gsub(/[" ]/,"",$2); print $2}' "$SURF_BIND")
ALLOW=$(awk -F= '/^allow/{gsub(/[" ]/,"",$2); print $2}' "$SURF_BIND")

cat > /app/qx/internal/band_k.go <<BAND
package internal

var BandLo int64 = ${LO:-0}

var BandHi int64 = ${HI:-99}
BAND

cat > /app/qx/internal/seat_k.go <<SEAT
package internal

var SeatMode = "${MODE:-live}"

var SeatAllow = "${ALLOW:-/data/}"
SEAT

cp /app/data/surface/stubs_mat_q.c /app/rz/mat_q.c
cp /app/data/surface/stubs_knit_m.c /app/rz/knit_m.c
