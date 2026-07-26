#!/bin/bash
set -euo pipefail
sedge_w() {
  local sr="${SD_RUN:-/var/run/ceph}"
  touch "$sr/probe.stamp"
}
sedge_w
