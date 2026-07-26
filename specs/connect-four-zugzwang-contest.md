### Decision
GO — Attempt 1. Connect Four zugzwang contest booklet under `games`: sealed
judge, twelve Yellow-to-move rounds, win/trap/draw with odd/even threat parity
and refutation coverage. No repair/debug framing. Languages bash (sealed jar).

### Metadata
- version: 2
- Task name: connect-four-zugzwang-contest
- Title: Connect Four Zugzwang
- Category: games
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [connect-four, zugzwang, threat-parity, tournament, table-judge, puzzle-book]
- Milestones: 0

## Authoring Brief

### Public contract
File `/output/c4-card.json` with `schema_tag = c4-zugzwang-v1` and twelve
rounds (`board_id`, `status`, `best_column`, `win_in`, `sequence`, `threats`,
`refutations`, `coop_win`). Gravity drops, odd/even threat parity, zugzwang
counting, the five-drop Yellow budget, and trap/draw refutation coverage live
under `/app/docs/`. Sealed `/app/bin/judge.jar`; leave judge and puzzles
unchanged. Emit twice on a finished card stays byte-identical.

### Failure topology
Agents that trust sensei column-legality cheers or the kiosk's seven-drop
cooperative all-win stamp mis-label traps and draws. Naive "make a four"
search ignores odd/even threat ownership and Red fighting replies. Forced wins
need lines that survive every Red reply inside five Yellow drops; traps and
draws need required ⊆ submitted refutations; padded `win_in` fails sealed
replay.

### Environment shape
`/app/puzzles/` sheets, `/app/docs/` house rules, `/app/bin/judge.jar` sealed
referee, `/app/tools/sensei_hint.sh` legality bait, `/app/kiosk/` overnight
draft, `/app/history/` dialect samples.

### Required artifacts
Standard task layout: instruction, task.toml, output_contract, Dockerfile,
twelve puzzles, docs, fixtures/judge.jar, kiosk, tools, history, solution
oracle (search-derived card), tests that recompute verdicts and replay the
judge.

### Test plan
- Card schema / ordering / verdict vocabulary
- Sealed judge integrity + sequence replay
- Independent win/trap/draw classification
- Forcing lines survive all Red replies
- Friendly lines reach connect-four
- Trap/draw refutation coverage (required ⊆ submitted)
- Draws not stamped win; seven-drop coop bait live
- win_in equals Yellow drops (no padding past connect)
- Threat rows match gravity landings
- Whole-booklet round_ok
- Emit twice byte-identical on finished card

### Drafting guardrails
Symptoms-only instruction; no answer-key tallies; sample card uses fictional
board ids; no intent comments on oracle fix path; languages=["bash"];
tournament tags; no `/app/ops/` repair aura.

### Triviality Ledger
- Kiosk all-win draft fails draw/trap tests and refutation coverage.
- Sensei legal-column whisper is not a verdict.
- Friendly-line-called-win fails forcing_ok.
- Missing threat/losing-drop refutations fail coverage ⊆ check.
- Padded win_in / non-forcing mid-line drops fail judge replay + force check.

### Per-gate Pitfall Inventory
- RC1/RC7: oracle is search over twelve sheets, not sed polarity.
- RC2: no broken_/golden_ names on solver surfaces.
- RC3: tests recompute play, not schema alone.
- RC4/RC5: EXPECTED live in test engine, not env goldens.
- RC6: instruction symptoms-only; rules in docs.
- GX9/GX10: no per-board answer recital or polarity contradiction.
- Category: games play booklet, not SE repair.

### Initial Draft Commitments
- tasks/connect-four-zugzwang-contest/instruction.md
- tasks/connect-four-zugzwang-contest/task.toml
- tasks/connect-four-zugzwang-contest/output_contract.toml
- tasks/connect-four-zugzwang-contest/environment/Dockerfile
- tasks/connect-four-zugzwang-contest/environment/.dockerignore
- tasks/connect-four-zugzwang-contest/environment/requirements.txt
- tasks/connect-four-zugzwang-contest/environment/fixtures/judge.jar
- tasks/connect-four-zugzwang-contest/environment/puzzles/board_01.txt … board_12.txt
- tasks/connect-four-zugzwang-contest/environment/docs/*.md
- tasks/connect-four-zugzwang-contest/environment/tools/sensei_hint.sh
- tasks/connect-four-zugzwang-contest/environment/kiosk/*
- tasks/connect-four-zugzwang-contest/environment/history/game_*.log
- tasks/connect-four-zugzwang-contest/solution/*
- tasks/connect-four-zugzwang-contest/tests/*

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
  signature: (sheet: Path, schema_tag: str) -> dict
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
    controls_tests: [test_e5_beryl_verdicts_match_play_from_the_sheets, test_g2_flint_forcing_sequences_really_force, test_j4_amber_friendly_sequences_reach_four, test_k7_topaz_refutations_cover_every_graded_drop]
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
  non_fix_purpose: seven-drop cooperative all-win overnight draft
- path: environment/tools/sensei_hint.sh
  kind: helper
  rhymes_with: op_a
  non_fix_purpose: legal-column surface whisper
- path: environment/kiosk/sheet_load.py
  kind: helper
  rhymes_with: op_c
  non_fix_purpose: list puzzle sheets for the printer
```

#### code_forbidden_tokens
```
code_forbidden_tokens: [zugzwang, parity, threat, column, gravity, refutation, verdict, trap, draw, win, sensei, kiosk, puzzle, board, floor, sequence, coop, yellow, red]
```
