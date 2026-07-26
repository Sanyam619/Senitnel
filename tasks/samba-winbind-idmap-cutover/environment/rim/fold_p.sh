#!/bin/bash
set -euo pipefail
PREF_D="${PREF_D:-/etc/samba/pref.d}"
META="${SAMBA_VAR:-/var/lib/samba}/meta"
mkdir -p "$META"
mode="unset"
if [[ -d "$PREF_D" ]]; then
  for f in $(ls "$PREF_D"/*.conf 2>/dev/null | sort); do
    if grep -q 'mode=' "$f" 2>/dev/null; then
      mode=$(grep -E '^mode=' "$f" | head -n1 | cut -d= -f2-)
      break
    fi
  done
fi
echo "$mode" >"$META/pref.mode"
rm -f "$META/pref.armed"
