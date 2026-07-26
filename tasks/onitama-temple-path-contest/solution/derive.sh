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

java -jar "$APP_ROOT/bin/judge.jar" view --board "$APP_ROOT/puzzles/board_01.txt" >/dev/null
PUZZLE_COUNT=0
for puzzle in $(printf '%s\n' "$APP_ROOT"/puzzles/board_*.txt | sort); do
    test -s "$puzzle"
    java -jar "$APP_ROOT/bin/judge.jar" view --board "$puzzle" >/dev/null
    PUZZLE_COUNT=$((PUZZLE_COUNT + 1))
done
test "$PUZZLE_COUNT" -eq 12

mkdir -p "$APP_ROOT/board_hunt" "$APP_ROOT/desk_books" "$APP_ROOT/card_out"
cp "$ROOT_DIR/board_hunt/engine.py" "$APP_ROOT/board_hunt/engine.py"
cp "$ROOT_DIR/board_hunt/op_b.py" "$APP_ROOT/board_hunt/op_b.py"
cp "$ROOT_DIR/desk_books/op_a.py" "$APP_ROOT/desk_books/op_a.py"
cp "$ROOT_DIR/card_out/op_c.py" "$APP_ROOT/card_out/op_c.py"
touch "$APP_ROOT/board_hunt/__init__.py" \
      "$APP_ROOT/desk_books/__init__.py" \
      "$APP_ROOT/card_out/__init__.py"

export PYTHONPATH="$APP_ROOT:${PYTHONPATH:-}"
FIRST="$(mktemp /tmp/answers-first.XXXXXX.json)"
SECOND="$(mktemp /tmp/answers-second.XXXXXX.json)"
trap 'rm -f "$FIRST" "$SECOND"' EXIT
python3 "$ROOT_DIR/card_out/op_c.py" "$FIRST"
python3 "$ROOT_DIR/card_out/op_c.py" "$SECOND"
cmp "$FIRST" "$SECOND"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d["schema_tag"] == "onitama-temple-v1"' "$FIRST"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert len(d["rounds"]) == 12' "$FIRST"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert [r["board_id"] for r in d["rounds"]] == sorted(r["board_id"] for r in d["rounds"])' "$FIRST"
cp "$FIRST" /app/answers.json

python3 - /app/answers.json "$APP_ROOT/bin/judge.jar" "$APP_ROOT/puzzles" <<'PY'
import json
import subprocess
import sys

card_path, judge, sheet_dir = sys.argv[1:4]
card = json.loads(open(card_path).read())
for row in card["rounds"]:
    if not row["sequence"]:
        continue
    cmd = [
        "java", "-jar", judge, "validate",
        "--board", f"{sheet_dir}/board_{row['board_id']}.txt",
        "--line", ";".join(row["sequence"]),
    ]
    if row["status"] == "trap":
        cmd.append("--coop")
    out = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert out.returncode == 0, (row["board_id"], out.stdout, out.stderr)
    seen = json.loads(out.stdout)
    assert seen["all_legal"], (row["board_id"], seen)
    assert seen["winner"] == "sensei", (row["board_id"], seen)
    assert seen["sensei_plies"] == row["mate_in"], (row["board_id"], seen)
    assert seen["sideboards"] == row["sideboard"], (row["board_id"], seen)
print("judge replayed every filed sequence", file=sys.stderr)
PY

test -f /app/answers.json
test -s /app/answers.json
