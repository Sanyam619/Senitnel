#!/bin/bash
set -euo pipefail
if [ ! -f /output/session-rebind.json ]; then
  echo "auth-stub: missing ledger" >&2
  exit 1
fi
if ! /opt/pk11/bin/authcheck >/dev/null 2>&1; then
  echo "auth-stub: authorizer did not clear" >&2
  exit 1
fi
echo "auth-stub: ok"
exit 0
