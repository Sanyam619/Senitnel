#!/bin/bash
# Derive the live ko family and tournament card. No hardcoded statuses.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
referee_jar=/app/bin/judge.jar
history_dir=/app/history
puzzle_dir=/app/puzzles
answers_path=/app/answers.json
src="$ROOT_DIR/DeriveAnswers.java"
work=/tmp/sko_oracle_build

test -f "$referee_jar"
test -d "$history_dir"
test -d "$puzzle_dir"
test -f "$src"

# Recover the superko family by comparing refusal colours to referenced plies.
# Cross-colour recreates_board refusals are positional-only evidence; same-colour
# refusals remain compatible with situational families.
recover_rule() {
  local psk_only=0
  local ambiguous=0
  local log line parts ply color move verdict rej ref ref_color
  local -A ply_colour=()

  for log in "$history_dir"/game_*.log; do
    ply_colour=()
    while IFS= read -r line || [ -n "$line" ]; do
      case "$line" in
        ''|\#*) continue ;;
      esac
      # shellcheck disable=SC2206
      parts=($line)
      if [ "${#parts[@]}" -lt 4 ]; then
        continue
      fi
      ply="${parts[0]}"
      color="${parts[1]}"
      verdict="${parts[3]}"
      if [ "$verdict" = "accepted" ]; then
        ply_colour["$ply"]="$color"
        ply_colour["$(echo "$ply" | sed 's/^0*//')"]="$color"
      fi
    done < "$log"

    while IFS= read -r line || [ -n "$line" ]; do
      case "$line" in
        *rejected*superko:recreates_board_from_ply_*) ;;
        *) continue ;;
      esac
      # shellcheck disable=SC2206
      parts=($line)
      if [ "${#parts[@]}" -lt 2 ]; then
        continue
      fi
      rej="${parts[1]}"
      ref="$(printf '%s\n' "$line" | sed -n 's/.*ply_\([0-9][0-9]*\).*/\1/p')"
      if [ -z "$ref" ]; then
        continue
      fi
      ref_color="${ply_colour[$ref]:-unknown}"
      if [ "$ref_color" = "unknown" ]; then
        ref_color="${ply_colour[$(echo "$ref" | sed 's/^0*//')]:-unknown}"
      fi
      if [ "$ref_color" = "unknown" ]; then
        continue
      fi
      if [ "$rej" != "$ref_color" ]; then
        psk_only=$((psk_only + 1))
      else
        ambiguous=$((ambiguous + 1))
      fi
    done < "$log"
  done

  if [ "$psk_only" -gt 0 ]; then
    printf '%s\n' "positional_superko"
  elif [ "$ambiguous" -gt 0 ]; then
    printf '%s\n' "situational_superko"
  else
    printf '%s\n' "natural_situational_superko"
  fi
}

echo "recovering ko family from match logs..." >&2
rule="$(recover_rule)"
echo "recovered rule=$rule" >&2

rm -rf "$work"
mkdir -p "$work"

# Materialize a copy under /app for collapse edit-distance accounting.
set +e
cp "$src" /app/_DeriveAnswers.java
set -e

javac -encoding UTF-8 -d "$work" "$src"
java -cp "$work" DeriveAnswers

test -f "$answers_path"

# Cross-check the jar-derived rule field against the match-log recovery.
python3 - "$answers_path" "$rule" <<'PY'
import json, sys
path, expected = sys.argv[1], sys.argv[2]
data = json.load(open(path))
if data.get("rule") != expected:
    raise SystemExit(
        f"rule mismatch: answers has {data.get('rule')!r}, logs imply {expected!r}"
    )
boards = data.get("boards")
if not isinstance(boards, list) or len(boards) != 12:
    raise SystemExit(f"expected 12 boards, got {boards!r}")
ids = [int(b["board_id"]) for b in boards]
if ids != list(range(1, 13)):
    raise SystemExit(f"board_id order broken: {ids}")
for entry in boards:
    status = entry.get("status")
    if status not in ("win", "unwinnable"):
        raise SystemExit(f"bad status: {entry}")
    if status == "win":
        seq = entry.get("sequence")
        if not isinstance(seq, list) or not seq:
            raise SystemExit(f"win missing sequence: {entry}")
print(f"answers.json OK rule={expected} boards=12", file=sys.stderr)
PY
