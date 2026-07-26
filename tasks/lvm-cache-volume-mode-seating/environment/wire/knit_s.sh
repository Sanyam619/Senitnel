#!/bin/bash
# knit_s — shift crumb for the operator log.
set -euo pipefail
mkdir -p /var/log/lvm
date -u +%Y-%m-%dT%H:%M:%SZ >/var/log/lvm/knit.stamp
