# Nine Men's Morris mill-fork tournament

Submit `/output/morris-card.json` covering the ten White-to-move mill rounds
under `/app/puzzles/`. Card vocabulary: schema_tag, rounds, board_id, status,
key_point, mill_in, sequence, removals, refutations, coop_fork. Mill lines,
forced removals, flying when a side is down to three men, and the mill-count
floor live under `/app/docs/`.

White is trying to close a mill inside each sheet's move budget. Black answers
when the fight matters. Sensei whispers and overnight kiosk drafts are
surface-only. The sealed table judge at `/app/bin/judge.jar` is the authority
for legal slides, flights, mill detection, and removal legality. Leave the
sealed judge and the puzzle sheets unchanged. A finished card must stay
byte-identical if it is filed again with no edits.
