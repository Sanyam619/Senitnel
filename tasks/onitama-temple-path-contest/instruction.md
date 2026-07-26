# Onitama temple-path tournament

Write `/app/answers.json` covering twelve Sensei-to-move Onitama rounds. For
each round, decide whether Sensei can force a temple step or master capture
when Pupil fights back with rotating move cards, and whether Sensei can still
finish if Pupil never moves.

Card vocabulary: rounds, board_id, status, card_used, mate_in, sequence,
sideboard, refutations, coop_temple. Move-card rotation, temple and master
capture finishes, mate-length floors, trap threat coverage, and the colour-tagged
move dialect live under `/app/docs/` (`tournament_card.md`, `table_judge.md`,
and the other house notes there).

An overnight kiosk draft under `/app/kiosk/` leans on a long cooperative hunt
and stamps every round a win. The sensei whisper at `/app/tools/sensei_hint.sh`
skips the post-move sideboard swap and is not the card verdict. Match logs under
`/app/history/` show how the sealed table judge at `/app/bin/judge.jar` speaks.
Leave the sealed judge and the puzzle sheets unchanged.
