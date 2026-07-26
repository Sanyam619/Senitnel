### Decision
GO — Attempt 1. Dual-language (Rust ledger + Go topology inspector) shed-replay stale-availability design with generation-pin barrier, adjacency cascade, and MW-threshold probe decoy; three-location flipping contract at 2/6 each.

### Metadata
- Task name: feeder-load-shed-replay
- Title: Feeder Load-Shed Replay
- Category: system-administration
- Languages: ["Rust", "Go"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: ["ops", "rust", "go", "topology", "ledger", "infrastructure"]
- Milestones: 0

### Discovery budget
- Discovery: Availability bitmap entries are keyed by topology generation; replay updates load-state and advances the ledger cursor but leaves the generation pin unchanged, so the Go inspector keeps serving pre-shed bits.
  Planned location: `environment/ledger/src/apply.rs` (`fold_q7`) and `environment/data/state/gen_pin.json`
  Why instruction must not reveal it: Naming the generation pin tells the agent to bump one integer and skip cascade/probe reasoning.

- Discovery: Feeder-level shed must cascade through adjacency to descendant circuits; writing only the feeder node into the bitmap leaves circuit-level probes green while feeder MW totals look correct.
  Planned location: `environment/topo/internal/walk/walk_r4.go` and fixture adjacency under `environment/data/topo/`
  Why instruction must not reveal it: Stating "walk children" collapses the hard coupling into a single graph recipe.

- Discovery: The Go probe exposes an MW-threshold fast path that ignores the bitmap; using it can pass shallow load-total checks but fails multi-circuit cascade and second-pass idempotence.
  Planned location: `environment/topo/cmd/topoprobe/main.go` and `environment/topo/internal/seal/seal_n2.go`
  Why instruction must not reveal it: Warning agents off the fast path removes the primary false-confidence trap.

- Discovery: Invalidation must be published before the ledger cursor advances; otherwise a second replay is a no-op that never rebuilds availability.
  Planned location: barrier ordering in `fold_q7` relative to `seal_n2` consumers
  Why instruction must not reveal it: Revealing cursor-after-invalidate ordering turns the task into a transcribed sequence.

### Anti-trivialization verdict
| Check | Verdict | Reasoning |
| --- | --- | --- |
| Disclosure-collapse | PASS | Symptoms-only brief omits pin/cascade/seal order |
| Hidden-instance | PASS | Fixed multi-feeder fixture; coordination not file-hunt |
| Single-artifact repair | PASS | Three roots required |
| Generalization | PASS | Multi-feeder cascade + idempotence |
| Prompt-honesty | PASS | No cause or component named |
| Cheating-vs-difficulty | PASS | Probes grade outcomes |
| Mechanical-fix filter | PASS | Not deps/timeouts |
| Localized-fix | PASS | Rust+Go distributed locus |
| Oracle-locality | PASS | Multi-file patch + rebuild |
| Small declarative-cluster | PASS | Not one config knob |
| Grep-collapse | PASS | Opaque symbols; forbidden tokens |
| Pre-factored-helper | PASS | Decoys rhyme, non-fix bodies |
| Recipe-discount | PASS | Cascade+barrier beyond cache flush |
| Security-aura discount | PASS | Ops, not security theater |
| Orthogonal-checklist | PASS | Coupled tradeoffs |
| Harness-discount | PASS | Single container |
| One-pass solvability | PASS | Cross-language correlation required |
| Hard-only gate | PASS | Hard |
| Discovery budget test | PASS | ≥3 discoveries |
| Instruction specificity test | PASS | symptoms-only |
| Topology distribution test | PASS | 3 topologies × ≥3 locs |

### Topology enumeration (3 candidate fix topologies)
- T1 Invalidation-first: `fold_q7` + `walk_r4` + `seal_n2` — pin bump alone insufficient without cascade and seal.
- T2 Cascade-first: `walk_r4` + `fold_q7` + `seal_n2` — full rebuild without pin/barrier still races or skips second pass.
- T3 Seal-first: `seal_n2` + `fold_q7` + `walk_r4` — correct seal cannot invent cascaded bits under the active generation.

### Rubric axes
- Verifiable: PASS — deterministic probes and JSON report.
- Well-specified: PASS — two readers agree on unavailable circuits + MW + idempotence.
- Solvable: PASS — expert hours, bounded codebase.
- Difficult: PASS — dual-language ops coupling.
- Interesting: PASS — real shed/availability drift.
- Outcome-verified: PASS — grade probe results not process.

### Hardness axes
- Discover: PASS — pin keying and fast-path trap not in instruction.
- Synthesize: PASS — Rust apply + Go walk + Go seal.
- Diagnose: PASS — symptoms without causes.
- Navigate coupling: PASS — barrier/cascade/seal tradeoffs.
- Reason beyond training: PASS — domain-specific dual-language ops, not textbook recipe.

### Instruction completeness test
Can the agent solve this by reading ONLY instruction.md without deeply engaging with the codebase? No — generation-pin semantics, cascade depth, and unsafe MW seal path are only recoverable from sources, fixtures, and probe behavior.

## Reviewer Appendix

### Implementation plan
Build a Rust ledger crate that can replay shed batches into load-state while initially advancing the cursor without bumping the generation pin (broken `fold_q7`). Build a Go inspector with adjacency walk (`walk_r4` initially marking only roots or writing under wrong key) and a seal path that defaults toward quantity thresholds (`seal_qty` wired, `seal_n2` incomplete). Seed multi-feeder fixtures so MW and edge dumps look healthy after naive replay. Oracle completes pin+barrier in Rust, adjacency cascade in Go, and bitmap-keyed seal; rebuilds binaries; runs replay; writes reconcile report. Verifier checks availability slots, MW alignment, edge stability, fan-out cascade, report shape, and second-pass idempotence.

### Proposed file inventory
Matches Authoring Brief Initial Draft Commitments (30+ environment files excluding Dockerfile/dockerignore): ledger Rust modules + ledctl, topo Go packages + topoprobe, data fixtures (journal, topo, state), config paths, rebuild/replay scripts.

### Oracle notes
`solve.sh` patches `fold_q7` to publish invalidation before cursor advance and sync pin; implements `walk_r4` to expand marked roots through adjacency into bitmap under active key; implements `seal_n2` to build report from bitmap+key (not MW thresholds); runs `scripts/rebuild.sh` then `scripts/run_replay.sh`; ensures `/output/reconcile-report.json` is produced. Do not copy golden `avail.bin` from fixtures.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
Coordinate three bodies across Rust apply and Go walk/seal plus rebuild/replay — not a single-file sed.

Likely editable frontier:
- `environment/ledger/src/apply.rs`
- `environment/topo/internal/walk/walk_r4.go`
- `environment/topo/internal/seal/seal_n2.go`
- (supporting types in pinstate, bitmap, graph — read heavily, edit lightly)

Requirement-to-file map:
- MW totals after replay -> ledger apply + load.json
- Circuit unavailable slots -> walk_r4 bitmap + seal_n2
- Cascade children -> walk_r4 + grid.json adjacency
- Report schema -> seal_n2 + topoprobe
- Second-pass idempotence -> fold_q7 barrier ordering
- Edge stability -> graph untouched (negative)

Oracle estimated complexity: 80–150 lines non-boilerplate across three fix sites + solve.sh orchestration

Red flags:
- recipe_discount on cache invalidation — mitigated by cascade depth, dual-language pin, MW decoy
- Dual-language Docker build complexity is harness, not hardness

Residual hardness:
Even with the file tree visible, the agent must infer that green MW and intact edges are insufficient, discover generation keying, reject `walk_fast`/`seal_qty`, and order invalidation before cursor commit.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
distribution, control, lab, Rust, event, ledger, Go, topology, inspector, operators, replay, feeder, shed, events, live, load-state, store, load, totals, journal, dumps, edges, circuit, availability, probes, circuits, available, consistent, deterministic, reconcile-report, fields, schema, flag, bin, output, report

**Renames during drafting:**
- `apply_shed_batch` → `fold_q7`: shed/apply noun overlap
- `cascade_availability` → `walk_r4`: availability telegraph
- `probe_report` → `seal_n2`: probes/report nouns
- `test_circuit_unavailable` → `test_k2_slot_bundle`
- `test_load_totals` → `test_m8_qty_align`
- `test_topology_edges` → `test_p3_link_stable`
- `test_feeder_cascade` → `test_q1_fan_pair`
- `test_report_schema` → `test_r6_out_shape`
- `test_replay_idempotent` → `test_t4_twice_ok`

**Test names audited:**
- test_k2_slot_bundle
- test_m8_qty_align
- test_p3_link_stable
- test_q1_fan_pair
- test_r6_out_shape
- test_t4_twice_ok

**Concentration math:**
- Total tests across `flipping_point_contract`: 6
- Per location:
  - L1 (`environment/ledger/src/apply.rs`): 2/6 = 0.333
  - L2 (`environment/topo/internal/walk/walk_r4.go`): 2/6 = 0.333
  - L3 (`environment/topo/internal/seal/seal_n2.go`): 2/6 = 0.333
- Cap: 0.5. Max ratio observed: 0.333. Status: PASS

### Per-test feasibility pre-check
- Test: test_k2_slot_bundle
  - Checks: shed circuits unavailable in probe output
  - Valid approaches: 2+ (any correct bitmap+seal path)
  - Chain-dependent: yes — on successful replay after fixes
  - Feasibility risk: LOW

- Test: test_m8_qty_align
  - Checks: MW totals match journal-derived expectations
  - Valid approaches: 2+
  - Chain-dependent: yes — on apply path
  - Feasibility risk: LOW

- Test: test_p3_link_stable
  - Checks: topology edge checksum unchanged
  - Valid approaches: 1 (must not rewrite graph)
  - Chain-dependent: no
  - Feasibility risk: LOW

- Test: test_q1_fan_pair
  - Checks: multi-depth children unavailable; sibling feeder ok
  - Valid approaches: 2+
  - Chain-dependent: yes — on cascade walk
  - Feasibility risk: MEDIUM (fixture depth must be clear in data)

- Test: test_r6_out_shape
  - Checks: reconcile-report.json schema/fields
  - Valid approaches: 2+
  - Chain-dependent: yes — on seal path
  - Feasibility risk: LOW

- Test: test_t4_twice_ok
  - Checks: second replay idempotent digests
  - Valid approaches: 1–2 (barrier must be correct)
  - Chain-dependent: yes — on first-pass success
  - Feasibility risk: MEDIUM (order-sensitive; document in triviality ledger, not instruction)
