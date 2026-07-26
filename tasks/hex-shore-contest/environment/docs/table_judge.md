# Table judge

The table judge is the sealed program at `/app/bin/judge.jar`. Ask it about
legal play with:

```
java -jar /app/bin/judge.jar <command> --board <round-file> [options]
```

Leave that jar unchanged. Integrity of the sealed binary is checked by the
verifier against a copy kept away from `/app/bin/`.

## Looking at a round

```
java -jar /app/bin/judge.jar view --board /app/puzzles/board_01.txt
```

The judge prints one JSON object. Useful fields:

- `size` — the board width.
- `to_move` — whose turn it is (always `black` in this booklet).
- `black_linked` / `white_linked` — whether that side already holds its
  finished shore chain on the position as printed (north-south for Black,
  east-west for White).
- `board` — the grid, rows joined by `/`.

## Trying a single stone

```
java -jar /app/bin/judge.jar probe --board <round-file> --side black --cell c3
```

Reports `legal` (the cell was empty and on the board), `links` (the played
side now holds a finished shore chain), and the `black_linked` /
`white_linked` flags after the stone is placed.

## Replaying a line

```
java -jar /app/bin/judge.jar validate --board <round-file> \
    --moves "black c3;white d2;black c4"
```

`--moves` is a semicolon-separated line of `<side> <cell>` steps starting
with the side to move. The judge replays it, reporting per-step legality
and, at the end, `all_legal`, `black_linked`, `white_linked`, and the
`final_board`. A step is rejected if it is off the board, lands on an
occupied cell, or is played out of turn.

The judge only reports legality and shore-chain status. It does not decide
whether a round is a forced win, a trap, or a fort — that is the card's job.

## House notes

- `/app/tools/sensei_hint.sh` only whispers a surface fillability guess for
  each round. It does not play White and is not the contest verdict, nor is
  it the refutation threat set.
- The overnight printer under `/app/kiosk/` prints a draft card, but it has
  disagreed with the sealed judge on several rounds. See
  `overnight_printer.md`.
