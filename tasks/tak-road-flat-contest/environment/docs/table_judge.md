# Table judge

The table judge is the sealed program at `/app/bin/judge.jar`. Ask it about
legal play with:

```
java -jar /app/bin/judge.jar <command> --board <round-file> [options]
```

Leave that jar unchanged. Integrity of the sealed binary is checked by the
verifier against sealed copies at `/opt/seal/judge.jar` and
`/opt/seal/puzzles/` (kept away from `/app/bin/`). An adjacent
`/app/bin/judge.jar.sha256` sidecar is not part of this desk.

## Looking at a round

```
java -jar /app/bin/judge.jar view --board /app/puzzles/board_01.txt
```

The judge answers with a short board summary: whose turn it is, remaining
reserves, the carry limit, whether a White north-south road already meets the
contest floor, and a grid print of the stacks (north first).

## Trying a single move

```
java -jar /app/bin/judge.jar probe --board <round-file> --move F:a1
```

Reports `legal`, a short `reason`, and the `white_road` value after the move
when it is legal. Illegal examples include occupied placements, spending a
flat or cap when none remain, carry above the limit, stacking onto a capstone,
or a multi-stone carry onto a standing stone.

## Replaying a line

```
java -jar /app/bin/judge.jar validate --board <round-file> \
    --moves "F:a2;F:a1"
```

`--moves` is a semicolon-separated line of placement and slide tokens. The
judge replays the line and reports per-step legality plus final `white_road`
and `road_complete`. The JSON includes `all_legal` (every token accepted).

The judge only reports legality and road length. It does not decide whether a
round is a forced win, a trap, or a fort — that is the card's job.

## House notes

- `/app/tools/sensei_hint.sh` only whispers a surface lane guess for each
  round. It does not play Black and is not the contest verdict, nor is it the
  refutation threat set.
- The overnight printer under `/app/kiosk/` prints a draft card, but it has
  disagreed with the sealed judge on several rounds. See
  `overnight_printer.md`.
- Scratch sessions under `/app/history/` show the judge dialect on throwaway
  boards. See `match_logs.md`. They are not the contest rounds.
