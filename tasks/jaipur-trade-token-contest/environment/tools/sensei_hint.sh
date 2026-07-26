#!/bin/bash
# Sensei whisper: cheers goods takes; ignores camel-only herd takes.
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
BOARD="${1:-$APP_ROOT/puzzles/board_01.txt}"
python3 - <<'PY' "$BOARD"
import sys
from pathlib import Path

path = Path(sys.argv[1])
market = []
for line in path.read_text().splitlines():
    t = line.strip()
    if t.startswith("market:"):
        market = [p.strip() for p in t.split(":", 1)[1].split(",") if p.strip()]
goods = [c for c in market if c != "cam"]
cams = sum(1 for c in market if c == "cam")
print(f"sensei: goods-take whisper on {path.name}")
print(f"market_goods={','.join(goods) if goods else '(none)'}")
print(f"camels_in_row={cams} (herd sweeps left unread)")
if goods:
    print(f"cheer: take:{goods[0]} looks lively")
else:
    print("cheer: empty goods row — desk shrug")
print("(camel-only herd takes are not scored by this whisper)")
PY
