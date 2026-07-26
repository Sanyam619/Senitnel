# Table judge

The sealed referee is `/app/bin/judge.jar`. A pristine twin sits at
`/opt/tbench/judge.jar`, and the booklet sheets are also pinned under
`/opt/tbench/puzzles`. Useful verbs:

- `view --board <sheet>` — grid, legal columns, budget reminder.
- `legal --board <sheet> --side yellow|red` — playable columns.
- `apply --board <sheet> --side yellow|red --column N` — one gravity drop.
- `validate --board <sheet> --line "yellow 3;red 1;yellow 3"` — replay a
  colour-tagged sequence; reports `all_legal`, `yellow_drops`, `connected`.

The jar is the table's voice for legality and connects. It does not print
tournament verdicts (`win` / `trap` / `draw`) for you. The overnight kiosk
drafts and the sensei whisper are not the referee.
