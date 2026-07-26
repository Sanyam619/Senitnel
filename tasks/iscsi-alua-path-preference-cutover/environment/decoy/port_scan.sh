#!/bin/bash
# Lists remote-port fixture names; does not resolve access states.
set -euo pipefail
DIR=/app/data/sysfs
if [[ -d "$DIR" ]]; then
  ls -1 "$DIR" | sort
fi
