#!/usr/bin/env bash
set -euo pipefail
/opt/wiretap/bin/wiretap analyze --manifest /opt/wiretap/data/manifest.json --out /tmp/smoke-out
test -f /tmp/smoke-out/findings.json
