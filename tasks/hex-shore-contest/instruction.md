# Hex shore tournament

Submit `/output/hex-card.json` covering the twelve Black-to-move Hex midgame rounds under `/app/puzzles/`. Card vocabulary: schema_tag, rounds, board_id, status, winning_side, coop_fillable, key_cells, refutations. Exact spellings, floors, and coverage rules are under `/app/docs/`.

Black is trying to build a chain of stones from the north shore to the south shore. White is trying to hold an east-west blockade. Sensei whispers and overnight kiosk drafts are surface-only. The sealed table judge at `/app/bin/judge.jar` is the authority for legal tries and shore-chain status. Leave the sealed judge and the puzzle sheets unchanged. A finished card must stay byte-identical if it is filed again with no edits.
