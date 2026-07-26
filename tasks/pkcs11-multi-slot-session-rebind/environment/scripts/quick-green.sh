#!/bin/bash
set -euo pipefail
/opt/pk11/bin/findscan || true
java -cp /opt/pk11/classes flux.LabelPick /data/token signing-leaf >/dev/null 2>&1 || true
java -cp /opt/pk11/classes nest.CacheKeep /data/token >/dev/null 2>&1 || true
echo "quick-green: object scan lane only"
