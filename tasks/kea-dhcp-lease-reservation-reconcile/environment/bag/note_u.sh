#!/bin/bash
# Decoy: appends a non-graded operator note.
set -euo pipefail
mkdir -p /var/log/kea
echo "note $(date -u +%Y%m%dT%H%M%SZ)" >>/var/log/kea/operator.note
