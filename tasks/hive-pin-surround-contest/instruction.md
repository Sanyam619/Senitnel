# Hive pin-and-surround tournament

Submit `/output/hive-card.json` covering the ten White-to-move insect rounds
under `/app/puzzles/`. Card vocabulary: schema_tag, rounds, board_id, status,
key_bug, sequence, freedom, refutations, coop_pin. Exact spellings, freedom
floors, insect movement, one-hive continuity, and coverage rules are under
`/app/docs/`.

White is trying to surround Black's queen so its freedom drops to the published
floor. Black answers when the fight matters. Sensei whispers and overnight
kiosk drafts are surface-only. The sealed table judge at `/app/bin/judge.jar`
is the authority for legal insect moves, beetle covers, grasshopper lines, and
freedom counts. Leave the sealed judge and the puzzle sheets unchanged. A
finished card must stay byte-identical if it is filed again with no edits.
