#!/bin/bash
# knit_p — decoy: status crumb only.
set -euo pipefail
mkdir -p /var/log/autofs
date -u +%Y-%m-%dT%H:%M:%SZ >/var/log/autofs/knit.stamp
