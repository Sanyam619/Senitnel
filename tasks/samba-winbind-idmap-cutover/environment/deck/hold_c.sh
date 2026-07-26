#!/bin/bash
set -euo pipefail
ROOT="${SAMBA_VAR:-/var/lib/samba}"
META="$ROOT/meta"
RUN="/var/run/samba"
mkdir -p "$RUN"
live=$(tr -d ' \t\r\n' <"$META/gen.live" 2>/dev/null || echo "")
target=$(tr -d ' \t\r\n' <"$META/gen.target" 2>/dev/null || echo "")
if [[ -n "$live" && "$live" == "$target" ]]; then
  rm -f "$RUN"/lease.*
  find "$ROOT/volumes" -type f -path '*/host/*' -delete 2>/dev/null || true
fi
