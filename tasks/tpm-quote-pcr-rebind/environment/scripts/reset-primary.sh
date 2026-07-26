#!/usr/bin/env bash
set -euo pipefail

cat > /data/traces/primary.evt <<'EOF'
{"idx":0,"bank":0,"payload":"CRTM"}
{"idx":1,"bank":0,"payload":"PostCode"}
{"idx":2,"bank":1,"payload":"PlatformConfig"}
{"idx":3,"bank":7,"payload":"OptionRom"}
{"idx":4,"bank":8,"payload":"BootLoader"}
EOF
