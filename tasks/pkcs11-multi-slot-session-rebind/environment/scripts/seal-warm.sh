#!/bin/bash
set -euo pipefail
BOUND=$(grep '^bound=' /data/token/provider.txt | head -1 | cut -d= -f2)
echo "seal-warm: using cached bound=$BOUND"
echo "0000000000000000" > /data/token/session.seal
echo "seal-warm: wrote placeholder"
