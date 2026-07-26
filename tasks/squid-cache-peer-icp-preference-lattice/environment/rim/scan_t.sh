#!/bin/bash
set -euo pipefail
# Lists conf.d filenames for operator inventory.
scan_t() {
  local sq_x="${SQ_ETC:-/etc/squid}"
  ls -1 "$sq_x"/conf.d 2>/dev/null || true
}
scan_t
