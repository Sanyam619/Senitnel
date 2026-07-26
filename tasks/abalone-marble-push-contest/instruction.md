# Abalone marble-push tournament

Write `/app/answers.json` covering ten Black-to-move Abalone midgame rounds. For
each round, decide whether Black can force a marble off the board when White
fights, whether Black only reaches the ejection floor if White sits still, or
whether the floor stays out of reach.

Card vocabulary: rounds, board_id, status, key_push, ejected, sequence,
refutations, coop_eject. Inline pushes, sumito strength, side-steps, the
ejection floor, the three-push Black budget, trap replies, and the move dialect
are documented under `/app/docs/` (`tournament_card.md`, `table_judge.md`, and
the other house notes there).

An overnight kiosk draft under `/app/kiosk/` stamps cheerful cooperative lines
as wins. The sensei whisper under `/app/tools/` only checks contiguous groups
and is not the card verdict. Match logs under `/app/history/` show how the
sealed table judge at `/app/bin/judge.jar` speaks. Leave the sealed judge and
the puzzle sheets unchanged.
