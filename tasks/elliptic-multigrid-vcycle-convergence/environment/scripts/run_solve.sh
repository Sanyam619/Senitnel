#!/usr/bin/env bash
set -euo pipefail
cd /app
make
mkdir -p /app/output /app/output/traces /app/output/fields
./elliptic_mg
