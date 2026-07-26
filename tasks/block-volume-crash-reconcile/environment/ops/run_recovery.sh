#!/bin/bash
set -euo pipefail
cd /opt/kvfs
./ops/apply_site_policy.sh
make bin/reconcile
mkdir -p /output
bin/reconcile
