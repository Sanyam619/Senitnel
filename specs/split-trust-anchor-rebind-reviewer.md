### Decision
GO — Attempt 1. Symptoms-only public contract; distributed fix across vault/pinset/capdec roots; opaque symbol table; eight verifier slices with no instruction-noun leakage in test names.

### Metadata
- Task name: split-trust-anchor-rebind
- Title: Split Trust Anchor Rebind
- Category: security
- Languages: [C]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: [mtls, trust-store, capability, c, admission, revocation]
- Milestones: 0

### Discovery budget
- Discovery: On-disk trust material must bind to the active runtime epoch from state, not the restore snapshot generation.
  Planned location: environment/src/vault/op_a.c and environment/data/state/runtime.json
  Why instruction must not reveal it: Naming the generation bind collapses diagnosis to swapping one store file.

- Discovery: Runtime pin material must score subject lineage bytes; mismatch forces reject even when the trust store path looks healthy.
  Planned location: environment/src/pinset/op_b.c coupled to environment/data/pins/active.set
  Why instruction must not reveal it: Stating pin-over-store precedence turns the task into policy-knob transcription.

- Discovery: Fresh revocation bytes beat cached capability decode on refresh windows.
  Planned location: environment/src/capdec/op_c.c coupled to environment/data/revocations/
  Why instruction must not reveal it: Revealing cache-vs-revocation precedence enables a one-branch patch without authority reasoning.

### Anti-trivialization verdict
All 21 checks PASS — see attempt-1 evidence JSON. Residual risk is surfcheck bait and decoy helpers; mitigated by outcome tests on conflict scenarios.

### Topology enumeration (3 candidate fix topologies)
1. **T1 Generation-first** — merge_row_a → merge_row_b → merge_row_c. No single merge suffices.
2. **T2 Freshness-first** — merge_row_c then generation/pin adapters. Cache-only leaves restore drift.
3. **T3 Pin-gate wrap** — merge_row_b wrapping store/decode adapters. Pin alone misses revocation freshness and generation bind.

### Rubric axes
- Verifiable: PASS — deterministic ledger checks.
- Well-specified: PASS — schema + decisions grounded.
- Solvable: PASS — expert hours, not weeks.
- Difficult: PASS — split-authority professional work.
- Interesting: PASS — real edge-gateway restore drift.
- Outcome-verified: PASS — grades decisions not process.

### Hardness axes
- Discover: PASS — precedence/freshness/generation not in instruction.
- Synthesize: PASS — three authority roots.
- Diagnose: PASS — symptoms-only wrong admit/reject.
- Navigate coupling: PASS — local fixes flip complementary subsets.
- Reason beyond training: PASS — not textbook TLS hardening.

### Instruction completeness test
No — instruction alone lacks precedence, generation bind, and freshness rules; codebase engagement required.

## Reviewer Appendix

### Implementation plan
Ship a C edge gateway with vault/pinset/capdec authorities deliberately disagreeing after restore. Baseline merge_row_* functions implement the wrong local policy (prefer restore gen, always-match pins, prefer cache). Oracle rewrites the three bodies. Tests assert hard conflict scenarios including reload hold. Health surfcheck remains TLS OK as verifier-bypass bait.

### Proposed file inventory
Matches Authoring Brief Initial Draft Commitments (45+ paths under environment/ including data fixtures).

### Oracle notes
solve.sh overwrites op_a.c / op_b.c / op_c.c with correct merge bodies, rebuilds, runs apply from restore consistently with runtime epoch, then run-admit.sh (and edge-reload + re-admit for stability).

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
Coordinate three merge functions (~80+ LOC substantive) so generation, lineage, and freshness agree under conflict.

Likely editable frontier:
- environment/src/vault/op_a.c
- environment/src/pinset/op_b.c
- environment/src/capdec/op_c.c

Requirement-to-file map:
- restore generation skew -> vault/op_a.c
- pin lineage skew -> pinset/op_b.c
- stale cache window -> capdec/op_c.c

Oracle estimated complexity: 80-120 lines non-boilerplate

Red flags:
- none if CR8 and RC6 held

Residual hardness:
Split-authority conflict under restore/replay with TLS-OK bait remains after file tree is visible.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
edge, gateway, restore, peers, handshake, service, capability, blob, surfcheck, TLS, admission, outcomes, matrix, scenarios, ledger, schema_version, cases, reload_epoch, integer, epoch, decision, accept, reject, reason_code, files, sources, scripts, path, peer, admit, field, ids

**Renames during drafting:**
- [`bind_trust_epoch` → `merge_row_a`: overlapped trust/epoch]
- [`score_pin_lineage` → `merge_row_b`: overlapped pin]
- [`pick_revocation_fresh` → `merge_row_c`: overlapped revocation]

**Test names audited:**
- test_emit_json_contract
- test_k9_slot_deny
- test_m2_slot_allow
- test_n4_stale_window
- test_p7_skew_hot
- test_q3_gen_skew
- test_r8_hold_same
- test_t1_rank_mix

**Concentration math:**
- Total tests across `flipping_point_contract`: 8
- Per location:
  - L1 (`environment/src/vault/op_a.c`): 3/8 = 0.375
  - L2 (`environment/src/pinset/op_b.c`): 3/8 = 0.375
  - L3 (`environment/src/capdec/op_c.c`): 2/8 = 0.25
- Cap: 0.5. Max ratio observed: 0.375. Status: PASS

### Per-test feasibility pre-check
- Test: test_emit_json_contract — Checks schema keys and reload_epoch — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_k9_slot_deny — Checks revoked case reject — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_m2_slot_allow — Checks aligned accept — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_n4_stale_window — Checks cache vs revocation — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: MEDIUM
- Test: test_p7_skew_hot — Checks pin mismatch reject — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_q3_gen_skew — Checks restore gen reject — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_r8_hold_same — Checks reload stability — Valid approaches: 2+ — Chain-dependent: no (sets up own reload) — Feasibility risk: MEDIUM
- Test: test_t1_rank_mix — Checks triple conflict reject — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: MEDIUM
