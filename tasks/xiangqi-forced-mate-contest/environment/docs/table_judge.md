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

Useful fields include `to_move`, `board`, `red_in_check`, `black_in_check`,
and `black_mated` on the printed position.

## Trying a single move

```
java -jar /app/bin/judge.jar probe --board <round-file> --side red --move e5e9
```

Reports `legal`, `gives_check`, `mates`, and the board after the try. ICCS
moves are four characters (`e5e9`).

## Replaying a line

```
java -jar /app/bin/judge.jar validate --board <round-file> \
    --moves "red e5e9;black e9d9;red e2e9"
```

`--moves` is a semicolon-separated line of `<side> <uci>` steps. The judge
replays it, reporting per-step legality and, at the end, `all_legal`,
`black_mated`, and `river_cross` (true when any step crossed the river).

The judge only reports legality, checks, and mate flags. It does not decide
whether a round is a forced win, a trap, or a fort — that is the card's job.

## House notes

- `/app/tools/sensei_hint.sh` only whispers a surface cooperative-mate guess
  and ignores horse hobble. It does not play Black and is not the contest
  verdict, nor is it the refutation threat set.
- The overnight printer under `/app/kiosk/` prints a draft card, but it has
  disagreed with the sealed judge on several rounds. See
  `overnight_printer.md`.
