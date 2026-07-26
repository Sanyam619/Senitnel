#!/usr/bin/env bash
# Verify that every fixture under /app/data still matches the SHA-256
# baked into /app/data/fixtures.sha256.
set -euo pipefail
cd /
sha256sum -c /app/data/fixtures.sha256
