#!/bin/bash
set -euo pipefail
scan_t() {
  local trf_x="${TRF_ETC:-/etc/traefik}"
  find "$trf_x/dynamic" -type f -name '*.yml' | sort
}
scan_t
