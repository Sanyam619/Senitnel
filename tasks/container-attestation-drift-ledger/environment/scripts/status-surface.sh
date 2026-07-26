#!/bin/bash
set -euo pipefail
/app/bin/digctl status
/app/bin/provcheck probe
echo "OK surface"
