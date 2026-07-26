# Xiangqi forced-mate tournament

Submit `/output/xiangqi-card.json` covering the twelve Red-to-move Xiangqi rounds under `/app/puzzles/`. Card vocabulary: schema_tag, rounds, board_id, status, mate_in, sequence, river_cross, refutations, coop_mate. Palace bounds, horse hobble, cannon screens, mate-length floors, river crossing, and sideline refutation coverage are under `/app/docs/`.

Forced mate against best Black defense is not the same as a cooperative mate line. Sensei whispers and overnight kiosk drafts are surface-only. The sealed table judge at `/app/bin/judge.jar` is the authority for legal tries. Leave the sealed judge and the puzzle sheets unchanged. A finished card must stay byte-identical if it is filed again with no edits.
