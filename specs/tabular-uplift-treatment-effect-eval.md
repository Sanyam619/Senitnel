### Decision
GO — Attempt 1. SoftHSM-class rematerialize × durable treatment tip × propensity
estimator × ranked AUUC/Qini seating for tabular uplift eval under
`machine-learning`. Symptoms-only seating instruction; no repair/debug framing.

### Metadata
- version: 2
- Task name: tabular-uplift-treatment-effect-eval
- Title: Tabular Uplift Eval
- Category: machine-learning
- Languages: [rust, bash]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [uplift, auuc, qini, propensity, treatment-tip, inference-eval]
- Milestones: 0

## Authoring Brief

### Public contract
`/app/scripts/run_uplift_eval.sh` rebuilds `/app/eng` and writes
`/output/uplift-eval.json` with `schema_tag`, `slices[]` (`id`, `auuc`,
`qini`, `treatment_tip`, `propensity`), and `eval_ok`. Bands and tip/
propensity outcomes live in `/app/docs/uplift_bands.md`. Frozen inputs under
`/app/data/{outcomes,treat,feat}/`. Two consecutive runs byte-identical;
verifier rebuild+rerun; novel sealed tip inject moves metrics.
`/app/tools/upliftprobe` may green while `eval_ok` is false.

### Failure topology
Trial evaluation preference rematerializes five seating surfaces on every
`cargo build` until selection is serving and `tip_bind.accept` matches the
registry-resolved durable tip (sealed, non-retired). Stub tip pick lands on
retired sealed-max; propensity stub emits surface decoy; AUUC/Qini stubs
score observational mean-difference paths that miss bands; shallow gate
greens on raw lift. Observational live tip and ledger bait sit beside the
durable journal.

### Environment shape
Rust eval crate under `/app/eng` with external seating modules
(`/app/seat`, `/app/flag`, `/app/mix`, `/app/score`, `/app/gate`), calib
preference + tip bind under `/app/calib/`, feature registry journal +
retired tips, outcome/treat/feat fixtures, docs, upliftprobe bait,
surface_ok fixture.

