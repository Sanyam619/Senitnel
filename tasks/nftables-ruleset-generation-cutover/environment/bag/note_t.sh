#!/bin/bash
# note_t — archive a non-graded fold memo.
set -euo pipefail
mkdir -p /var/log/nft
if [[ -f /var/lib/nft/ops/fold.nft ]]; then
  wc -l </var/lib/nft/ops/fold.nft >/var/log/nft/fold_lines.txt || true
fi
