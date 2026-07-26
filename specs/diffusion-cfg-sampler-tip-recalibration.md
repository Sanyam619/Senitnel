### Decision
GO — Attempt 1. SoftHSM-class calib gate × dual build.rs rematerialize of all four seating surfaces; multi-step tip resolution (durable minus retired); CFG×sampler schedule pair; VAE resume unpack; tip-roster mixes; ML framing via calib/eval (no ops cutover vocabulary).

### Metadata
- version: 2
- Task name: diffusion-cfg-sampler-tip-recalibration
- Title: Diffusion CFG Recalibration
- Category: machine-learning
- Languages: ["rust"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: ["diffusion", "cfg-scale", "sampler", "checkpoint-resume", "fid", "clip-score"]
- Milestones: 0

## Authoring Brief

### Public contract

- Entry point: `/app/scripts/run_diff_eval.sh` rebuilds `/app/eng` and writes `/output/diff-eval.json`.
- Report: `schema_tag` = `diff-eval-v2`; `scenarios` with ids `cold_a`, `resume_a`, `cold_b`, `resume_b`, `mix_c`, `mix_d`; each carries `fid`, `clip_score`, `cfg_scale`, `sampler`, `tip_epoch`; `bands_ok` boolean.
- Cold/resume pairs: `fid` and `clip_score` agree within `1e-4`.
- `tip_epoch` equals the durable tip generation (not live, not retired).
- `cfg_scale` and `sampler` equal the durable schedule pair from `/app/docs/diff_bands.md`.
- Frozen inputs under `/app/data/`; bands doc frozen.
- Surface fixture may look healthy while `bands_ok` is false.
- Report only from rebuild+run; hand-written JSON fails; two runs byte-identical.
- Novel durable tip inject moves tip_epoch, cfg_scale, sampler, and mix metrics.

### Failure topology

Four seating polarities plus a dual-crate rematerialize gate interact. Tip binder selects newest-any generation instead of durable-minus-retired. Schedule resolver reads the newest-any sheet family (live short-sampler bait) instead of the bound tip's sheet. Resume VAE unpack skips block-scale coefficients when coef ≤ 1. Mix assembler folds all bank segments instead of the tip roster. While `calib/trial_pref.toml` stays on trial selection or `tip_bind.accept` mismatches the registry-resolved tip, both `core/build.rs` and `rank/build.rs` rematerialize all four seating sources from seeds on every cargo build.

### Environment shape

- `core/` — banks IO, VAE unpack, mix assembly, metric gauge.
- `rank/` — tip bind + CFG/sampler schedule resolve; build.rs rematerialize.
- `emit/` — report/trace binary.
- `calib/` — trial_pref + tip_bind.accept gate.
- `eval/` — pin decoy + runbooks.
- `data/` — banks, checkpoints, tip journal + retired, schedules, surface bait, leftover ledger.
- `docs/` — bands + report schema.
- `scripts/` — entrypoint.

### Required artifacts

Standard layout: instruction, task.toml, output_contract, Dockerfile with hashed pytest, .dockerignore, tests, solve.sh, 20+ environment files.

### Test plan

1. `test_j2_pyrite` — frozen input digests.
2. `test_k4_agate` — schema + ids + types.
3. `test_p7_jasper` — cold/resume parity.
4. `test_w1_topaz` — durable CFG + sampler pair.
5. `test_v8_lazuli` — tip_epoch = durable generation.
6. `test_q1_flint` — not retired (8) or live (9).
7. `test_r3_garnet` — cold engine EXPECTED.
8. `test_t6_beryl` — resume engine EXPECTED (VAE unpack).
9. `test_m5_onyx` — mix engine EXPECTED.
10. `test_g6_coral` — bands + bands_ok.
11. `test_h3_umber` — not surface bait / not euler_short.
12. `test_d9_quartz` — byte-identical republish.
13. `test_n8_zircon` — novel tip shifts binding + mix.

### Drafting guardrails

No ops/cutover vocabulary; no intent comments on seating sites; opaque fix symbols; dual dissimilar build.rs; all four surfaces rematerialized; symptoms instruction without fix checklist.

### Triviality Ledger

- Source-only polarity flips undone by rematerialize until calib serving + tip_bind = tip_g7.
- Calib-only flip leaves wrong bodies; all band/parity tests stay red.
- Greening cold_a alone fails resume/mix/tip/cfg cells.
- Copying surface_ok fails umber + quartz.
- Newest-durable tip_g9 is retired; newest-any is tip_live — both decoys.

### Per-gate Pitfall Inventory

- RC1–RC7 / CR1–CR9 / GX9–GX10: SoftHSM dual rematerialize; opaque symbols; EXPECTED in tests; symptoms instruction; mineral test names; CFG band stated once without polarity contradiction.
- Static: PLW1510 check=, no v==v, hashed requirements, .dockerignore, eval/ not ops/.

### Initial Draft Commitments

- instruction.md, task.toml, output_contract.toml
- environment/{Dockerfile,.dockerignore,requirements.txt,Cargo.toml,Cargo.lock}
- environment/{core,rank,emit}/… (crates + seeds + build.rs)
- environment/calib/{trial_pref.toml,tip_bind.accept,trace_pref.toml}
- environment/eval/{pin.toml,runbooks/eval_notes.md}
- environment/docs/{diff_bands.md,report_schema.md}
- environment/scripts/run_diff_eval.sh
- environment/data/… (banks, checkpoints, registry, sched, fixtures, ledger)
- build_helpers/gen_data.py
- tests/{test.sh,test_outputs.py,data.sha256}
- solution/solve.sh

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: rank/src/knot.rs
  symbol: knot_r
  kind: function
  signature: pub fn knot_r(marks: &[Mark], retired: &HashSet<String>) -> u32
  purpose: Selects the tip generation the emission binds to.
- path: rank/src/facet.rs
  symbol: facet_q
  kind: function
  signature: pub fn facet_q(idx: u32, root: &Path) -> SheetRow
  purpose: Resolves CFG/sampler schedule pair for a bound generation.
- path: core/src/lens.rs
  symbol: lens_unfold
  kind: function
  signature: pub fn lens_unfold(blob: &[u8]) -> Vec<Vec<f32>>
  purpose: Decodes checkpoint blobs including VAE block-scale frames.
- path: core/src/weave.rs
  symbol: weave_m
  kind: function
  signature: pub fn weave_m(marks: &[Mark], lots: &[Lot], retired: &HashSet<String>) -> Vec<Lot>
  purpose: Assembles mix collections from the bound tip roster.
- path: calib/trial_pref.toml
  symbol: EVAL_SELECTION
  kind: constant
  signature: [evaluation] selection = "trial" | "serving"
  purpose: Evaluation selection consumed by dual build.rs gates.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: rank/src/knot.rs
    controls_tests: [test_v8_lazuli, test_q1_flint, test_w1_topaz, test_n8_zircon]
  - id: B
    path: rank/src/facet.rs
    controls_tests: [test_w1_topaz, test_r3_garnet, test_g6_coral, test_n8_zircon]
  - id: C
    path: core/src/lens.rs
    controls_tests: [test_p7_jasper, test_t6_beryl]
  - id: D
    path: core/src/weave.rs
    controls_tests: [test_m5_onyx, test_g6_coral]
  - id: E
    path: calib/trial_pref.toml
    controls_tests: [test_d9_quartz, test_n8_zircon, test_g6_coral]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: core/src/braid.rs
  kind: helper
  rhymes_with: lens_unfold
  non_fix_purpose: query batching spans for the gauge
- path: rank/src/dial.rs
  kind: helper
  rhymes_with: facet_q
  non_fix_purpose: trace stride prefs from calib
- path: eval/pin.toml
  kind: config-reader
  rhymes_with: EVAL_SELECTION
  non_fix_purpose: non-graded pin decoy
- path: data/ledger/journal.jsonl
  kind: helper
  rhymes_with: knot_r
  non_fix_purpose: leftover sweep ledger bait
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [diffusion, evaluation, engine, banks, checkpoints, report, schema_tag, scenarios, bands_ok, cold, resume, mix, fid, clip_score, cfg_scale, sampler, tip_epoch, durable, tip, retired, live, schedule, bands, selection, bind, seating, surfaces, rebuild, entrypoint, verifier, surface, ledger, journal, registry, VAE, teacher, short]
```