### Required artifacts
instruction.md, task.toml, output_contract.toml, environment/** (≥20 files),
solution/solve.sh, tests/test.sh + test_outputs.py, hashed requirements,
.dockerignore.

### Test plan
- test_a3_garnet: fixtures.sha256 intact
- test_b7_zircon: schema + slice field types/order
- test_c1_biotite: treatment_tip == resolved durable epoch
- test_d9_epidote: tip ≠ retired sealed-max and ≠ live observational
- test_e2_scoria: propensity == durable `dr` (not surface)
- test_f5_dolomite: auuc/qini match ranked+shift recompute
- test_g8_feldspar: all bands + eval_ok true
- test_i6_marl: observational path misses band
- test_h4_gneiss: report ≠ surface_ok bait
- test_j0_schist: rebuild from /app/eng byte-matches report
- test_k3_pumice: two runs identical
- test_l7_dunite: novel tip moves treatment_tip + metrics
- test_m2_andesite: tip_bind.accept propensity matches registry

### Drafting guardrails
No answer-key tip recipe in instruction; no intent comments on stubs; opaque
symbols; EXPECTED recomputed in tests; ML framing (calib/, no ops/cutover);
no independent greppable polarity frontier without rematerialize.

### Triviality Ledger
- Grep-flip five stubs alone → rematerialize undoes until serving+receipt.
- Copy surface_ok → schema/band/tip tests fail.
- Bind tip_g9/tip_live → tip/propensity/band cells fail.
- Hardcode tip_g7 metrics → novel tip inject fails.
- Trust upliftprobe → eval_ok / band tests still fail.

### Per-gate Pitfall Inventory
- RC1/RC7: oracle rewrites five bodies + calib bind (≥30 LOC logic).
- RC2: mineral test names; opaque knit/xv/ward/helm/emit symbols.
- RC3: domain recomputes + bands + novel inject, not schema-only.
- RC4/RC5: no golden under environment/; fixtures pinned by sha256.
- RC6: symptoms-only instruction; bands as outcomes in docs.
- GX9/GX10: no per-slice numeric answer recital; no polarity contradiction.
- PLR0124/PLW1510: finite range checks; check=False on subprocess.run.
- Category: ML opener + uplift tags; calib/ not ops/; no repair framing.

### Initial Draft Commitments
- instruction.md, task.toml, output_contract.toml
- solution/solve.sh, tests/test.sh, tests/test_outputs.py
- environment/Dockerfile, .dockerignore, requirements.txt
- environment/eng/{Cargo.toml,Cargo.lock,build.rs,stub_main.rs,seeds/s1-s5.rs.in,src/*}
- environment/{seat,flag,mix,score,gate}/*.rs
- environment/calib/{trial_pref.toml,trace_pref.toml}
- environment/data/{outcomes,treat,feat}/*.json
- environment/data/feature_registry/{tip_journal.jsonl,retired_tips.jsonl}
- environment/data/{fixtures/surface_ok.json,ledger/journal.jsonl,fixtures.sha256}
- environment/docs/{uplift_bands.md,desk_notes.md,report_schema.md}
- environment/scripts/{run_uplift_eval.sh,verify_fixtures.sh}
- environment/tools/{upliftprobe,probe_calc.py}

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table
```
- path: seat/knit_b.rs
  symbol: pick_t
  kind: function
  signature: pub fn pick_t(a: &str, b: &str, c: &str) -> TipPick
  purpose: select tip row from journal materials
- path: flag/xv_c.rs
  symbol: bit_z
  kind: function
  signature: pub fn bit_z(a: &str, b: i64, c: &str) -> String
  purpose: emit propensity label string
- path: mix/ward_d.rs
  symbol: mix_w
  kind: function
  signature: pub fn mix_w(base: f64, causal: f64, leak: f64, shift: f64, epoch: i64) -> f64
  purpose: produce auuc numeric from fixture channels
- path: score/helm_e.rs
  symbol: score_u
  kind: function
  signature: pub fn score_u(base: f64, causal: f64, leak: f64, shift: f64, horizon: i64) -> f64
  purpose: produce qini numeric from fixture channels
- path: gate/emit_f.rs
  symbol: gate_y
  kind: function
  signature: pub fn gate_y(auucs: &[f64], qinis: &[f64], props: &[String], rows_ok: bool) -> bool
  purpose: combine row health into eval_ok
```

#### flipping_point_contract
```
locations:
  - id: A
    path: seat/knit_b.rs
    controls_tests: [test_c1_biotite, test_d9_epidote, test_l7_dunite]
  - id: B
    path: flag/xv_c.rs
    controls_tests: [test_e2_scoria, test_m2_andesite]
  - id: C
    path: mix/ward_d.rs
    controls_tests: [test_f5_dolomite, test_g8_feldspar, test_i6_marl]
  - id: D
    path: score/helm_e.rs
    controls_tests: [test_f5_dolomite, test_g8_feldspar]
  - id: E
    path: gate/emit_f.rs
    controls_tests: [test_g8_feldspar]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest
```
- path: eng/src/decoy_p.rs
  kind: helper
  rhymes_with: mix_w
  non_fix_purpose: weighted roll summary discarded by main
- path: eng/src/decoy_q.rs
  kind: helper
  rhymes_with: score_u
  non_fix_purpose: EWMA history summary discarded by main
- path: calib/trace_pref.toml
  kind: config-reader
  rhymes_with: trial_pref
  non_fix_purpose: unused surface prefer decoy
- path: data/ledger/journal.jsonl
  kind: config-reader
  rhymes_with: tip_journal
  non_fix_purpose: observational ledger bait
```

#### code_forbidden_tokens
```
code_forbidden_tokens: [uplift, auuc, qini, propensity, treatment, tip, slice,
eval, schema, durable, observational, estimator, band, report, outcome,
feature, assignment, seating, rematerialize, rebuild, ipw, dr, tmle, surface]
```
