#!/bin/bash
# Sensei whisper: cheers city/road glyph density. Does not read farmer majority.
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
BOARD="${1:-$APP_ROOT/puzzles/board_01.txt}"
if [[ ! -f "$BOARD" ]]; then
  echo "no sheet"
  exit 1
fi
python3 - "$BOARD" <<'PY'
import sys
from pathlib import Path
text = Path(sys.argv[1]).read_text()
cities = text.count("C")
roads = text.count("R")
print(f"sensei: city_edges≈{cities} road_edges≈{roads}")
if cities >= 2 or roads >= 2:
    print("sensei: fill looks ready (farmer majority not checked)")
else:
    print("sensei: sparse landscape")
PY
