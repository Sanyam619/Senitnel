### Decision
GO — Attempt 1. Security-category SoftHSM-backed JCE preference lattice across C JNI pack/mode, Java revoke/window, and durable keystore root under a sealed expected fingerprint; opaque symbols; surfcheck false-green; no repair/debug framing; no SealExpect calculator.

### Metadata
- Task name: softhsm-jce-preference-lattice
- Title: SoftHSM JCE Preference Lattice
- Category: security
- Languages: [Java, C]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: [tool_specific]
- Tags: [softhsm, jce, trust-authority, admission, revocation, attestation]
- Milestones: 0

### Discovery budget
- Discovery: surfcheck greens on a leaf token digest while the sealed host gate requires SoftHSM pack rank + mode tag from the JNI bridge to match the baked expected lattice fingerprint.
  Planned location: environment/native/knit_xv.c, environment/scripts/surfcheck, sealed /opt/desk/lib/gate.jar
  Why instruction must not reveal it: Naming pack/mode as the surface-vs-host split collapses diagnose to a checklist.
- Discovery: Revoke marks inside the freshness window must emit stale_slot; marks outside the window emit revoked — polarity is not documented and cases carry no answer-shaped stale/revoked flags.
  Planned location: environment/nest/OpB.java and environment/data/revoke/
  Why instruction must not reveal it: Stating window polarity turns reason_code selection into transcription.
- Discovery: Durable keystore generation under data/roots/disk must bind sessions; live.bundle is a decoy that looks current but fails across desk-reload.
  Planned location: environment/forge/OpC.java and environment/data/roots/
  Why instruction must not reveal it: Naming durable-over-live removes the root_skew discovery tax.

### Anti-trivialization verdict
All 21 checks PASS — multi-authority SoftHSM/JCE lattice with sealed expected fingerprint, opaque symbols, false-green surfcheck, EXPECTED only in tests, no SealExpect, no repair/debug framing. See attempt-1 evidence JSON.

### Topology enumeration (3 candidate fix topologies)
1. **T1** — knit_xv × op_b × op_c: pack/mode, revoke window, durable root. No single locus covers wrong_pack + stale/revoked + root_skew/reload.
2. **T2** — PrefA × signhold re-entry × sealed gate classpath: prefs without decision logic fail reasons; forged JSON fails re-invoke; moved gate without lattice still rejects.
3. **T3** — token headers × revoke marks/window × disk vs live roots: each data domain alone leaves the other authorities wrong under sealed expect.

### Rubric axes
- Verifiable: PASS — deterministic ledger + re-invoked scripts + sealed gate.
- Well-specified: PASS — schema, reasons, reload hold, prohibited paths documented.
- Solvable: PASS — expert reconstructible from bridge + prefs + sealed rejects.
- Difficult: PASS — professional HSM/JCE cutover, not undergrad provider tutorial.
- Interesting: PASS — real signing-desk SoftHSM preference work.
- Outcome-verified: PASS — grades admit/reject and reload durability.

### Hardness axes
- Discover: PASS — pack/mode, window polarity, durable root recovered from code/runtime.
- Synthesize: PASS — C JNI × Java policy × root × sealed fingerprint.
- Diagnose: PASS — symptoms only (surface green vs sealed reject).
- Navigate coupling: PASS — local greens fail distant cases / reload / seal.
- Reason beyond training: PASS — not textbook JCE or PKCS#11 slot rebind.

### Instruction completeness test
Can the agent solve from instruction.md alone? No — must engage SoftHSM bridge, revoke materials, root bundles, and sealed-gate behavior.

## Reviewer Appendix

### Implementation plan
Ship a SoftHSM-style token store with a C JNI bridge and a Java desk that emits `/output/sign-ledger.json`. Three opaque decision bodies ship wrong: `knit_xv` always pack-greens, `op_b` ignores window polarity, `op_c` prefers live root. Preference sheets exist as opaque integers consumed by the sealed gate; expected lattice fingerprint is XOR-baked into `gate.jar` at image build and placed first on the classpath (not replaceable by `make install`). `surfcheck` uses `skim_xv` leaf digests. Cases are opaque JSON without stale/revoked flags. Tests re-run `run-desk.sh` / `desk-reload.sh` / `signhold` and embed EXPECTED. Instruction is symptoms-only security framing (admit/reject / sealed host), no make recipe lead-in.

### Proposed file inventory
Matches authoring Initial Draft Commitments (≥20 environment files excl. Docker). Gate source `gate/GateSeal.java` is compiled into sealed jar then removed from the runtime image (or left only as build-time COPY that Dockerfile deletes).

### Oracle notes
`solve.sh` overwrites `knit_xv.c`, `OpB.java`, and `OpC.java` with correct lattice logic: pack_ok requires SoftHSM rank+mode match; policy code 2=stale_slot in-window marked, 1=revoked out-of-window marked, 0=clear; root bind requires durable gen equality. Rebuild via make; run desk emit.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
Rewrite three decision bodies (~80+ LOC) and rebuild; cannot forge sealed fingerprint via self-consistent prefs calculator.

Likely editable frontier:
- native/knit_xv.c, nest/OpB.java, forge/OpC.java, flux/PrefA.java, data/revoke/*, data/roots/*

Requirement-to-file map:
- wrong_pack → knit_xv
- stale_slot/revoked → op_b
- root_skew/reload → op_c

Oracle estimated complexity: 90–140 non-boilerplate LOC

Red flags:
- none if SealExpect absent and gate sealed ahead of rebuildable classes

Residual hardness:
Multi-authority SoftHSM/JCE lattice under opaque sealed expect with false-green surfcheck and re-invoked sign paths.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
signing, desk, SoftHSM, JCE, provider-pack, cutover, surface, probes, tokens, sealed, host, gate, verify, generations, provider, order, mode, bits, keystore, generation, binding, revoke, windows, root, sessions, admits, ledger, cases, schema_version, jce-desk-1, rows, decision, accept, reject, reason_code, bind_epoch, epoch, runtime, decisions, desk-reload, run-desk, vocabulary, pack, refusals, wrong_pack, mismatches, durable, live, roots, root_skew, in-window, revoked, prior-generation, material, stale_slot, revocation, window, admit, ok_bound, authority, surfcheck, outputs, rebuild, path, stand-ins, sign, key, case

**Renames during drafting:**
- `select_provider` → `knit_xv`: avoided provider/pack nouns
- `check_revoke_window` → `op_b`: avoided revoke/window nouns
- `bind_keystore_root` → `op_c`: avoided keystore/root nouns

**Test names audited:**
- test_q3_mica
- test_w7_slate
- test_n2_basalt
- test_k4_flint
- test_p9_shale
- test_r6_chert

**Concentration math:**
- Total tests across flipping_point_contract: 6
- Per location:
  - L1 (`native/knit_xv.c`): 2/6 = 0.333
  - L2 (`nest/OpB.java`): 2/6 = 0.333
  - L3 (`forge/OpC.java`): 2/6 = 0.333
- Cap: 0.5. Max ratio observed: 0.333. Status: PASS

### Per-test feasibility pre-check
- Test: test_q3_mica — Checks wrong_pack reject — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_w7_slate — Checks second wrong_pack — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_n2_basalt — Checks root_skew — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_k4_flint — Checks stale_slot polarity — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_p9_shale — Checks revoked polarity — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_r6_chert — Checks schema, ok_bound set, reload hold, surfcheck bait, prohibited paths — Valid approaches: 2+ — Chain-dependent: no (re-runs desk itself) — Feasibility risk: LOW
