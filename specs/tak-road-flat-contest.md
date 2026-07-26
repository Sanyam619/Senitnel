### Decision
GO — Attempt 1.
- Primary activity is Tak road analysis and tournament-card filing under a sealed table judge, so open category `games` fits.
- Hardness is road connectivity × standing-stone blocks × capstone flatten × stack carry limits, plus win/trap/fort discrimination against sensei/kiosk surface bait.

### Metadata
- version: 2
- Task name: tak-road-flat-contest
- Title: Tak Road Contest
- Category: games
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [tak, road-contest, tournament, table-judge, puzzle-book, score-card]
- Milestones: 0

## Authoring Brief

### Public contract
The player files `/app/answers.json` for eleven White-to-move Tak midgame rounds under `/app/puzzles/`. Schema: `schema_tag`, `rounds` array of `{board_id, status, key_square, road_len, sequence, refutations, coop_road}`. House rules for roads, standing stones, capstone flattening, stack carry limits, and road-length floors live under `/app/docs/`. Puzzle bytes and sealed `/app/bin/judge.jar` remain unchanged. Sensei and kiosk drafts are surface-only. A win may finish immediately or after every legal Black flat reply, and its representative sequence alternates White/Black/White when needed. Trap rounds need refutation coverage (required ⊆ submitted) for every graded blocking first move. A finished card must stay byte-identical when refiled with no edits. Verifier re-validates roads with the sealed judge.

### Failure topology
The booklet mixes forced north–south White roads (`win`), cooperative-only roads (`trap`), and unreachable roads (`fort`). Sensei ignores carry limits and stamps coop-looking lanes as ready; the overnight kiosk stamps those as wins. Correct filing requires combining winding connectivity, stack legality, standing blocks, capstone flatten, every adversarial Black flat reply, dense threat coverage, and exact shortest-road length (no padding via non-forcing slides).

### Environment shape
Eleven puzzle sheets, sealed Java table judge, contest docs (score card, table judge, board format, contest rules, road floors, overnight printer, match logs), sample history, surface-only sensei, overnight card printer. Verifier independently recomputes outcomes from sealed puzzles.

### Required artifacts
Standard non-milestone layout: `instruction.md`, `task.toml`, `output_contract.toml`, `environment/` (≥20 files excl. Dockerfile), `solution/solve.sh` + opaque desk packages, `tests/test.sh` + `test_outputs.py`.

### Test plan
1. `test_card_shape` — schema_tag, eleven ascending rounds, required fields (not format-only; status vocabulary checked).
2. `test_printer_repeats_completed_card` — emit_card.sh twice is byte-identical on a finished card.
3. `test_judge_seal_unchanged` — judge + puzzles match `/opt/seal` seals.
4. `test_status_matches_search` — at least ten win/trap/fort + coop_road rows match independent force/coop search.
5. `test_win_key_square_and_sequence` — all but one win has a forcing first square + judge-legal alternating sequence; road_len exact.
6. `test_reply_proof_slide_wins` — non-immediate wins survive Black's reply and finish by legal slide.
7. `test_trap_refutation_coverage` — all but one trap covers required threat moves; each submitted reply kills immediate finish.
8. `test_dense_trap_refutations` — the widest threat set has near-complete legal reply coverage.
9. `test_fort_rows` — forts have empty keys/seqs/refs; coop unreachable.
10. `test_sensei_is_not_the_verdict` — all but one trap that sensei calls ready stays a trap.
11. `test_road_len_not_padded` — all but one win road_len equals the true shortest road after sequence.
12. `test_carry_limit_respected` — win sequences include legal slides and never exceed the board carry limit.
13. `test_standing_blocks_road` — near-complete win lines form real roads and at least one flattens a standing top.

Every test is independently scorable from the card + sealed fixtures (no chain dependency on a single golden).

### Drafting guardrails
Do not publish per-board answers, label puzzle sheets with statuses, expose a force-search command in the judge, or turn the instruction into a board-by-board checklist. Document ROAD_FLOOR, threat/refutation, carry limit, and coop_road in `/app/docs/` for fairness. Keep `languages=["python"]` and tournament tags. No repair/debug/cutover vocabulary.

### Triviality Ledger
- Sensei "ready_lane" on traps → filing all ready rounds as `win` fails status + refutation tests.
- Kiosk draft stamps sensei wins → fails independent force/coop search and judge-validated sequences.
- Padding `road_len` or inventing long non-forcing slides → fails road_len equality and forcing checks.
- Ignoring carry limits (sensei-style) → illegal slides fail judge validate.
- Counting standing stones as road stones → road connectivity fails vs judge.
- Covering only some threat first moves → fails ⊆ refutation coverage on traps.
- Editing judge/puzzles → fails seal immutability test.

