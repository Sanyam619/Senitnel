# Table judge

The table judge is the sealed program at `/app/bin/judge.jar`. Ask it about
legal play with:

```
java -jar /app/bin/judge.jar <command> --board <round-sheet> [options]
```

Leave that jar unchanged. Integrity of the sealed binary is checked by the
desk against a copy kept away from `/app/bin/`.

## Looking at a round

```
java -jar /app/bin/judge.jar view --board /app/puzzles/board_01.txt
```

The judge prints one JSON object. Useful fields:

- `size` — the board width.
- `to_move` — whose turn it is (always `black` in this booklet).
- `black_connected` / `white_connected` — whether that side's surviving
  pieces already form a single group on the position as printed.
- `black_components` / `white_components` — how many groups that side holds.
- `board` — the grid, rows joined by `/`.

## Trying one move

```
java -jar /app/bin/judge.jar probe --board <round-sheet> \
    --side black --move c3-b3
```

Reports `legal` (the move obeys the house dialect), `connects` (the side
that moved now holds a single group), and the connection and group counts
for both sides after the move. An illegal try comes back with `legal` false
and the position untouched.

## Replaying a line

```
java -jar /app/bin/judge.jar validate --board <round-sheet> \
    --moves "black a1-a3;white c3-c1;black d3-b3"
```

`--moves` is a semicolon-separated line of `<side> <move>` steps. The judge
replays them in order, reporting per-step legality and, at the end,
`all_legal`, `black_connected`, `white_connected`, the group counts, and the
`final_board`. Replay stops at the first illegal step. A step is turned away
when it breaks the travel distance, passes over an enemy piece, lands on its
own colour, or leaves the board.

The judge only reports legality, connection, and group counts. It does not
decide whether a round is a forced gather, a fighting trap, or a walled-off
fort — that is the card's job.

## House notes

- `/app/tools/sensei_hint.sh` whispers a surface reading for each round. It
  does not play White, it does not respect the travel distance, and it is
  neither the contest verdict nor the refutation threat set.
- The overnight printer under `/app/kiosk/` prints a draft card, but it has
  disagreed with the sealed judge on several rounds. See
  `overnight_printer.md`.
