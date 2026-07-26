#!/bin/bash
# axle_p — preference gate
set -euo pipefail

pref=/var/lib/time/ops/prefer.toml
surf=/var/lib/time/surface
etc_chrony=/etc/chrony
etc_ts=/etc/systemd/timesyncd.conf.d

mkdir -p "$etc_chrony/sources.d" "$etc_ts" /var/lib/chrony /var/lib/time/ops

cp -a "$surf/sources.d/." "$etc_chrony/sources.d/"
cp -a "$surf/timesync.d/." "$etc_ts/"

if [[ -f "$pref" ]]; then
  grep -E '^mode[[:space:]]*=' "$pref" | head -1 \
    | sed 's/.*=[[:space:]]*//;s/"//g;s/[[:space:]]*$//' \
    | tr -d ' ' > /var/lib/time/ops/mode.active \
    || echo live > /var/lib/time/ops/mode.active
else
  echo live > /var/lib/time/ops/mode.active
fi
