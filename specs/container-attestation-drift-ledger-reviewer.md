### Decision
GO — Attempt 1. Dual-language (Rust + Go) promotion-replay drift task with fix locus split across hop binding, subject resolution, and epoch frontier evaluation; security-relevant consistency work, not checklist hardening.

### Metadata
- Task name: container-attestation-drift-ledger
- Title: Attestation Drift Ledger
- Category: security
- Languages: ["Rust", "Go", "bash"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: ["containers", "attestation", "supply-chain", "rust", "go", "security"]
- Milestones: 0

### Discovery budget
- Discovery: Ledger hop writer must bind each promotion to the platform-manifest content digest selected by the lab arch filter, not the OCI index digest stored in the journal dest field after tag push.
  Planned location: environment/crates/alpha/src/hop.rs (op_a) and environment/config/arch-filter.toml
  Why instruction must not reveal it: Naming index-vs-platform binding collapses the Rust diagnosis to a one-line digest swap.

- Discovery: Auditor subject resolution must walk attestation subjects through the image index to the same platform child the ledger tracks; verifying the index digest alone yields false admit/deny.
  Planned location: environment/go/wire/subject.go (fold_b) and environment/data/attest/
  Why instruction must not reveal it: Stating the subject-walk rule turns the Go fix into a recited recipe.

- Discovery: Policy admit compares against the post-replay renumbered numeric epoch frontier; string equality with pre-replay stage labels admits stale ledger rows.
  Planned location: environment/go/eval/phase.go (phase_c) and environment/data/policy/roots.toml
  Why instruction must not reveal it: Revealing numeric-vs-string epoch compare removes the policy-side discovery.

### Anti-trivialization verdict
| Check | Verdict | Reasoning |
| --- | --- | --- |
| Disclosure-collapse | PASS | Honest symptoms-only prompt still omits platform-child binding, subject walk, and numeric epoch frontier. |
| Hidden-instance | PASS | Fixed multi-image lab with systematic coupling bugs, not hunt-one-corrupt-file. |
| Single-artifact repair | PASS | Must coordinate Rust hop recording, Go subject resolution, and policy epoch compare. |
| Generalization | PASS | Tests cover multiple images/stages with computed digests and admit booleans. |
| Prompt-honesty | PASS | Honest prompt does not name hop.rs, subject.go, or epoch compare as the fault. |
| Cheating-vs-difficulty | PASS | Difficulty is cross-view digest identity, not anti-cheat scaffolding. |
| Mechanical-fix filter | PASS | Not a deps/timeout/footer task. |
| Localized-fix | PASS | Three module roots on the fix path across Rust and Go packages. |
| Oracle-locality | PASS | Oracle patches substantive logic in three files, not wholesale one-file replace. |
| Small declarative-cluster | PASS | Not a single config/policy table fill-in. |
| Grep-collapse | PASS | Opaque fix-path symbols; instruction nouns banned from those symbols. |
| Pre-factored-helper | PASS | Helpers do not mirror prompt verbs. |
| Recipe-discount | PASS | Not cosign-verify or SLSA checklist; residual work is identity consistency under replay. |
| Security-aura discount | PASS | Security framing present; hardness is consistency, not checklist hardening. |
| Orthogonal-checklist | PASS | Requirements couple through one digest-identity invariant. |
| Harness-discount | PASS | Dual-language build adds realism, not hardness. |
| One-pass solvability | PASS | 25+ env files, decoys, and false-green surface status block one-pass solve. |
| Hard-only gate | PASS | Residual reasoning clearly hard under Edition 2. |
| Discovery budget test | PASS | Three discoveries with locations and non-disclosure rationale. |
| Instruction specificity test | PASS | Symptoms-only level. |
| Topology distribution test | PASS | Three topologies each with ≥3 coordinating locations. |

### Topology enumeration (3 candidate fix topologies)
- T1 Content-digest identity: `hop.rs::op_a`, `subject.go::fold_b`, `phase.go::phase_c`. No single location suffices because correct ledger digests alone still fail admit matrix if subjects or epochs disagree.
- T2 Index-vs-platform: `journal.rs`, `bundle.go`, `join.go`. Selecting the platform child in one place without joining all three views leaves mismatches populated.
- T3 Replay-renumber: `store.rs`, `phase.go::phase_c`, `provcheck/main.go`. Renumbering epochs without policy frontier and report emission still fails cross-view agreement tests.

### Rubric axes
- Verifiable: PASS — Deterministic JSON fields, digests, and admit booleans.
- Well-specified: PASS — Output path and schema fields stated; equivalent verifiers.
- Solvable: PASS — Expert OCI/promotion engineer can finish in hours.
- Difficult: PASS — Cross-language identity under replay exceeds undergrad scope.
- Interesting: PASS — Real supply-chain promotion-replay drift problem.
- Outcome-verified: PASS — Grades converged report, not process.

### Hardness axes
- Discover: PASS — Platform-vs-index binding, subject walk, and numeric epoch frontier must be recovered from code/fixtures.
- Synthesize: PASS — Rust hop binder, Go subject resolver, and policy evaluator must agree.
- Diagnose: PASS — Instruction states disagreeing admits and healthy surface status, not causes.
- Navigate coupling: PASS — Single-subsystem fixes leave distant mismatches.
- Reason beyond training: PASS — Index-vs-platform identity under replay renumbering is not a textbook verify recipe.

### Instruction completeness test
Can the agent solve this by reading ONLY instruction.md without deeply engaging with the codebase? No. The instruction does not state platform-child binding, subject walk, or numeric epoch frontier; those live in Rust/Go sources and fixtures.

## Reviewer Appendix

### Implementation plan
Build a dual-language lab: Rust `digctl` maintains a digest ledger across promotion hops; Go `provcheck`/`polgate`/`replayctl` verify attestations, evaluate policy, and replay the journal. Seed three images whose index digests differ from platform children, with attestations bound to index/source subjects and policy roots using pre-replay string stage labels. Defects in `op_a`, `fold_b`, and `phase_c` cause post-replay drift. The agent must repair those three sites so a fresh replay emits a consistent `/output/drift-report.json`. Decoy `scan.rs` and `probe.go` power the false-green surface path.

### Proposed file inventory
- environment/Dockerfile, .dockerignore — toolchains + pytest
- environment/Cargo.toml, crates/alpha/**, cmd/digctl/main.rs — Rust ledger stack
- environment/go.mod, go/wire/{subject,probe,bundle}.go, go/eval/{phase,join}.go — Go check/gate
- environment/go/cmd/{provcheck,polgate,replayctl}/main.go — CLIs
- environment/scripts/{status-surface,replay-stub}.sh — surface wrappers
- environment/config/{lab,arch-filter}.toml — paths and arch select
- environment/data/journal/*.jsonl, store/img-{a,b,c}/*, attest/*, policy/roots.toml, fixtures/anchors/* — fixtures
- instruction.md, task.toml, output_contract.toml, solution/solve.sh, tests/*

### Oracle notes
`solve.sh` patches `op_a` to select platform-child digest via arch filter, `fold_b` to walk attestation subject through index to that child, and `phase_c` to compare numeric post-replay epoch against frontier; rebuilds binaries; runs replayctl then report emission. No golden file copy.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
Three coordinated logic edits — Rust hop platform binding, Go subject walk, Go numeric frontier — plus rebuild/replay. One-file or config-only patches cannot clear the flipping-point subsets.

Likely editable frontier:
- environment/crates/alpha/src/hop.rs
- environment/go/wire/subject.go
- environment/go/eval/phase.go

Requirement-to-file map:
- digest alignment → hop.rs
- admit matrix / shape → subject.go (+ report join)
- mismatches / cross-agree → phase.go (+ join)

Oracle estimated complexity: 80–140 lines non-boilerplate across three files plus rebuild glue

Red flags:
- none if decoys stay non-fix and surface status remains genuinely shallow

Residual hardness:
After the file tree is visible, the agent still must discover index-vs-platform identity and epoch renumber semantics by reading fixtures and tracing CLI paths; opaque symbols and decoys prevent grep-to-fix.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
promotion, journal, container, image, attestations, digest, ledger, runtime, policy, gate, images, manifests, surface, status, views, stages, replay, admit, report, mismatches, reason, fixtures, anchors, drift, attestation, rows, stage, ref, files

**Renames during drafting:**
- [`gate_c` → `phase_c`: contained instruction noun gate]
- [`test_m8_admit_matrix` → `test_m8_slot_matrix`: contained admit]
- [`test_p2_digest_align` → `test_p2_hash_align`: contained digest]
- [`test_r6_mismatch_list` → `test_r6_delta_list`: contained mismatch/mismatches]
- [`test_t1_stage_frontier` → `test_t1_tier_frontier`: contained stage]
- [`test_w3_cross_view` → `test_w3_cross_agree`: near-match with views]

**Test names audited:**
- test_k4_shape_bundle
- test_m8_slot_matrix
- test_p2_hash_align
- test_r6_delta_list
- test_t1_tier_frontier
- test_w3_cross_agree

**Concentration math:**
- Total tests across `flipping_point_contract`: 6
- Per location:
  - L1 (`environment/crates/alpha/src/hop.rs`): 2/6 = 0.333333
  - L2 (`environment/go/wire/subject.go`): 2/6 = 0.333333
  - L3 (`environment/go/eval/phase.go`): 2/6 = 0.333333
- Cap: 0.5. Max ratio observed: 0.333333. Status: PASS

### Per-test feasibility pre-check
- Test: test_k4_shape_bundle
  - Checks: Report schema and required image refs present
  - Valid approaches: 2+
  - Chain-dependent: no
  - Feasibility risk: LOW

- Test: test_m8_slot_matrix
  - Checks: Per-image admit booleans match converged fixture expectation
  - Valid approaches: 2+
  - Chain-dependent: yes — on subject+frontier agreement
  - Feasibility risk: MEDIUM

- Test: test_p2_hash_align
  - Checks: Per-image digest equals platform-manifest content digest from store fixtures
  - Valid approaches: 2+
  - Chain-dependent: yes — on hop binding
  - Feasibility risk: MEDIUM

- Test: test_r6_delta_list
  - Checks: mismatches array empty after repair
  - Valid approaches: 2+
  - Chain-dependent: yes — on three-view agreement
  - Feasibility risk: MEDIUM

- Test: test_t1_tier_frontier
  - Checks: stage values and admit set respect post-replay frontier
  - Valid approaches: 2+
  - Chain-dependent: yes — on hop+epoch coupling
  - Feasibility risk: MEDIUM

- Test: test_w3_cross_agree
  - Checks: Re-run replay+report yields identical admit set; views agree
  - Valid approaches: 2+
  - Chain-dependent: yes — on full fix
  - Feasibility risk: MEDIUM
