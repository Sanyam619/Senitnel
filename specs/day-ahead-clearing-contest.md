### Decision
GO — Attempt 1. Games contest booklet (no repair/debug): sealed table judge.jar, twelve puzzle rounds with feasible_clear / infeasible / reserve_short lattice, clause refutations, kiosk false-green; hardness in multi-round adjudication not code patches.

### Metadata
- version: 2
- Task name: day-ahead-clearing-contest
- Title: Day-Ahead Clearing Contest
- Category: games
- Languages: ["python", "java", "bash"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: ["contest", "puzzles", "clearing", "reserve", "judge"]
- Milestones: 0

## Authoring Brief

### Public contract

A day-ahead clearing contest under a sealed table judge. Agents play twelve puzzle rounds and file a contest card. Primary work is contest reasoning (commitment lines, SMP, reserve binding, clause refutations) — not source repair.

**Symptoms / framing (instruction.md level):**
- Twelve puzzles under `/app/puzzles/`; house rules under `/app/docs/contest_rules.md`.
- Sealed judge at `/app/bin/judge.jar`; kiosk projector under `/app/kiosk/` may disagree.
- Submit `/output/market-clearing-card.json` via `/app/ops/run_clearing_card.sh` (must invoke the sealed judge).

**Required outcomes:**
- Card `version` == 1; `rounds` length 12.
- Each round: `round_id` (string), `cleared` (array of `{unit_id, mw, offer_price}`), `smp` (number), `reserve_binds` (boolean), `status` among `feasible_clear`|`infeasible`|`reserve_short`.
- For `infeasible` / `reserve_short`: `refutation` string = rulebook `clause_id` blocking naive full-clear.
- `feasible_clear`: judge accepts cleared set, mw, and smp against defending constraints.
- `infeasible`: judge accepts that no feasible energy clear exists.
- `reserve_short`: energy clears but reserve is short; `reserve_binds` true.
- Judge binary/jar unchanged; two consecutive entrypoint runs → byte-identical card.

**Constraints:**
- `category = games`; `allow_internet = false`.
- No repair of judge sources; not multi-container / not UI.
- Paths use contest nouns (`puzzles/`, `contest_rules.md`, `judge.jar`) — not `market_judge` / `/app/rounds/` (data_proc bait).

### Failure topology

Three clusters. (1) Force-style feasible clears vs traps: naive merit-order / full-offer lines look fine on kiosk but fail judge on reserve or energy. (2) Reserve polarity: energy-feasible but reserve-short rounds are `reserve_short`, not `infeasible`. (3) Clause refutations: blocked rounds need the correct rulebook clause_id covering the naive full-clear; wrong or missing refs fail coverage tests.

Hard because wrong L2 (reserve vs infeasible) fails several rounds at once; SMP tie-break couples cleared sets to `smp`; kiosk false-greens reinforce the wrong policy.

### Environment shape

- Sealed judge.jar (built in Docker from opaque sources, only jar in runtime image; Python or Java — no ELF toolchain aura).
- Twelve puzzle sheets, contest rulebook with clause ids, optional history samples, kiosk drafts, desk entrypoint, false-green sensei hint.
- No golden card under environment/.

### Required artifacts

- Standard layout: instruction.md, task.toml, output_contract.toml, environment/**, solution/solve.sh (+ derive helpers lane_knit/seat_fold/roll_emit), tests/test.sh + test_outputs.py.
- ≥20 non-Docker environment files.
- Oracle derives card via search + judge validate (≥30 substantive LOC); no hardcoded full answer blob as the only path.

### Test plan

- `test_k3_zircon` — card shape: version 1, twelve rounds, required fields, schema nesting.
- `test_m8_obsidian` — judge.jar present + checksum intact; entrypoint invokes judge.
- `test_p2_garnet` — feasible_clear rounds: judge-accepted cleared/mw/smp; reserve_binds consistent.
- `test_q7_topaz` — reserve_short rounds: status + reserve_binds true + clause refutation; energy line judge-ok, reserve short.
- `test_r1_onyx` — infeasible rounds: status + refutation; judge rejects energy feasibility.
- `test_t6_amber` — kiosk/sensei false-greens naive clears while card keeps blocked statuses.
- `test_v4_jade` — SMP matches judge-accepted marginal on feasible and reserve_short energy clears.
- `test_w9_flint` — deep feasible rounds meet irreducible commitment constraints (no padded dummy units).

Multiple search strategies OK if judge outcomes match. Not chain-dependent across unrelated rounds.

### Drafting guardrails

Symptoms-only contest instruction. No fix checklist, no LP algorithm paste, no per-round answer key. Opaque oracle module names (`op_a`/`op_b`/`op_c`). EXPECTED statuses only in tests. Kiosk must genuinely false-green. Docs describe outcomes and card vocabulary without listing per-round answers. Prefer jar judge over Rust ELF (category SE risk).

### Triviality Ledger

- Copying kiosk full-clear lines as `feasible_clear` fails every reserve_short/infeasible test while judge rejects those lines.
- Labeling all non-clears as `infeasible` fails reserve_short cells that need energy-ok + reserve short + `reserve_binds true`.
- Omitting or inventing clause_ids fails refutation coverage on blocked rounds.
- Hand-writing JSON without judge-legal cleared/mw/smp fails legality tests on feasible rounds.
- A global merit-order script that ignores reserve demand greens some cells and fails the matrix.

### Per-gate Pitfall Inventory

- RC1: Oracle adds derivation/search logic; never restore a golden card from environment/.
- RC3: Tests assert judge-validated clears, statuses, SMP, refutations — not mere JSON existence.
- RC5: No golden market-clearing-card.json under environment/.
- RC6: Instruction symptoms-only; SMP/reserve polarity recovered from rules+judge behavior.
- RC7: derive path ≥30 substantive LOC across op_a/op_b/op_c.
- CR1/CR2: Manifest symbols in distinct roots; concentration ≤0.5.
- CR7/GX9: Opaque test names; no per-round answer recital in instruction.
- Category: contest paths + jar judge; avoid arbiter/forensics/ELF/Cargo in the zip.
- Static: allow_internet=false, .dockerignore, absolute /app paths, no hidden COPY sources.

### Initial Draft Commitments

- `tasks/day-ahead-clearing-contest/task.toml`
- `tasks/day-ahead-clearing-contest/instruction.md`
- `tasks/day-ahead-clearing-contest/output_contract.toml`
- `tasks/day-ahead-clearing-contest/tests/test.sh`
- `tasks/day-ahead-clearing-contest/tests/test_outputs.py`
- `tasks/day-ahead-clearing-contest/solution/solve.sh`
- `tasks/day-ahead-clearing-contest/solution/derive.sh`
- `tasks/day-ahead-clearing-contest/solution/lane_knit/op_a.py`
- `tasks/day-ahead-clearing-contest/solution/seat_fold/op_b.py`
- `tasks/day-ahead-clearing-contest/solution/roll_emit/op_c.py`
- `tasks/day-ahead-clearing-contest/environment/Dockerfile`
- `tasks/day-ahead-clearing-contest/environment/.dockerignore`
- `tasks/day-ahead-clearing-contest/environment/docs/contest_rules.md`
- `tasks/day-ahead-clearing-contest/environment/docs/puzzle_format.md`
- `tasks/day-ahead-clearing-contest/environment/docs/score_card.md`
- `tasks/day-ahead-clearing-contest/environment/ops/run_clearing_card.sh`
- `tasks/day-ahead-clearing-contest/environment/tools/sensei_hint.sh`
- `tasks/day-ahead-clearing-contest/environment/kiosk/draft_01.txt`
- `tasks/day-ahead-clearing-contest/environment/kiosk/draft_02.txt`
- `tasks/day-ahead-clearing-contest/environment/kiosk/draft_03.txt`
- `tasks/day-ahead-clearing-contest/environment/judge_src/` (build-only; stripped from runtime image)
- `tasks/day-ahead-clearing-contest/environment/data/tools/judge.jar` (or materialize to `/app/bin/judge.jar` in Dockerfile)
- `tasks/day-ahead-clearing-contest/environment/puzzles/round_01.sheet` … `round_12.sheet` (12 files)
- `tasks/day-ahead-clearing-contest/environment/history/sample_a.log`
- `tasks/day-ahead-clearing-contest/environment/history/sample_b.log`
- `tasks/day-ahead-clearing-contest/environment/history/sample_c.log`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: lane_knit/op_a.py
  symbol: op_a
  kind: function
  signature: def op_a(a, b):
  purpose: recover marginal price token from offer boards and judge samples
- path: seat_fold/op_b.py
  symbol: op_b
  kind: function
  signature: def op_b(a, b):
  purpose: classify round status and build cleared unit rows
- path: roll_emit/op_c.py
  symbol: op_c
  kind: function
  signature: def op_c(a, b):
  purpose: attach clause refutations and emit the contest card
```

#### flipping_point_contract

```
locations:
  - id: A
    path: lane_knit/op_a.py
    controls_tests: [test_k3_zircon, test_v4_jade]
  - id: B
    path: seat_fold/op_b.py
    controls_tests: [test_p2_garnet, test_r1_onyx, test_w9_flint]
  - id: C
    path: roll_emit/op_c.py
    controls_tests: [test_q7_topaz, test_t6_amber, test_m8_obsidian]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: tools/sensei_hint.sh
  kind: helper
  rhymes_with: op_b
  non_fix_purpose: kiosk-style whisper that false-greens naive full-clear lines
- path: docs/puzzle_format.md
  kind: config-reader
  rhymes_with: op_a
  non_fix_purpose: documents puzzle sheet layout without listing statuses
- path: ops/run_clearing_card.sh
  kind: helper
  rhymes_with: op_c
  non_fix_purpose: desk entrypoint that invokes sealed judge on claimed lines
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [puzzle, puzzles, rounds, clearing, contest, generators, marginal, price, reserve, binds, rulebook, judge, kiosk, projector, card, status, statuses, refutation, clause, feasible, infeasible, entrypoint, offer, curves, demand, smp, unit, mw, energy, auction, market, desk, board, boards, sheet, sheets, commitment, line, lines]
```
