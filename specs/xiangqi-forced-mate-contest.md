### Decision
GO — Attempt 1. Games contest booklet under sealed Xiangqi judge; primary activity is filing a forced-mate tournament card (not repair/debug). Hardness from palace/hobble/cannon/river polarities × forced vs cooperative mate × refutation coverage; sensei/kiosk are surface baits.

### Metadata
- version: 2
- Task name: xiangqi-forced-mate-contest
- Title: Xiangqi Forced-Mate Contest
- Category: games
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["xiangqi", "mate-contest", "tournament", "table-judge", "puzzle-book", "score-card"]
- Milestones: 0

## Authoring Brief

### Public contract
Submit `/output/xiangqi-card.json` for twelve Red-to-move rounds under `/app/puzzles/`. Schema: `schema_tag` (`xiangqi-mate-v1`), `rounds` ordered by `board_id`, each with `board_id`, `status` (`win`|`trap`|`fort`), `mate_in`, `sequence`, `river_cross`, `refutations` (`move`/`reply`), `coop_mate`. House rules under `/app/docs/`. Sealed judge `/app/bin/judge.jar`. Sensei and kiosk are surface-only. Do not alter judge or puzzles. Filing the finished card twice must stay byte-identical.

### Failure topology
Liberty-style / chess-pattern search mislabels traps when horse hobble, palace bounds, or cannon screens are ignored. Cooperative mate lines are not forced wins. Mate-length padding fails exact `mate_in`. Sensei ignores hobble; kiosk drafts allow illegal palace entry.

### Environment shape
`/app/puzzles/` (12 sheets), `/app/docs/` (score card, board format, table judge, house rules, printer notes), `/app/bin/judge.jar` (+ `/opt/tbench` seals), `/app/tools/sensei_hint.sh`, `/app/kiosk/emit_card.sh`, `/app/history/` announce samples.

### Required artifacts
instruction.md, task.toml, output_contract.toml, environment/*, solution/{solve.sh,derive.sh,board_hunt,desk_books,card_out}, tests/{test.sh,test_outputs.py}. ≥20 environment files excl. Docker.

### Test plan
Hard tests only: card shape/schema; printer repeat byte-identical; judge+puzzle seals unchanged; status/coop_mate match independent search; win sequences judge-legal, exact mate_in, river_cross, forcing; trap refutation coverage (required ⊆ submitted); fort rows empty sequences/refs; sensei fillable traps are not wins; novel-ish padding / illegal palace rejected via sequence validation.

### Drafting guardrails
Symptoms/outcomes instruction; no repair framing; languages=["bash"]; tournament tags; no answer-key mate lines in instruction; rules live in docs as outcomes.

### Triviality Ledger
- Sensei coop-fillable ≠ win (traps look fillable).
- Kiosk palace-illegal drafts fail sealed validate.
- Mate_in padding fails exact length.
- Ignoring hobble/cannon screens flips trap↔win.

### Per-gate Pitfall Inventory
- RC6: symptoms-only contest instruction (no fix recipes).
- Category: games framing; no SE repair aura; languages bash.
- GX9: no per-board answer triples in instruction.
- PLW1510/PLR0124: explicit check=; no v==v.
- Pip hashed lockfile; .dockerignore present.

### Initial Draft Commitments
- instruction.md, task.toml, output_contract.toml
- environment/Dockerfile, .dockerignore, requirements.txt
- environment/fixtures/judge.jar
- environment/puzzles/board_01.txt … board_12.txt
- environment/docs/{score_card,board_format,table_judge,house_rules,overnight_printer,match_logs}.md
- environment/tools/sensei_hint.sh
- environment/kiosk/{emit_card.sh,draft.py,sheet_load.py}
- environment/history/game_01.log … game_04.log
- solution/{solve.sh,derive.sh,board_hunt/op_b.py,desk_books/op_a.py,card_out/op_c.py}
- tests/{test.sh,test_outputs.py}

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table
```
- path: (oracle-only) board_hunt/op_b.py
  symbol: op_b
  kind: function
  signature: def op_b(sheet_path: str) -> dict
  purpose: classify one round into a card row
- path: (oracle-only) desk_books/op_a.py
  symbol: op_a
  kind: function
  signature: def op_a(docs_dir: str) -> str
  purpose: read schema tag string from docs
- path: (oracle-only) card_out/op_c.py
  symbol: op_c
  kind: function
  signature: def op_c(rows: list, out_path: str) -> None
  purpose: write ordered card JSON
```

#### flipping_point_contract
```
locations:
  - id: A
    path: solution/board_hunt/op_b.py
    controls_tests: [test_status_matches_search, test_win_sequences, test_trap_refutation_coverage]
  - id: B
    path: solution/desk_books/op_a.py
    controls_tests: [test_card_shape]
  - id: C
    path: solution/card_out/op_c.py
    controls_tests: [test_printer_repeats_completed_card, test_card_shape]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest
```
- path: environment/tools/sensei_hint.sh
  kind: helper
  rhymes_with: op_b
  non_fix_purpose: surface coop-mate whisper ignoring horse hobble
- path: environment/kiosk/draft.py
  kind: helper
  rhymes_with: op_c
  non_fix_purpose: overnight draft that stamps sensei verdicts / illegal palace tries
```

#### code_forbidden_tokens
xiangqi, mate, palace, horse, cannon, river, trap, fort, refutation, sequence, board, judge, sensei, kiosk, card, hobble, screen, forced, cooperative

#### naming_pass
Oracle packages use opaque op_a/op_b/op_c; test names avoid instruction nouns where required by validator; contests grade domain search not code repair.
