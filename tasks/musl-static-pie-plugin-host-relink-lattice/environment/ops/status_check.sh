#!/bin/bash
# Existence-only status check used by ops dashboards. Not authoritative for load readiness.
set -euo pipefail
ROOT="${1:-/app}"
ok=1
for p in \
  "$ROOT/h4/Makefile" \
  "$ROOT/p7/Cargo.toml" \
  "$ROOT/g3/go.mod" \
  "$ROOT/ops/matrix.toml"
do
  if [[ ! -e "$p" ]]; then
    echo "missing: $p"
    ok=0
  fi
done
if [[ "$ok" -eq 1 ]]; then
  echo "status: binaries_present"
  exit 0
fi
echo "status: incomplete"
exit 1
