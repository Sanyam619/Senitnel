### Decision
GO — Attempt 1.

### Metadata
- Task name: dnssec-chain-trust-reconstruction
- Title: Signed Rollover Audit
- Category: security
- Languages: ["rust", "bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["security", "rust", "protocol", "validation"]
- Milestones: 0

### Discovery budget
- Discovery: Withdrawal cutoff overrides active intervals.
  Planned location: `environment/core/atlas.rs`.
  Why instruction must not reveal it: It would collapse to one predicate.
- Discovery: Parent anchor digest must match the issuer.
  Planned location: `environment/clock/sieve.rs`.
  Why instruction must not reveal it: It discloses chain construction.
- Discovery: Replay reporting is stale-only, not any stale-looking overlap.
  Planned location: `environment/report/emit.rs`.
  Why instruction must not reveal it: It is the core semantic boundary.

### Anti-trivialization verdict
PASS.

### Topology enumeration (3 candidate fix topologies)
Filtering-first, chain-first, and report-first topologies each require at least three locations.

### Rubric axes
All pass.

### Hardness axes
All pass.

### Instruction completeness test
No; the instruction omits row semantics and temporal chain rules.

## Reviewer Appendix

### Implementation plan
Distributed Rust analyzer repair across candidate filtering, chain assembly, and report emission.

### Proposed file inventory
See authoring spec.

### Oracle notes
Oracle rewrites three Rust modules and runs the binary.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
Update node usability, route construction, candidate ordering, and replay reporting.

Likely editable frontier:
- `environment/core/phase.rs`
- `environment/core/atlas.rs`
- `environment/clock/sieve.rs`
- `environment/report/emit.rs`

Requirement-to-file map:
- Mixed window -> core/clock
- Stale-only -> report/core
- Determinism -> scan/report

Oracle estimated complexity: 80+ lines.

Red flags:
- Security flavor can be overvalued.

Residual hardness:
The solver must infer semantics from data and code.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
analyzer, app, naming, catalog, credential, rollover, snapshots, lookups, proof, material, wall-clock, instant, Rust, project, output, validation, json, replayed, query, id, name, status, chain, reason, authorities, machine, time, inputs, files

**Renames during drafting:**
- `select_chain` -> `fold_c`: avoids chain.

**Test names audited:**
- test_alpha
- test_bravo
- test_charlie
- test_delta
- test_echo
- test_foxtrot

**Concentration math:**
- Total tests across `flipping_point_contract`: 6
- Per location:
  - A (`core/phase.rs`): 2/6 = 0.333333
  - B (`clock/sieve.rs`): 2/6 = 0.333333
  - C (`report/emit.rs`): 3/6 = 0.500
- Cap: 0.5. Max ratio observed: 0.500. Status: PASS

### Per-test feasibility pre-check
All six tests have 2+ valid approaches, low feasibility risk.
