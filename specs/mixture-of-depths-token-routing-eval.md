### Decision
GO — Attempt 1. SoftHSM-class rematerialize × durable router tip capacity ×
avg-depth seating × cold/resume perplexity parity for mixture-of-depths
token routing eval under `machine-learning`. Symptoms-only seating
instruction; no repair/debug framing.

### Metadata
- version: 2
- Task name: mixture-of-depths-token-routing-eval
- Title: Mixture-of-Depths Eval
- Category: machine-learning
- Languages: [rust, bash]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [mixture-of-depths, token-routing, avg-depth, capacity-tip, tip-epoch, inference-eval]
- Milestones: 0

## Authoring Brief

### Public contract
`/app/scripts/run_mod_eval.sh` rebuilds `/app/eng` and writes
`/output/mod-eval.json` with `schema_tag`, `scenarios[]` (`id`,
`perplexity`, `avg_depth`, `capacity`, `tip_epoch`), and `bands_ok`.
Required ids: `cold_a`, `resume_a`, `cold_b`, `resume_b`, `mix_c`,
`mix_d`. Bands and tip/capacity outcomes live in `/app/docs/mod_bands.md`.
Frozen inputs under `/app/data/{ckpt,routers,eval}/`. Cold/resume
perplexity pairs agree within `1e-4`. Capacity equals the durable router
tip (not the live full-depth decoy). `tip_epoch` equals the sealed
journal tip. Two consecutive runs byte-identical; verifier rebuild+rerun;
novel sealed tip inject moves capacity, avg_depth, and tip_epoch.
`/app/data/fixtures/surface_ok.json` may look healthy while `bands_ok`
is false. `/app/tools/modprobe` may green while deep evaluation is not.

### Failure topology
Trial evaluation preference rematerializes five seating surfaces on every
`cargo build` until selection is serving and `tip_bind.accept` matches the
registry-resolved durable tip (sealed, non-retired). Stub tip pick lands on
retired sealed-max; capacity stub emits live full-depth; avg_depth stub
uses uniform full layers; resume scoring reloads the live tip; shallow gate
greens on finite numbers. Live router sheet and ledger schedule mirror sit
beside the durable journal. Depth schedule authority is
`data/routers/depth_schedule.json`; stale `data/ledger/schedule_mirror.json`
lands out of band.

### Environment shape
Rust eval crate under `/app/eng` with external seating modules
(`/app/seat`, `/app/flag`, `/app/mix`, `/app/score`, `/app/gate`), calib
preference + tip bind under `/app/calib/`, router tip journal + retired
tips, ckpt/eval fixtures, docs, modprobe bait, surface_ok fixture.

