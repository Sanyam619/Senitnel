#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="${APP_ROOT:-/app}"
export APP_ROOT

test -f "$APP_ROOT/bin/judge.jar"
test -d "$APP_ROOT/puzzles"
test -f "$APP_ROOT/docs/tournament_card.md"
test -f "$APP_ROOT/docs/table_judge.md"
test -x "$APP_ROOT/tools/sensei_hint.sh"

java -jar "$APP_ROOT/bin/judge.jar" view \
    --board "$APP_ROOT/puzzles/board_01.txt" >/dev/null
mapfile -t PUZZLES < <(printf '%s\n' "$APP_ROOT"/puzzles/board_*.txt | sort)
test "${#PUZZLES[@]}" -eq 11
for puzzle in "${PUZZLES[@]}"; do
    test -s "$puzzle"
    java -jar "$APP_ROOT/bin/judge.jar" view --board "$puzzle" >/dev/null
done

mkdir -p "$APP_ROOT/board_hunt" "$APP_ROOT/desk_books" "$APP_ROOT/card_out"
cp "$ROOT_DIR/board_hunt/op_b.py" "$APP_ROOT/board_hunt/op_b.py"
cp "$ROOT_DIR/desk_books/op_a.py" "$APP_ROOT/desk_books/op_a.py"
cp "$ROOT_DIR/card_out/op_c.py" "$APP_ROOT/card_out/op_c.py"
touch "$APP_ROOT/board_hunt/__init__.py" \
      "$APP_ROOT/desk_books/__init__.py" \
      "$APP_ROOT/card_out/__init__.py"

export PYTHONPATH="$APP_ROOT:${PYTHONPATH:-}"
FIRST="$(python3 -c 'import tempfile; print(tempfile.mkstemp(suffix=".json")[1])')"
SECOND="$(python3 -c 'import tempfile; print(tempfile.mkstemp(suffix=".json")[1])')"
trap 'rm -f "$FIRST" "$SECOND"' EXIT
python3 "$ROOT_DIR/card_out/op_c.py" "$FIRST"
python3 "$ROOT_DIR/card_out/op_c.py" "$SECOND"
cmp "$FIRST" "$SECOND"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d["schema_tag"] == "tak-road-v1"' "$FIRST"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert len(d["rounds"]) == 11' "$FIRST"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert [r["board_id"] for r in d["rounds"]] == sorted(r["board_id"] for r in d["rounds"])' "$FIRST"
cp "$FIRST" "$APP_ROOT/answers.json"

test -f "$APP_ROOT/answers.json"
test -s "$APP_ROOT/answers.json"
