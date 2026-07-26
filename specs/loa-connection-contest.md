### Decision
GO — Attempt 1.
- Primary activity is Lines of Action connection play and tournament-card filing under a sealed table judge, so open category `games` fits.
- Hardness is the checker-count step law × enemy-block paths × 8-connected grouping, plus win/trap/fort discrimination against sensei and overnight-kiosk surface bait.

### Metadata
- version: 2
- Task name: loa-connection-contest
- Title: Lines of Action Connection Contest
- Category: games
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [lines-of-action, connection-contest, tournament, table-judge, puzzle-book]
- Milestones: 0

## Authoring Brief

### Public contract
The player files `/output/loa-card.json` for twelve Black-to-move Lines of Action rounds under `/app/puzzles/`. Schema: `schema_tag = "loa-connection-v1"`, `rounds` array of `{board_id, status, key_move, components, sequence, refutations, coop_connect}`. House rules for ortholinear steps, the rank/file checker count that fixes the step length, enemy blocking versus friendly jumping, capture-on-landing, and 8-connected grouping live under `/app/docs/`. Puzzle bytes and the sealed `/app/bin/judge.jar` remain unchanged. Sensei whispers and the overnight kiosk draft are surface-only. A `win` finishes inside two Black turns — either immediately, or with a first move after which every legal White answer still leaves an immediate finish. A `trap` connects only when White never moves, and needs a White answer for every graded pressing first move (required ⊆ submitted). A `fort` cannot be gathered even with White standing still. A finished card must stay byte-identical when the printer refiles it.

### Failure topology
The booklet mixes forced gathers (`win`), cooperative-only gathers (`trap`), and ungatherable positions (`fort`). Sensei searches with any orthogonal step length and no enemy blocking, so it reports `looks_ready_if_uncontested` on every trap and every fort; the overnight kiosk stamps those readings as wins. Correct filing needs the real step law, adversarial White answers, the pressing-move set on traps, the true component count after the filed line, and diagonal adjacency in grouping.

### Environment shape
Twelve puzzle sheets, sealed Java table judge (`view` / `probe` / `validate`), contest docs (tournament card, table judge, board format, contest rules, component floors, overnight printer, match logs), four sample history dialogues on scratch positions, surface-only sensei, overnight card printer with a byte-stable refile path. The verifier independently recomputes every verdict from the sealed puzzles and re-validates filed lines with the judge.

### Required artifacts
Standard non-milestone layout: `instruction.md`, `task.toml`, `output_contract.toml`, `environment/` (30 files excl. Dockerfile), `solution/solve.sh` + `derive.sh` + opaque desk packages, `tests/test.sh` + `tests/test_outputs.py`.

### Test plan
1. `test_card_shape` — schema tag, twelve ascending rounds, field types, status vocabulary.
2. `test_printer_repeats_completed_card` — `emit_card.sh` twice on a finished card is byte-identical.
3. `test_judge_seal_unchanged` — judge + puzzles match the `/opt/table` seals.
4. `test_status_matches_search` — at least eleven of twelve status + `coop_connect` rows match independent force/cooperative search.
5. `test_win_key_move_and_sequence` — all but one win carries a forcing first move, a judge-legal line ending connected, and `components == 1`; the wins that cannot finish at once must file a line that carries a White answer.
6. `test_trap_refutation_coverage` — required pressing moves ⊆ submitted for at least four of five traps; each submitted answer kills the immediate second-move gather.
7. `test_dense_trap_refutations` — the widest pressing set has near-complete legal answer coverage.
8. `test_fort_rows` — forts have empty key/sequence/refutations, `coop_connect` false, and components equal to the sheet count.
9. `test_sensei_is_not_the_verdict` — traps that sensei calls ready stay traps.
10. `test_components_not_padded` — filed win components equal the true count after the filed line, never inflated.
11. `test_checker_count_moves_respected` — win lines validate through the judge, so every step length matches the rank/file checker count.
12. `test_connection_is_eight_adjacent` — at least two win endings are one group only under diagonal adjacency, so 4-adjacency readings fail.

Every test scores independently from the card plus sealed fixtures; no chain dependency on a single golden.

### Drafting guardrails
Do not publish per-board answers, label puzzle sheets with statuses, expose a force search in the judge, or turn the instruction into a board-by-board checklist. Document the step law, the pressing/answer definitions, the force budget (two Black turns), the cooperative budget (five Black moves), and the component floors under `/app/docs/` for fairness. Keep `languages=["bash"]` and tournament tags. No repair/debug/cutover vocabulary anywhere.

### Triviality Ledger
- Sensei `looks_ready_if_uncontested` on traps and forts → filing every ready round as `win` fails status, refutation, and fort tests.
- Kiosk draft stamps sensei readings as wins → fails independent search and judge-validated lines.
- Ignoring the checker count (sensei-style free steps) → illegal lines fail judge `validate`.
- Jumping an enemy checker → illegal line, same failure.
- Reading groups with 4-adjacency only → wrong component counts and wrong verdicts on the diagonal-finish boards.
- Filing a longer gathering plan as a `win` → fails the force budget in the status recompute.
- Padding `components` with extra rearrangements → fails the component floor.
- Covering only some pressing moves on traps → fails ⊆ coverage.
- Editing judge or puzzles → fails seal immutability.