### Required artifacts
instruction.md, task.toml, output_contract.toml, environment/** (≥20 files),
solution/solve.sh, tests/test.sh + test_outputs.py, hashed requirements,
.dockerignore.

### Test plan
- test_a3_garnet: fixtures.sha256 intact
- test_b7_zircon: schema + required scenario ids + field types
- test_c1_biotite: tip_epoch == resolved durable epoch
- test_d9_epidote: capacity == durable tip capacity (≠ live full-depth, ≠ retired)
- test_e2_scoria: avg_depth in documented bands for every scenario
- test_f5_dolomite: cold/resume perplexity pairs agree within 1e-4
- test_g8_feldspar: perplexity bands + bands_ok true
- test_i6_marl: full-depth / live path misses avg_depth or capacity band
- test_h4_gneiss: report ≠ surface_ok bait
- test_j0_schist: rebuild from /app/eng byte-matches report
- test_k3_pumice: two runs identical
- test_l7_dunite: novel tip moves tip_epoch + capacity + avg_depth
- test_m2_andesite: tip_bind.accept matches registry resolve
- test_n8_basalt: stale schedule_mirror lands out of band vs authority

### Drafting guardrails
No answer-key tip recipe in instruction; no intent comments on stubs; opaque
symbols; EXPECTED recomputed in tests; ML framing (calib/, no ops/cutover);
no independent greppable polarity frontier without rematerialize; no hidden
arithmetic as the last graded hop.

### Triviality Ledger
- Grep-flip five stubs alone → rematerialize undoes until serving+receipt.
- Copy surface_ok → schema/band/tip tests fail.
- Bind tip_g9/tip_live → tip/capacity/depth cells fail.
- Hardcode tip_g7 metrics → novel tip inject fails.
- Trust modprobe / surface_ok → bands_ok / band tests still fail.
- Use schedule_mirror → n8_basalt fails.

### Per-gate Pitfall Inventory
- RC1/RC7: oracle rewrites five bodies + calib bind (≥30 LOC logic).
- RC2: mineral test names; opaque knit/xv/ward/helm/emit symbols.
- RC3: domain recomputes + bands + novel inject, not schema-only.
- RC4/RC5: no golden under environment/; fixtures pinned by sha256.
- RC6: symptoms-only instruction; bands as outcomes in docs.
- GX9/GX10: no per-scenario numeric answer recital; no polarity contradiction.
- PLR0124/PLW1510: finite range checks; check=False on subprocess.run.
- Category: ML opener + MoD tags; calib/ not ops/; no repair framing.

### Initial Draft Commitments
- instruction.md, task.toml, output_contract.toml
- solution/solve.sh, tests/test.sh, tests/test_outputs.py
- environment/Dockerfile, .dockerignore, requirements.txt
- environment/eng/{Cargo.toml,Cargo.lock,build.rs,stub_main.rs,seeds/s1-s5.rs.in,src/*}
- environment/{seat,flag,mix,score,gate}/*.rs
- environment/calib/{trial_pref.toml,trace_pref.toml}
- environment/data/{ckpt,routers,eval,fixtures,ledger}/*
- environment/docs/{mod_bands.md,desk_notes.md,report_schema.md}
- environment/scripts/{run_mod_eval.sh,verify_fixtures.sh}
- environment/tools/{modprobe,probe_calc.py}

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
  signature: pub fn bit_z(a: f64, b: f64, c: &str) -> f64
  purpose: emit seated capacity scalar
- path: mix/ward_d.rs
  symbol: mix_w
  kind: function
  signature: pub fn mix_w(scores: &[f64], cap: f64, shallow: f64, deep: f64) -> f64
  purpose: produce avg_depth from token scores and capacity
- path: score/helm_e.rs
  symbol: score_u
  kind: function
  signature: pub fn score_u(base_nll: f64, cap: f64, mode: &str, live_cap: f64) -> f64
  purpose: produce perplexity; resume must not reload live capacity
- path: gate/emit_f.rs
  symbol: gate_y
  kind: function
  signature: pub fn gate_y(depths: &[f64], ppls: &[f64], caps: &[f64], rows_ok: bool) -> bool
  purpose: combine row health into bands_ok
```

#### flipping_point_contract
```
locations:
  - id: A
    path: seat/knit_b.rs
    controls_tests: [test_c1_biotite, test_d9_epidote, test_l7_dunite]
  - id: B
    path: flag/xv_c.rs
    controls_tests: [test_d9_epidote, test_m2_andesite]
  - id: C
    path: mix/ward_d.rs
    controls_tests: [test_e2_scoria, test_g8_feldspar, test_i6_marl, test_n8_basalt]
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
- path: data/ledger/schedule_mirror.json
  kind: config-reader
  rhymes_with: depth_schedule
  non_fix_purpose: stale depth schedule bait
- path: data/routers/live.toml
  kind: config-reader
  rhymes_with: durable tip
  non_fix_purpose: full-depth capacity decoy
```

#### code_forbidden_tokens
```
code_forbidden_tokens: [mixture, depths, token, routing, eval, perplexity,
avg_depth, capacity, tip_epoch, band, schema, scenario, checkpoint, resume,
cold, router, journal, durable, live, surface, rebuild, engine, report,
sealed, retired, serving, selection, depth, schedule, fixture]
```
