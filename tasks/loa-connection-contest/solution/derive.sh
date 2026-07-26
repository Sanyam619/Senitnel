#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="${APP_ROOT:-/app}"
export APP_ROOT

test -f "$APP_ROOT/bin/judge.jar"
test -d "$APP_ROOT/puzzles"
test -f "$APP_ROOT/docs/tournament_card.md"
test -f "$APP_ROOT/docs/table_judge.md"
test -f "$APP_ROOT/docs/contest_rules.md"
test -f "$APP_ROOT/docs/component_floors.md"
test -x "$APP_ROOT/tools/sensei_hint.sh"

# Confirm the sealed judge is reachable before scoring the rounds; the
# win/trap/fort verdicts themselves come from the searches below.
java -jar "$APP_ROOT/bin/judge.jar" view --board "$APP_ROOT/puzzles/board_01.txt" >/dev/null
SHEETS=()
while IFS= read -r sheet; do
    SHEETS+=("$sheet")
done < <(printf '%s\n' "$APP_ROOT"/puzzles/board_*.txt | sort)
test "${#SHEETS[@]}" -eq 12
for sheet in "${SHEETS[@]}"; do
    test -s "$sheet"
    java -jar "$APP_ROOT/bin/judge.jar" view --board "$sheet" >/dev/null
done

mkdir -p "$APP_ROOT/line_walk" "$APP_ROOT/desk_books" "$APP_ROOT/tally_room"
cp "$ROOT_DIR/line_walk/op_b.py" "$APP_ROOT/line_walk/op_b.py"
cp "$ROOT_DIR/desk_books/op_a.py" "$APP_ROOT/desk_books/op_a.py"
cp "$ROOT_DIR/tally_room/op_c.py" "$APP_ROOT/tally_room/op_c.py"
touch "$APP_ROOT/line_walk/__init__.py" \
      "$APP_ROOT/desk_books/__init__.py" \
      "$APP_ROOT/tally_room/__init__.py"

OUT=/output/loa-card.json
mkdir -p "$(dirname "$OUT")"
export PYTHONPATH="$APP_ROOT:${PYTHONPATH:-}"
FIRST="$(mktemp /tmp/loa-card-first.XXXXXX.json)"
SECOND="$(mktemp /tmp/loa-card-second.XXXXXX.json)"
trap 'rm -f "$FIRST" "$SECOND"' EXIT
python3 "$ROOT_DIR/tally_room/op_c.py" "$FIRST"
python3 "$ROOT_DIR/tally_room/op_c.py" "$SECOND"
cmp "$FIRST" "$SECOND"

python3 - "$FIRST" <<'PY'
import json
import sys

card = json.load(open(sys.argv[1]))
assert card["schema_tag"] == "loa-connection-v1"
rounds = card["rounds"]
assert len(rounds) == 12
ids = [row["board_id"] for row in rounds]
assert ids == sorted(ids)
statuses = {row["status"] for row in rounds}
assert statuses <= {"win", "trap", "fort"}
for row in rounds:
    assert isinstance(row["components"], int) and row["components"] >= 1
    assert isinstance(row["coop_connect"], bool)
    if row["status"] == "win":
        assert row["key_move"] and row["sequence"] and not row["refutations"]
        assert row["sequence"][0] == row["key_move"]
        assert row["components"] == 1
    elif row["status"] == "trap":
        assert not row["key_move"] and not row["sequence"]
        assert row["refutations"]
    else:
        assert not row["key_move"] and not row["sequence"]
        assert not row["refutations"] and row["coop_connect"] is False
print("card checks passed", file=sys.stderr)
PY

cp "$FIRST" "$OUT"
test -s "$OUT"
