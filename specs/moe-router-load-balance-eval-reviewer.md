### Decision
GO — Attempt 1 (hardened after platform TRIVIAL 100%/100%). Machine-learning MoE inference/eval seating desk with five coupled loci (journal-resolved durable tip, epoch-windowed hold ledger, capacity-weighted load renormalization, natural-log scoring, deep eval gate) plus a build-script rematerialize authority (`eng/build.rs` + `eng/seeds/` + `calib/` trial preference and tip binding). Plausible-wrong module bodies replace textbook stubs; stale-mirror and overstated-roster fixture baits; capacity blend discoverable from an archived healthy seating sample; verifier rebuild + novel-slice + novel-journal injects.

### Metadata
- Task name: moe-router-load-balance-eval
- Title: MoE Router Eval Desk
- Category: machine-learning
- Languages: [rust, bash]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [mixture-of-experts, router, load-balance, perplexity, inference-eval, held-expert]
- Milestones: 0

### Discovery budget
- Discovery: The durable tip resolves from the sealed-max entry of the router tip journal; the mirror sheet is stale (0.8) and the live sheet (2.0) carries the newest epoch — both are traps for plausible resolution rules.
  Planned location: `/app/data/routers/tip_journal.jsonl` vs `durable.toml` / `live.toml`; resolution in `seat/knit_b.rs`
  Why instruction must not reveal it: Docs state the sealed-max outcome; pasting the resolution beside the fix path would collapse tip seating to transcription.

- Discovery: Holds and releases apply by epoch window against the resolved tip epoch ({e1,e3} at epoch 4); the flat roster overstates holds (lists e4, whose hold is at epoch 7). Tip epoch and hold window are coupled.
  Planned location: `/app/data/routers/hold_ledger.jsonl` + `hold.json` bait + `flag/xv_c.rs`
  Why instruction must not reveal it: An enumerated held/active table is an answer key; semantics are documented, membership must be computed.

- Discovery: Expert capacity multiplies the routed softmax before post-hold renormalization; recoverable only from the archived healthy seating sample.
  Planned location: `/app/data/experts/*.json` + `/app/data/eval/audit/seated_sample.json` + `mix/ward_d.rs`
  Why instruction must not reveal it: The blend formula must be reverse-derived from audit behavior, not transcribed.

- Discovery: Engine builds rematerialize the five seating surfaces from `eng/seeds/` until `calib/trial_pref.toml` is cleared and `calib/tip_bind.accept` matches the journal-resolved tip. One-pass module flips are undone by the verifier rebuild.
  Planned location: `eng/build.rs` + `calib/`
  Why instruction must not reveal it: Instruction/docs state the trial-mode refresh and the binding format as outcomes; the coupling to the journal resolution is the discovery.

- Discovery: `moeprobe` reports balanced on near-uniform shares regardless of holds; `eval_ok` must encode deep invariants, not the probe heuristic.
  Planned location: `/app/tools/moeprobe` + `gate/emit_f.rs`
  Why instruction must not reveal it: Spelling the probe formula lets agents hardcode eval_ok=true after any uniform or any deep check without discovering coupling.

### Anti-trivialization verdict
1 Disclosure-collapse: PASS — outcomes documented; tip/hold/renorm algebra not.
2 Hidden-instance: PASS — multi-slice matrix, not one broken file hunt.
3 Single-artifact: PASS — ≥3 coupled modules.
4 Generalization: PASS — novel-slice inject.
5 Prompt-honesty: PASS — symptoms/outcomes without naming fix modules.
6 Cheating-vs-difficulty: PASS — rebuild/idempotence are anti-cheat beside real MoE seating.
7 Mechanical-fix: PASS.
8 Localized-fix: PASS — three loci.
9 Oracle-locality: PASS — multi-file rewrite.
10 Small declarative-cluster: PASS — engine math, not config-only.
11 Grep-collapse: PASS — opaque symbols vs instruction nouns.
12 Pre-factored-helper: PASS — decoys rhyme; fix names opaque.
13 Recipe-discount: PASS — MoE hold×temp×renorm not textbook CRUD.
14 Security-aura: N/A (ML).
15 Orthogonal-checklist: PASS — coupled clusters.
16 Harness-discount: PASS.
17 One-pass solvability: PASS — probe bait + coupling.
18 Hard-only: PASS (target).
19 Discovery budget: PASS (≥3).
20 Instruction specificity: symptoms-only / outcomes.
21 Topology distribution: PASS (see below).

### Topology enumeration (3 candidate fix topologies)
1. Tip×hold×renorm in knit_b / xv_c / ward_d — no single module greens temp + held-zero + unit-sum.
2. Tip×score×gate in knit_b / helm_e / emit_f — bands and eval_ok still fail without hold/renorm.
3. Hold×mix×probe-gate in xv_c / ward_d / emit_f — durable temp/perplexity still fail without tip seating.

### Rubric axes
- Verifiable: Pass — deterministic JSON + rebuild.
- Well-specified: Pass — schema + docs bands.
- Solvable: Pass — expert hours, finite Rust loci.
- Difficult: Pass — coupled MoE seating beyond training stubs.
- Interesting: Pass — real MoE load-balance eval work.
- Outcome-verified: Pass — grade report metrics, not process.

