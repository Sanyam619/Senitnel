#!/bin/bash
# warp_h — status crumb only.
set -euo pipefail
mkdir -p /var/log/ipa
date -u +%Y-%m-%dT%H:%M:%SZ >/var/log/ipa/warp.stamp
