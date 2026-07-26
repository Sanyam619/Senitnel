#!/bin/bash
set -euo pipefail
# Publish the seating report.
slate_j() {
  exec /app/bin/sentiseat
}
slate_j
