#!/usr/bin/env bash
set -euo pipefail
if [[ -x /opt/ramp/bin/rampd ]]; then
	echo "runner: present"
	exit 0
fi
echo "runner: missing" >&2
exit 1
