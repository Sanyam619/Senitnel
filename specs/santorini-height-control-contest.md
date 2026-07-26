# Santorini Height-Control Contest

## Metadata
- version: 2
- task_name: santorini-height-control-contest
- category: games
- difficulty: hard
- languages: [bash]
- codebase_size: small

## Idea summary

Eleven First-to-move Santorini midgame sheets. File `/output/santorini-card.json`
with win/trap/fort summit verdicts, forcing lines, threat refutations, and true
`height_delta`. Sealed `judge.jar` referees move+build legality and ascent wins.
Sensei ignores domes; kiosk stamps cooperative summits as wins. Primary activity
is play under house rules — not repair/debug.

## Authoring Brief

### Goal

Contest booklet: classify each round as forced summit (`win`), cooperative-only
summit (`trap`), or unreachable (`fort`); prove wins with judge-legal sequences;
cover every graded losing first-climb threat on traps (required ⊆ submitted).

### Triviality Ledger

- Do not leave hardness as schema transcription: sensei/kiosk false-green all
  coop summits as wins; tests require fighting force and refutation coverage.
- Do not ship answer-key board tables or closed-form climb algebra in docs.
- Do not grade metric-only fields without play: `height_delta` must match true
  climb on the summit move; padding fails.
- Oracle searches with fighting Second replies; no hardcoded PV table.

### Per-gate Pitfall Inventory

- category_classifier: lead with tournament/play outcomes; `languages=["bash"]`;
  tags santorini/height-control/tournament/table-judge/puzzle-book/score-card;
  no repair/ops/API manuals; desk packages `desk_books`/`board_hunt`/`card_out`.
- Instruction sufficiency: document threat = non-summit first turn that leaves a
  next-turn coop summit; required ⊆ submitted; win = force vs every legal Second
  reply inside budget; coop_summit polarity; ascent wins before build; dome blocks.
- Ruff: explicit `check=` on every `subprocess.run`; no `v == v`.

### Initial Draft Commitments

- Card path `/output/santorini-card.json` (idea surface).
- Eleven boards: 4 wins, 5 traps, 2 forts; mix immediate and multi-ply wins;
  traps with ≥1 dome-denial refutation each; forts that look climbable to sensei.
- Sealed jar twin under `/opt/tbench/`; puzzles sealed beside it.
- Byte-identical refile via kiosk emit twice.

#### symbol_table

| id | path | role |
| --- | --- | --- |
| desk_a | solution/desk_books/op_a.py | dialect / history announce recovery |
| hunt_b | solution/board_hunt/op_b.py | Santorini search: force / coop / threats |
| card_c | solution/card_out/op_c.py | assemble tournament card |

#### flipping_point_contract

- desk_a controls announce/dialect cells only (history match).
- hunt_b controls status / coop_summit / refutation / height_delta correctness.
- card_c controls schema ordering / emit shape / refile identity.
- No single package flips a majority of mineral tests alone.
