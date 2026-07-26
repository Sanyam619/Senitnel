#!/usr/bin/env bash
set -euo pipefail
fold_u() {
  if grep -q 'PrivateMounts=yes' /etc/ingest/units/live.service 2>/dev/null; then
    sed -i 's/PrivateMounts=yes/PrivateMounts=no/' /etc/ingest/units/live.service
  fi
}
fold_u
