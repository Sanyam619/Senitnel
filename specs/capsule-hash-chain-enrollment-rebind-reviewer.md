### Decision
GO — Attempt 1. Security-category capsule hash-chain enrollment rebind across C frame tip, Rust revoke/freshness gate, and Go reload root rebind; opaque symbols; surfcheck false-green bait; no debugging/segfault framing.

### Metadata
- Task name: capsule-hash-chain-enrollment-rebind
- Title: Capsule Hash-Chain Enrollment Rebind
- Category: security
- Languages: ["C", "Rust", "Go"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: ["tool_specific"]
- Tags: ["capsules", "enrollment", "revocation", "hash-chain", "rust", "go"]
- Milestones: 0

### Discovery budget
- Discovery: Host reload re-reads the on-disk policy root under data/roots/; the broken Go path keeps the pre-rotation in-memory root so accept flips after reload.
  Planned location: environment/enroll/internal/slot_w.go and environment/scripts/host-reload.sh
  Why instruction must not reveal it: Naming the disk-vs-memory root split collapses diagnose to a one-line Go patch.

- Discovery: Revoke epoch beats prior-generation local verify inside the freshness window (stale_chain); outside the window the reason is revoked. Signature OK alone must not admit.
  Planned location: environment/policy/src/gate_r.rs and environment/data/revoke/
  Why instruction must not reveal it: Stating the precedence table turns the Rust gate into recipe transcription.

- Discovery: Sibling gen_skew is decided by parent-hash tip continuity on the C capsule frame, not by leaf signature match that surfcheck and skim_frame validate.
  Planned location: environment/frame/fold_q.c and environment/scripts/surfcheck
  Why instruction must not reveal it: Telling solvers the tip-binding rule removes the discoverability tax.

### Anti-trivialization verdict
All 21 checks PASS for this attempt (see evidence JSON). Security-aura, grep-collapse, and pre-factored-helper explicitly cleared via opaque symbols and decoy skim helpers.

### Topology enumeration (3 candidate fix topologies)
- T1: fold_q → gate_r → slot_w. Tip-only still admits revoked/stale and drifts on reload.
- T2: gate_r → fold_q → slot_w. Correct revoke still fails gen_skew and post-reload root flip.
- T3: slot_w → fold_q → gate_r. Stable reload of a wrong admit set still fails domain reason codes.

### Rubric axes
- Verifiable: PASS — deterministic JSON ledger.
- Well-specified: PASS — schema tokens and reason codes named.
- Solvable: PASS — expert can patch three sites in hours.
- Difficult: PASS — split authorities + decoy surface.
- Interesting: PASS — firmware enrollment ops value.
- Outcome-verified: PASS — grades decisions not process.

### Hardness axes
- Discover: PASS — root split, revoke precedence, tip binding hidden.
- Synthesize: PASS — C×Rust×Go coupling.
- Diagnose: PASS — symptoms only.
- Navigate coupling: PASS — partial fixes reopen other scenarios.
- Reason beyond training: PASS — not TPM/Sigstore/HMAC recipe.

### Instruction completeness test
Can the agent solve by reading ONLY instruction.md? No — must recover tip binding, revoke window precedence, and disk root rebind from code/runtime.

## Reviewer Appendix

### Implementation plan
Broken baseline: fold_q ignores parent tip (sibling wrongly accepts); gate_r admits on signature despite revoke window; slot_w keeps memory root across reload. Oracle rewrites all three bodies, rebuilds, runs enroll. Tests embed expected decision map; prohibit rewriting scenarios/surfcheck.

### Proposed file inventory
Matches authoring Initial Draft Commitments (40+ environment files including capsules and scenarios).

### Oracle notes
solve.sh overwrites fold_q.c, gate_r.rs, and slot_w.go with correct decision logic (≥80 LOC), runs make / rebuild-tools.sh, then run-enroll.sh. Does not hardcode ledger rows.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
Three decision-body rewrites across C/Rust/Go plus rebuild; not a one-flag flip.

Likely editable frontier:
- environment/frame/fold_q.c
- environment/policy/src/gate_r.rs
- environment/enroll/internal/slot_w.go

Requirement-to-file map:
- gen_skew siblings -> fold_q
- stale_chain / revoked -> gate_r
- reload stability / schema emit -> slot_w + enrollctl

Oracle estimated complexity: 90-140 lines non-boilerplate

Red flags:
- none

Residual hardness:
Decoy skim_* and surfcheck still look like the verify recipe; coupling across languages remains.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
device, update, capsules, stack, key, rotation, partial, revoke, check, enrollment, host, reload, sibling, devices, capsule, family, surfcheck, scenarios, ledger, schema_version, cases, device_id, decision, accept, reject, reason_code, reload_epoch, epoch, runtime, decisions, refusals, material, generation, stale_chain, revocation, window, revoked, mismatch, gen_skew, signature, surface, authority, make

**Renames during drafting:**
bind_chain_tip → fold_q; apply_revoke_gate → gate_r; rebind_policy_root → slot_w

**Test names audited:**
test_m8_obsidian, test_p7_garnet, test_n4_topaz, test_k9_onyx, test_r1_amber, test_t6_zircon

**Concentration math:**
total_tests=6; A=2 (0.333), B=2 (0.333), C=2 (0.333); cap=0.5
