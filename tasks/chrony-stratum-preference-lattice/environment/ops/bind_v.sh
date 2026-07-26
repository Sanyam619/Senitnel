#!/bin/bash
# bind_v — write chrony sources
set -euo pipefail

etc=/etc/chrony/sources.d
mkdir -p "$etc" /var/lib/time/ops
ls -1 "$etc" > /var/lib/time/ops/bound.list || true
: > /var/lib/time/ops/selected.list
for f in "$etc"/*.sources; do
  [[ -f "$f" ]] || continue
  base=$(basename "$f" .sources)
  echo "pool-$base" >> /var/lib/time/ops/selected.list
done
