### Decision
GO — Attempt 3. Hard system-administration design with distributed VRRP authority reconciliation and dynamic re-entry cases.

### Metadata
- Task name: keepalived-vrrp-split-brain-seating
- Title: Keepalived VRRP Split-Brain Seating
- Category: system-administration
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["tool_specific"]
- Tags: ["keepalived", "vrrp", "split-brain", "priority-fold", "transition-journal", "generation-gate"]
- Milestones: 0

### Discovery budget
- Discovery: conf.d uses lexical scoped replace/delta folding and a late saved
  sheet can shadow current values.
  Planned location: `plane/fold_h.sh`, live drop-ins, `docs/weight-format.md`.
  Why instruction must not reveal it: exact parser/order disclosure would turn
  the work into transcription.
- Discovery: latest complete sealed generation wins; incomplete later batches
  and live mirrors are non-authoritative.
  Planned location: `state/choice_m.sh` and durable preference JSONL.
  Why instruction must not reveal it: naming the selected batch leaks the core
  authority decision.
- Discovery: retractions bind event ids within committed batches.
  Planned location: `history/trace_p.sh` and transition JSONL.
  Why instruction must not reveal it: an event table would become an answer key.
- Discovery: a generation-bound receipt suppresses pre-fold saved-sheet replay.
  Planned location: `guard/window_c.sh` and entrypoint ordering.
  Why instruction must not reveal it: naming the guard would expose the durable
  edit directly.

### Anti-trivialization verdict
All 21 checks PASS in `keepalived-vrrp-split-brain-seating-attempt-3-evidence.json`.
The key defenses are dynamic peer/generation/history injections, six distributed
fix loci, no schema-only scoring cell, and re-entry that defeats output or live
state hardcoding.

### Topology enumeration (3 candidate fix topologies)
1. Fold-first: `plane/fold_h.sh::fold_h`,
   `guard/window_c.sh::window_c`, `emit/report_y.sh::report_y`. Correct fold
   data is overwritten without the guard and invisible without publication.
2. Candidate-first: `state/choice_m.sh::choice_m`,
   `guard/hold_c.sh::hold_c`, `emit/report_y.sh::report_y`. Batch selection,
   eligibility, and winner emission must agree.
3. History-first: `history/trace_p.sh::trace_p`,
   `state/choice_m.sh::choice_m`, `emit/report_y.sh::report_y`. History can veto
   an otherwise valid winner, but it cannot produce a valid desk alone.

### Rubric axes
- Verifiable: PASS — deterministic live and JSON outcomes.
- Well-specified: PASS — complete public contract without patch recipe.
- Solvable: PASS — bounded Bash control plane for an HA administrator.
- Difficult: PASS — six coupled loci and dynamic scenario matrix.
- Interesting: PASS — realistic split-brain prevention.
- Outcome-verified: PASS — behavior and state, never source form.

### Hardness axes
- Discover: PASS — four authority facts must be recovered.
- Synthesize: PASS — fold, preference, eligibility, history, and replay interact.
- Diagnose: PASS — prompt gives outcomes, not causes.
- Navigate coupling: PASS — local fixes are undone or vetoed elsewhere.
- Reason beyond training: PASS — committed-batch/event-id semantics are
  task-specific and cross-VRID.

### Instruction completeness test
No. The instruction lets an expert judge a ledger but does not identify the
authoritative batch, exact fold grammar, retraction binding implementation, or
replay gate. The solver must engage with live behavior and distributed scripts.

## Reviewer Appendix

### Implementation plan
Build a single Ubuntu image containing only Bash task sources plus standard
operator tools. Seed live `/etc/keepalived` and durable
`/var/lib/keepalived/ops` state at image build. The entrypoint executes neutral
phases that prepare effective rows, select durable candidates, apply
eligibility, reduce active movements, and publish deterministic JSON. The
shipped phase bodies disagree across authority boundaries; the oracle
coordinates all six without changing frozen peer fixtures.

