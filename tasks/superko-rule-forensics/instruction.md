# Weiqi capture tournament

Twelve Black-to-move rounds sit under `/app/puzzles/`. Match books under `/app/history/` use this table's ko rule. Sealed judge: `/app/bin/judge.jar`. Sensei whisper: `/app/tools/`. House rules, card format, and overnight printer floor notes (including where the printer sources live and how to run its doctor/emit checks) are under `/app/docs/`.

The overnight printer recently diverged from the sealed table on three points: its ko-family guess from the match books, stamping White-pass fills as forced wins, and filing pass-only reply certificates on trap rounds. Sensei-green rounds still look fillable when White always passes, yet White liberty answers leave the target stone in place.

Repair the overnight printer so its doctor and emit checks agree with the sealed table on the live ko family, forced wins versus White-pass traps, and White liberty replies that keep the target. Hand-writing `/app/answers.json` alone does not clear grading. Also hand in `/app/answers.json` covering every round under the live ko rule. Card vocabulary: rule, boards, board_id, status, coop_capturable, sequence, refutations. Leave the sealed judge binary unchanged.
