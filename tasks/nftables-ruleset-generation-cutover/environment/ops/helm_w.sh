#!/bin/bash
helm_w() {
  set -euo pipefail

  ABORT_D="${ABORT_D:-/var/lib/nft/ops/abort.d}"
  LIVE_D="${LIVE_D:-/etc/nftables.d}"

  mkdir -p "$LIVE_D"
  if [[ -f "$ABORT_D/90-local.nft" ]]; then
    cp -f "$ABORT_D/90-local.nft" "$LIVE_D/90-local.nft"
  fi
}
helm_w
