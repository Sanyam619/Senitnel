### Decision
GO — Attempt 1. Security cutover (no repair/debug framing); distributed across Go issuance publish, Java TrustManager/SPI sieve, and session-ticket gate; opaque symbols; false-green readycheck; hard multi-scenario outcome tests; distinct from split-trust-anchor.

### Metadata
- Task name: workload-svid-trust-mesh-cutover
- Title: Workload SVID Trust-Mesh Cutover
- Category: security
- Languages: ["Go", "Java"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: ["spiffe", "svid", "mtls", "trust-manager", "go", "java"]
- Milestones: 0

### Discovery budget
- Discovery: Live trust bundle epoch is owned by fold_a publish into live-bundle.json; CA PEM side copies leave issuance on the pre-cutover root.
  Planned location: environment/k9/fold_a.go and fold_legacy.go
  Why instruction must not reveal it: Naming the live-bundle owner collapses diagnose into a CA-file checklist.
- Discovery: Java sieve_b must rebuild TrustManager from the live bundle and enforce intermediate not-after; cached TrustManager accepts expired intermediates until SPI rebind.
  Planned location: environment/m2/.../sieve_b.java
  Why instruction must not reveal it: Stating rebuild + not-after turns the task into recipe transcription.
- Discovery: Resumed handshakes reuse ticket_epoch; emit_c must reject when ticket_epoch is below live epoch; readycheck only curls readiness.
  Planned location: environment/p7/emit_c.go and tools/readycheck
  Why instruction must not reveal it: Telling solvers tickets must be invalidated removes the discoverability tax.

### Anti-trivialization verdict
All 21 checks PASS — see attempt evidence JSON. Security-aura and recipe-discount explicitly addressed: residual reasoning is issuance × TrustManager cache × ticket reuse under dual roots, not checklist TLS hardening.

### Topology enumeration (3 candidate fix topologies)
- T1 Issuance-first: fold_a → sieve_b → emit_c. Publish-only insufficient.
- T2 TrustManager-first: sieve_b → fold_a → emit_c. Trust-only insufficient.
- T3 Resumption-first: emit_c → fold_a → sieve_b. Ticket-only insufficient.

### Rubric axes
- Verifiable: PASS — deterministic JSON outcomes.
- Well-specified: PASS — schema fields and notes binding.
- Solvable: PASS — expert hours via three modules + meshctl.
- Difficult: PASS — cross-language trust under session reuse.
- Interesting: PASS — real mesh cutover economics.
- Outcome-verified: PASS — grades probe ledger.

### Hardness axes
- Discover: PASS — live-bundle owner, TrustManager cache, ticket gate not in instruction.
- Synthesize: PASS — Go + Java + resumption couple.
- Diagnose: PASS — symptoms-only readiness/reuse/expired-intermediate.
- Navigate coupling: PASS — local CA or flush leaves other cases red.
- Reason beyond training: PASS — SPIFFE SVID × JVM TrustManager × tickets under dual roots.

### Instruction completeness test
Can the agent solve this by reading ONLY instruction.md without deeply engaging with the codebase? No — must recover live-bundle ownership, TrustManager rebuild rules, and ticket gating from Go/Java modules and ops notes.

## Reviewer Appendix

### Implementation plan
Environment ships a Go Workload-API-style issuer path (k9), a Java TrustManager/SPI decision path (m2), and a Go ledger/resumption gate (p7). Mid-cutover stubs leave readycheck green while meshctl probe scenarios disagree with mesh-notes. Agent completes cutover so probe outcomes match notes. Oracle patches fold_a, sieve_b, emit_c then runs meshctl.

### Proposed file inventory
Matches Initial Draft Commitments in authoring spec (30+ environment files excluding Dockerfile).

### Oracle notes
solve.sh rewrites fold_a to publish active root+epoch from runtime/material, sieve_b to clear cache and enforce not-after + SPI subject bind, emit_c to reject resumed tickets with ticket_epoch < live epoch and assemble cases array; then invokes meshctl probe.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
Three-module logic rewrite plus meshctl probe (≥30 LOC).

Likely editable frontier:
- k9/fold_a.go
- m2/.../sieve_b.java
- p7/emit_c.go

Requirement-to-file map:
- fresh accept / dual-root post → fold_a
- expired intermediate / SPI bind → sieve_b
- resume reject / ledger emit → emit_c

Oracle estimated complexity: 80–140 non-boilerplate lines

Red flags:
- none if readycheck stays shallow and decoys do real non-fix work

Residual hardness:
Cross-language refresh clocks and session reuse remain hard after the file tree is visible.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
mesh, cutover, Workload, API, SVID, issuance, Go, side, Java, services, peers, KeyStore, TrustManager, material, custom, SPI, Surface, readiness, RPCs, connection, chains, intermediate, JVM, stale, refresh, session, reuse, agreement, meshctl, probe, output, notes, ops, scenario, scenarios, data, report, stand-in, fixtures, schema_version, epoch, state, runtime, cases, array, id, decision, accept, reject, reason_code, handshake, fresh, resumed, trust_epoch, values

**Renames during drafting:**
- publish_bundle → fold_a
- rebuild_trust_manager → sieve_b
- invalidate_tickets → emit_c

**Test names audited:**
- test_k9_zircon
- test_m2_quartz
- test_n3_garnet
- test_p7_topaz
- test_r8_onyx
- test_t1_amber

**Concentration math:**
- Total tests across flipping_point_contract: 6
- Per location:
  - L1 (k9/fold_a.go): 2/6 = 0.333333
  - L2 (m2/.../sieve_b.java): 2/6 = 0.333333
  - L3 (p7/emit_c.go): 2/6 = 0.333333
- Cap: 0.5. Max ratio observed: 0.333333. Status: PASS

### Per-test feasibility pre-check
- Test: test_k9_zircon — Checks fresh_ok accept — Valid approaches: 2+ — Chain-dependent: needs probe — Feasibility risk: LOW
- Test: test_m2_quartz — Checks resume_stale reject — Valid approaches: 2+ — Chain-dependent: needs probe — Feasibility risk: LOW
- Test: test_n3_garnet — Checks expired_inter reject — Valid approaches: 2+ — Chain-dependent: needs probe — Feasibility risk: LOW
- Test: test_p7_topaz — Checks dual_post reject — Valid approaches: 2+ — Chain-dependent: needs probe — Feasibility risk: LOW
- Test: test_r8_onyx — Checks spi_bind accept subject — Valid approaches: 2+ — Chain-dependent: needs probe — Feasibility risk: LOW
- Test: test_t1_amber — Checks schema/epoch/all cases + fixtures — Valid approaches: 2+ — Chain-dependent: needs probe — Feasibility risk: LOW
