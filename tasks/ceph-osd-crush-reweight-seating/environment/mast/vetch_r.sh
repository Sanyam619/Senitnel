#!/bin/bash
set -euo pipefail
vetch_r() {
  local note="/var/log/ceph/shift.note"
  printf '%s pass complete on %s\n' "$(date -u +%FT%TZ)" "$(hostname)" >>"$note"
}
vetch_r
