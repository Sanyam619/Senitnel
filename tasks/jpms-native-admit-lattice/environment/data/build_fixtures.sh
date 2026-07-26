#!/bin/bash
# Fixtures are committed under data/; this script is a no-op integrity check.
set -euo pipefail
test -f /app/data/state/runtime.json
test -d /app/data/cases
test -d /app/data/token
echo "fixtures ok"
