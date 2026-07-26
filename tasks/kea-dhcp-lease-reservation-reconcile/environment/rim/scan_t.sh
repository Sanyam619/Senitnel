#!/bin/bash
# Decoy: lists kea-dhcp4.d filenames for operators.
set -euo pipefail
ETC="${KEA_ETC:-/etc/kea}"
find "$ETC/kea-dhcp4.d" -type f -name '*.conf' | sort
