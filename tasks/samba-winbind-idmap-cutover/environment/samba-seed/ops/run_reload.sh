#!/bin/bash
set -euo pipefail

export SAMBA_ETC="${SAMBA_ETC:-/etc/samba}"
export SAMBA_VAR="${SAMBA_VAR:-/var/lib/samba}"
export DESK_SEAL="${DESK_SEAL:-/etc/samba/desk.seal}"
export IDMAP_ROSTER="${IDMAP_ROSTER:-/etc/samba/idmap.roster}"
export IDMAP_TDB="${IDMAP_TDB:-/var/lib/samba/idmap.tdb}"
export IDMAP_REPORT="${IDMAP_REPORT:-/output/idmap-cutover.json}"
export PREF_D="${PREF_D:-/etc/samba/pref.d}"
export SAMBA_DESKD_ENV="${SAMBA_DESKD_ENV:-/etc/samba/deskd.env}"

mkdir -p "$SAMBA_VAR/meta" "$SAMBA_VAR/journal" "$SAMBA_ETC/smb.conf.d"

/app/ops/skim_r.sh
/app/ops/run_idmapseat.sh
