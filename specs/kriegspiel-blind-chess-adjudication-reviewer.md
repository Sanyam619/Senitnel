### Decision
GO — Attempt 1. Games booklet (no repair/debug): sealed Rust arbiter, 12-sheet Kriegspiel force/coop lattice, history-discovered announce dialect, false-green open-board scout; hardness in multi-board adjudication not code patches.

### Metadata
- Task name: kriegspiel-blind-chess-adjudication
- Title: Kriegspiel Blind Chess Adjudication
- Category: games
- Languages: ["rust", "bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["kriegspiel", "blind-chess", "adjudication", "imperfect-information", "board-game", "arbiter"]
- Milestones: 0

### Discovery budget
- Discovery: Live capture-announce dialect (square-tagged vs silent) implied by refuse/accept patterns in match books.
  Planned location: `/app/history/game_*.log` + arbiter validate announce checks
  Why instruction must not reveal it: Naming the dialect collapses history discrimination into a one-field guess (Weiqi `rule` failure mode).
- Discovery: Which sheets are force-wins vs coop∩unwinnable traps vs forts under adversarial White.
  Planned location: `/app/sheets/board_*.txt` + arbiter probe/validate behavior
  Why instruction must not reveal it: Per-sheet answer key in instruction is GX9 collapse.
- Discovery: Irreducible adversarial PV length and legal White resistance points (no cooperative pass; no padding).
  Planned location: arbiter validate + score_card floors
  Why instruction must not reveal it: Publishing exact PVs or per-sheet ply tables enables padding/transcription.

### Anti-trivialization verdict
All 21 checks PASS for a games booklet with sealed arbiter, multi-sheet coupling, no repair surface, ≥3 discoveries, symptoms-only instruction, three topologies (dialect/force/refutation). Hard-only gate PASS relative to Weiqi EASY collapse lessons (no single categorical field; traps dominate; floors irreducible).

### Topology enumeration (3 candidate fix topologies)
1. **Dialect-first:** recover announce tags from history → annotate win sequences → classify boards. Locations: history parser, sequence tagger, win validator. No single location yields trap refutations.
2. **Force-search-first:** adversarial search per sheet → coop probe → dialect tag pass. Locations: force search, coop probe, dialect tagger. Search alone mis-tags dialect-coupled validates.
3. **Refutation-matrix-first:** enumerate threat tries → White replies → residual wins/forts → dialect. Locations: threat enum, reply search, residual classifier. Refutations alone do not produce legal deep win PVs.

### Rubric axes
- Verifiable: PASS — arbiter-backed deterministic pytest.
- Well-specified: PASS — score-card vocabulary in docs; instruction points at outcomes.
- Solvable: PASS — expert with arbiter probes in a few hours.
- Difficult: PASS — imperfect-info adjudication + trap matrix beyond textbook chess puzzles.
- Interesting: PASS — real Kriegspiel adjudication skill.
- Outcome-verified: PASS — grades `/app/answers.json` via arbiter, not process.

### Hardness axes
- Discover: PASS — dialect + statuses from history/sheets/arbiter, not instruction.
- Synthesize: PASS — dialect × force/coop × refutations across 12 sheets.
- Diagnose: PASS — symptoms (scout cheerful; traps look fillable) not causes.
- Navigate coupling: PASS — wrong coop labeling fails many traps; wrong dialect fails multiple wins.
- Reason beyond training: PASS — Kriegspiel announce/try + force/coop certificates, not standard chess mate books.

### Instruction completeness test
No — instruction alone lacks per-sheet statuses, dialect identity, PVs, and refutation covers; agent must engage sheets, history, and arbiter.

## Reviewer Appendix

### Implementation plan
Ship a correct sealed Rust arbiter implementing chess legality + Kriegspiel announce tags + validate/probe CLIs. Twelve crafted endgame sheets (4 deep wins, 7 coop traps, 1 fort). Match logs encode square-announce dialect. Scout open-board false-greens traps. Oracle Python modules (opaque) search with arbiter and write the card — agents never patch Rust.

### Proposed file inventory
As Initial Draft Commitments in authoring spec (12 sheets, 8 logs, 4 docs, scout, Rust workspace crates, Docker, tests, solution derive modules).

### Oracle notes
`derive.sh` copies `op_a`/`op_b`/`op_c` into `/app`, recovers dialect, solves each sheet via arbiter-backed search, emits `/app/answers.json`. No hardcoded full golden blob as sole path; jar/arbiter re-check every PV.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
Write a complete score card that passes arbiter-validated force/coop/refutation/dialect checks — not a tiny config edit.

Likely editable frontier:
- `/app/answers.json` (primary)
- exploratory use of arbiter/scout (read-only)

Requirement-to-file map:
- score card → answers.json
- dialect → history + sequence tags
- statuses → sheet search

Oracle estimated complexity: 200+ LOC across three modules + derive.sh

Red flags:
- Residual risk that frontier chess engines + arbiter still clear boards (mitigated by trap/refutation contract and dialect tags).

Residual hardness:
Multi-sheet force/coop certificates under Kriegspiel announce rules with irreducible floors and false-green scout — same structural harden as Weiqi round-4, new imperfect-info domain.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
kriegspiel, blindfold, adjudication, sheets, history, arbiter, scout, announce, dialect, try, tries, sequence, status, coop, capturable, refutations, boards, board, win, unwinnable, capture, target, white, black, score, card, table, books, house, customs, resistance, force, cooperative, padding, ply

**Renames during drafting:**
- None — first-pass naming was already clean against the forbidden list

**Test names audited:**
- test_k3_zircon
- test_m8_obsidian
- test_p2_garnet
- test_q7_topaz
- test_r1_onyx
- test_t6_amber
- test_v4_jade
- test_w9_flint

**Concentration math:**
- Total tests across `flipping_point_contract`: 8
- Per location:
  - L1 (`lane_knit/op_a.py`): 2/8 = 0.25
  - L2 (`seat_fold/op_b.py`): 3/8 = 0.375
  - L3 (`roll_emit/op_c.py`): 3/8 = 0.375
- Cap: 0.5. Max ratio observed: 0.375. Status: PASS

### Per-test feasibility pre-check
- Test: test_k3_zircon — Checks: card shape — Valid approaches: 2+ — Chain-dependent: no — Feasibility: LOW
- Test: test_m8_obsidian — Checks: arbiter intact — Valid approaches: 1 — Chain-dependent: no — Feasibility: LOW
- Test: test_p2_garnet — Checks: win PVs — Valid approaches: 2+ — Chain-dependent: no — Feasibility: MEDIUM
- Test: test_q7_topaz — Checks: traps+refs — Valid approaches: 2+ — Chain-dependent: no — Feasibility: MEDIUM
- Test: test_r1_onyx — Checks: fort — Valid approaches: 2+ — Chain-dependent: no — Feasibility: LOW
- Test: test_t6_amber — Checks: scout false-green — Valid approaches: 2+ — Chain-dependent: no — Feasibility: LOW
- Test: test_v4_jade — Checks: dialect tags — Valid approaches: 2+ — Chain-dependent: no — Feasibility: MEDIUM
- Test: test_w9_flint — Checks: White-ply floors — Valid approaches: 2+ — Chain-dependent: no — Feasibility: MEDIUM
