#!/bin/bash
# stitch_r — fold conf.d drop-ins
set -euo pipefail

dir=/etc/multipath/conf.d
out=/var/lib/multipath/ops/group.map
mkdir -p /var/lib/multipath/ops

: > "$out"
first=$(ls -1 "$dir"/*.conf 2>/dev/null | sort | head -1)
if [[ -n "${first:-}" ]]; then
  grep -E '^weight ' "$first" | awk '{print $2" "$3}' >> "$out" || true
fi
