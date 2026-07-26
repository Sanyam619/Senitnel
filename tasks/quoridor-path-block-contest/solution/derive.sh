#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="${APP_ROOT:-/app}"
export APP_ROOT

test -f "$APP_ROOT/bin/judge.jar"
test -d "$APP_ROOT/puzzles"
test -f "$APP_ROOT/docs/score_card.md"
test -f "$APP_ROOT/docs/table_judge.md"
test -x "$APP_ROOT/tools/sensei_hint.sh"

# Confirm the sealed judge is reachable before scoring the rounds; the
# win/trap/fort verdicts themselves are computed by the path search below.
java -jar "$APP_ROOT/bin/judge.jar" view --board "$APP_ROOT/puzzles/board_01.txt" >/dev/null
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

mkdir -p /output
export PYTHONPATH="$APP_ROOT:${PYTHONPATH:-}"
FIRST="$(mktemp /tmp/answers-first.XXXXXX.json)"
SECOND="$(mktemp /tmp/answers-second.XXXXXX.json)"
trap 'rm -f "$FIRST" "$SECOND"' EXIT
python3 "$ROOT_DIR/card_out/op_c.py" "$FIRST"
python3 "$ROOT_DIR/card_out/op_c.py" "$SECOND"
cmp "$FIRST" "$SECOND"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d["schema_tag"] == "quoridor-path-v1"' "$FIRST"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert len(d["rounds"]) == 11' "$FIRST"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert [r["board_id"] for r in d["rounds"]] == sorted(r["board_id"] for r in d["rounds"])' "$FIRST"
cp "$FIRST" /output/quoridor-card.json

test -f /output/quoridor-card.json
test -s /output/quoridor-card.json
