#!/bin/bash
# Decoy: touches a probe stamp under the runtime dir.
set -euo pipefail
RUN="${KEA_RUN:-/var/run/kea}"
mkdir -p "$RUN"
: >"$RUN/probe.stamp"
