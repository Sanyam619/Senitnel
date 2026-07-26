#!/usr/bin/env bash
set -euo pipefail
hold_r() {
  mkdir -p /etc/ingest/units/abort.d
  cat > /etc/ingest/units/abort.d/90-isolate.conf <<'EOF'
[Service]
PrivateMounts=yes
EOF
}
hold_r
