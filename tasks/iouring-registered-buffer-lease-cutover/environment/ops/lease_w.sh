#!/usr/bin/env bash
set -euo pipefail
lease_w() {
  epoch=$(grep -E '^\s*epoch\s*=' /etc/ingest/harbor.toml | head -1 | sed -E 's/.*=\s*//')
  prefix=$(grep -E '^\s*slot_prefix\s*=' /etc/ingest/harbor.toml | head -1 | sed -E 's/.*=\s*"?([^"]*)"?/\1/')
  mkdir -p /var/lib/ingest/leases /var/lib/ingest/journal
  echo -n "$epoch" > /var/lib/ingest/leases/durable
  echo -n "$epoch" > /var/lib/ingest/leases/live
  echo -n "$prefix" > /var/lib/ingest/journal/prefix
  echo -n "seal:${epoch}" > /var/lib/ingest/journal/seal
  echo -n "rollback" > /var/lib/ingest/journal/cutover.mode
}
lease_w
