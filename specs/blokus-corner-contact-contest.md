### Decision
GO — Attempt 1. Blokus corner-contact packing booklet under `games`: sealed
judge, ten first-player rounds, win/trap/fort with inventory-threat refutations,
kiosk fourth-placement bait and bounding-box sensei. No repair/debug framing.

### Metadata
- version: 2
- Task name: blokus-corner-contact-contest
- Title: Blokus Corner Contact
- Category: games
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [blokus, corner-contact, tournament, table-judge, puzzle-book, score-card]
- Milestones: 0

## Authoring Brief

### Public contract
File `/output/blokus-card.json` with `schema_tag = blokus-corner-v1` and ten
rounds (`board_id`, `status`, `piece_id`, `placement`, `squares_left`,
`sequence`, `refutations`, `coop_fill`). House Blokus rules (corner-touch-only
same-colour adjacency, edge-touch illegality), piece inventory, squares-left
floor, three-placement Blue budget, and trap threat coverage live under
`/app/docs/`. Sealed `/app/bin/judge.jar`; leave judge and puzzles unchanged.
`/app/kiosk/emit_card.sh` run twice on a finished card stays byte-identical.
Verifier judge-checks every placement sequence.

### Failure topology
Agents that trust sensei bounding-box fit or the kiosk's fourth-placement win
stamp mis-label traps and forts. Area-packing heuristics that allow own-colour
edge contact fail sealed legality. Forced fills need lines that survive every
Yellow reply; traps need required ⊆ submitted refutations for every
inventory-threatening first placement; padded `squares_left` fails sealed
replay.

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
- Forcing lines survive all Yellow replies
- Friendly lines reach the squares-left floor
- Trap refutation coverage (required ⊆ submitted)
- Forts not stamped win; fourth-placement coop bait live
- squares_left matches judge (no padding)
- Whole-booklet round_ok
- Emit twice byte-identical on finished card

### Drafting guardrails
Symptoms-only instruction; no answer-key tallies; sample card uses fictional
board ids; no intent comments on oracle fix path; languages=["bash"];
tournament tags; no `/app/ops/` repair aura; graded facts are play outcomes,
not metric formulas.

### Triviality Ledger
- Kiosk all-win draft fails fort/trap tests and refutation coverage.
- Sensei bounding-box cheer allows edge-adjacent own-colour placements.
- Friendly-line-called-win fails forcing_ok.
- Missing inventory-threat refutations fail coverage ⊆ check.
- Padded squares_left fails judge replay equality.
- Naive area packing that ignores corner-only adjacency fails legality.

### Per-gate Pitfall Inventory
- RC1/RC7: oracle is search over ten sheets, not sed polarity.
- RC2: no broken_/golden_ names on solver surfaces.
- RC3: tests recompute play, not schema alone.
- RC4/RC5: EXPECTED live in test engine, not env goldens.
- RC6: instruction symptoms-only; rules in docs.
- GX9/GX10: no per-board answer recital or polarity contradiction.
- Category: games play booklet, not SE repair; languages=["bash"].

