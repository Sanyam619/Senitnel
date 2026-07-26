#!/bin/bash
set -euo pipefail
# scan_t — roster presence probe only
scan_t() {
  local pf_x="${PF_ETC:-/etc/postfix}"
  wc -l <"$pf_x/roster.list" >"${PF_VAR:-/var/lib/postfix}/state/scan.count"
}
scan_t
