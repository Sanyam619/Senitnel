#!/bin/bash
set -euo pipefail
# Lightweight prep: ensure directories exist.
dune_p() {
  mkdir -p /etc/redis/monitors.d /etc/redis/sentinel.d /etc/redis/floors \
    /var/lib/redis/state /var/lib/redis/ops/state /output
}
dune_p
