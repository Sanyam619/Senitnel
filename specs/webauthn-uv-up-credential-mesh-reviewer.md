### Decision
GO — Attempt 1. Security-category WebAuthn UV/UP credential mesh; Java+Rust; opaque symbols; jarcheck false-green; documented stale/revoked + hold/presence polarities.

### Metadata
- Task name: webauthn-uv-up-credential-mesh
- Title: WebAuthn UV/UP Credential Mesh
- Category: security
- Languages: [Java, Rust]
- Difficulty: hard
- Codebase size: small
- Subcategories: [tool_specific]
- Tags: [webauthn, trust-authority, admission, revocation, attestation, capability]
- Milestones: 0

### Discovery budget
- Discovery: Inclusive sealed preference window maps marked claim epochs to stale_cred vs revoked; surface window is bait.
  Planned location: rp/src/fold_w.rs + data/prefs/sealed.toml vs data/surface/window.toml
  Why instruction must not reveal it: naming lo/hi or the surface-vs-sealed read would collapse window authority to transcription.
- Discovery: Held status satisfies presence while revoked does not; unmarked revoked uses no_presence; marks are a separate window path.
  Planned location: nest/OpB.java + data/revoke/marks.rl + roster status field
  Why instruction must not reveal it: naming the status enum→code table would grep-collapse presence.
- Discovery: Pack preference mismatch outranks mark window reasons on the same case (h8).
  Planned location: rp/src/slot_v.rs combined with emit decide order in main.rs
  Why instruction must not reveal it: stating the call order would turn precedence into a checklist; instruction names the outcome only.
- Discovery: UV-required ceremonies reject UP-only assertions via cap_ok from Java op_a; jarcheck still greenglights.
  Planned location: nest/OpA.java vs nest/SkimA.java / bin/jarcheck
  Why instruction must not reveal it: naming op_a or the cap_ok field collapses capability mesh.

### Anti-trivialization verdict
Checks 1–21 PASS for hard security mesh with ≥3 discoveries, symptoms-only instruction, four coupled loci, no three-stub SoftHSM clone, no answer-key cases.

### Topology enumeration (3 candidate fix topologies)
1. Java-first capability/presence + Rust window/pack (chosen): OpA, OpB, fold_w, slot_v.
2. All-Rust RP with Java as pure fixture emitter: would concentrate in Rust — rejected for language split fidelity.
3. Sealed-gate fingerprint only with preference TOML edits: collapses to SoftHSM forgery class — rejected.

### Rubric axes
Verifiable PASS; Well-specified PASS; Solvable PASS; Difficult PASS; Interesting PASS; Outcome-verified PASS.

### Hardness axes
Discover PASS; Synthesize PASS; Diagnose PASS; Navigate coupling PASS; Reason beyond training PASS (ceremony capability × lifecycle, not textbook WebAuthn checklist).

### Instruction completeness test
No — instruction states outcomes but not which module binds UV/UP, presence, sealed window, or pack precedence; solvers must run the mesh and read Java/Rust authorities.

## Reviewer Appendix

### Implementation plan
Broken Java always-OK capability and always-present presence; broken Rust fold clears marks and slot always pack-OK. Oracle rewrites four bodies, rebuilds, runs mesh. Tests re-invoke run-mesh and assert EXPECTED embedded in test code.

### Proposed file inventory
Matches Authoring Brief Initial Draft Commitments (≥40 environment files).

### Oracle notes
solve.sh cats corrected OpA/OpB/fold_w/slot_v, make all && install, run-mesh.

### Collapse audit
Stage: implementation-plan
Smallest plausible successful patch: rewrite four decision bodies (~120 LOC).
Likely editable frontier: nest/OpA.java, nest/OpB.java, rp/src/fold_w.rs, rp/src/slot_v.rs
Oracle estimated complexity: ~120 LOC
Red flags: none structural if CR1–CR8 held
Residual hardness: preference-vs-surface window + pack-over-mark + hold/presence after UV fix
Collapse verdict: PASS

### Naming-pass record
**Instruction nouns extracted:** relying-party, lab, ceremonies, credential, cutover, Java, authenticator, emulator, Rust, RP, admit, path, Surface, jarcheck, UV-bait, host, generations, Preference, sheets, windows, surface, window, file, Held, credentials, presence, revoked, Pack, capability, preference, failures, revoke, marking, case, ceremony-ledger, schema_version, webauthn-mesh-1, rows, id, decision, accept, reject, reason_code, bind_epoch, epoch, runtime, mesh-reload, run-mesh, uv_gap, user, verification, assertion, pack_skew, stale_cred, marked, material, claim, freshness, no_presence, ok_bound, authority, Outputs, rebuild, stand-ins

**Renames during drafting:** None — first-pass naming used opaque op_a/op_b/fold_w/slot_v

**Test names audited:** test_q3_mica, test_w7_slate, test_j2_onyx, test_h8_jasper, test_n5_beryl, test_k4_flint, test_b4_coral, test_p9_shale, test_r6_chert

**Concentration math:**
- Total tests: 9
- A OpA: 2/9=0.22
- B OpB: 2/9=0.22
- C fold_w: 2/9=0.22
- D slot_v: 3/9=0.33
- Cap 0.5. Max 0.33. Status: PASS

### Per-test feasibility pre-check
All nine tests: domain reason codes; 2+ approaches (fix authorities vs equivalent correct emit); not chain-dependent beyond shared emit; feasibility LOW.
