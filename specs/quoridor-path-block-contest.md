### Decision
GO — Attempt 1.
- The primary activity is Quoridor path-block analysis and tournament-card filing, so `games` is the natural open category.
- Difficulty comes from distinguishing forced path-floor wins from cooperative-only traps across a mixed booklet and constructing valid threat refutations.

### Metadata
- version: 2
- Task name: quoridor-path-block-contest
- Title: Quoridor Path-Block Contest
- Category: games
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [quoridor, path-block, tournament, table-judge, puzzle-book, score-card]
- Milestones: 0

## Authoring Brief

### Public contract
The player files `/output/quoridor-card.json` for eleven Black-to-move Quoridor wall rounds under `/app/puzzles/`. The card records each round's forced/cooperative/fort outcome, a forcing first wall and sequence on wins, cooperative path length on traps/forts, and legal White pawn replies covering every threat wall on traps. Black raises White's south-edge shortest path to PATH_FLOOR=7. Puzzle bytes and sealed `/app/bin/judge.jar` remain unchanged. Output is deterministic JSON in ascending round order.

### Failure topology
The booklet mixes forced wins, cooperative-only traps, and forts. Surface corridor whispers deliberately mark traps as looks_blocked, so sensei cannot decide the tournament result. Correct filing requires combining Quoridor legality, shortest-path floors, adversarial wall/pawn search, and local threat coverage.

### Environment shape
Eleven puzzle sheets, sealed Java table judge, contest docs, sample history logs, surface-only sensei helper, overnight card printer. Verifier independently recomputes outcomes from sealed puzzles.

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table
- path: solution/board_hunt/op_b.py
  symbol: force_win
  kind: function
  signature: force_win(black, white, walls, walls_left, black_to_move=True)
  purpose: evaluate whether Black can force White path >= PATH_FLOOR
- path: solution/desk_books/op_a.py
  symbol: classify
  kind: function
  signature: classify(state)
  purpose: assign win/trap/fort from force and coop searches
- path: solution/desk_books/op_a.py
  symbol: build_trap_refs
  kind: function
  signature: build_trap_refs(state)
  purpose: cover every threat wall with a White pawn reply
- path: solution/card_out/op_c.py
  symbol: build_round
  kind: function
  signature: build_round(board_id, path)
  purpose: assemble one derived tournament row

#### flipping_point_contract
locations:
  - id: A
    path: solution/board_hunt/op_b.py
    controls_tests: [test_status_matches_search, test_win_key_wall_and_sequence]
  - id: B
    path: solution/desk_books/op_a.py
    controls_tests: [test_trap_refutation_coverage, test_fort_rows]
  - id: C
    path: solution/card_out/op_c.py
    controls_tests: [test_card_shape, test_sensei_is_not_the_verdict]
no_single_location_flips_majority: true
concentration_cap: 0.5

#### decoy_manifest
- environment/tools/sensei_hint.sh — greedy corridor false-green on traps
- environment/kiosk/draft.py — overnight draft that stamps looks_blocked as win

#### code_forbidden_tokens
Derived from instruction nouns that must not appear as fix-path symbols:
force_win, classify, build_trap_refs, build_round, PATH_FLOOR, threat_walls
(oracle package names desk_books/board_hunt/card_out and op_a/op_b/op_c are opaque).

### Drafting guardrails
Do not publish per-board answers, label puzzle sheets, expose a force-search command in the judge, or turn the instruction into a board-by-board checklist. Document PATH_FLOOR, threat/refutation, and coop_block in docs for fairness.

### Triviality Ledger
- Sensei `looks_blocked` on traps → filing all blocked rounds as `win` fails status + refutation tests.
- Kiosk draft stamps sensei wins → fails independent force/coop search and judge-validated sequences.
- Padding `path_len` or inventing long sequences → fails path_len equality and inventory tests.
- Covering only some threat walls → fails ⊆ refutation coverage on traps.
- Editing judge/puzzles → fails seal immutability test.

### Per-gate Pitfall Inventory
- RC1/RC7: oracle derives card via search packages (not sed/revert); substantive LOC in op_a/op_b/op_c.
- RC2: avoid `broken_*` / answer filenames; desk package names stay opaque (`op_a`/`op_b`/`op_c`).
- RC3: tests recompute win/trap/fort and judge-validate sequences — not format-only.
- RC4/RC5: EXPECTED from sealed `/opt/tbench` puzzles inside tests, not golden files under environment.
- RC6: instruction symptoms-only; rules live under `/app/docs/`.
- GX9/GX10: no per-board answer triples in instruction; no polarity contradictions.
- Static: hashed pytest lockfile, `check=` on subprocess, `languages=["bash"]`, games tags.

### Initial Draft Commitments
- `tasks/quoridor-path-block-contest/instruction.md`
- `tasks/quoridor-path-block-contest/task.toml`
- `tasks/quoridor-path-block-contest/output_contract.toml`
- `tasks/quoridor-path-block-contest/environment/Dockerfile`
- `tasks/quoridor-path-block-contest/environment/.dockerignore`
- `tasks/quoridor-path-block-contest/environment/requirements.txt`
- `tasks/quoridor-path-block-contest/environment/fixtures/judge.jar`
- `tasks/quoridor-path-block-contest/environment/puzzles/board_01.txt` … `board_11.txt`
- `tasks/quoridor-path-block-contest/environment/docs/{score_card,table_judge,board_format,contest_rules,path_floors,overnight_printer}.md`
- `tasks/quoridor-path-block-contest/environment/tools/sensei_hint.sh`
- `tasks/quoridor-path-block-contest/environment/kiosk/{emit_card.sh,draft.py,sheet_load.py}`
- `tasks/quoridor-path-block-contest/environment/history/game_0{1,2,3,4}.log`
- `tasks/quoridor-path-block-contest/solution/{solve.sh,derive.sh,board_hunt/op_b.py,desk_books/op_a.py,card_out/op_c.py}`
- `tasks/quoridor-path-block-contest/tests/{test.sh,test_outputs.py}`
- `specs/quoridor-path-block-contest.md`
- `specs/quoridor-path-block-contest-reviewer.md`
