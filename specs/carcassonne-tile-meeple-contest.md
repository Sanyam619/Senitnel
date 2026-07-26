### Decision
GO — Attempt 1. Carcassonne tile-meeple tournament booklet under `games`:
sealed judge, eleven First-to-move farm/city rounds, win/trap/fort with
contested-claim refutation coverage, kiosk cooperative-claim win bait and
sensei that ignores farmer majority. No repair/debug framing. Primary
activity is play under a table judge.

### Metadata
- version: 2
- Task name: carcassonne-tile-meeple-contest
- Title: Carcassonne Tile-Meeple Contest
- Category: games
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [puzzle-book, tournament, table-contest, board-game, carcassonne, tile-meeple]
- Milestones: 0

## Authoring Brief

### Public contract
File `/app/answers.json` with `schema_tag = carcassonne-meeple-v1` and eleven
rounds (`board_id`, `status`, `tile`, `meeple`, `score_delta`, `sequence`,
`refutations`, `coop_claim`). House rules for tile edges, meeple claims,
city/road/cloister completion, farmer scoring, and score floors live under
`/app/docs/`. Sealed `/app/bin/judge.jar`; leave judge and puzzles unchanged.
Emit twice on a finished card stays byte-identical.

### Failure topology
Agents that trust sensei (city/road fill without farmer majority) or the
kiosk's cooperative win stamp mis-label traps and forts. Territory heuristics
from Amazons/Hex mis-handle shared features and contested meeples. Forced
wins need lines that survive every Blue reply; traps need required ⊆
submitted refutations for every graded contested first claim; padded
`score_delta` fails sealed replay.

### Environment shape
`/app/puzzles/` sheets, `/app/docs/` house rules, `/app/bin/judge.jar` sealed
referee, `/app/tools/sensei_hint.sh` surface bait, `/app/kiosk/` overnight
draft, `/app/history/` dialect samples.

### Required artifacts
Standard task layout: instruction, task.toml, output_contract, Dockerfile,
puzzles, docs, fixtures/judge.jar, kiosk, tools, history, solution oracle
(search-derived card), tests that recompute verdicts and replay the judge.

### Test plan
- Card schema / ordering / verdict vocabulary / schema_tag
- Sealed judge integrity + sequence replay
- Independent win/trap/fort classification
- Forcing lines survive all Blue replies
- Friendly lines reach the score floor
- Trap refutation coverage (required ⊆ submitted)
- Forts not stamped win; coop-as-win bait live
- score_delta matches judge (no padding)
- Whole-booklet round_ok
- Emit twice byte-identical on finished card

### Drafting guardrails
Symptoms-only instruction; no answer-key tallies; sample card uses fictional
board ids; no intent comments on oracle fix path; languages=["bash"];
tournament tags leading puzzle-book/tournament/table-contest; no `/app/ops/`
repair aura; graded play facts not SE metrics; card at `/app/answers.json`
(not `/output/*-card.json` API surface).

### Triviality Ledger
- Kiosk all-win draft fails fort/trap tests and refutation coverage.
- Sensei city/road cheer ignores farmer majority → false greens on farm rounds.
- Friendly-line-called-win fails forcing_ok.
- Missing threat refutations fail coverage ⊆ check.
- Padded score_delta fails judge replay equality.

### Per-gate Pitfall Inventory
- RC1/RC7: oracle is search over eleven sheets, not sed polarity.
- RC2: no broken_/golden_ names on solver surfaces.
- RC3: tests recompute play, not schema alone.
- RC4/RC5: EXPECTED live in test engine, not env goldens.
- RC6: instruction symptoms-only; rules in docs.
- GX9/GX10: no per-board answer recital or polarity contradiction.
- Category: games play booklet, not SE repair.

### Initial Draft Commitments
- tasks/carcassonne-tile-meeple-contest/instruction.md
- tasks/carcassonne-tile-meeple-contest/task.toml
- tasks/carcassonne-tile-meeple-contest/output_contract.toml
- tasks/carcassonne-tile-meeple-contest/environment/Dockerfile
- tasks/carcassonne-tile-meeple-contest/environment/.dockerignore
- tasks/carcassonne-tile-meeple-contest/environment/requirements.txt
- tasks/carcassonne-tile-meeple-contest/environment/fixtures/judge.jar
- tasks/carcassonne-tile-meeple-contest/environment/puzzles/board_01.txt … board_11.txt
- tasks/carcassonne-tile-meeple-contest/environment/docs/*.md
- tasks/carcassonne-tile-meeple-contest/environment/tools/sensei_hint.sh
- tasks/carcassonne-tile-meeple-contest/environment/kiosk/*
- tasks/carcassonne-tile-meeple-contest/environment/history/game_*.log
- tasks/carcassonne-tile-meeple-contest/solution/*
- tasks/carcassonne-tile-meeple-contest/tests/*

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table
```
- path: solution/desk_books/op_a.py
  symbol: op_a
  kind: function
  signature: (history_dir: str) -> str
  purpose: confirm match logs present; return schema token
- path: solution/board_hunt/op_b.py
  symbol: op_b
  kind: function
  signature: (sheet: Path) -> dict
  purpose: classify one sheet into a card row
- path: solution/card_out/op_c.py
  symbol: op_c
  kind: function
  signature: (rows: list, dest: str) -> None
  purpose: write canonical tournament card JSON
```

#### flipping_point_contract
```
locations:
  - id: A
    path: solution/board_hunt/op_b.py
    controls_tests: [test_e5_beryl_verdicts_match_play_from_the_sheets, test_g2_flint_forcing_sequences_really_force, test_j4_amber_friendly_sequences_reach_the_floor, test_k7_topaz_refutations_cover_every_threat]
  - id: B
    path: solution/card_out/op_c.py
    controls_tests: [test_a1_onyx_card_reads_as_a_tournament_card, test_r6_mica_emit_twice_stays_byte_identical_on_a_finished_card]
  - id: C
    path: solution/desk_books/op_a.py
    controls_tests: [test_p5_quartz_whole_booklet_stands_up]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest
```
- path: environment/kiosk/draft.py
  kind: helper
  rhymes_with: op_b
  non_fix_purpose: cooperative-claim all-win overnight draft
- path: environment/tools/sensei_hint.sh
  kind: helper
  rhymes_with: op_a
  non_fix_purpose: city/road fill whisper (ignores farmer majority)
- path: environment/kiosk/sheet_load.py
  kind: helper
  rhymes_with: op_c
  non_fix_purpose: list puzzle sheets for the printer
```

#### code_forbidden_tokens
```
code_forbidden_tokens: [farmer, meeple, carcassonne, tile, claim, refutation, verdict, trap, fort, win, sensei, kiosk, puzzle, board, floor, sequence, coop, city, road, cloister, score]
```
