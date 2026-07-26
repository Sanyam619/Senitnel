# Table judge

The table judge is the sealed program at `/app/bin/judge.jar`. Ask it about
legal play with:

```
java -jar /app/bin/judge.jar <command> --board <round-file> [options]
```

Leave that jar unchanged. Integrity of the sealed binary is checked by the
verifier against sealed copies at `/opt/tbench/judge.jar` and
`/opt/tbench/puzzles/`.

## Looking at a round

```
java -jar /app/bin/judge.jar view --board /app/puzzles/board_01.txt
```

The judge prints one JSON object with `board_id`, `to_move`, `moves_left`,
side counts, flying flags, and the current men.

## Legal slides / flights

```
java -jar /app/bin/judge.jar legal --board <round-file>
```

Adds a `legal_moves` array of tokens for the side to move.

## Trying a single turn

```
java -jar /app/bin/judge.jar probe --board <round-file> \
    --move W:g4-g7 --remove b6
```

Reports `legal`, a short `reason`, `mills` formed by the landing, and the
resulting layout when the turn (including required removals) is accepted.
`--remove` may list several points separated by commas when a landing
closes more than one mill.

## Replaying a line

```
java -jar /app/bin/judge.jar validate --board <round-file> \
    --moves "W:f4-g4;B:a4-b4;W:g4-g7" --removals "b6"
```

`--moves` is a semicolon-separated line of move tokens. `--removals` is a
semicolon-separated list of Black points consumed in mill order after each
White mill on that line. The judge reports per-step legality, `all_legal`,
and `mill_total`.

The judge only reports legality, mills, and removals. It does not decide
whether a round is a forced win, a trap, or a fort — that is the card's
job.

## House notes

- `/app/tools/sensei_hint.sh` only whispers a quick same-budget guess for
  each round. It does not play Black and is not the contest verdict, nor
  is it the refutation threat set. It also ignores the mill-removal
  restriction when it cheers.
- The overnight printer under `/app/kiosk/` prints a draft card, but it has
  disagreed with the sealed judge on several rounds. See
  `overnight_printer.md`.
- Scratch sessions under `/app/history/` show the judge dialect on
  throwaway boards. See `match_logs.md`. They are not the contest rounds.
