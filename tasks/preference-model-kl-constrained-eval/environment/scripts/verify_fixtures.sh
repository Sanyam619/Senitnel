#!/usr/bin/env bash
set -euo pipefail
ROOT="${PREF_DATA_ROOT:-/app/data}"
if [[ -f /app/data/fixtures.sha256 ]]; then
  (cd / && sha256sum -c /app/data/fixtures.sha256) >/dev/null
fi
test -d "${ROOT}/prefs"
test -d "${ROOT}/ref"
test -d "${ROOT}/policy"
test -d "${ROOT}/tips"
