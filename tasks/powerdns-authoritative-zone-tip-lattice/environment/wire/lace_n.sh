#!/bin/bash
set -euo pipefail
# Touches the desk probe stamp for watchdog sweeps.
lace_n() {
  local pd_y="${PD_VAR:-/var/lib/powerdns}"
  mkdir -p "$pd_y/state"
  date +%s >"$pd_y/state/probe.stamp"
}
lace_n
