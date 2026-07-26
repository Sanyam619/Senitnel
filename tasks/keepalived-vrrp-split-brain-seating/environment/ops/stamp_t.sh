#!/bin/bash
set -euo pipefail
MAP="${TOKEN_MAP:-/etc/keepalived/runtime/token.map}"
mkdir -p "$(dirname "$MAP")"
printf '%s\n' 'peer_a MASTER' 'peer_b MASTER' 'peer_e MASTER' >"$MAP"
