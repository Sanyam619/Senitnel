#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="${APP_ROOT:-/app}"
judge="$APP_ROOT/bin/judge.jar"
history_dir="$APP_ROOT/history"
sheet_dir="$APP_ROOT/puzzles"
answers_path="$APP_ROOT/answers.json"

test -f "$judge"
test -d "$history_dir"
test -d "$sheet_dir"

mkdir -p "$APP_ROOT/desk_books" "$APP_ROOT/board_hunt" "$APP_ROOT/card_out"
cp "$ROOT_DIR/desk_books/op_a.py" "$APP_ROOT/desk_books/op_a.py"
cp "$ROOT_DIR/board_hunt/op_b.py" "$APP_ROOT/board_hunt/op_b.py"
cp "$ROOT_DIR/board_hunt/engine.py" "$APP_ROOT/board_hunt/engine.py"
touch "$APP_ROOT/board_hunt/__init__.py" "$APP_ROOT/desk_books/__init__.py" "$APP_ROOT/card_out/__init__.py"
cp "$ROOT_DIR/card_out/op_c.py" "$APP_ROOT/card_out/op_c.py"

export APP_ROOT
export PYTHONPATH="$APP_ROOT:${PYTHONPATH:-}"

python3 <<'PY'
import os, sys
app = os.environ["APP_ROOT"]
sys.path.insert(0, app)
from desk_books.op_a import op_a
from board_hunt.op_b import op_b
from card_out.op_c import op_c
dialect = op_a(app + "/history", app + "/bin/judge.jar")
rows = [op_b(i, dialect) for i in range(1, 10)]
op_c(rows, app + "/answers.json")
print(f"wrote {app}/answers.json dialect={dialect} boards={len(rows)}", file=sys.stderr)
PY

test -f "$answers_path"
