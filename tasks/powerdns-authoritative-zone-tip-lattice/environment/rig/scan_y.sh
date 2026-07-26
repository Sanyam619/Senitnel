#!/bin/bash
set -euo pipefail
# Lists pdns.d filenames for operator inventory.
scan_y() {
  local pd_x="${PD_ETC:-/etc/powerdns}"
  ls -1 "$pd_x"/pdns.d 2>/dev/null || true
}
scan_y
