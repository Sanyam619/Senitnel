#!/bin/bash
fold_k() {
  set -euo pipefail

  SRC_D="${SRC_D:-/etc/nftables.d}"
  OUT="${FOLD_OUT:-/var/lib/nft/ops/fold.nft}"
  FLOOR_D="${FLOOR_D:-/etc/nft/floors}"

  mkdir -p "$(dirname "$OUT")"
  : >"$OUT"

  shopt -s nullglob
  for f in $(ls -1 "$SRC_D"/*.nft 2>/dev/null | sort); do
    cat "$f" >>"$OUT"
    printf '\n' >>"$OUT"
  done
  shopt -u nullglob
}
fold_k
