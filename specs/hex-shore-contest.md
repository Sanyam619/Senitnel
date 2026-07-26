### Decision
GO — Attempt 1.
- The primary activity is Hex position analysis and tournament-card filing, so `games` is the natural open category.
- Difficulty comes from distinguishing forced links from cooperative links across a mixed booklet and constructing valid threat refutations.

### Metadata
- version: 2
- Task name: hex-capture-contest
- Title: Hex Territory Contest
- Category: games
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [hex, territory-contest, tournament, table-judge, puzzle-book]
- Milestones: 0

## Authoring Brief

### Public contract
The player files `/output/hex-card.json` for twelve Black-to-move Hex rounds under `/app/puzzles/`. The card records each round's forced/cooperative outcome, winning side, viable Black first moves for forced wins, and legal White answers covering every one-stone threat on non-forced but cooperatively linkable rounds. Black connects top to bottom and White connects left to right. The puzzle bytes and sealed `/app/bin/judge.jar` remain unchanged. Output is deterministic JSON in ascending round order.

### Failure topology
The booklet mixes forced wins, cooperative-only traps, and completed White walls. Surface reachability deliberately agrees on wins and traps, so it cannot decide the tournament result. Correct filing requires combining Hex connectivity, adversarial turn order, first-move analysis, and local threat coverage; a classifier that gets one distinction right still fails distant rounds and certificate checks.

The sealed judge handles board legality and completed links, not strategic minimax. The overnight printer and sensei reading provide plausible tournament-desk observations without containing the complete card.

### Environment shape
The environment contains twelve puzzle sheets, a sealed Java table judge, tournament and board-format documents, sample match logs, a surface-only sensei helper, and an overnight card printer. The verifier independently checks game outcomes and submitted move certificates.

### Required artifacts
- Root task metadata, concise instruction, and output contract.
- Offline Docker environment with pinned Python, Java, pytest, and pytest-json-ctrf dependencies.
- Twelve distinct puzzle sheets, sealed judge, tournament documents, match logs, sensei helper, and kiosk modules.
- Oracle modules that derive the card from the puzzle sheets rather than embedding a result table.
- At least six deterministic pytest checks covering schema, sealed assets, strategic outcomes, winning moves, trap refutations, forts, and surface false-greens.

### Test plan
- Card shape: checks complete ordered coverage and field types; multiple card-generation approaches pass; not chain-dependent.
- Repeated filing: checks the completed card remains byte-identical through two kiosk passes; independent of the strategic solver.
- Judge seal: checks the shipped judge is unchanged; independent of card-generation approach.
- Round outcomes: independently checks forced/cooperative classification; search, proof enumeration, or manual play analysis can pass; not chain-dependent.
- Winning first plays: checks listed cells are legal and preserve a forced Black link; multiple search implementations pass.
- Trap refutations: checks required threat coverage and legal White answers; any valid covering reply passes.
- Fort rows: checks completed White walls and empty move certificates; multiple connectivity methods pass.
- Sensei false-greens: checks cooperative reachability is not used as the forced-win verdict; independent of implementation.

### Drafting guardrails
Do not publish the per-board answer table, label puzzle sheets, expose a force-search command in the judge, or turn the instruction into a board-by-board checklist. Tests should accept valid certificate subsets/supersets where the contract permits them and must not require the oracle's chosen refutation when another legal reply works.

### Triviality Ledger
- Surface flood-fill cannot classify traps as wins because strategic outcome checks independently distinguish adversarial White play.
- A status-only answer table cannot pass because wins need valid first moves and traps need complete legal refutation coverage.
- Copying the overnight printer cannot pass because it conflates cooperative reachability with forced play and does not provide certificates.
- Modifying puzzle or judge bytes cannot bypass analysis because the verifier pins the judge and reconstructs outcomes from verifier-owned puzzle inputs.
- One-move probes do not settle the win rounds; none of the curated forced wins is already completed by its winning first move.

### Per-gate Pitfall Inventory
- RC1: oracle performs full board parsing, graph traversal, adversarial search, threat extraction, and card assembly rather than deleting or flipping a setting.
- RC2: puzzle and helper names use tournament vocabulary without `broken`, `golden`, or answer-label tokens.
- RC3: tests assert domain-correct strategic outcomes and legal certificates, not file existence alone.
- RC4: the judge is compared to a verifier-owned copy and expected outcomes are recomputed rather than loaded from writable environment answers.
- RC5: no golden card or per-board status table appears under `environment/`.
- RC6: instruction describes the card and observed disagreement without an algorithm, answer matrix, or implementation recipe.
- RC7: transitive oracle logic comfortably exceeds the substantive line floor.
- GX1: environment comments describe helper mechanics, not corrections or intended fixes.
- GX3: oracle materializes three substantive runtime modules with more than eighty semantic lines.
- GX9: instruction contains status semantics but no board-to-status/value recital.
- GX10: each status polarity is scoped to a separate sentence and scenario.
- Static checks: all subprocess calls use explicit `check=`, verifier dependencies are installed offline in the Dockerfile, and `.dockerignore` excludes caches.

