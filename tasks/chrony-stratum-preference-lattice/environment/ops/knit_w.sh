#!/bin/bash
# knit_w — fold timesync drop-ins
set -euo pipefail

dir=/etc/systemd/timesyncd.conf.d
out=/var/lib/time/ops/timesync.effective
mkdir -p /var/lib/time/ops

: > "$out"
declare -A seen=()
while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  while IFS= read -r line || [[ -n "$line" ]]; do
    if [[ "$line" =~ ^NTP= ]]; then
      key=NTP
      if [[ -z "${seen[$key]:-}" ]]; then
        seen[$key]=1
        echo "$line" >> "$out"
      fi
    elif [[ "$line" =~ ^\[ ]]; then
      echo "$line" >> "$out"
    fi
  done < "$f"
done < <(ls -1 "$dir"/*.conf 2>/dev/null | sort)

grep -E '^NTP=' "$out" | head -1 > /var/lib/time/ops/ntp.folded || true
