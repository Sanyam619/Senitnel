# Table judge

The sealed referee is `/app/bin/judge.jar`. A pristine twin sits at
`/opt/tbench/judge.jar`, and the booklet sheets are also pinned under
`/opt/tbench/puzzles`. Useful verbs:

- `view --board <sheet>` — board, hands, sideboard, budget, temples.
- `legal --board <sheet> --side sensei|pupil` — playable colour-tagged moves
  for that side as if it were to move.
- `apply --board <sheet> --move "sensei Tiger:c2-c4"` — one legal ply with
  card rotation.
- `validate --board <sheet> --line "sensei Tiger:c2-c4;pupil Frog:a5-b4"` —
  replay a colour-tagged sequence; reports `all_legal`, `sensei_plies`,
  `temple`, `master_capture`, `winner`, `sideboards`.
- `validate --coop ...` — after each Sensei ply, if the game is not over,
  force the turn back to Sensei (Pupil sits; cards already rotated).

The jar is the table's voice for legality and finishes. It does not print
tournament verdicts (`win` / `trap` / `fort`) for you. The overnight kiosk
drafts and the sensei whisper are not the referee.
