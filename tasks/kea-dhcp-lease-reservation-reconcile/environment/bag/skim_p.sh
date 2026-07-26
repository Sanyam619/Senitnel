#!/bin/bash
set -euo pipefail
skim_p() {
  local kea_y="${KEA_VAR:-/var/lib/kea}"
  local lease_dir="$kea_y/state/lease_hits"
  mkdir -p "$lease_dir"
  rm -f "$lease_dir"/*
  : >"$kea_y/state/lease_hits.tsv"
}
skim_p
