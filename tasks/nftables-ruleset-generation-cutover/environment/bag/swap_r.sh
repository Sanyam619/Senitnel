#!/bin/bash
swap_r() {
  set -euo pipefail

  FOLD="${FOLD_OUT:-/var/lib/nft/ops/fold.nft}"
  mkdir -p /var/lib/nft/state
  touch /var/lib/nft/state/append.flag
  /usr/local/bin/nft -f "$FOLD"
}
swap_r
