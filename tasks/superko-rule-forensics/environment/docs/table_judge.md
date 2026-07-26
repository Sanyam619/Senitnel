# Table judge

The table judge is the sealed program at `/app/bin/judge.jar` (with sibling checksum `/app/bin/judge.jar.sha256`). You ask it about legal play with:

```
java -jar /app/bin/judge.jar <command> [options]
```

## Trying a line on a contest round

```
java -jar /app/bin/judge.jar validate --board <board-file> --moves "<sequence>"
```

- `--board` points at a round file (see `board_format.md`).
- `--moves` is a semicolon-separated line such as `black 3,4;white 3,5;black pass`. An empty string means no moves yet.

Turns follow `to_move` in the round file and then alternate. A pass uses the turn without placing a stone.

The judge prints one JSON summary including `all_legal`, `target_empty`, `final_board`, and `steps` (plus target coordinates). It never names which ko family is live — that is part of the contest.

## Scratch replay on an empty goban

```
java -jar /app/bin/judge.jar replay --size 9 --first black --moves "<sequence>"
```

Useful for recreating positions from the match books under `/app/history/`.

## House rules

- The ko family is fixed for this table; there is no switch.
- Gobans are 9×9. Suicide is illegal unless the play captures.
- `/app/tools/sensei_hint.sh` only whispers liberty counts. It does not play White and is not the tournament card verdict.
