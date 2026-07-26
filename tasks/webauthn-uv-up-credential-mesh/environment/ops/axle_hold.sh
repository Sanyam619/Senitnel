#!/bin/bash
# axle_hold.sh — seat ledger hold bound into live ceremony state.
set -euo pipefail

mkdir -p /var/lib/ceremony/state
printf 'inclusive\n' >/var/lib/ceremony/state/hold_bound
