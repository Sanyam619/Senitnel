#!/bin/bash
set -euo pipefail

ATTACH_D="${ATTACH_D:-/etc/libvirt/qemu/attach.d}"
mkdir -p "$ATTACH_D"

printf 'authority=surface\n' > "$ATTACH_D/10-select.conf"