### Initial Draft Commitments
- tasks/blokus-corner-contact-contest/instruction.md
- tasks/blokus-corner-contact-contest/task.toml
- tasks/blokus-corner-contact-contest/output_contract.toml
- tasks/blokus-corner-contact-contest/environment/Dockerfile
- tasks/blokus-corner-contact-contest/environment/.dockerignore
- tasks/blokus-corner-contact-contest/environment/requirements.txt
- tasks/blokus-corner-contact-contest/environment/fixtures/judge.jar
- tasks/blokus-corner-contact-contest/environment/puzzles/board_01.txt
- tasks/blokus-corner-contact-contest/environment/puzzles/board_02.txt
- tasks/blokus-corner-contact-contest/environment/puzzles/board_03.txt
- tasks/blokus-corner-contact-contest/environment/puzzles/board_04.txt
- tasks/blokus-corner-contact-contest/environment/puzzles/board_05.txt
- tasks/blokus-corner-contact-contest/environment/puzzles/board_06.txt
- tasks/blokus-corner-contact-contest/environment/puzzles/board_07.txt
- tasks/blokus-corner-contact-contest/environment/puzzles/board_08.txt
- tasks/blokus-corner-contact-contest/environment/puzzles/board_09.txt
- tasks/blokus-corner-contact-contest/environment/puzzles/board_10.txt
- tasks/blokus-corner-contact-contest/environment/docs/board_format.md
- tasks/blokus-corner-contact-contest/environment/docs/contest_rules.md
- tasks/blokus-corner-contact-contest/environment/docs/overnight_printer.md
- tasks/blokus-corner-contact-contest/environment/docs/tournament_card.md
- tasks/blokus-corner-contact-contest/environment/docs/table_judge.md
- tasks/blokus-corner-contact-contest/environment/docs/match_logs.md
- tasks/blokus-corner-contact-contest/environment/docs/score_card.md
- tasks/blokus-corner-contact-contest/environment/tools/sensei_hint.sh
- tasks/blokus-corner-contact-contest/environment/kiosk/emit_card.sh
- tasks/blokus-corner-contact-contest/environment/kiosk/draft.py
- tasks/blokus-corner-contact-contest/environment/kiosk/sheet_load.py
- tasks/blokus-corner-contact-contest/environment/history/game_01.log
- tasks/blokus-corner-contact-contest/environment/history/game_02.log
- tasks/blokus-corner-contact-contest/environment/history/game_03.log
- tasks/blokus-corner-contact-contest/environment/history/game_04.log
- tasks/blokus-corner-contact-contest/solution/solve.sh
- tasks/blokus-corner-contact-contest/solution/derive.sh
- tasks/blokus-corner-contact-contest/solution/desk_books/__init__.py
- tasks/blokus-corner-contact-contest/solution/desk_books/op_a.py
- tasks/blokus-corner-contact-contest/solution/board_hunt/__init__.py
- tasks/blokus-corner-contact-contest/solution/board_hunt/op_b.py
- tasks/blokus-corner-contact-contest/solution/board_hunt/engine.py
- tasks/blokus-corner-contact-contest/solution/card_out/__init__.py
- tasks/blokus-corner-contact-contest/solution/card_out/op_c.py
- tasks/blokus-corner-contact-contest/tests/test.sh
- tasks/blokus-corner-contact-contest/tests/test_outputs.py

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
    controls_tests: [test_e5_beryl_verdicts_match_play_from_the_sheets, test_g2_flint_forcing_sequences_really_force, test_j4_amber_friendly_sequences_reach_the_floor, test_k7_topaz_refutations_cover_every_threat, test_m8_jade_forts_are_not_the_kiosk_cheer]
  - id: B
    path: solution/card_out/op_c.py
    controls_tests: [test_a1_onyx_card_reads_as_a_tournament_card, test_r6_mica_emit_twice_stays_byte_identical_on_a_finished_card, test_c3_slate_filed_sequences_replay_past_the_sealed_judge, test_n2_coral_squares_left_is_not_padded]
  - id: C
    path: solution/desk_books/op_a.py
    controls_tests: [test_p5_quartz_whole_booklet_stands_up, test_w3_garnet_edge_touch_is_illegal_for_same_colour]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest
```
- path: environment/kiosk/draft.py
  kind: helper
  rhymes_with: op_b
  non_fix_purpose: fourth-placement cooperative all-win overnight draft
- path: environment/tools/sensei_hint.sh
  kind: helper
  rhymes_with: op_a
  non_fix_purpose: bounding-box fit surface whisper
- path: environment/kiosk/sheet_load.py
  kind: helper
  rhymes_with: op_c
  non_fix_purpose: list puzzle sheets for the printer
```

#### code_forbidden_tokens
```
code_forbidden_tokens: [corner, contact, blokus, polyomino, inventory, refutation, verdict, trap, fort, win, sensei, kiosk, puzzle, board, floor, placement, sequence, coop, fill, squares]
```
