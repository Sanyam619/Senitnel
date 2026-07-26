### Decision
GO — Attempt 1. Games booklet (no repair/debug): sealed Rust arbiter, 12-sheet Kriegspiel force/coop lattice, history-discovered announce dialect, false-green open-board scout; hardness in multi-board adjudication not code patches.

### Metadata
- version: 2
- Task name: kriegspiel-blind-chess-adjudication
- Title: Kriegspiel Blind Chess Adjudication
- Category: games
- Languages: ["rust", "bash"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: ["kriegspiel", "blind-chess", "adjudication", "imperfect-information", "board-game", "arbiter"]
- Milestones: 0

## Authoring Brief

### Public contract

A Kriegspiel (blind chess) adjudication booklet under a sealed Rust arbiter. Agents file a score card at `/app/answers.json` grading twelve sheets. Primary work is imperfect-information game reasoning — legal try lines, force vs cooperative status, announce-dialect consistency — not source repair.

**Symptoms / framing (instruction.md level):**
- Twelve sheets under `/app/sheets/`; match books under `/app/history/`; house docs under `/app/docs/`.
- Sealed arbiter at `/app/bin/arbiter`; scout tool under `/app/tools/` may look cheerful on trap sheets.
- Some sheets look capturable when the defender cooperates and still count unwinnable when the defender resists under announce/try customs.

**Required outcomes:**
- `/app/answers.json` with `boards` ordered by `board_id` 1..12.
- Each row: `board_id`, `status` (`win`|`unwinnable`), `coop_capturable` (bool).
- Wins carry `sequence` (colour-prefixed UCI tries with announce tags the live dialect accepts).
- Coop∩unwinnable traps carry `refutations` covering every productive first Black try the arbiter treats as a threat try.
- Arbiter binary checksum unchanged.

**Constraints:**
- `category = games`; languages rust+bash; `allow_internet = false`.
- No repair/debug of arbiter sources; leave `/app/bin/arbiter` sealed.
- Not multi-container / not UI.

### Failure topology

Three interacting clusters. (1) Force vs coop: open-board or pass-defense fills look like wins on trap sheets; adversarial White replies keep the target. (2) Announce/try dialect: history books discriminate whether captures emit squares; wrong tags fail validate on multiple win lines. (3) Order-critical / try-budget fights: ply floors equal irreducible adversarial length; padding and cooperative White passes are rejected.

Hard because wrong L2 (coop vs force) fails many sheet statuses at once; dialect and sequence tags couple distant boards; scout false-greens traps.

### Environment shape

- Sealed Rust arbiter binary (built in Docker from opaque crates, only binary in runtime image).
- Twelve sheet files, match-history logs, tournament docs, false-green scout tool.
- No answer-shaped golden card under environment/.

### Required artifacts

- Standard task layout: instruction, task.toml, output_contract.toml, environment/**, solution/solve.sh (+ derive helpers), tests/test.sh + test_outputs.py.
- ≥20 non-Docker environment files.
- Oracle derives the card via search + arbiter validate (≥30 substantive LOC); no hardcoded full answer blob as the only path.

### Test plan

- `test_k3_zircon` — card shape: boards 1..12 with required fields.
- `test_m8_obsidian` — arbiter binary present + sha256 intact.
- `test_p2_garnet` — win sheets: status win, sequences arbiter-legal, target captured, min Black stone floors, White resistance present, no cooperative White pass.
- `test_q7_topaz` — trap sheets: status unwinnable, coop_capturable true, coop fill empties target, refutations cover threat tries and leave target occupied.
- `test_r1_onyx` — fort sheet: unwinnable and not coop_capturable.
- `test_t6_amber` — scout false-greens traps while card keeps them unwinnable.
- `test_v4_jade` — win sequences carry announce tags accepted only under the history-implied dialect.
- `test_w9_flint` — deep wins meet White-ply floors (irreducible resistance).

Multiple search strategies OK if arbiter outcomes match. Not chain-dependent across unrelated sheets.

### Drafting guardrails

Symptoms-only instruction (tournament language). No fix checklist, no repair verbs, no paste of announce algebra. Opaque oracle module names. EXPECTED statuses only in tests. Scout must genuinely false-green. Docs describe outcomes and score-card vocabulary without listing per-sheet answers.

### Triviality Ledger

- Treating scout open-board “fillable” as `win` fails every trap status test while coop fills still prove `coop_capturable`.
- Omitting refutations or covering only a subset of threat tries fails trap refutation coverage.
- Padding short captures with re-tries fails min Black floors and cooperative-pass rejection.
- Using silent capture tags when history proves square-announce (or the reverse) fails dialect-coupled win validates on ≥2 boards.
- Hand-writing JSON without arbiter-legal lines fails sequence legality tests.

### Per-gate Pitfall Inventory

- RC1: Oracle adds derivation/search logic; never delete-bug or restore a golden card from environment/.
- RC3: Tests assert arbiter-validated captures, refutations, floors — not mere JSON existence.
- RC5: No golden answers.json under environment/.
- RC6: Instruction symptoms-only; dialect recovered from history/docs behavior.
- RC7: derive path ≥30 substantive LOC.
- CR1/CR2: Manifest symbols `op_a`/`op_b`/`op_c` in distinct roots; concentration ≤0.5.
- CR7/GX9: Opaque test names; no per-sheet answer recital in instruction.
- Static: allow_internet=false, .dockerignore, absolute /app paths, category games, Rust language surface.

### Initial Draft Commitments

- `tasks/kriegspiel-blind-chess-adjudication/task.toml`
- `tasks/kriegspiel-blind-chess-adjudication/instruction.md`
- `tasks/kriegspiel-blind-chess-adjudication/output_contract.toml`
- `tasks/kriegspiel-blind-chess-adjudication/tests/test.sh`
- `tasks/kriegspiel-blind-chess-adjudication/tests/test_outputs.py`
- `tasks/kriegspiel-blind-chess-adjudication/solution/solve.sh`
- `tasks/kriegspiel-blind-chess-adjudication/solution/derive.sh`
- `tasks/kriegspiel-blind-chess-adjudication/solution/lane_knit/op_a.py`
- `tasks/kriegspiel-blind-chess-adjudication/solution/seat_fold/op_b.py`
- `tasks/kriegspiel-blind-chess-adjudication/solution/roll_emit/op_c.py`
- `tasks/kriegspiel-blind-chess-adjudication/environment/Dockerfile`
- `tasks/kriegspiel-blind-chess-adjudication/environment/.dockerignore`
- `tasks/kriegspiel-blind-chess-adjudication/environment/Cargo.toml`
- `tasks/kriegspiel-blind-chess-adjudication/environment/crates/seat_q/Cargo.toml`
- `tasks/kriegspiel-blind-chess-adjudication/environment/crates/seat_q/src/lib.rs`
- `tasks/kriegspiel-blind-chess-adjudication/environment/crates/fold_r/Cargo.toml`
- `tasks/kriegspiel-blind-chess-adjudication/environment/crates/fold_r/src/lib.rs`
- `tasks/kriegspiel-blind-chess-adjudication/environment/crates/gate_w/Cargo.toml`
- `tasks/kriegspiel-blind-chess-adjudication/environment/crates/gate_w/src/lib.rs`
- `tasks/kriegspiel-blind-chess-adjudication/environment/crates/arbiter/Cargo.toml`
- `tasks/kriegspiel-blind-chess-adjudication/environment/crates/arbiter/src/main.rs`
- `tasks/kriegspiel-blind-chess-adjudication/environment/docs/score_card.md`
- `tasks/kriegspiel-blind-chess-adjudication/environment/docs/table_arbiter.md`
- `tasks/kriegspiel-blind-chess-adjudication/environment/docs/match_books.md`
- `tasks/kriegspiel-blind-chess-adjudication/environment/docs/sheet_format.md`
- `tasks/kriegspiel-blind-chess-adjudication/environment/tools/scout_hint.sh`
- `tasks/kriegspiel-blind-chess-adjudication/environment/sheets/board_01.txt` … `board_12.txt` (12 files)
- `tasks/kriegspiel-blind-chess-adjudication/environment/history/game_01.log` … `game_08.log` (8 files)

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: lane_knit/op_a.py
  symbol: op_a
  kind: function
  signature: def op_a(a, b):
  purpose: recover announce dialect token from match-book refuse/accept patterns
- path: seat_fold/op_b.py
  symbol: op_b
  kind: function
  signature: def op_b(a, b):
  purpose: classify force/coop outcomes and build win sequences or fort rows
- path: roll_emit/op_c.py
  symbol: op_c
  kind: function
  signature: def op_c(a, b):
  purpose: build trap refutation covers and emit the finished score card
```

#### flipping_point_contract

```
locations:
  - id: A
    path: lane_knit/op_a.py
    controls_tests: [test_v4_jade, test_k3_zircon]
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
- path: tools/scout_hint.sh
  kind: helper
  rhymes_with: op_b
  non_fix_purpose: open-board fillability whisper that false-greens coop traps
- path: docs/sheet_format.md
  kind: config-reader
  rhymes_with: op_a
  non_fix_purpose: documents sheet file layout without listing statuses
- path: crates/fold_r/src/lib.rs
  kind: module
  rhymes_with: op_c
  non_fix_purpose: compile-time announce emission inside sealed arbiter (correct; not agent-edited)
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [kriegspiel, blindfold, adjudication, sheets, history, arbiter, scout, announce, dialect, try, tries, sequence, status, coop, capturable, refutations, boards, board, win, unwinnable, capture, target, white, black, score, card, table, books, house, customs, resistance, force, cooperative, padding, ply]
```
