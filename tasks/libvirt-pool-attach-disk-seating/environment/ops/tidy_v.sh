#!/bin/bash
set -euo pipefail

LEASE_DIR="${LEASE_DIR:-/var/run/libvirt}"
mkdir -p "$LEASE_DIR"

exit 0
