#!/bin/bash
# Decoy: lists conf.d filenames for operators.
set -euo pipefail
ETC="${HAP_ETC:-/etc/haproxy}"
find "$ETC/conf.d" -type f -name '*.cfg' | sort
