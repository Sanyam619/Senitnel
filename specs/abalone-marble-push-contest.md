### Decision
GO — Attempt 1. Abalone marble-push tournament booklet under `games`: sealed
judge, ten Black-to-move midgame rounds, win/trap/fort with over-push
refutation coverage, kiosk fourth-turn coop bait and contiguous-only sensei.
No repair/debug framing. Primary activity is play under a table judge.

### Metadata
- version: 2
- Task name: abalone-marble-push-contest
- Title: Abalone Marble-Push Contest
- Category: games
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [abalone, marble-push, tournament, table-judge, puzzle-book, score-card]
- Milestones: 0

## Authoring Brief

### Public contract
File `/output/abalone-card.json` with `schema_tag = abalone-push-v1` and ten
rounds (`board_id`, `status`, `key_push`, `ejected`, `sequence`,
`refutations`, `coop_eject`). House Abalone rules (inline pushes, sumito
strength, side-steps, ejection floor, suicide ban) live under `/app/docs/`.
Sealed `/app/bin/judge.jar`; leave judge and puzzles unchanged. Emit twice on
a finished card stays byte-identical.

### Failure topology
Agents that trust sensei contiguous cheers (illegal 2-vs-3) or the kiosk's
fourth-turn win stamp mis-label traps and forts. Hex/territory heuristics
misread sumito physics. Forced wins need lines that survive every White
reply; traps need required ⊆ submitted refutations for every over-push first
threat; padded `ejected` fails sealed replay.

### Environment shape
`/app/puzzles/` sheets, `/app/docs/` house rules, `/app/bin/judge.jar` sealed
referee, `/app/tools/sensei_hint.sh` surface bait, `/app/kiosk/` overnight
draft, `/app/history/` dialect samples.

### Required artifacts
Standard task layout: instruction, task.toml, output_contract, Dockerfile,
puzzles, docs, fixtures/judge.jar, kiosk, tools, history, solution oracle
(search-derived card), tests that recompute verdicts and replay the judge.

### Test plan
- Card schema / ordering / verdict vocabulary
- Sealed judge integrity + sequence replay
- Independent win/trap/fort classification
- Forcing lines survive all White replies
- Friendly lines reach the ejection floor
- Trap refutation coverage (required ⊆ submitted)
- Forts not stamped win; fourth-turn coop bait live
- ejected matches judge (no padding / reversible cycles)
- Whole-booklet round_ok
- Emit twice byte-identical on finished card

### Drafting guardrails
Symptoms-only instruction; no answer-key tallies; sample card uses fictional
board ids; no intent comments on oracle fix path; languages=["bash"];
tournament tags; no `/app/ops/` repair aura; graded play facts not SE metrics.

### Triviality Ledger
- Kiosk all-win draft fails fort/trap tests and refutation coverage.
- Sensei contiguous-group cheer allows illegal 2-vs-3 sumito.
- Friendly-line-called-win fails forcing_ok.
- Missing threat refutations fail coverage ⊆ check.
- Padded ejected / cycle padding fails judge replay equality.

### Per-gate Pitfall Inventory
- RC1/RC7: oracle is search over ten sheets, not sed polarity.
- RC2: no broken_/golden_ names on solver surfaces.
- RC3: tests recompute play, not schema alone.
- RC4/RC5: EXPECTED live in test engine, not env goldens.
- RC6: instruction symptoms-only; rules in docs.
- GX9/GX10: no per-board answer recital or polarity contradiction.
- Category: games play booklet, not SE repair.

### Initial Draft Commitments
- tasks/abalone-marble-push-contest/instruction.md
- tasks/abalone-marble-push-contest/task.toml
- tasks/abalone-marble-push-contest/output_contract.toml
- tasks/abalone-marble-push-contest/environment/Dockerfile
- tasks/abalone-marble-push-contest/environment/.dockerignore
- tasks/abalone-marble-push-contest/environment/requirements.txt
- tasks/abalone-marble-push-contest/environment/fixtures/judge.jar
- tasks/abalone-marble-push-contest/environment/puzzles/board_01.txt … board_10.txt
- tasks/abalone-marble-push-contest/environment/docs/*.md
- tasks/abalone-marble-push-contest/environment/tools/sensei_hint.sh
- tasks/abalone-marble-push-contest/environment/kiosk/*
- tasks/abalone-marble-push-contest/environment/history/game_*.log
- tasks/abalone-marble-push-contest/solution/*
- tasks/abalone-marble-push-contest/tests/*

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
  non_fix_purpose: fourth-turn cooperative all-win overnight draft
- path: environment/tools/sensei_hint.sh
  kind: helper
  rhymes_with: op_a
  non_fix_purpose: contiguous-group surface whisper (allows illegal 2-vs-3)
- path: environment/kiosk/sheet_load.py
  kind: helper
  rhymes_with: op_c
  non_fix_purpose: list puzzle sheets for the printer
```

#### code_forbidden_tokens
```
code_forbidden_tokens: [sumito, eject, marble, abalone, push, refutation, verdict, trap, fort, win, sensei, kiosk, puzzle, board, floor, sequence, coop, suicide]
```
