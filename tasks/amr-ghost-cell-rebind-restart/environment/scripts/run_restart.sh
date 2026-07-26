#!/usr/bin/env bash
set -euo pipefail
cd /app
make
mkdir -p /output/fields
./amr_hydro recover-all
