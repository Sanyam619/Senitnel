#!/bin/bash
# Surface smoke — does not write seating output.
set -euo pipefail
/usr/local/bin/timehealth >/tmp/timehealth.skim || true
echo "skim_z: surface health captured"