### Hardness axes
- Discover: tip polarity, hold roster, renorm necessity, probe non-authority.
- Synthesize: routers + eval logits + engine modules.
- Diagnose: symptoms (bands/sum/held) without cause names.
- Navigate coupling: local tip or hold fixes break distant cells.
- Reason beyond training: hold-aware renorm × durable temp × deep eval_ok, not generic softmax tutorial.

### Instruction completeness test
No — instruction alone does not name durable-vs-live resolution, hold ids, renorm rule, or eval_ok predicate; agent must read materials and engine behavior.

## Reviewer Appendix

### Implementation plan
Ship a Rust MoE eval engine that (broken) resolves the tip by newest on-disk epoch (live bait), trusts the overstated roster summary instead of the epoch ledger, seats plain softmax without capacity, scores entropy in log2 with an e-base exponentiation, and gates eval_ok on a probe-like spread heuristic. `eng/build.rs` rematerializes all five surfaces from `eng/seeds/` on every build while trial mode is armed or the tip binding does not match the journal. Oracle clears `calib/trial_pref.toml`, writes `calib/tip_bind.accept` from the journal, and rewrites pick_t / bit_z / mix_w / score_u / gate_y bodies. Tests recompute expectations from frozen fixtures (mini-oracle helpers), rebuild the crate, inject a novel slice and a novel sealed journal entry (which also shifts the hold window), and require byte-identical re-runs.

### Proposed file inventory
Matches authoring Initial Draft Commitments (25+ env files).

### Oracle notes
solve.sh removes calib/trial_pref.toml, derives calib/tip_bind.accept from the journal (python one-shot), overwrites knit_b, xv_c, ward_d, helm_e, emit_f with correct journal-resolve / epoch-window / capacity-softmax-renorm / natural-log score / gate implementations, then runs run_moe_eval.sh.

### Collapse audit
Stage: post-TRIVIAL harden
Smallest plausible successful patch: clear trial preference + journal-matched tip binding + rewrite five coupled seating functions (~130+ LOC), or equivalently rewrite the five seed files after discovering the rematerialize authority.
Likely editable frontier: seat/flag/mix/score/gate modules (or eng/seeds/*.rs.in) + calib/
Requirement-to-file map: journal tip→knit_b; hold window→xv_c; capacity renorm→ward_d; metrics→helm_e; eval_ok→emit_f; durability→calib gate
Oracle estimated complexity: 130+ non-boilerplate LOC across 6 surfaces
Red flags: none if opaque naming held; measured strategy matrix — NOP 11/13 fail, module-only 8/13 fail, calib-only 8/13 fail, oracle 13/13 pass
Residual hardness: journal vs mirror vs live tip polarity; epoch-coupled hold window vs roster bait; capacity blend reverse-derivation from audit sample; rematerialize authority discovery; novel-journal generalization
Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
mixture, experts, inference, desk, schema, load, share, active, slices, perplexity, entropy, router, temp, eval, materials, routers, band, durable, tip, held, probe, balanced, reports, engine, softmax, renormal, hold, mask, temperature, logit

**Renames during drafting:**
- `mask_z` → `bit_z`: avoid instruction noun `mask`

**Test names audited:**
- test_g6_shale
- test_n4_quartz
- test_w7_beryl
- test_k2_topaz
- test_m9_jade
- test_r6_onyx
- test_p3_flint
- test_c8_coral
- test_v5_mica
- test_h1_slate
- test_u4_basalt
- test_y2_chert
- test_j3_pyrite

**Concentration math:**
- Total tests: 13
- A knit_b: 3/13 = 0.23
- B xv_c: 3/13 = 0.23
- C ward_d: 3/13 = 0.23
- D helm_e: 3/13 = 0.23
- E emit_f: 2/13 = 0.15
- F calib gate: 1/13 = 0.08 (also required transitively by every metric test via rebuild)
- Cap: 0.5. Max ratio observed: 0.23. Status: PASS

### Per-test feasibility pre-check
- test_g6_shale — checksum — 1 — no — LOW
- test_n4_quartz — schema keys — 2+ approaches — no — LOW
- test_w7_beryl — unit sum — 2+ — no — LOW
- test_k2_topaz — ledger-window holds + roster-bait active — 2+ — no — MEDIUM
- test_m9_jade — journal-resolved tip equality — 2+ — no — MEDIUM
- test_r6_onyx — band membership — 2+ — weak chain on tip — MEDIUM
- test_p3_flint — Shannon agree (fixture-derived) — 2+ — no — MEDIUM
- test_c8_coral — boolean + spread — 2+ — no — LOW
- test_v5_mica — exact capacity-weighted loads — 2+ — audit-sample derivation — MEDIUM
- test_h1_slate — rebuild parity under rematerialize gate — 1 (rebuild) — no — MEDIUM
- test_u4_basalt — bytes — 2+ — no — LOW
- test_y2_chert — novel slice generalization — 2+ — no — MEDIUM
- test_j3_pyrite — novel journal tip + hold-window shift — 2+ — no — MEDIUM
