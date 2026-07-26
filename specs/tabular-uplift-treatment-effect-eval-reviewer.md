### Decision
GO — Attempt 1. Same decision as authoring spec.

### Metadata
- Task name: tabular-uplift-treatment-effect-eval
- Title: Tabular Uplift Eval
- Category: machine-learning
- Languages: [rust, bash]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [uplift, auuc, qini, propensity, treatment-tip, inference-eval]
- Milestones: 0

### Discovery budget
- Discovery: sealed-max tip is retired; durable tip is tip_g7 epoch 4 propensity dr
  Planned location: data/feature_registry/{tip_journal,retired_tips}.jsonl + seat pick
  Why instruction must not reveal it: naming the tip id collapses tip resolution
- Discovery: AUUC/Qini must use ranked channels (+ tip shift), not observational
  Planned location: mix/ward_d.rs + score/helm_e.rs + outcomes/*.json fields
  Why instruction must not reveal it: naming channels turns stubs into checklist
- Discovery: rematerialize until serving selection AND tip_bind.accept matches registry
  Planned location: eng/build.rs + calib/
  Why instruction must not reveal it: exact receipt tokens become a recipe

### Anti-trivialization verdict
Checks 1–21 PASS for SoftHSM rematerialize × tip × propensity × ranked metrics.
Hard-only gate PASS. Discovery budget ≥3. Topology distribution ≥3.

### Topology enumeration (3 candidate fix topologies)
1. Tip-first: knit + xv + ward/helm — tip wrong leaves bands/propensity red.
2. Metric-first: ward + helm + gate — tip/propensity cells still fail.
3. Calib-first: trial_pref + tip_bind + all five stubs — stubs alone rematerialize.

### Rubric axes
Verifiable PASS; Well-specified PASS; Solvable PASS; Difficult PASS;
Interesting PASS; Outcome-verified PASS.

### Hardness axes
Discover PASS; Synthesize PASS; Diagnose PASS; Navigate coupling PASS;
Reason beyond training PASS (uplift tip×propensity seating, not textbook AUUC).

### Instruction completeness test
Cannot solve from instruction alone — tip resolution, propensity binding,
ranked vs observational polarity, and rematerialize gate live in code/runtime.

## Reviewer Appendix

### Implementation plan
Rust uplift-eval engine with SoftHSM rematerialize of five seating modules;
ML calib preference; frozen tabular outcomes/treat/feat; bands docs; probe bait.

### Oracle notes
Resolve sealed non-retired tip; write serving + tip_bind.accept; patch five
bodies to ranked path + durable propensity + deep gate; run entrypoint.

### Collapse audit
Stage: implementation-plan
Smallest plausible successful patch: calib bind + five seating bodies (~50–110 LOC).
Likely editable frontier: seat/flag/mix/score/gate + calib.
Oracle estimated complexity: 100+ LOC.
Red flags: none material (RC2 WARN on calib/seat dir keywords justified by SoftHSM class).
Residual hardness: tip×propensity×ranked metrics under rematerialize.
Collapse verdict: PASS (with documented WARN)

### Naming-pass record
**Instruction nouns extracted:** uplift, evaluation, scripts, report, schema_tag,
slices, eval_ok, outcomes, treatments, features, auuc, qini, treatment_tip,
propensity, durable, observational, estimator, tip, bands, seating, surfaces,
engine, rebuild, probe, verifier
**Renames during drafting:** None — first-pass opaque pick_t/bit_z/mix_w/score_u/gate_y
**Test names audited:** test_a3_garnet … test_m2_andesite (mineral names)
**Concentration math:** 13 tests; max location share ≤3/13 < 0.5 — PASS

### Per-test feasibility pre-check
All 13 tests independently achievable under full seating; multiple approaches
accepted for tip discovery; not chain-dependent on hand-written JSON.
