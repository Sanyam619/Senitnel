#!/bin/bash
set -euo pipefail
echo "slotctl=$(command -v slotctl || true)"
echo "hdrgen=$(command -v hdrgen || true)"
echo "unify_probe=$(command -v unify_probe || true)"
ls -1 /app/config/profiles 2>/dev/null || true
