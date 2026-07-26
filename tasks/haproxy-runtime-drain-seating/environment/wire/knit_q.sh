#!/bin/bash
# Decoy: touches a probe stamp under the runtime dir.
set -euo pipefail
RUN="${HAP_RUN:-/var/run/haproxy}"
mkdir -p "$RUN"
: >"$RUN/probe.stamp"