### Initial Draft Commitments
- tasks/hex-capture-contest/instruction.md
- tasks/hex-capture-contest/task.toml
- tasks/hex-capture-contest/output_contract.toml
- tasks/hex-capture-contest/environment/.dockerignore
- tasks/hex-capture-contest/environment/Dockerfile
- tasks/hex-capture-contest/environment/fixtures/judge.jar
- tasks/hex-capture-contest/environment/puzzles/board_01.txt
- tasks/hex-capture-contest/environment/puzzles/board_02.txt
- tasks/hex-capture-contest/environment/puzzles/board_03.txt
- tasks/hex-capture-contest/environment/puzzles/board_04.txt
- tasks/hex-capture-contest/environment/puzzles/board_05.txt
- tasks/hex-capture-contest/environment/puzzles/board_06.txt
- tasks/hex-capture-contest/environment/puzzles/board_07.txt
- tasks/hex-capture-contest/environment/puzzles/board_08.txt
- tasks/hex-capture-contest/environment/puzzles/board_09.txt
- tasks/hex-capture-contest/environment/puzzles/board_10.txt
- tasks/hex-capture-contest/environment/puzzles/board_11.txt
- tasks/hex-capture-contest/environment/puzzles/board_12.txt
- tasks/hex-capture-contest/environment/docs/board_format.md
- tasks/hex-capture-contest/environment/docs/table_judge.md
- tasks/hex-capture-contest/environment/docs/tournament_card.md
- tasks/hex-capture-contest/environment/docs/match_logs.md
- tasks/hex-capture-contest/environment/docs/overnight_printer.md
- tasks/hex-capture-contest/environment/history/game_01.log
- tasks/hex-capture-contest/environment/history/game_02.log
- tasks/hex-capture-contest/environment/history/game_03.log
- tasks/hex-capture-contest/environment/history/game_04.log
- tasks/hex-capture-contest/environment/tools/sensei_hint.sh
- tasks/hex-capture-contest/environment/kiosk/boardio.py
- tasks/hex-capture-contest/environment/kiosk/draft.py
- tasks/hex-capture-contest/environment/kiosk/emit_card.sh
- tasks/hex-capture-contest/solution/solve.sh
- tasks/hex-capture-contest/solution/derive.sh
- tasks/hex-capture-contest/solution/board_hunt/engine.py
- tasks/hex-capture-contest/solution/board_hunt/reader.py
- tasks/hex-capture-contest/solution/board_hunt/writer.py
- tasks/hex-capture-contest/tests/test.sh
- tasks/hex-capture-contest/tests/test_outputs.py

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table
- path: runtime/link_scan/engine.py
  symbol: solve
  kind: function
  signature: solve(black, white, side, n)
  purpose: evaluate whether Black can force a completed vertical link from a position
- path: runtime/desk_read/reader.py
  symbol: classify
  kind: function
  signature: classify(black, white, n)
  purpose: assign one tournament status from connectivity and adversarial play
- path: runtime/desk_read/reader.py
  symbol: refutation_for
  kind: function
  signature: refutation_for(black, white, c, n)
  purpose: select a legal White answer that removes a one-stone completion
- path: runtime/card_out/writer.py
  symbol: build_round
  kind: function
  signature: build_round(board_id, path)
  purpose: assemble one derived tournament row

#### flipping_point_contract
locations:
  - id: A
    path: runtime/link_scan/engine.py
    controls_tests: [test_status_matches_search, test_win_key_cells]
  - id: B
    path: runtime/desk_read/reader.py
    controls_tests: [test_trap_refutation_coverage, test_fort_rows]
  - id: C
    path: runtime/card_out/writer.py
    controls_tests: [test_card_shape, test_sensei_is_not_the_verdict]
no_single_location_flips_majority: true
concentration_cap: 0.5

#### decoy_manifest
- path: kiosk/boardio.py
  kind: helper
  rhymes_with: B
  non_fix_purpose: enumerate and parse sheets for the overnight desk
- path: tools/sensei_hint.sh
  kind: helper
  rhymes_with: A
  non_fix_purpose: report cooperative surface reachability
- path: kiosk/draft.py
  kind: module
  rhymes_with: C
  non_fix_purpose: emit an overnight desk draft from surface readings

#### code_forbidden_tokens
code_forbidden_tokens: [territory, contest, card, round, Black, White, Hex, puzzle, link, edge, status, win, trap, fort, winning-side, cooperative, key-cell, refutation, judge, sensei, printer, verdict]
