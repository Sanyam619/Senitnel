#!/usr/bin/env bash
set -euo pipefail
cd /app
sha256sum -c /app/data/fixtures.sha256
