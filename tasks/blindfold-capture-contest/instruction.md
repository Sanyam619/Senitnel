# Blindfold capture tournament

Write `/app/answers.json` covering nine Black-to-move rounds. For each round, decide whether Black can force capture of the marked White piece within five Black stone plays when White fights to keep it on the board, and whether Black can still take that piece if White always passes.

Card vocabulary: boards, board_id, status, coop_capturable, sequence, refutations. Stone-count floors, the five-stone force budget, White fighting replies, fort shapes (`coop_capturable` false when the mark survives even White-pass), announce customs including `taken:<sq>+check`, and refutation coverage are documented under `/app/docs/` (`tournament_card.md`, `table_judge.md`, and the other house notes there).

An overnight card printer disagreed with the sealed table judge on several rounds and on how captures are announced. Match logs under `/app/history/` show the announce custom the table expects. The sensei whisper under `/app/tools/` only checks surface fillability and is not the card verdict.

Rounds: `/app/puzzles/`. Printer drafts: `/app/kiosk/`. Sealed judge: `/app/bin/judge.jar`. Leave the sealed judge unchanged.
