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

The judge prints one JSON object with `to_move`, `budget`, height rows, and
occupancy.

## Legal turns

```
java -jar /app/bin/judge.jar legal --board <round-file> [--side first|second]
```

Lists legal move tokens for the chosen side (default: side to move).

## Trying a single turn

```
java -jar /app/bin/judge.jar apply --board <round-file> --move F:b3-c3
```

Applies one legal token and prints the resulting view.

## Replaying a line

```
java -jar /app/bin/judge.jar validate --board <round-file> \
    --moves "F:b3-c2:b3;S:e1-d1:c1;F:c2-b3"
```

`--moves` is a semicolon-separated line of move tokens. The judge reports
`all_legal` and whether a First summit onto level 3 occurred.

The judge only reports legality and ascent detection. It does not decide
whether a round is a forced win, a trap, or a fort — that is the card's job.

## House notes

- `/app/tools/sensei_hint.sh` only whispers a quick peak look for each round.
  It ignores dome blocks and does not play Second. It is not the contest
  verdict, nor is it the refutation threat set.
- The overnight printer under `/app/kiosk/` prints a draft card, but it has
  disagreed with the sealed judge on several rounds. See
  `overnight_printer.md`.
- Scratch sessions under `/app/history/` show the judge dialect on throwaway
  boards. See `match_logs.md`. They are not the contest rounds.
