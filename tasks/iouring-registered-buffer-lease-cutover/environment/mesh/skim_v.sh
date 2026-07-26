#!/usr/bin/env bash
set -euo pipefail
skim_v() {
  if [[ -f /var/lib/ingest/decoys/prefix.legacy ]]; then
    cp -f /var/lib/ingest/decoys/prefix.legacy /var/lib/ingest/journal/prefix
  fi
}
skim_v
