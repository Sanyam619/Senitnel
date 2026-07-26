#!/usr/bin/env bash
set -euo pipefail

cd /app/data
sha256sum -c fixtures.sha256
