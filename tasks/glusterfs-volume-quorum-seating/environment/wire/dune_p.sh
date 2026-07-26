#!/bin/bash
# dune_p — shift crumb for the operator log.
set -euo pipefail
mkdir -p /var/log/gluster
date -u +%Y-%m-%dT%H:%M:%SZ >/var/log/gluster/dune.stamp
