#!/bin/bash
set -euo pipefail
MAP="${LOADED_MAP:-/run/systemd/watch-seat/loaded.map}"
mkdir -p "$(dirname "$MAP")"
printf '%s\n' 'deploy-artifact ARMED' 'config-reload ARMED' 'spool-flush ARMED' >"$MAP"
