#!/bin/bash
# knit_q — prepare runtime lock dirs only.
set -euo pipefail
mkdir -p /var/run/cluster /var/log/cluster
: >/var/run/cluster/knit.stamp
