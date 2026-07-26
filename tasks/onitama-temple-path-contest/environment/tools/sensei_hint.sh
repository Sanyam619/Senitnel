#!/bin/bash
# Sensei whisper — surface cheer only. NOT the contest verdict.
# Names hand cards plus the current sideboard without applying a swap.
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
python3 - "$APP_ROOT" <<'PY'
import sys
from pathlib import Path

app = Path(sys.argv[1])
for sheet in sorted((app / "puzzles").glob("board_*.txt")):
    bid = sheet.stem.replace("board_", "")
    cards = []
    side = ""
    for line in sheet.read_text().splitlines():
        if line.startswith("sensei_cards:"):
            cards = [c.strip() for c in line.split(":", 1)[1].split(",")]
        if line.startswith("sideboard:"):
            side = line.split(":", 1)[1].strip()
    # Surface reading: hand cards plus the current sideboard token.
    hot = ",".join(cards + ([side] if side else []))
    print(f"{bid} hot_cards={hot} whisper=path_open")
PY
