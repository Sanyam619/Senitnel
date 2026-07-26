#!/bin/bash
set -euo pipefail
sock_v() {
  local hap_z="${HAP_RUN:-/var/run/haproxy}"
  mkdir -p "$hap_z"
  date +%s >"$hap_z/probe.stamp"
}
sock_v
