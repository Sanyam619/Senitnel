### Decision

GO — Attempt 1. Walk-forward forecast backtest evaluation with a durable split-tip
lattice: tip binding, train-only scaling, and causal feature windows must agree
before every rolling window lands inside its published sMAPE/MASE bands.

### Metadata

- Task name: forecast-backtest-leakage-eval
- Title: Forecast Backtest Leakage Eval
- Category: machine-learning
- Languages: [rust, bash]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [forecasting, backtest, leakage, split-tip, smape, inference-eval]
- Milestones: 0

### Discovery budget

- Discovery: Durable tip is sealed-max among non-retired journal rows; tip_g9 is
  retired bait and tip_live is the all-data live bait.
  Planned location: data/feature_registry/{tip_journal,retired_tips}.jsonl + seat/knit_b.rs
  Why instruction must not reveal it: naming tip ids or the retired filter collapses tip resolution.

- Discovery: Trial selection rematerializes five seating surfaces unless
  selection=serving and tip_bind.accept matches the resolved tip/scaler.
  Planned location: calib/trial_pref.toml + eng/build.rs
  Why instruction must not reveal it: naming the gate recipe turns the task into a checklist.

- Discovery: Causal smape/mase bases (not leak bases) plus tip shift produce band
  hits; global scaler and lookahead bases miss multi-window bands.
  Planned location: data/series/*.json fields + mix/ward_d.rs + score/helm_e.rs + flag/xv_c.rs
  Why instruction must not reveal it: publishing the formula + field names is an answer key.

### Anti-trivialization verdict

1 Disclosure-collapse PASS — honest outcomes still require tip×scaler×causal coupling.
2 Hidden-instance PASS — not one broken file hunt.
3 Single-artifact repair PASS — five seating sites + calib gate.
4 Generalization PASS — five windows + novel tip inject.
5 Prompt-honesty PASS — symptoms-only.
6 Cheating-vs-difficulty PASS — rematerialize is authority, not a cheat wall.
7 Mechanical-fix filter PASS.
8 Localized-fix PASS — distributed loci.
9 Oracle-locality PASS — oracle rewrites multiple modules + calib.
10 Small declarative-cluster PASS — not one TOML flip.
11 Grep-collapse PASS — opaque symbols.
12 Pre-factored-helper PASS — decoys rhyme without owning policy.
13 Recipe-discount PASS — not textbook sMAPE homework.
14 Security-aura discount N/A (ML).
15 Orthogonal-checklist PASS — coupled tip×scaler×causal.
16 Harness-discount PASS.
17 One-pass solvability PASS — rematerialize blocks one-pass source edits.
18 Hard-only gate PASS.
19 Discovery budget PASS — three discoveries above.
20 Instruction specificity PASS — symptoms-only.
21 Topology distribution PASS — three topologies below.

### Topology enumeration (3 candidate fix topologies)

1. Tip-first: knit_b + xv_c + ward_d (≥3); tip alone leaves scaler/metrics wrong.
2. Metric-first: ward_d + helm_e + emit_f (≥3); metrics alone leave tip/scaler wrong.
3. Authority-first: trial_pref + tip_bind + knit_b + xv_c (≥3); calib alone rematerializes wrong seeds.

### Rubric axes

1 Verifiable PASS — deterministic JSON + rebuild tests.
2 Well-specified PASS — bands doc + schema.
3 Solvable PASS — expert hours, small oracle.
4 Difficult PASS — coupled lattice + rematerialize.
5 Interesting PASS — real forecast leakage eval work.
6 Outcome-verified PASS — grades report, not process.

### Hardness axes

- Discover: tip resolution and rematerialize gate are not in instruction.
- Synthesize: tip, scaler, causal metrics, and eval_ok must agree.
- Diagnose: symptoms (bands, probe false-green) without named causes.
- Navigate coupling: local scaler fix fails distant windows / tip tests.
- Reason beyond training: durable-vs-live tip lattice under forecast leakage, not generic sMAPE.

### Instruction completeness test

No — instruction states outcomes and paths but not tip ids, formulas, or which
modules to edit; solver must engage the registry, calib gate, and seating code.

## Reviewer Appendix

### Implementation plan

Ship a Rust fc-eval emitter with five wrong seating modules rematerialized from
seeds while evaluation selection is trial. Oracle binds serving + durable tip,
rewrites seating to sealed-minus-retired tip pick, train_only scaler label,
causal smape/mase, and deep eval_ok. Verifier recomputes EXPECTED and injects a
novel sealed tip.

### Proposed file inventory

Matches authoring Initial Draft Commitments (20+ environment files).

### Oracle notes

Write serving + tip_bind.accept for tip_g7; rewrite five seating files; run
run_forecast_eval.sh.

### Collapse audit

Stage: implementation-plan

Smallest plausible successful patch:
Serving preference + tip bind + five seating rewrites (~100+ LOC).

Likely editable frontier:
seat/knit_b.rs, flag/xv_c.rs, mix/ward_d.rs, score/helm_e.rs, gate/emit_f.rs, calib/*

Requirement-to-file map:
- durable tip -> knit_b
- scaler label -> xv_c
- causal smape -> ward_d
- causal mase -> helm_e
- eval_ok -> emit_f
- rematerialize stop -> trial_pref + tip_bind

Oracle estimated complexity: 90+ non-boilerplate LOC

Red flags: none structural if intent comments stay stripped

Residual hardness: tip×scaler×causal coupling under rematerialize + novel tip

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
forecasting, backtest, evaluation, scripts, forecast_eval, output, forecast-eval,
metric, bands, docs, forecast_bands, desk, layout, notes, desk_notes, series, data,
split, definitions, splits, preference, tip, binding, calib, report, schema_tag,
windows, array, eval_ok, flag, field, layout, window, set, smape, mase, causal,
features, split_tip, durable, walk-forward, live, all-data, scaler, train-only,
trial, seating, surfaces, engine, build, tools, fcprobe, status, line, unhealthy,
verifier, eng, materials, sealed, tips, hand-written, reports, consecutive, runs,
byte-identical

**Renames during drafting:**
- None — first-pass naming used opaque pick_t/bit_z/mix_w/score_u/gate_y

**Test names audited:**
- test_a3_garnet, test_b7_zircon, test_c1_biotite, test_d9_epidote, test_e2_scoria,
  test_h2_horizon, test_f5_dolomite, test_g8_feldspar, test_i6_marl, test_h4_gneiss,
  test_j0_schist, test_k3_pumice, test_l7_dunite

**Concentration math:**
- Total tests across flipping_point_contract: 13 unique
- Per location (declared controls, allowing overlap):
  - A seat/knit_b.rs: 3/13 = 0.23
  - B flag/xv_c.rs: 2/13 = 0.15
  - C mix/ward_d.rs: 2/13 = 0.15
  - D score/helm_e.rs: 2/13 = 0.15
  - E gate/emit_f.rs: 2/13 = 0.15
- Cap: 0.5. Max ratio observed: 0.23. Status: PASS

### Per-test feasibility pre-check

- test_a3_garnet: digest pin; approaches 1; chain no
- test_b7_zircon: schema; approaches 2+; chain no
- test_c1_biotite: tip epoch; approaches 2+; chain no
- test_d9_epidote: not retired/live; approaches 2+; chain no
- test_e2_scoria: scaler train_only; approaches 2+; chain no
- test_h2_horizon: horizon match; approaches 2+; chain no
- test_f5_dolomite: metric semantics; approaches 1–2; chain no
- test_g8_feldspar: bands+eval_ok; approaches 2+; chain no
- test_i6_marl: leak miss band; approaches 2+; chain no
- test_h4_gneiss: anti-bait; approaches 2+; chain no
- test_j0_schist: rebuild identity; approaches 1; chain no
- test_k3_pumice: byte-identical; approaches 1; chain no
- test_l7_dunite: novel tip; approaches 1–2; chain no
