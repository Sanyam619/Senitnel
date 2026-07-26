#!/bin/bash
# Thin wrapper around the surface status helper for smoke checks.
set -euo pipefail
/usr/local/bin/mpathhealth | tail -1
