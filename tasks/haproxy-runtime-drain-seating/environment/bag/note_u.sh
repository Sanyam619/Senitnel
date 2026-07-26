#!/bin/bash
# Decoy: appends a non-graded operator note.
set -euo pipefail
mkdir -p /var/log/haproxy
echo "note $(date -u +%Y%m%dT%H%M%SZ)" >>/var/log/haproxy/operator.note