### Per-gate Pitfall Inventory
- RC1/RC7: oracle derives the card through search packages (no sed, no revert); substantive LOC across `op_a`/`op_b`/`op_c`.
- RC2: oracle package directories stay opaque (`line_walk`, `desk_books`, `tally_room`); the card path is written directly, not through a keyword-bearing variable.
- RC3: tests recompute verdicts and judge-validate lines — not format-only.
- RC4/RC5: EXPECTED recomputed inside tests from the sealed `/opt/table` puzzles; no golden answer files under `environment/`.
- RC6: instruction symptoms-only; all vocabulary lives under `/app/docs/`.
- GX9/GX10: no per-board answer triples in the instruction; no polarity contradictions.
- Static: hashed pytest lockfile, explicit `check=` on every `subprocess.run`, no `v == v` idiom, games tags, `languages=["bash"]`, `allow_internet = false`.

### Initial Draft Commitments
- `tasks/loa-connection-contest/instruction.md`
- `tasks/loa-connection-contest/task.toml`
- `tasks/loa-connection-contest/output_contract.toml`
- `tasks/loa-connection-contest/environment/Dockerfile`
- `tasks/loa-connection-contest/environment/.dockerignore`
- `tasks/loa-connection-contest/environment/requirements.txt`
- `tasks/loa-connection-contest/environment/fixtures/judge.jar`
- `tasks/loa-connection-contest/environment/puzzles/board_01.txt` … `board_12.txt`
- `tasks/loa-connection-contest/environment/docs/tournament_card.md`
- `tasks/loa-connection-contest/environment/docs/table_judge.md`
- `tasks/loa-connection-contest/environment/docs/board_format.md`
- `tasks/loa-connection-contest/environment/docs/contest_rules.md`
- `tasks/loa-connection-contest/environment/docs/component_floors.md`
- `tasks/loa-connection-contest/environment/docs/overnight_printer.md`
- `tasks/loa-connection-contest/environment/docs/match_logs.md`
- `tasks/loa-connection-contest/environment/tools/sensei_hint.sh`
- `tasks/loa-connection-contest/environment/kiosk/emit_card.sh`
- `tasks/loa-connection-contest/environment/kiosk/draft.py`
- `tasks/loa-connection-contest/environment/kiosk/sheet_load.py`
- `tasks/loa-connection-contest/environment/history/game_01.txt` … `game_04.txt`
- `tasks/loa-connection-contest/solution/solve.sh`
- `tasks/loa-connection-contest/solution/derive.sh`
- `tasks/loa-connection-contest/solution/line_walk/op_b.py`
- `tasks/loa-connection-contest/solution/desk_books/op_a.py`
- `tasks/loa-connection-contest/solution/tally_room/op_c.py`
- `tasks/loa-connection-contest/tests/test.sh`
- `tasks/loa-connection-contest/tests/test_outputs.py`
- `specs/loa-connection-contest.md`
- `specs/loa-connection-contest-reviewer.md`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table
- path: solution/line_walk/op_b.py
  symbol: moves_for
  kind: function
  signature: moves_for(mine, theirs, size)
  purpose: enumerate legal steps under the rank/file checker count with friendly jumps and enemy blocks
- path: solution/line_walk/op_b.py
  symbol: forcing_moves
  kind: function
  signature: forcing_moves(mine, theirs, size)
  purpose: first moves that survive every legal answer and still finish inside the turn budget
- path: solution/line_walk/op_b.py
  symbol: unopposed_plan
  kind: function
  signature: unopposed_plan(mine, theirs, size, budget)
  purpose: shortest gathering run with the opposing side standing still
- path: solution/line_walk/op_b.py
  symbol: answer_to
  kind: function
  signature: answer_to(mine, theirs, size, press)
  purpose: opposing reply that kills the immediate follow-up gather after a pressing move
- path: solution/desk_books/op_a.py
  symbol: classify
  kind: function
  signature: classify(mine, theirs, size)
  purpose: assign win/trap/fort from the force and unopposed searches
- path: solution/desk_books/op_a.py
  symbol: build_trap_refs
  kind: function
  signature: build_trap_refs(mine, theirs, size)
  purpose: cover every pressing first move with an answer
- path: solution/desk_books/op_a.py
  symbol: scored_components
  kind: function
  signature: scored_components(mine, theirs, size, verdict)
  purpose: component count for the filed position under the floor rules
- path: solution/tally_room/op_c.py
  symbol: build_round
  kind: function
  signature: build_round(board_id, path)
  purpose: assemble one derived contest row

#### flipping_point_contract
locations:
  - id: A
    path: solution/line_walk/op_b.py
    controls_tests: [test_status_matches_search, test_checker_count_moves_respected, test_connection_is_eight_adjacent]
  - id: B
    path: solution/desk_books/op_a.py
    controls_tests: [test_trap_refutation_coverage, test_dense_trap_refutations, test_fort_rows, test_components_not_padded]
  - id: C
    path: solution/tally_room/op_c.py
    controls_tests: [test_card_shape, test_win_key_move_and_sequence, test_sensei_is_not_the_verdict]
no_single_location_flips_majority: true
concentration_cap: 0.5

#### decoy_manifest
- environment/tools/sensei_hint.sh — searches with free orthogonal step lengths and no enemy blocking; false-green on every trap and fort
- environment/kiosk/draft.py — overnight draft that stamps sensei readings as wins

#### code_forbidden_tokens
[connection, trap, fort, refutation, threat, sequence, schema, booklet, tournament, puzzle, judge, sensei, kiosk, card]
