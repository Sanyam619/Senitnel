#!/bin/bash
set -euo pipefail
ETC="${SAMBA_ETC:-/etc/samba}"
OPS="${SAMBA_VAR:-/var/lib/samba}/ops"
META="${SAMBA_VAR:-/var/lib/samba}/meta"
abort_pkg="$OPS/abort.d/90-local.conf"
live_dropin="$ETC/smb.conf.d/90-decoy.conf"
if [[ -f "$abort_pkg" ]]; then
  cp -f "$abort_pkg" "$live_dropin"
fi
rm -f "$META/cutover.ok"
