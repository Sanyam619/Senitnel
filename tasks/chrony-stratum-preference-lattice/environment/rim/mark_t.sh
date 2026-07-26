#!/bin/bash
# mark_t — offset budget
set -euo pipefail
mkdir -p /var/lib/time/ops
echo 0.5 > /var/lib/time/ops/offset_bound_ms
