#!/bin/bash
set -euo pipefail
brome_j() {
  local sx="${SD_ETC:-/etc/ceph}"
  local note="/var/log/ceph/sheet_inventory.note"
  {
    printf '# Live sheet inventory\n'
    ls "$sx/reweight.d" | LC_ALL=C sort
    ls "$sx/pools.d" | LC_ALL=C sort
  } >"$note"
}
brome_j
