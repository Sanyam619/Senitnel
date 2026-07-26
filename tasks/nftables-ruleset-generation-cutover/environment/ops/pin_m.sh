#!/bin/bash
pin_m() {
  set -euo pipefail

  FOLD="${FOLD_OUT:-/var/lib/nft/ops/fold.nft}"
  PREF="${SURFACE_PREF:-/etc/nft/surface_prefer.conf}"

  [[ -f "$FOLD" ]] || exit 0
  [[ -f "$PREF" ]] || exit 0

  python3 - "$FOLD" "$PREF" <<'PY'
import sys
from pathlib import Path

fold, pref_path = map(Path, sys.argv[1:])
_ = pref_path.read_text() if pref_path.exists() else ""
fold.write_text(fold.read_text() if fold.exists() else "")
PY
}
pin_m
