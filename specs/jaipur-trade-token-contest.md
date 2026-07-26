### Decision
GO — Attempt 1. Jaipur trade-token tournament booklet under `games`: sealed
judge, twelve Trader-to-move market rounds, win/trap/fort with seal-losing
first-sell refutation coverage, kiosk fourth-action coop bait and camel-blind
sensei. No repair/debug framing. Primary activity is play under a table judge.

### Metadata
- version: 2
- Task name: jaipur-trade-token-contest
- Title: Jaipur Trade-Token Contest
- Category: games
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [jaipur, trade-token, tournament, table-judge, puzzle-book, score-card]
- Milestones: 0

## Authoring Brief

### Public contract
File `/output/jaipur-card.json` with `schema_tag = jaipur-trade-v1` and twelve
rounds (`board_id`, `status`, `action`, `tokens`, `score`, `sequence`,
`refutations`, `coop_seal`). House Jaipur rules (take / exchange / sell, camel
herds, goods-token tiers, seal bonuses, score floors) live under `/app/docs/`.
Sealed `/app/bin/judge.jar`; leave judge and puzzles unchanged. Emit twice on
a finished card stays byte-identical. Trap rounds need refutation coverage for
every graded seal-losing first sell.

### Failure topology
Agents that trust sensei (ignores camel-only herd takes) or the kiosk's
fourth-action win stamp mis-label traps and forts. Pure point-max heuristics
mis-time seals and fail `coop_seal` traps. Forced wins need lines that survive
every rival reply; traps need required ⊆ submitted refutations for every
seal-losing first sell threat; padded `score` fails sealed replay.

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
- Forcing lines survive all rival replies
- Friendly lines reach the score floor
- Trap refutation coverage (required ⊆ submitted)
- Forts not stamped win; fourth-action coop bait live
- score matches judge (no padding / suboptimal sell padding)
- tokens list matches claim order from the filed line
- Whole-booklet round_ok
- Emit twice byte-identical on finished card
- Camel-herd legality / precious min-sell polarity

### Drafting guardrails
Symptoms-only instruction; no answer-key tallies; sample card uses fictional
board ids; no intent comments on oracle fix path; languages=["bash"];
tournament tags; no `/app/ops/` repair aura; graded play facts not SE metrics.

### Triviality Ledger
- Kiosk all-win draft fails fort/trap tests and refutation coverage.
- Sensei camel-blind cheer allows herd-skip misreads.
- Friendly-line-called-win fails forcing_ok.
- Missing threat refutations fail coverage ⊆ check.
- Padded score / extra token claims fail judge replay equality.

### Per-gate Pitfall Inventory
- RC1/RC7: oracle is search over twelve sheets, not sed polarity.
- RC2: no broken_/golden_ names on solver surfaces.
- RC3: tests recompute play, not schema alone.
- RC4/RC5: EXPECTED live in test engine, not env goldens.
- RC6: instruction symptoms-only; rules in docs.
- GX9/GX10: no per-board answer recital or polarity contradiction.
- Category: games play booklet, not SE repair.

### Initial Draft Commitments
- tasks/jaipur-trade-token-contest/instruction.md
- tasks/jaipur-trade-token-contest/task.toml
- tasks/jaipur-trade-token-contest/output_contract.toml
- tasks/jaipur-trade-token-contest/environment/Dockerfile
- tasks/jaipur-trade-token-contest/environment/.dockerignore
- tasks/jaipur-trade-token-contest/environment/requirements.txt
- tasks/jaipur-trade-token-contest/environment/fixtures/judge.jar
- tasks/jaipur-trade-token-contest/environment/puzzles/board_01.txt … board_12.txt
- tasks/jaipur-trade-token-contest/environment/docs/*.md
- tasks/jaipur-trade-token-contest/environment/tools/sensei_hint.sh
- tasks/jaipur-trade-token-contest/environment/kiosk/*
- tasks/jaipur-trade-token-contest/environment/history/game_*.log
- tasks/jaipur-trade-token-contest/solution/*
- tasks/jaipur-trade-token-contest/tests/*

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
  non_fix_purpose: fourth-action cooperative all-win overnight draft
- path: environment/tools/sensei_hint.sh
  kind: helper
  rhymes_with: op_a
  non_fix_purpose: surface whisper that ignores camel-only herd takes
- path: environment/kiosk/sheet_load.py
  kind: helper
  rhymes_with: op_c
  non_fix_purpose: list puzzle sheets for the printer
```

#### code_forbidden_tokens
```
code_forbidden_tokens: [jaipur, seal, token, camel, herd, sell, take, exchange, refutation, verdict, trap, fort, win, sensei, kiosk, puzzle, board, floor, sequence, coop, trader, rival]
```
