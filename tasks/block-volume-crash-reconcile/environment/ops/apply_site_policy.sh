#!/bin/bash
set -euo pipefail

POLICY="/opt/kvfs/config/recovery_policy.ini"

cat > "$POLICY" <<'EOF'
# KVFS batch recovery policy — still emitting pre-standard knobs
# (see /opt/kvfs/config/site_recovery_standard.ini for KVFS-441 closeout)
[replay]
order=journal
forget_mode=forward

[bitmap]
metadata_used_end=8

[image]
patch_zero_pad=0
preserve_superblocks=0

[header]
prefer=durable_tx
EOF
