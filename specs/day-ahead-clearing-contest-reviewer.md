### Decision
GO — Attempt 1. Games contest booklet (no repair/debug): sealed table judge.jar, twelve puzzle rounds with feasible_clear / infeasible / reserve_short lattice, clause refutations, kiosk false-green; hardness in multi-round adjudication not code patches.

### Metadata
- Task name: day-ahead-clearing-contest
- Title: Day-Ahead Clearing Contest
- Category: games
- Languages: ["python", "java", "bash"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: ["contest", "puzzles", "clearing", "reserve", "judge"]
- Milestones: 0

### Discovery budget
- Discovery: Energy-feasible clearings that miss reserve demand must be status reserve_short with reserve_binds true, not infeasible.
  Planned location: environment/docs/contest_rules.md + sealed judge
  Why instruction must not reveal it: Checklist polarity collapses half the booklet.
- Discovery: Which rulebook clause_id blocks the naive full-clear on each blocked round.
  Planned location: contest_rules.md clauses + puzzles/*.sheet
  Why instruction must not reveal it: Pasted mapping is an answer key for refutations.
- Discovery: SMP equals offer_price of the marginal cleared unit under house tie-break from examples/judge probes.
  Planned location: docs + history samples + judge behavior
  Why instruction must not reveal it: Closed-form dump turns SMP into a one-liner.
- Discovery: Kiosk projector lines are non-authoritative even when energy-feasible.
  Planned location: environment/kiosk/
  Why instruction must not reveal it: Must not enumerate which kiosk lines are wrong.

### Anti-trivialization verdict
All 21 checks PASS in attempt-1 evidence. Highlights: not hidden-instance; not single-artifact repair; oracle derives via op_a/op_b/op_c; instruction symptoms-only; topology distribution satisfied.

### Topology enumeration (3 candidate fix topologies)
- T1 Rules × boards × card emission — contest_rules.md, puzzles, roll_emit/op_c.py; no single file suffices.
- T2 SMP recovery × commitment search × reserve classify — lane_knit/op_a.py, seat_fold/op_b.py, judge.jar; no single location writes a full correct card.
- T3 Kiosk bait × blocked refutations × feasible wins — kiosk/, op_c.py, op_b.py; ignoring kiosk alone does not classify statuses.

### Rubric axes
- Verifiable: PASS — judge-validated deterministic card.
- Well-specified: PASS — pinned paths/schema/statuses.
- Solvable: PASS — expert desk, finite boards, sealed judge.
- Difficult: PASS — multi-status trap matrix.
- Interesting: PASS — paid ISO-style clearing as contest.
- Outcome-verified: PASS — grade card outcomes, not process.

### Hardness axes
- Discover: PASS — SMP, reserve polarity, clause ids from env/judge.
- Synthesize: PASS — twelve coupled rounds + kiosk.
- Diagnose: PASS — symptoms-only contest framing.
- Navigate coupling: PASS — wrong L2 fails many cells.
- Reason beyond training: PASS — contest certificates ≠ textbook LP homework.

### Instruction completeness test
Can the agent solve from instruction.md alone? No — per-round statuses, SMPs, and clause ids require puzzles, rules, and judge engagement.

## Reviewer Appendix

### Implementation plan
Ship a weiqi-shaped contest: `/app/puzzles/` (12 sheets with offer curves + reserve demand), `/app/docs/contest_rules.md` (clause ids + scenario prose for reserve_short vs infeasible), sealed `/app/bin/judge.jar` built then sources stripped, `/app/kiosk/` false-green drafts, `/app/ops/run_clearing_card.sh` invoking judge, sensei hint decoy. Oracle search helpers under solution/ derive the card; tests re-validate with judge and assert schema/status/SMP/refutation/kiosk divergence. Keep category games via contest language and jar aura (no Cargo/ELF arbiter).

### Proposed file inventory
Matches authoring Initial Draft Commitments (≥20 env files): Dockerfile, .dockerignore, docs (3), ops entrypoint, tools/sensei_hint.sh, kiosk drafts (3), history samples (3), puzzles (12), judge materialization path, plus build-only judge_src excluded from runtime.

### Oracle notes
solve.sh → derive.sh runs op_a (marginal), op_b (status+cleared), op_c (refutations+emit), calling judge.jar to validate lines. Substantive search LOC ≥30; no golden blob copy from environment/.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
A single merit-order script cannot satisfy reserve_short, infeasible, and clause refutations together.

Likely editable frontier:
- solution/lane_knit/op_a.py, seat_fold/op_b.py, roll_emit/op_c.py (oracle)
- Agent-visible: puzzles, contest_rules, kiosk, judge CLI — reasoning, not patches

Requirement-to-file map:
- SMP → op_a + judge
- status/cleared → op_b + puzzles
- refutations/card → op_c + contest_rules clauses
- kiosk false-green → kiosk/ + test_t6_amber

Oracle estimated complexity: 80–150 LOC search/emit across three modules

Red flags:
- Answer-labeled sheet comments
- Readable LP formula in docs next to EXPECTED
- ELF/Cargo judge (SE classifier)

Residual hardness:
Multi-round status matrix under sealed judge with reserve polarity and clause coverage.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
puzzle, puzzles, rounds, clearing, contest, generators, marginal, price, reserve, binds, rulebook, judge, kiosk, projector, card, status, statuses, refutation, clause, feasible, infeasible, entrypoint, offer, curves, demand, smp, unit, mw, energy, auction, market, desk, board, boards, sheet, sheets, commitment, line, lines

**Renames during drafting:**
- `pick_smp` → `op_a`: avoid smp/marginal in symbol
- `classify_reserve` → `op_b`: avoid reserve in symbol
- `emit_card` → `op_c`: avoid card in symbol

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
- Total tests across flipping_point_contract: 8
- Per location:
  - L1 (`lane_knit/op_a.py`): 2/8 = 0.25
  - L2 (`seat_fold/op_b.py`): 3/8 = 0.375
  - L3 (`roll_emit/op_c.py`): 3/8 = 0.375
- Cap: 0.5. Max ratio observed: 0.375. Status: PASS

### Per-test feasibility pre-check
- Test: test_k3_zircon — Checks schema/nesting — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_m8_obsidian — Checks judge intact + entrypoint — Valid approaches: 1 — Chain-dependent: no — Feasibility risk: LOW
- Test: test_p2_garnet — Checks feasible_clear judge lines — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: MEDIUM
- Test: test_q7_topaz — Checks reserve_short + refutation — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: MEDIUM
- Test: test_r1_onyx — Checks infeasible + refutation — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: MEDIUM
- Test: test_t6_amber — Checks kiosk divergence — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_v4_jade — Checks SMP marginal — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: MEDIUM
- Test: test_w9_flint — Checks deep feasible constraints — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: MEDIUM
