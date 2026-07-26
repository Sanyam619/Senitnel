# Quoridor path-block tournament

Submit `/output/quoridor-card.json` covering the eleven Black-to-move Quoridor wall rounds under `/app/puzzles/`. Card vocabulary: schema_tag, rounds, board_id, status, key_wall, path_len, sequence, refutations, coop_block. Exact spellings, floors, and coverage rules are under `/app/docs/`.

Black is trying to raise White's shortest path to the south edge up to the published floor by placing walls. White answers with pawn steps when the fight matters. Sensei whispers and overnight kiosk drafts are surface-only. The sealed table judge at `/app/bin/judge.jar` is the authority for legal walls, pawn steps, and shortest-path lengths. Leave the sealed judge and the puzzle sheets unchanged. A finished card must stay byte-identical if it is filed again with no edits.
