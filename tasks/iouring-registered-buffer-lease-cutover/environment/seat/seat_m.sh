#!/usr/bin/env bash
set -euo pipefail
seat_m() {
  mkdir -p /var/lib/ingest/mnt/host/ten /var/lib/ingest/mnt/broker/ten /var/lib/ingest/identity
  for n in ten-alpha ten-beta ten-gamma; do
    echo -n "marker:$n" > "/var/lib/ingest/mnt/host/ten/$n"
    rm -f "/var/lib/ingest/mnt/broker/ten/$n"
  done
  echo -n "host" > /var/lib/ingest/identity/mnt_ns
}
seat_m
