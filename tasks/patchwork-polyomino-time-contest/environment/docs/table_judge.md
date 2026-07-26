# Talking to the sealed table judge

`/app/bin/judge.jar` is the referee for this booklet. It parses a sheet and
replays a filed line of turns, reporting what the table saw. It never rates a
round — the verdict is yours.

```
java -jar /app/bin/judge.jar view --board /app/puzzles/board_01.txt
java -jar /app/bin/judge.jar validate --board /app/puzzles/board_01.txt \
  --line 'red take P1 @ r0c2;blue advance;red advance'
```

## Move dialect

A line is a semicolon-separated list of turns. Each turn names the side and the
action:

- `red take P3 @ r1c0` — Red takes patch `P3` and lays it with its top-left cell
  (its smallest row, then smallest column) anchored at `r1c0`.
- `red advance` — Red advances.
- `blue take P2` — Blue takes patch `P2` (no placement; Blue's quilt is not
  tracked).
- `blue advance` — Blue advances.

The judge enforces turn order: a turn is illegal if it is filed for the side
that is not to move. It also enforces affordability, market availability, and —
for Red takes — that the polyomino lands inside the quilt without overlapping a
blocked or already-covered cell.

## What `validate` reports

A JSON object with, among others:

- `all_legal` — every filed turn was legal.
- `terminal` — both tokens reached the end of the track.
- `red_time`, `blue_time`, `red_buttons` — end-of-line positions and Red's bank.
- `red_score` — Red's closing score (buttons minus two per empty cell).
- `floor`, `floor_met` — the sheet floor and whether the line reached it.
- `red_first_patch` — the first patch Red took, or empty.
- `blue_advances_only` — true when Blue only advanced across the whole line.