### Per-gate Pitfall Inventory
- RC1/RC7: oracle derives card via search packages (not sed/revert); substantive LOC in op_a/op_b/op_c.
- RC2: avoid `broken_*` / answer filenames; desk package names stay opaque (`op_a`/`op_b`/`op_c`).
- RC3: tests recompute win/trap/fort and judge-validate sequences — not format-only.
- RC4/RC5: EXPECTED from sealed `/opt/seal` puzzles inside tests, not golden files under environment.
- RC6: instruction symptoms-only; rules live under `/app/docs/`.
- GX9/GX10: no per-board answer triples in instruction; no polarity contradictions.
- Static: hashed pytest lockfile, `check=` on subprocess, `languages=["python"]`, games tags, no PLR0124 `v==v`.

### Initial Draft Commitments
- `tasks/tak-road-flat-contest/instruction.md`
- `tasks/tak-road-flat-contest/task.toml`
- `tasks/tak-road-flat-contest/output_contract.toml`
- `tasks/tak-road-flat-contest/environment/Dockerfile`
- `tasks/tak-road-flat-contest/environment/.dockerignore`
- `tasks/tak-road-flat-contest/environment/requirements.txt`
- `tasks/tak-road-flat-contest/environment/fixtures/judge.jar`
- `tasks/tak-road-flat-contest/environment/puzzles/board_01.txt` … `board_11.txt`
- `tasks/tak-road-flat-contest/environment/docs/tournament_card.md`
- `tasks/tak-road-flat-contest/environment/docs/table_judge.md`
- `tasks/tak-road-flat-contest/environment/docs/board_format.md`
- `tasks/tak-road-flat-contest/environment/docs/contest_rules.md`
- `tasks/tak-road-flat-contest/environment/docs/road_floors.md`
- `tasks/tak-road-flat-contest/environment/docs/overnight_printer.md`
- `tasks/tak-road-flat-contest/environment/docs/match_logs.md`
- `tasks/tak-road-flat-contest/environment/tools/sensei_hint.sh`
- `tasks/tak-road-flat-contest/environment/kiosk/emit_card.sh`
- `tasks/tak-road-flat-contest/environment/kiosk/draft.py`
- `tasks/tak-road-flat-contest/environment/kiosk/sheet_load.py`
- `tasks/tak-road-flat-contest/environment/history/game_01.txt`
- `tasks/tak-road-flat-contest/environment/history/game_02.txt`
- `tasks/tak-road-flat-contest/environment/history/game_03.txt`
- `tasks/tak-road-flat-contest/environment/history/game_04.txt`
- `tasks/tak-road-flat-contest/solution/solve.sh`
- `tasks/tak-road-flat-contest/solution/board_hunt/op_b.py`
- `tasks/tak-road-flat-contest/solution/desk_books/op_a.py`
- `tasks/tak-road-flat-contest/solution/card_out/op_c.py`
- `tasks/tak-road-flat-contest/tests/test.sh`
- `tasks/tak-road-flat-contest/tests/test_outputs.py`
- `specs/tak-road-flat-contest.md`
- `specs/tak-road-flat-contest-reviewer.md`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table
- path: solution/board_hunt/op_b.py
  symbol: force_win
  kind: function
  signature: force_win(state, white_to_move=True)
  purpose: evaluate whether White can force a north-south road against fighting Black
- path: solution/desk_books/op_a.py
  symbol: classify
  kind: function
  signature: classify(state)
  purpose: assign win/trap/fort from force and coop searches
- path: solution/desk_books/op_a.py
  symbol: build_trap_refs
  kind: function
  signature: build_trap_refs(state)
  purpose: cover every threat first move with a Black reply
- path: solution/card_out/op_c.py
  symbol: build_round
  kind: function
  signature: build_round(board_id, path)
  purpose: assemble one derived tournament row

#### flipping_point_contract
locations:
  - id: A
    path: solution/board_hunt/op_b.py
    controls_tests: [test_status_matches_search, test_win_key_square_and_sequence, test_road_len_not_padded]
  - id: B
    path: solution/desk_books/op_a.py
    controls_tests: [test_trap_refutation_coverage, test_fort_rows, test_standing_blocks_road]
  - id: C
    path: solution/card_out/op_c.py
    controls_tests: [test_card_shape, test_sensei_is_not_the_verdict, test_carry_limit_respected]
no_single_location_flips_majority: true
concentration_cap: 0.5

#### decoy_manifest
- environment/tools/sensei_hint.sh — ignores carry limits; false-green ready_lane on traps
- environment/kiosk/draft.py — overnight draft that stamps ready_lane as win

#### code_forbidden_tokens
[road, flat, standing, capstone, carry, trap, fort, refutation, threat, sequence, schema, booklet, tournament, puzzle, judge, sensei, kiosk]
