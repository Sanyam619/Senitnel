### Decision
GO — Attempt 1. Amazons territory enclosure booklet under `games`: sealed
judge, eleven White-to-move endgames, win/trap/fort with refutation coverage,
kiosk fourth-turn bait and empty-count sensei. No repair/debug framing.

### Metadata
- version: 2
- Task name: amazons-territory-enclosure-contest
- Title: Amazons Territory Enclosure
- Category: games
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [amazons, territory-contest, tournament, table-judge, puzzle-book, score-card]
- Milestones: 0

## Authoring Brief

### Public contract
File `/output/amazons-card.json` with `schema_tag = amazons-territory-v1` and
eleven rounds (`board_id`, `status`, `best_move`, `territory_delta`,
`sequence`, `refutations`, `coop_enclose`). House Amazons rules, exclusive
territory floor 2, three-turn White budget, and trap threat coverage live under
`/app/docs/`. Sealed `/app/bin/judge.jar`; leave judge and puzzles unchanged.
Emit twice on a finished card stays byte-identical.

### Failure topology
Agents that trust sensei empty counts or the kiosk's fourth-turn win stamp
mis-label traps and forts. Disc/liberty heuristics from other games do not
transfer to queen-move + arrow partitions. Forced wins need lines that survive
every Black reply; traps need required ⊆ submitted refutations for every
one-turn enclosure threat; padded `territory_delta` fails sealed replay.

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
- Forcing lines survive all Black replies
- Friendly lines reach the floor
- Trap refutation coverage (required ⊆ submitted)
- Forts not stamped win; fourth-turn coop bait live
- territory_delta matches judge (no padding)
- Whole-booklet round_ok
- Emit twice byte-identical on finished card

### Drafting guardrails
Symptoms-only instruction; no answer-key tallies; sample card uses fictional
board ids; no intent comments on oracle fix path; languages=["bash"];
tournament tags; no `/app/ops/` repair aura.

### Triviality Ledger
- Kiosk all-win draft fails fort/trap tests and refutation coverage.
- Sensei empty-count cheer is not exclusive territory.
- Friendly-line-called-win fails forcing_ok.
- Missing threat refutations fail coverage ⊆ check.
- Padded territory_delta fails judge replay equality.

### Per-gate Pitfall Inventory
- RC1/RC7: oracle is search over eleven sheets, not sed polarity.
- RC2: no broken_/golden_ names on solver surfaces.
- RC3: tests recompute play, not schema alone.
- RC4/RC5: EXPECTED live in test engine, not env goldens.
- RC6: instruction symptoms-only; rules in docs.
- GX9/GX10: no per-board answer recital or polarity contradiction.
- Category: games play booklet, not SE repair.

### Initial Draft Commitments
- tasks/amazons-territory-enclosure-contest/instruction.md
- tasks/amazons-territory-enclosure-contest/task.toml
- tasks/amazons-territory-enclosure-contest/output_contract.toml
- tasks/amazons-territory-enclosure-contest/environment/Dockerfile
- tasks/amazons-territory-enclosure-contest/environment/.dockerignore
- tasks/amazons-territory-enclosure-contest/environment/requirements.txt
- tasks/amazons-territory-enclosure-contest/environment/fixtures/judge.jar
- tasks/amazons-territory-enclosure-contest/environment/puzzles/board_01.txt … board_11.txt
- tasks/amazons-territory-enclosure-contest/environment/docs/*.md
- tasks/amazons-territory-enclosure-contest/environment/tools/sensei_hint.sh
- tasks/amazons-territory-enclosure-contest/environment/kiosk/*
- tasks/amazons-territory-enclosure-contest/environment/history/game_*.log
- tasks/amazons-territory-enclosure-contest/solution/*
- tasks/amazons-territory-enclosure-contest/tests/*

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
  non_fix_purpose: empty-square surface whisper
- path: environment/kiosk/sheet_load.py
  kind: helper
  rhymes_with: op_c
  non_fix_purpose: list puzzle sheets for the printer
```

#### code_forbidden_tokens
```
code_forbidden_tokens: [territory, enclosure, amazons, arrow, queen, refutation, verdict, trap, fort, win, sensei, kiosk, puzzle, board, floor, delta, sequence, coop]
```
