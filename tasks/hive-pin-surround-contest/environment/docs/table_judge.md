# Table judge

The table judge is the sealed program at `/app/bin/judge.jar`. Ask it about
legal play with:

```
java -jar /app/bin/judge.jar <command> --board <round-file> [options]
```

Leave that jar unchanged. Integrity of the sealed binary is checked by the
verifier against sealed copies at `/opt/tbench/judge.jar` and
`/opt/tbench/puzzles/` (kept away from `/app/bin/`).

## Looking at a round

```
java -jar /app/bin/judge.jar view --board /app/puzzles/board_01.txt
```

The judge prints one JSON object. Useful fields:

- `round_id`, `to_move`, `moves_left` — header echo.
- `black_freedom` / `white_freedom` — empty-neighbor counts for each
  side's queen (a beetle-covered neighbor counts as occupied).
- `one_hive` / `hive_connected` — whether the current layout is a single
  connected group.
- `pieces` — every piece's `id`, `color`, `kind`, `q`, `r`, `h`.

## Trying a single move

```
java -jar /app/bin/judge.jar probe --board <round-file> --move W-G1>1,0
```

Reports `legal`, a short `reason` (`ok`, `illegal_move`, or
`unknown_piece`), and `black_freedom` / `moves_left` after the move when it
is legal.

## Replaying a line

```
java -jar /app/bin/judge.jar validate --board <round-file> \
    --moves "W-G1>1,0;B-S1>-1,-2;W-B1>0,-1"
```

`--moves` is a semicolon-separated line of move tokens, alternating white
and black. The judge replays the line and reports per-step legality plus
the final `black_freedom`, `moves_left`, and piece layout. The JSON
includes `all_legal` (every token accepted) and a `steps` array with one
entry per token.

The judge only reports legality and freedom counts. It does not decide
whether a round is a forced win, a trap, or a fort — that is the card's
job.

## House notes

- `/app/tools/sensei_hint.sh` only whispers a quick same-move-budget guess
  for each round. It does not play Black and is not the contest verdict,
  nor is it the refutation threat set.
- The overnight printer under `/app/kiosk/` prints a draft card, but it has
  disagreed with the sealed judge on several rounds. See
  `overnight_printer.md`.
- Scratch sessions under `/app/history/` show the judge dialect on
  throwaway boards. See `match_logs.md`. They are not the contest rounds.
