#!/bin/bash
# knit_p — operator crumb writer.
set -euo pipefail
mkdir -p /var/log/nft
date -u +%Y-%m-%dT%H:%M:%SZ >/var/log/nft/last_seat.stamp
echo "crumb ok" >/var/log/nft/crumb.txt
