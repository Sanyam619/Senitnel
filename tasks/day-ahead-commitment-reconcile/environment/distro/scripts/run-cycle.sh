#!/bin/bash
# Commitment batch cycle — emit /data/out/answers.json from fixture boards.
set -euo pipefail

ROOT="${DISTRO_ROOT:-/opt/distro}"
FIX="${FIXTURE_ROOT:-/data/fixtures}"
CARD_OUT="${CARD_OUT:-/data/out/answers.json}"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
mkdir -p "$(dirname "$CARD_OUT")"

python3 - "$ROOT" "$FIX" "$CARD_OUT" <<'PY'
import sys
from pathlib import Path

root, fix, card_out = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, root)
from mod_a.op_a import binds_flag, op_a
from mod_b.op_b import op_b
from mod_c.op_c import op_c

boards = sorted(Path(fix).glob("board_*.txt"))
if len(boards) != 12:
    raise SystemExit(f"expected 12 boards, found {len(boards)}")

rows_out = []
for sheet in boards:
    info = op_b(str(sheet), None)
    status = info["status"]
    if status == "feasible_clear":
        info["smp"] = op_a(info["rows"], info["cleared"])
        info["binds"] = binds_flag(info["rows"], info["cleared"], info["reserve"])
    elif status == "reserve_short":
        info["smp"] = op_a(info["rows"], info["cleared"]) if info["cleared"] else 0
        info["binds"] = True
    else:
        info["smp"] = 0
        info["binds"] = False
    rows_out.append(info)

op_c(rows_out, card_out)
print(f"wrote {card_out}", file=sys.stderr)
PY
