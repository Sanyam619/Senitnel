### Decision
GO — Attempt 1. Onitama temple-path booklet under `games`: sealed table
judge, twelve Sensei-to-move rounds, win/trap/fort with card-rotation and
refutation coverage. No repair/debug framing; primary activity is contest
play under the rulebook and sealed referee.

### Metadata
- version: 2
- Task name: onitama-temple-path-contest
- Title: Onitama Temple Path
- Category: games
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [onitama, temple-path, card-rotation, tournament, table-judge, puzzle-book]
- Milestones: 0

## Authoring Brief

### Public contract
File `/output/onitama-card.json` with `schema_tag = onitama-temple-v1` and
twelve rounds (`board_id`, `status`, `card_used`, `mate_in`, `sequence`,
`sideboard`, `refutations`, `coop_temple`). House rules for move-card
rotation, temple capture, master capture, mate-length floors, and trap
threat coverage live under `/app/docs/`. Sealed `/app/bin/judge.jar`; leave
judge and puzzles unchanged. Emit twice on a finished card stays
byte-identical. Sensei whisper is non-authoritative for card legality after
rotation.

### Failure topology
Chess-mate heuristics ignore rotating move sets and mis-label traps as
wins. Kiosk drafts reuse cards illegally and pad `mate_in`. Sensei whispers
skip the post-move sideboard swap. Forced wins need lines that survive every
Pupil reply under live card rotation; traps need required ⊆ submitted
refutations for every graded losing first card; forts stay unreachable even
with Pupil sitting still inside the published Sensei-move budget.

### Environment shape
`/app/puzzles/` sheets, `/app/docs/` house rules, `/app/bin/judge.jar`
sealed referee, `/app/tools/sensei_hint.sh` surface bait, `/app/kiosk/`
overnight draft, `/app/history/` dialect samples.

### Required artifacts
Standard task layout: instruction, task.toml, output_contract, Dockerfile,
puzzles, docs, fixtures/judge.jar, kiosk, tools, history, solution oracle
(search-derived card), tests that recompute verdicts and replay the judge.

### Test plan
- Card schema / ordering / verdict vocabulary (all three statuses present)
- Sealed judge integrity + sequence replay
- Independent win/trap/fort classification vs search
- Forcing lines survive all Pupil replies under card rotation
- Friendly lines reach temple or master capture with Pupil sitting still
- Trap refutation coverage (required ⊆ submitted)
- Forts not stamped win; illegal-reuse / padded-budget kiosk bait live
- `mate_in` matches Sensei plies to the finishing blow (no padding)
- Whole-booklet round_ok
- Emit twice byte-identical on finished card
- Sensei whisper ≠ contest verdict on trap sheets

### Drafting guardrails
Symptoms-only instruction; no answer-key tallies or board-id status tables;
sample card uses fictional board ids; no intent comments on oracle packages;
languages=["bash"]; tournament tags; no `/app/ops/` repair aura; desk package
names `desk_books` / `board_hunt` / `card_out`.

### Triviality Ledger
- Kiosk all-win draft with illegal card reuse fails fort/trap and judge replay.
- Sensei whisper that ignores sideboard swap is not card legality after rotation.
- Friendly-line-called-win fails forcing_ok against fighting Pupil.
- Missing threat refutations fail coverage ⊆ check.
- Padded `mate_in` / dangling plies after temple or master capture fail judge equality.
- Chess-style fixed-piece search without card rotation fails distant trap cells.

### Per-gate Pitfall Inventory
- RC1/RC7: oracle is search over twelve sheets, not sed polarity.
- RC2: no broken_/golden_ names on solver surfaces.
- RC3: tests recompute play, not schema alone.
- RC4/RC5: EXPECTED live in test engine, not env goldens.
- RC6: instruction symptoms-only; rules in docs.
- GX9/GX10: no per-board answer recital or polarity contradiction.
- Category: games play booklet, not SE repair; jar is sealed tooling, languages bash.

### Initial Draft Commitments
- tasks/onitama-temple-path-contest/instruction.md
- tasks/onitama-temple-path-contest/task.toml
- tasks/onitama-temple-path-contest/output_contract.toml
- tasks/onitama-temple-path-contest/environment/Dockerfile
- tasks/onitama-temple-path-contest/environment/.dockerignore
- tasks/onitama-temple-path-contest/environment/requirements.txt
- tasks/onitama-temple-path-contest/environment/fixtures/judge.jar
- tasks/onitama-temple-path-contest/environment/puzzles/board_01.txt … board_12.txt
- tasks/onitama-temple-path-contest/environment/docs/*.md
- tasks/onitama-temple-path-contest/environment/tools/sensei_hint.sh
- tasks/onitama-temple-path-contest/environment/kiosk/*
- tasks/onitama-temple-path-contest/environment/history/game_*.log
- tasks/onitama-temple-path-contest/solution/*
- tasks/onitama-temple-path-contest/tests/*

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
    controls_tests: [test_e5_beryl_verdicts_match_play_from_the_sheets, test_g2_flint_forcing_sequences_really_force, test_j4_amber_friendly_sequences_reach_temple_or_master, test_k7_topaz_refutations_cover_every_graded_card]
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
  non_fix_purpose: padded-budget illegal-reuse all-win overnight draft
- path: environment/tools/sensei_hint.sh
  kind: helper
  rhymes_with: op_a
  non_fix_purpose: whisper that ignores post-move sideboard swap
- path: environment/kiosk/sheet_load.py
  kind: helper
  rhymes_with: op_c
  non_fix_purpose: list puzzle sheets for the printer
```

#### code_forbidden_tokens
```
code_forbidden_tokens: [temple, path, onitama, card, rotation, master, capture, refutation, verdict, trap, fort, win, sensei, kiosk, puzzle, board, floor, sequence, sideboard, coop, mate]
```
