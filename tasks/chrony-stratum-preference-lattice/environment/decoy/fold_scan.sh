#!/bin/bash
# Lists timesync drop-in basenames; does not fold NTP keys.
set -euo pipefail
DIR=/etc/systemd/timesyncd.conf.d
if [[ -d "$DIR" ]]; then
  ls -1 "$DIR" | sort
fi
