#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="${APP_ROOT:-/app}"
judge="$APP_ROOT/bin/judge.jar"
history_dir="$APP_ROOT/history"
sheet_dir="$APP_ROOT/puzzles"
card_path="${1:-/output/patchwork-card.json}"

test -f "$judge"
test -d "$history_dir"
test -d "$sheet_dir"

mkdir -p "$APP_ROOT/desk_books" "$APP_ROOT/board_hunt" "$APP_ROOT/card_out"
cp "$ROOT_DIR/desk_books/op_a.py" "$APP_ROOT/desk_books/op_a.py"
cp "$ROOT_DIR/board_hunt/engine.py" "$APP_ROOT/board_hunt/engine.py"
cp "$ROOT_DIR/board_hunt/op_b.py" "$APP_ROOT/board_hunt/op_b.py"
cp "$ROOT_DIR/card_out/op_c.py" "$APP_ROOT/card_out/op_c.py"
touch "$APP_ROOT/desk_books/__init__.py" "$APP_ROOT/board_hunt/__init__.py" \
  "$APP_ROOT/card_out/__init__.py"

export APP_ROOT
export PYTHONPATH="$APP_ROOT:${PYTHONPATH:-}"

python3 - "$card_path" <<'PY'
import os
import sys

app = os.environ["APP_ROOT"]
sys.path.insert(0, app)
from board_hunt.op_b import op_b
from card_out.op_c import op_c
from desk_books.op_a import SCHEMA_TAG, dialect, sheets

card_path = sys.argv[1]
grammar = dialect(app + "/history")
rows = [op_b(sheet, grammar) for sheet in sheets(app + "/puzzles")]
op_c(rows, SCHEMA_TAG, card_path)
tally = {}
for row in rows:
    tally[row["status"]] = tally.get(row["status"], 0) + 1
print(f"filed {len(rows)} rounds {tally}", file=sys.stderr)
PY

test -f "$card_path"

# Replay every filed line past the sealed table judge before leaving the desk.
python3 - "$card_path" "$judge" "$sheet_dir" <<'PY'
import json
import subprocess
import sys

card_path, judge, sheet_dir = sys.argv[1:4]
card = json.loads(open(card_path).read())
for row in card["rounds"]:
    seq = row.get("sequence") or []
    if not seq:
        continue
    out = subprocess.run(
        [
            "java", "-jar", judge, "validate",
            "--board", f"{sheet_dir}/board_{row['board_id']}.txt",
            "--line", ";".join(seq),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    seen = json.loads(out.stdout)
    assert seen["all_legal"], (row["board_id"], seen)
    assert seen["terminal"], (row["board_id"], seen)
    assert seen["floor_met"], (row["board_id"], seen)
    assert seen["red_first_patch"] == row["patch_id"], (row["board_id"], seen)
    if row["status"] == "trap":
        assert seen["blue_advances_only"], (row["board_id"], seen)
print("judge replayed every filed line", file=sys.stderr)
PY
