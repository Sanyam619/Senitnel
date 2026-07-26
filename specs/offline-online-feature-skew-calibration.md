### Decision
GO — Attempt 1. Machine-learning serving calibration desk: offline/online feature skew × multi-slice AUC/Brier × durable tip seating, with surface feathealth false-green and prefer×build rematerialize. No repair/debug framing; primary activity is calibration/eval against published bands.

### Metadata
- version: 2
- Task name: offline-online-feature-skew-calibration
- Title: Offline-online feature skew calibration
- Category: machine-learning
- Languages: ["rust"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["feature-store", "offline-online", "skew", "auc", "brier", "serving-eval"]
- Milestones: 0

## Authoring Brief

### Public contract
- Entrypoint: `/app/scripts/run_feature_eval.sh` writes `/output/feature-eval.json`.
- Report schema: `schema_tag` (string), `features` (array of `{name, offline_mean, online_mean, skew, source}`), `slices` (array of `{id, auc, brier}`), `calibration_ok` (boolean).
- Frozen inputs: `/app/data/offline/`, `/app/data/online/`, ledger, docs bands.
- Per-feature `|skew|` ≤ published bound in `/app/docs/skew_bands.md`; slice auc/brier inside those bands; `source` is the durable store tip (not live shadow).
- `/app/tools/feathealth` may print aligned while `calibration_ok` is false.
- Report only from rebuilding/running the engine under `/app/eng`. Two consecutive runs → byte-identical report. Verifier republishes and requires byte identity.

### Failure topology
Surface health can look aligned while deep serving eval is outside skew and slice bands. Online seating has a durable tip and a live shadow; binding the shadow can shrink some feature gaps while breaking a high-cardinality feature and a holdout Brier cell. Skew polarity (difference vs ratio bait), tip seating, source labeling, and prefer-gated rematerialize interact so local mean edits or hand-written JSON fail distant cells or rebuild compare.

### Environment shape
- `/app/eng` Rust workspace (core/rank/emit) scoring offline/online stores into the report.
- `/app/data/offline` feature store; `/app/data/online` tip snapshots; `/app/data/ledger` tip journal; `/app/data/fixtures` surface bait.
- `/app/docs/skew_bands.md` published bands; `/app/ops` prefer + decoy pin + runbook.
- `/app/scripts/run_feature_eval.sh` rebuild+emit; `/app/tools/feathealth` surface probe.

### Required artifacts
Standard layout: instruction.md, task.toml, output_contract.toml, environment/ (20+ files, Dockerfile, .dockerignore, hashed requirements), solution/solve.sh, tests/{test.sh,test_outputs.py}, build_helpers/gen_data.py for fixture regen. construction_manifest.json authoring-only (not in zip).

### Test plan
1. `test_frozen_inputs_integrity` — offline/online/ledger/docs digests unchanged (not chain-dependent).
2. `test_report_schema_and_order` — schema_tag, feature/slice order and types (multiple approaches to produce report; schema fixed).
3. `test_feature_skew_inside_published_bands` — per-feature |skew| and means (domain values).
4. `test_source_is_durable_tip` — every feature source equals durable tip id.
5. `test_slice_metrics_inside_published_bands` — auc/brier bands + calibration_ok true.
6. `test_holdout_brier_rejects_shadow_high_card` — holdout brier matches durable seating (fails shadow overlay).
7. `test_skew_is_online_minus_offline` — skew equals online_mean − offline_mean (not ratio).
8. `test_report_disagrees_with_surface_fixture` — at least one graded cell ≠ surface_ok bait.
9. `test_entrypoint_republish_is_byte_identical` — verifier re-run byte-identical; two consecutive runs identical.
10. `test_feathealth_aligned_does_not_imply_calibration_ok` — documenting surface≠authority (feathealth can be aligned).

### Drafting guardrails
Symptoms/outcomes instruction only — no fix-site names, no skew formula recipe beyond the graded polarity outcome (online−offline), no tip id checklist as a repair menu. Opaque eng symbols. No intent comments on fix path. EXPECTED metrics live in tests. Prefer rematerialize undoes naive rank patches.

### Triviality Ledger
- Hand-writing `/output/feature-eval.json` from bands → fails republish byte-identity (engine rebuild required).
- Fixing only skew polarity while tip stays on live shadow → f_zip band + holdout Brier fail.
- Fixing tip/means but leaving ratio skew → abs(skew) fails published bounds.
- Copying surface_ok / trusting feathealth → disagrees with engine semantics tests.
- Patching rank sources without prefer=anchor → build.rs rematerializes seeds on verifier rebuild.
- Independent polarity stubs alone → blocked by prefer×tip×skew×source×holdout coupling.

### Per-gate Pitfall Inventory
- RC1: oracle writes substantive tip/skew/source/prefer bodies, not delete-only.
- RC2: no broken_/golden_/expected_ names on solver surfaces.
- RC3: tests assert computed skew, durable source, slice metrics, not schema alone.
- RC4/RC5: EXPECTED embedded in tests; no golden report under environment/.
- RC6: symptoms-only instruction; bands in docs as published contract (fair outcomes).
- RC7: solve.sh ≥30 LOC non-boilerplate across multiple surfaces.
- GX9/GX10: no per-cell answer recital; no polarity contradictions in one sentence.
- PLW1510/PLR0124: explicit check= on subprocess; finite checks without v==v.
- Category: ML framing (calibration/eval/bands); languages=["rust"]; no cutover/repair aura.
- Packaging: hashed requirements; stub→fetch→src Dockerfile; .dockerignore; no COPY dotdirs.

### Initial Draft Commitments
- instruction.md
- task.toml
- output_contract.toml
- construction_manifest.json
- solution/solve.sh
- tests/test.sh
- tests/test_outputs.py
- tests/data.sha256
- build_helpers/gen_data.py
- environment/Dockerfile
- environment/.dockerignore
- environment/requirements.txt
- environment/Cargo.toml
- environment/Cargo.lock
- environment/core/Cargo.toml
- environment/core/src/lib.rs
- environment/core/src/base.rs
- environment/core/src/pull.rs
- environment/core/src/mesh.rs
- environment/core/src/braid.rs
- environment/rank/Cargo.toml
- environment/rank/build.rs
- environment/rank/seeds/op_seed.rs.in
- environment/rank/seeds/delta_seed.rs.in
- environment/rank/seeds/mark_seed.rs.in
- environment/rank/src/lib.rs
- environment/rank/src/op_v.rs
- environment/rank/src/delta_q.rs
- environment/rank/src/mark_w.rs
- environment/rank/src/dial.rs
- environment/emit/Cargo.toml
- environment/emit/src/main.rs
- environment/scripts/run_feature_eval.sh
- environment/tools/feathealth
- environment/ops/prefer.toml
- environment/ops/pin.toml
- environment/ops/runbooks/eval_notes.md
- environment/docs/skew_bands.md
- environment/data/ledger/journal.jsonl
- environment/data/offline/features.jsonl
- environment/data/online/tip_g7.json
- environment/data/online/tip_live.json
- environment/data/slices/retail.jsonl
- environment/data/slices/corporate.jsonl
- environment/data/slices/mobile.jsonl
- environment/data/slices/holdout.jsonl
- environment/data/fixtures/surface_ok.json

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: environment/ops/prefer.toml
  symbol: bind.mode
  kind: constant
  signature: mode = "skim" | "anchor"
  purpose: Binding preference; while skim, rank build rematerializes working seeds and runtime mesh overlays high-card from live shadow.
- path: environment/rank/build.rs
  symbol: main
  kind: function
  signature: fn main()
  purpose: Restores op_v/delta_q/mark_w from seeds unless prefer mode is anchor.
- path: environment/rank/src/op_v.rs
  symbol: op_v
  kind: function
  signature: pub fn op_v(rows: &[Row]) -> String
  purpose: Selects online tip id from journal rows.
- path: environment/rank/src/delta_q.rs
  symbol: delta_q
  kind: function
  signature: pub fn delta_q(a: f64, b: f64) -> f64
  purpose: Computes per-feature skew from offline and online means.
- path: environment/rank/src/mark_w.rs
  symbol: mark_w
  kind: function
  signature: pub fn mark_w(tip: &str) -> String
  purpose: Emits the source string written into each feature row.
- path: environment/core/src/mesh.rs
  symbol: mesh_k
  kind: function
  signature: pub fn mesh_k(on: &FeatMap, shadow: &FeatMap, mode: &str) -> FeatMap
  purpose: Runtime feature seating; when mode is not anchor, overlays high-card column from shadow.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: environment/ops/prefer.toml
    controls_tests: [test_entrypoint_republish_is_byte_identical, test_holdout_brier_rejects_shadow_high_card, test_source_is_durable_tip]
  - id: B
    path: environment/rank/src/op_v.rs
    controls_tests: [test_source_is_durable_tip, test_feature_skew_inside_published_bands, test_holdout_brier_rejects_shadow_high_card]
  - id: C
    path: environment/rank/src/delta_q.rs
    controls_tests: [test_skew_is_online_minus_offline, test_feature_skew_inside_published_bands]
  - id: D
    path: environment/rank/src/mark_w.rs
    controls_tests: [test_source_is_durable_tip]
  - id: E
    path: environment/core/src/mesh.rs
    controls_tests: [test_holdout_brier_rejects_shadow_high_card, test_slice_metrics_inside_published_bands]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: environment/core/src/braid.rs
  kind: helper
  rhymes_with: mesh_k
  non_fix_purpose: Trace batching helper used only by the unused trace path.
- path: environment/rank/src/dial.rs
  kind: helper
  rhymes_with: delta_q
  non_fix_purpose: Trace stride reader for pin.toml; not used by graded emit.
- path: environment/ops/pin.toml
  kind: config
  rhymes_with: prefer.toml
  non_fix_purpose: Trace stride config that looks like a binding preference.
- path: environment/data/fixtures/surface_ok.json
  kind: fixture
  rhymes_with: feature-eval.json
  non_fix_purpose: Stale surface sweep feathealth reads; desk never grades from it.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [feature, skew, offline, online, durable, shadow, store, tip, auc, brier, calibration, source, slice, mean, band, eval, serving, health, report, schema, schema_tag, features, slices, calibration_ok, offline_mean, online_mean, feathealth, prefer, rematerialize]
```
