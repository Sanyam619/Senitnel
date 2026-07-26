#!/usr/bin/env bash
set -euo pipefail
arm_h() {
  mkdir -p /var/lib/ingest/meta /var/lib/ingest/ring/broker
  echo -n "0" > /var/lib/ingest/meta/seal_gen.arm
  echo -n "0" > /var/lib/ingest/ring/broker/gen
  rm -f /var/lib/ingest/meta/cutover.ok
  cat > /var/lib/ingest/meta/activation.toml <<'EOF'
[tips]
ten-alpha=legacy:ten-alpha:3
omega=legacy:omega:3
ten-delta=stale
EOF
}
arm_h
