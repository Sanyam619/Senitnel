#!/bin/bash
# pull_m — hold window
set -euo pipefail

mkdir -p /var/lib/chrony /var/lib/time/ops
echo 'held = []' > /var/lib/chrony/holds.toml
cp /var/lib/chrony/holds.toml /var/lib/time/ops/holds.active
