# Amazons territory enclosure contest

File `/output/amazons-card.json` for the eleven White-to-move Amazons endgame
rounds under `/app/puzzles/`. Card vocabulary: schema_tag, rounds, board_id,
status, best_move, territory_delta, sequence, refutations, coop_enclose. Queen
moves, arrow shots, exclusive-region counting, the territory floor, the
three-turn White budget, trap refutation coverage, and the announce-free move
dialect are documented under `/app/docs/`.

An overnight kiosk draft under `/app/kiosk/` leans on a fourth-turn cooperative
hunt and stamps every round a win. The sensei whisper under `/app/tools/` counts
empty squares, not reachable exclusive territory. Match logs under
`/app/history/` show how the sealed table judge at `/app/bin/judge.jar` speaks.
Leave the sealed judge and the round sheets unchanged. A finished card must stay
byte-identical when the desk emits it twice with no edits.
