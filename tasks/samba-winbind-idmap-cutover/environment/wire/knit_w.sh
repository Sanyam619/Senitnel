#!/bin/bash
set -euo pipefail
META="${SAMBA_VAR:-/var/lib/samba}/meta"
mkdir -p "$META"
rm -f "$META/tip.ok"
exec /app/bin/tipfold
