# Tak road-and-flat tournament

Write `/app/answers.json` covering eleven White-to-move Tak midgame rounds. For each round, decide whether White can force a north-south road of flats and capstones when Black answers with flats, and whether White can still finish that road if Black never moves.

Card vocabulary: rounds, board_id, status, key_square, road_len, sequence, refutations, coop_road. Standing stones block roads, a capstone may flatten a standing top, stack slides obey the carry limit, road length floors, threat coverage, and the move dialect are documented under `/app/docs/` (`tournament_card.md`, `table_judge.md`, and the other house notes there).

An overnight kiosk draft under `/app/kiosk/` stamps cheerful ready lanes as wins. The sensei whisper under `/app/tools/` ignores carry and standing rules and is not the card verdict. Match logs under `/app/history/` show how the sealed table judge at `/app/bin/judge.jar` speaks. Leave the sealed judge and the puzzle sheets unchanged.
