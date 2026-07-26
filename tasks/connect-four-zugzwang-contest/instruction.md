# Connect Four zugzwang contest

File `/output/c4-card.json` for the twelve Yellow-to-move Connect Four rounds
under `/app/puzzles/`. Card vocabulary: schema_tag, rounds, board_id, status,
best_column, win_in, sequence, threats, refutations, coop_win. Gravity drops,
odd/even threat parity, zugzwang counting, the Yellow drop budget, trap and draw
refutation coverage, and the colour-tagged column dialect are documented under
`/app/docs/`.

An overnight kiosk draft under `/app/kiosk/` leans on a long cooperative hunt and
stamps every round a win. The sensei whisper under `/app/tools/` only checks
which columns still accept a disc. Match logs under `/app/history/` show how the
sealed table judge at `/app/bin/judge.jar` speaks. Leave the sealed judge and the
round sheets unchanged. A finished card must stay byte-identical when the desk
emits it twice with no edits.
