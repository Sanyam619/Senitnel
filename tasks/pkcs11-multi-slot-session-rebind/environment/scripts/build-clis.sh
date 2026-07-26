#!/bin/bash
set -euo pipefail
cd /app
make clean
make
make install
cp -f /app/config/*.toml /opt/pk11/config/
echo "build-clis: installed"
