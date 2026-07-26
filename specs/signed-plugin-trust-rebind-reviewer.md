### Decision
GO — Attempt 1. Java signed-plugin multi-authority trust rebind (security, not debug/repair framing); distributed fix across tier_a/b/c; opaque resolve_a/b/c; nine hard scenario tests with jarcheck digest-only bait.

### Metadata
- Task name: signed-plugin-trust-rebind
- Title: Signed Plugin Trust Rebind
- Category: security
- Languages: ["Java"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: ["signed-jar", "keystore", "plugin", "java", "trust", "admission"]
- Milestones: 0

### Discovery budget
- Discovery: The host admission path consults a generation-bound keystore lineage selected from runtime epoch, while jarcheck only hashes JAR bytes and ignores lineage.
  Planned location: environment/src/tier_a/OpAlpha.java coupled to environment/bin/jarcheck and environment/data/state/runtime.json
  Why instruction must not reveal it: Naming host-vs-jarcheck authority split collapses diagnosis to ignoring the verifier without discovering lineage selection.

- Discovery: Policy grants must bind to code-signer identity under the active lineage; stale grant rows remaining after refresh must refuse even if the JAR signature verifies.
  Planned location: environment/src/tier_b/OpBeta.java coupled to environment/data/grants/
  Why instruction must not reveal it: Stating grant-vs-signer binding turns the task into policy-knob transcription.

- Discovery: Module-layer install must complete after revoke/refresh ordering; wiring from a pre-refresh snapshot leaves accept decisions that disagree with post-reload runtime epoch.
  Planned location: environment/src/tier_c/OpGamma.java coupled to environment/scripts/host-reload.sh
  Why instruction must not reveal it: Revealing refresh-before-wire order enables a one-branch patch without authority reasoning.

### Anti-trivialization verdict
All 21 checks PASS — see attempt-1 evidence JSON. Residual risk is jarcheck digest bait and decoy helpers; mitigated by hard outcome tests on conflict scenarios. Not framed as debug/repair; primary category is security.

### Topology enumeration (3 candidate fix topologies)
1. **T1 Lineage-first** — resolve_a → resolve_b → resolve_c. No single resolve suffices.
2. **T2 Grant-scope-first** — resolve_b then lineage/layer adapters. Scope alone misses wrong-root refuses.
3. **T3 Layer/reload fold** — resolve_c with host-reload and resolve_a. Wiring alone misses grant drift and lineage bind.

### Rubric axes
- Verifiable: PASS — deterministic ledger checks.
- Well-specified: PASS — schema + decisions grounded.
- Solvable: PASS — expert hours, not weeks.
- Difficult: PASS — split-authority professional work.
- Interesting: PASS — real Java host key-rotation trust drift.
- Outcome-verified: PASS — grades decisions not process.

### Hardness axes
- Discover: PASS — lineage/grant/layer rules not in instruction.
- Synthesize: PASS — three authority roots.
- Diagnose: PASS — symptoms-only wrong accept/reject.
- Navigate coupling: PASS — local fixes flip complementary subsets.
- Reason beyond training: PASS — not textbook JAR signing checklist.

### Instruction completeness test
No — instruction alone lacks lineage selection, grant-scope binding, and layer/reload ordering; codebase engagement required.

## Reviewer Appendix

### Implementation plan
Ship a Java signed-plugin host with tier_a/b/c authorities deliberately disagreeing after key-rotation. Baseline resolve_* methods implement the wrong local policy (prefer gen0 root, always-match grants, wire from pre.snap). Oracle rewrites the three bodies. Tests assert hard conflict scenarios including reload hold and jarcheck disagreement. jarcheck remains digest-only as verifier-bypass bait. No debug/repair framing in instruction or subcategories.

### Proposed file inventory
Matches Authoring Brief Initial Draft Commitments (40+ paths under environment/ including data fixtures).

### Oracle notes
solve.sh overwrites OpAlpha.java / OpBeta.java / OpGamma.java with correct resolve bodies, rebuilds, runs admission, then host-reload + re-admit for stability.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
Coordinate three resolve functions (~80+ LOC substantive) so lineage, grant scope, and layer wiring agree under conflict.

Likely editable frontier:
- environment/src/tier_a/OpAlpha.java
- environment/src/tier_b/OpBeta.java
- environment/src/tier_c/OpGamma.java

Requirement-to-file map:
- wrong lineage refuse/accept -> tier_a/OpAlpha.java
- stale grant / revoke order -> tier_b/OpBeta.java
- layer wire / jarcheck disagreement / ledger+reload -> tier_c/OpGamma.java

Oracle estimated complexity: 80-140 lines non-boilerplate

Red flags:
- none if CR8 and RC6 held; watch similarity to split-trust-anchor-rebind (C/mTLS) — this task is Java/signed-plugin specific

Residual hardness:
Split-authority conflict under key-rotation/reload with digest-only bait remains after file tree is visible.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
java, host, plugins, catalog, key-rotation, trust-store, refresh, load, behavior, authorization, intent, grants, enter, signed, refused, keystore, lineage, verifier, tool, configuration, reject, reverse, admission, path, scenario, scenarios, accept, decision, emit, output, plugin-ledger, schema_version, plugin-admit-1, cases, array, objects, id, reason_code, reload_epoch, epoch, field, state, runtime, scripts, host-reload, repeating, preserve, modify, jarcheck, fixtures, case, ids, local

**Renames during drafting:**
- [`select_keystore_lineage` → `resolve_a`: overlapped keystore/lineage]
- [`bind_grant_scope` → `resolve_b`: overlapped grants]
- [`wire_module_layer` → `resolve_c`: telegraph risk]
- [`test_m2_obsidian` → `test_m2_feldspar`: substring id]

**Test names audited:**
- test_k9_zircon
- test_m2_feldspar
- test_n4_garnet
- test_p7_topaz
- test_q3_onyx
- test_r8_amber
- test_v6_flint
- test_w2_quartz
- test_t1_shale

**Concentration math:**
- Total tests across `flipping_point_contract`: 9
- Per location:
  - L1 (`environment/src/tier_a/OpAlpha.java`): 3/9 = 0.333
  - L2 (`environment/src/tier_b/OpBeta.java`): 3/9 = 0.333
  - L3 (`environment/src/tier_c/OpGamma.java`): 4/9 = 0.444
- Cap: 0.5. Max ratio observed: 0.444. Status: PASS

### Per-test feasibility pre-check
- Test: test_v6_flint — Checks schema keys and reload_epoch — Valid approaches: 2+ — Chain-dependent: yes (needs admit run) — Feasibility risk: LOW
- Test: test_k9_zircon — Checks wrong-lineage reject — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_m2_feldspar — Checks aligned accept — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_n4_garnet — Checks stale grant reject — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: MEDIUM
- Test: test_p7_topaz — Checks revoke/refresh refuse — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: MEDIUM
- Test: test_q3_onyx — Checks layer wire reject — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_r8_amber — Checks jarcheck≠host conflict — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: MEDIUM
- Test: test_w2_quartz — Checks reload stability — Valid approaches: 2+ — Chain-dependent: yes (reload) — Feasibility risk: MEDIUM
- Test: test_t1_shale — Checks triple conflict reject — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: MEDIUM
