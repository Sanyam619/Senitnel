#!/bin/bash
set -euo pipefail
ETC="${SAMBA_ETC:-/etc/samba}"
VAR="${SAMBA_VAR:-/var/lib/samba}"
LEGACY_PREF="$VAR/journal/legacy.prefer"
ABORT_D="$VAR/ops/abort.d"
LEGACY_LIVE="$ETC/smb.conf.d/40-legacy.conf"

if [[ -f "$LEGACY_PREF" ]]; then
  cp -f "$LEGACY_PREF" "$LEGACY_LIVE"
fi
if [[ -d "$ABORT_D" ]]; then
  for f in "$ABORT_D"/*.conf; do
    [[ -f "$f" ]] || continue
    cp -f "$f" "$ETC/smb.conf.d/$(basename "$f")"
  done
fi
echo "0" >"$VAR/journal/stale.gen"
rm -f "$VAR/meta/pref.armed" "$VAR/meta/gen.live"
