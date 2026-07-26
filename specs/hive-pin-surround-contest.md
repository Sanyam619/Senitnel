### Decision
GO — Attempt 1.
- The primary activity is Hive queen-surround analysis and tournament-card filing, so `games` is the natural open category.
- Difficulty comes from distinguishing forced-surround wins from cooperative-only traps across a mixed booklet of one-hive/beetle/grasshopper/ant/spider movement, and constructing valid threat refutations.

### Metadata
- version: 2
- Task name: hive-pin-surround-contest
- Title: Hive Pin & Surround Contest
- Category: games
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [hive, pin-surround, tournament, table-judge, puzzle-book, score-card]
- Milestones: 0

## Authoring Brief

### Public contract
The player files `/output/hive-card.json` for ten White-to-move Hive surround rounds under `/app/puzzles/`. The card records each round's forced/cooperative/fort outcome, a forcing first move and sequence on wins, cooperative queen freedom on traps/forts, and legal Black replies covering every threat move on traps. White drives Black's queen freedom to PIN_FLOOR=0 (full surround). Puzzle bytes and sealed `/app/bin/judge.jar` remain unchanged. Output is deterministic JSON in ascending round order.

### Failure topology
The booklet mixes forced wins, cooperative-only traps, and forts. A surface sensei whisper deliberately "teleports" pieces past the one-hive rule and false-greens traps as looks_pinned, so sensei cannot decide the tournament result. Correct filing requires combining Hive legality (one-hive rule, beetle climb/cover, grasshopper jump, ant perimeter freedom floor, spider exact three-step slide), the PIN_FLOOR outcome, adversarial move search, and local threat coverage.

### Environment shape
Ten puzzle sheets, sealed Java table judge, contest docs, sample history logs, surface-only sensei helper, overnight card printer. Verifier independently recomputes outcomes from sealed puzzles.

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table
- path: solution/board_hunt/op_b.py
  symbol: force_win
  kind: function
  signature: force_win(state)
  purpose: evaluate whether White can force Black queen freedom to PIN_FLOOR against fighting Black
- path: solution/board_hunt/op_b.py
  symbol: coop_pinable
  kind: function
  signature: coop_pinable(state)
  purpose: evaluate whether White can reach PIN_FLOOR if Black passes/cooperates
- path: solution/desk_books/op_a.py
  symbol: classify
  kind: function
  signature: classify(state)
  purpose: assign win/trap/fort from force and coop searches
- path: solution/desk_books/op_a.py
  symbol: build_trap_refs
  kind: function
  signature: build_trap_refs(state)
  purpose: cover every threat move with a legal Black reply that prevents the follow-up surround
- path: solution/card_out/op_c.py
  symbol: build_round
  kind: function
  signature: build_round(board_id, path)
  purpose: assemble one derived tournament row

#### flipping_point_contract
locations:
  - id: A
    path: solution/board_hunt/op_b.py
    controls_tests: [test_status_matches_search, test_win_key_bug_and_sequence]
  - id: B
    path: solution/desk_books/op_a.py
    controls_tests: [test_trap_refutation_coverage, test_fort_rows]
  - id: C
    path: solution/card_out/op_c.py
    controls_tests: [test_card_shape, test_sensei_is_not_the_verdict]
no_single_location_flips_majority: true
concentration_cap: 0.5

#### decoy_manifest
- environment/tools/sensei_hint.sh — teleport-past-one-hive false-green on traps
- environment/kiosk/draft.py — overnight draft that stamps looks_pinned as win

#### code_forbidden_tokens
Derived from instruction nouns that must not appear as fix-path symbols:
force_win, classify, build_trap_refs, build_round, PIN_FLOOR, threat_moves
(oracle package names desk_books/board_hunt/card_out and op_a/op_b/op_c are opaque).

### Drafting guardrails
Do not publish per-board answers, label puzzle sheets, expose a force-search command in the judge, or turn the instruction into a board-by-board checklist. Document PIN_FLOOR, ANT_FREEDOM_FLOOR, threat/refutation, and coop_pin in docs for fairness.

### Triviality Ledger
- Sensei `looks_pinned` on traps → filing all pinned rounds as `win` fails status + refutation tests.
- Kiosk draft stamps sensei wins → fails independent force/coop search and judge-validated sequences.
- Padding `freedom` or inventing long sequences → fails freedom equality and move-budget tests.
- Covering only some threat moves → fails ⊆ refutation coverage on traps.
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
- `tasks/hive-pin-surround-contest/instruction.md`
- `tasks/hive-pin-surround-contest/task.toml`
- `tasks/hive-pin-surround-contest/output_contract.toml`
- `tasks/hive-pin-surround-contest/environment/Dockerfile`
- `tasks/hive-pin-surround-contest/environment/.dockerignore`
- `tasks/hive-pin-surround-contest/environment/requirements.txt`
- `tasks/hive-pin-surround-contest/environment/fixtures/judge.jar`
- `tasks/hive-pin-surround-contest/environment/puzzles/board_01.txt` … `board_10.txt`
- `tasks/hive-pin-surround-contest/environment/docs/{score_card,table_judge,board_format,contest_rules,freedom_floors,overnight_printer,match_logs}.md`
- `tasks/hive-pin-surround-contest/environment/tools/sensei_hint.sh`
- `tasks/hive-pin-surround-contest/environment/kiosk/{emit_card.sh,draft.py,sheet_load.py}`
- `tasks/hive-pin-surround-contest/environment/history/game_0{1,2,3,4}.txt`
- `tasks/hive-pin-surround-contest/solution/{solve.sh,derive.sh,board_hunt/op_b.py,desk_books/op_a.py,card_out/op_c.py}`
- `tasks/hive-pin-surround-contest/tests/{test.sh,test_outputs.py}`
- `specs/hive-pin-surround-contest.md`