The verifier independently reconstructs expected outcomes. Baseline tests cover
several VRIDs and peers; mutation tests snapshot state, add a peer or sealed
batch, invoke the same operator path, assert generalized behavior, and restore
state. This prevents baseline winner tables and keeps tests order-independent.

### Proposed file inventory
The authoritative inventory is the `Initial Draft Commitments` section in the
authoring spec: 57 task paths, including 50 environment paths. Major groups are
Docker/verifier lock files; six fix-path scripts; four genuine surface helpers;
three docs; site policy and packaging pin; six frozen peers; five live
Keepalived seed files; preference/transition journals; holds; floors; and
generation/receipt/abort state.

### Oracle notes
The oracle writes a matching generation receipt and correct live local sheet,
then replaces six general Bash functions. It implements lexical scoped
replace/delta fold, complete sealed batch selection, floor and half-open hold
eligibility, event-id movement cancellation, generation-sensitive replay, and
stable sorted JSON publication. It runs the entrypoint twice. Estimated
semantic delta: 180–260 lines.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
Six coordinated Bash functions plus matching live/receipt state. A report-only,
config-only, winner-table, or latest-row implementation fails re-entry or
dynamic scenarios.

Likely editable frontier:
- `plane/fold_h.sh`
- `state/choice_m.sh`
- `guard/hold_c.sh`
- `history/trace_p.sh`
- `guard/window_c.sh`
- `emit/report_y.sh`
- live local drop-in and durable receipt

Requirement-to-file map:
- Effective priorities -> fold + replay + publisher
- Durable winner -> batch selection + eligibility + publisher
- Movement veto -> history + selection + publisher
- Stable re-entry -> replay + fold + publisher
- Independent VRIDs -> selection + history + publisher

Oracle estimated complexity: 180–260 substantive lines.

Red flags:
- Strong thematic proximity to Pacemaker/HAProxy seating tasks.
- Public structured schema could become a free test if isolated.

Residual hardness:
The event-id continuity, complete-batch selection, independent-VRID winner
matrix, and dynamic mutation tests materially differ from the existing
single-ledger seating pattern. Schema and fixture assertions are always coupled
to computed behavior.

Collapse verdict: PASS

### Naming-pass record
**Instruction nouns extracted:**
keepalived, vrrp, split, brain, seat, virtual, IP, failover, desk, output,
schema, tag, instances, array, name, vrid, state, priority, vip, generation,
transitions, epoch, boolean, MASTER, peer, weight, configuration, durable,
floor, hold, journal, event, retraction, health, fixtures, entrypoint, JSON

**Renames during drafting:**
- `priority/fold.sh` -> `plane/fold_h.sh`: removed an instruction noun.
- `election/select.sh` -> `state/choice_m.sh`: hid the election locus.
- `journal/reduce.sh` -> `history/trace_p.sh`: removed an instruction noun.

**Test names audited:**
`test_q3_topaz`, `test_n4_beryl`, `test_w7_quartz`, `test_v5_coral`,
`test_p9_jade`, `test_h8_amber`, `test_c1_flint`, `test_r6_slate`,
`test_u2_mica`, `test_m1_opal`, `test_k5_garnet`, `test_s8_zircon`,
`test_t4_pearl`, `test_b6_cobalt`, `test_d4_jet`, `test_x7_agate`.

**Concentration math:**
- Total tests: 16.
- L1: 4/16 = 0.25.
- L2: 3/16 = 0.1875.
- L3: 3/16 = 0.1875.
- L4: 3/16 = 0.1875.
- L5: 3/16 = 0.1875.
- L6: 4/16 = 0.25.
- Cap: 0.5. Maximum 0.25: PASS.

### Per-test feasibility pre-check
All 16 tests accept at least two approaches: modifying the existing phase
architecture or replacing the operator pipeline with another general
implementation that preserves the public paths and state. Mutation tests own
snapshot/restore setup. Exact values are justified by deterministic fixture
and journal authority. Feasibility risk is LOW for baseline and re-entry tests,
MEDIUM for the three mutation tests due to setup complexity; each mutation is
self-contained and does not require execution order.
