# Table judge

The table judge is the sealed program at `/app/bin/judge.jar`. Ask it about
legal play with:

```
java -jar /app/bin/judge.jar <command> --board <round-file> [options]
```

Leave that jar unchanged. Integrity of the sealed binary is checked by the
verifier against sealed copies at `/opt/tbench/judge.jar` and
`/opt/tbench/puzzles/` (kept away from `/app/bin/`). An adjacent
`/app/bin/judge.jar.sha256` sidecar is not part of this desk.

## Looking at a round

```
java -jar /app/bin/judge.jar view --board /app/puzzles/board_01.txt
```

The judge prints one JSON object. Useful fields:

- `size` — always 5 for this booklet.
- `to_move` — whose turn it is (always `black` here).
- `black` / `white` — pawn squares.
- `walls` — placed wall ids.
- `walls_left` — Black's remaining wall inventory.
- `black_path` / `white_path` — shortest orthogonal path lengths to each
  side's goal (or `null` if cut off).
- `black_reachable` / `white_reachable` — whether a path still exists.
- `board` — grid rows joined by `/` (north first).

## Trying a single wall

```
java -jar /app/bin/judge.jar probe --board <round-file> --wall h-b2
```

Reports `legal`, a short `reason`, and the `black_path` / `white_path`
values after the wall when it is legal. Illegal placements include
off-board anchors, overlapping or crossing segments, spending a wall when
none remain, or cutting either pawn off from its goal.

## Replaying a line

```
java -jar /app/bin/judge.jar validate --board <round-file> \
    --moves "wall:h-b2;pawn:c4;wall:v-d3"
```

`--moves` is a semicolon-separated line of `wall:<id>` and `pawn:<cell>`
tokens. Walls are Black placements; `pawn:` steps move White. The judge
replays the line and reports per-step legality plus final paths and
positions. The JSON includes `all_legal` (every token accepted),
`white_path`, `black_path`, and the final pawn squares.

The judge only reports legality and shortest-path lengths. It does not
decide whether a round is a forced win, a trap, or a fort — that is the
card's job.

## House notes

- `/app/tools/sensei_hint.sh` only whispers a greedy corridor guess for each
  round. It does not play White and is not the contest verdict, nor is it
  the refutation threat set.
- The overnight printer under `/app/kiosk/` prints a draft card, but it has
  disagreed with the sealed judge on several rounds. See
  `overnight_printer.md`.
- Scratch sessions under `/app/history/` show the judge dialect on throwaway
  boards. See `match_logs.md`. They are not the contest rounds.
