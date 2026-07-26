#!/bin/bash
echo_t() {
  set -euo pipefail

  FOLD="${FOLD_OUT:-/var/lib/nft/ops/fold.nft}"
  OUT="${APPLIED_OUT:-/var/lib/nft/ops/applied.nft}"
  mkdir -p "$(dirname "$OUT")"
  cp -f "$FOLD" "$OUT"
}
echo_t
