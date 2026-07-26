#!/bin/bash
# latch_m — hold window
set -euo pipefail

mkdir -p /var/lib/multipath/ops
echo 'held = []' > /var/lib/multipath/ops/holds.active
