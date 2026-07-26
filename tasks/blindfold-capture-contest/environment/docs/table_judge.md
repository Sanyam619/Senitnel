# Table judge

The table judge is the sealed program at `/app/bin/judge.jar`. You ask it about legal play with:

```
java -jar /app/bin/judge.jar <command> [options]
```

Leave that jar unchanged. Integrity of the sealed binary is checked by the verifier against a copy under `/opt/tbench/` that is not stored beside the jar under `/app/bin/`.

## Trying a line on a contest round

```
java -jar /app/bin/judge.jar validate --board <board-file> --moves "<sequence>"
```

- `--board` points at a round file (see `board_format.md`).
- `--moves` is a semicolon-separated line such as `black e2e4|silent;white e7e5|silent`. An empty string means no moves yet.

The judge prints one JSON summary. Important fields:

- `all_legal` — every tagged step matched house rules.
- `target_captured` — the marked defender piece is no longer on the board.
- `target_empty` — same condition as `target_captured` (the mark has left the board). Either flag may be used to recognize a finished capture.
- `final_board` / `steps` — replay detail.

On an announce mismatch, a step carries `announce_expected` (the house-correct tag the judge computed) and `announce_provided` (the tag on the submitted segment). Capture-with-check uses the compound form `taken:<sq>+check`.

The judge never names which announce custom is live in prose — recover it from match logs and from these fields.

## Scratch try

```
java -jar /app/bin/judge.jar probe --board <board-file> --try <move>
```

## Round view

```
java -jar /app/bin/judge.jar view --board <board-file>
```

## House notes

- `/app/tools/sensei_hint.sh` only whispers a surface fillability guess. It does not play White and is not the tournament card verdict.
