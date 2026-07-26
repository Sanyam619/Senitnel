#!/usr/bin/env bash
set -euo pipefail
mkdir -p /output /tmp/edge_slots
rm -f /tmp/edge_slots/*
/app/bin/edgegate admit /output/admit-ledger.json
