# Santorini summit tournament

Write `/app/answers.json` covering eleven First-to-move Santorini midgame
rounds. For each round, decide whether First can force a level-3 summit when
Second answers with ordinary turns, whether First can still summit if Second
never moves, and — on rounds Second can hold — which Second reply answers
each of First's threats.

Card vocabulary: rounds, board_id, status, key_move, sequence, refutations,
coop_summit. Worker moves, build heights, dome blocks, win-by-ascent, turn
budgets, threat coverage, and the move dialect are documented under
`/app/docs/`.

An overnight kiosk printed a draft card the table has thrown out, and the
sensei whisper ignores dome blocks. Match logs under `/app/history/` show the
dialect the table expects for move tokens.

Rounds: `/app/puzzles/`. Kiosk draft: `/app/kiosk/draft_card.json`. Whisper:
`/app/tools/sensei_hint.sh`. Sealed judge: `/app/bin/judge.jar`. Leave the
sealed judge and the round sheets unchanged.
