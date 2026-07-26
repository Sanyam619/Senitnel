#!/bin/bash
set -euo pipefail
# Rematerialize drifted live surfaces before seating helpers run.
ETC="${SAMBA_ETC:-/etc/samba}"
VAR="${SAMBA_VAR:-/var/lib/samba}"
PREF_D="${PREF_D:-/etc/samba/pref.d}"
META="$VAR/meta"
ENV_FILE="${SAMBA_DESKD_ENV:-/etc/samba/deskd.env}"
LEGACY_LIVE="$ETC/smb.conf.d/40-legacy.conf"
HAMMER="$VAR/journal/legacy.prefer"
ABORT_D="$VAR/ops/abort.d"

mkdir -p "$META" "$PREF_D" "$ETC/smb.conf.d" "$VAR/journal" "$VAR/ops"

cp -f "$META/backends.crash.toml" "$META/backends.toml"
rm -f "$META/tip.ok" "$META/pref.armed"
if [[ -f "$HAMMER" ]]; then
  cp -f "$HAMMER" "$LEGACY_LIVE"
fi
if [[ -f "$ABORT_D/90-local.conf" ]]; then
  cp -f "$ABORT_D/90-local.conf" "$ETC/smb.conf.d/90-decoy.conf"
fi
rm -f "$PREF_D"/*.conf
printf 'mode=shadow-only\n' >"$PREF_D/00-shadow.conf"

if [[ -f "$ENV_FILE" ]]; then
  tmp="$(mktemp)"
  while IFS= read -r line || [[ -n "${line:-}" ]]; do
    [[ "$line" == PAYLOAD_LINEAGE=* || "$line" == HOLD_TOKEN=* ]] && continue
    printf '%s\n' "$line"
  done <"$ENV_FILE" >"$tmp"
  printf 'PAYLOAD_LINEAGE=decoy\nHOLD_TOKEN=lab-tmp\n' >>"$tmp"
  mv -f "$tmp" "$ENV_FILE"
else
  printf 'PAYLOAD_LINEAGE=decoy\nHOLD_TOKEN=lab-tmp\n' >"$ENV_FILE"
fi
