#!/bin/bash
set -euo pipefail

export SAMBA_ETC="${SAMBA_ETC:-/etc/samba}"
export SAMBA_VAR="${SAMBA_VAR:-/var/lib/samba}"
export IDMAP_ROSTER="${IDMAP_ROSTER:-/etc/samba/idmap.roster}"
export IDMAP_TDB="${IDMAP_TDB:-/var/lib/samba/idmap.tdb}"
export DESK_SEAL="${DESK_SEAL:-/etc/samba/desk.seal}"
export IDMAP_REPORT="${IDMAP_REPORT:-/output/idmap-cutover.json}"
export PREF_D="${PREF_D:-/etc/samba/pref.d}"
export SAMBA_DESKD_ENV="${SAMBA_DESKD_ENV:-/etc/samba/deskd.env}"

mkdir -p "$SAMBA_VAR/meta" "$SAMBA_VAR/ops" "$SAMBA_VAR/attach" \
  "$SAMBA_VAR/origins" /var/run/samba /output "$(dirname "$IDMAP_REPORT")"

exec 9>/var/run/samba/seat.lock
flock 9

META="$SAMBA_VAR/meta"
LEGACY_LIVE="$SAMBA_ETC/smb.conf.d/40-legacy.conf"
HAMMER="$SAMBA_VAR/journal/legacy.prefer"

/app/ops/prep_s.sh
/app/rim/fold_p.sh
/app/wire/knit_w.sh
/app/ops/axle_j.sh
/app/ops/fold_a.sh
/app/deck/leg_w.sh
/app/deck/hold_c.sh
/app/dock/link_v.sh
/app/ops/deskd

if [[ -f "$LEGACY_LIVE" ]] && [[ -f "$HAMMER" ]] && cmp -s "$LEGACY_LIVE" "$HAMMER"; then
  cp -f "$META/backends.crash.toml" "$META/backends.toml"
  rm -f "$META/tip.ok"
fi

exec /app/bin/idmapctl
