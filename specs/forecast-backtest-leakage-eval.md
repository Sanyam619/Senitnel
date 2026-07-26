### Decision

GO — Attempt 1. Walk-forward forecast backtest evaluation with a durable split-tip
lattice: tip binding, train-only scaling, and causal feature windows must agree
before every rolling window lands inside its published sMAPE/MASE bands.

### Metadata

- version: 2
- Task name: forecast-backtest-leakage-eval
- Title: Forecast Backtest Leakage Eval
- Category: machine-learning
- Languages: [rust, bash]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [forecasting, backtest, leakage, split-tip, smape, inference-eval]
- Milestones: 0

## Authoring Brief

### Public contract

`/app/scripts/run_forecast_eval.sh` rebuilds the evaluation workspace and
publishes `/output/forecast-eval.json` carrying:

- `schema_tag` (string)
- `windows` (array of `{id:string, smape:number, mase:number, horizon:integer, split_tip:integer, scaler:string}`)
- `eval_ok` (boolean)

Rolling window ids and metric bands live under `/app/docs/forecast_bands.md`.
Frozen series sit under `/app/data/series/`; split definitions under
`/app/data/splits/`. For every window, sMAPE/MASE must land inside published
bands under strictly causal features; `split_tip` must equal the durable
walk-forward tip epoch (not the live all-data tip); `scaler` must be the
train-only preference bound from that tip. `/app/tools/fcprobe` may report
pass while `eval_ok` is false (it allows lookahead). Report must come from
rebuild+run only; leakage across the split boundary breaks the bands. Two
consecutive runs are byte-identical. Verifier also injects a novel sealed tip.

### Failure topology

Published metrics disagree with the bands whenever tip resolution, scaler
preference, and causal feature seating diverge. The durable tip is sealed-max
among non-retired journal rows; a retired newest sealed tip and a live
all-data tip bait wrong epochs, horizons, and scaler labels. Globally fit
scaling greens a shallow probe window but moves distant windows out of band.
Lookahead feature windows (including horizon off-by-one past the split) inflate
error metrics off the published causal bands. Trial evaluation selection plus a
mismatched tip bind receipt rematerialize seating surfaces on every engine
rebuild, so source-only edits do not stick.

### Environment shape

- Rust evaluation crate with build-time seating gate driven by evaluation
  selection and tip bind receipt; five seating modules outside the crate root.
- Frozen data: per-window series, split tables, tip journal + retired ledger,
  leftover ledger bait, surface probe fixture.
- Docs: forecast bands + schema; desk notes for evaluation selection language.
- Entrypoint script and surface probe tool (`fcprobe`).

### Required artifacts

`instruction.md`, `task.toml`, `output_contract.toml`, `environment/` (Dockerfile,
`.dockerignore`, hashed requirements, eng workspace, seating modules, data,
docs, scripts, tools; 20+ files excl. Docker), `solution/solve.sh`,
`tests/{test.sh,test_outputs.py}`, `build_helpers/gen_data.py`.

### Test plan

1. Frozen series/splits/registry digests unchanged.
2. Schema tag, window id order, field types.
3. `split_tip` equals durable sealed-minus-retired epoch on every window.
4. `split_tip` is neither retired sealed-max nor live all-data epoch.
5. `scaler` equals tip train-only preference on every window (not global).
6. `horizon` equals bound tip horizon.
7. Per-window sMAPE/MASE match causal+train-only engine semantics.
8. Every window inside published bands and `eval_ok` true.
9. Report is not the surface_ok / fcprobe bait.
10. Leakage (global scaler or lookahead) path misses at least one band.
11. Verifier rebuild re-emits matching report.
12. Two consecutive runs byte-identical.
13. Novel sealed tip shifts epoch, horizon, scaler binding, and metrics.

### Drafting guardrails

Symptoms-only instruction; no tip ids, band numbers, or fix recipes. Opaque
fix-path symbols. No intent comments. No ops/cutover vocabulary. Bands and
schema live in docs; EXPECTED recomputed in tests.

### Triviality Ledger

- Flipping scaler alone leaves tip epoch/horizon wrong → tip and band tests fail.
- Editing seating without serving + matching tip bind is undone by build.rs.
- Hardcoding tip/metrics fails novel sealed-tip injection.
- Trusting fcprobe or surface_ok fails deep bands and anti-bait tests.
- Global scaler may look fine on one window but breaks multi-window bands.

### Per-gate Pitfall Inventory

- RC1: oracle adds tip resolution + causal/train-only seating logic, not flag deletes.
- RC2/CR7: no broken_/golden_ tokens; opaque symbols disjoint from instruction nouns.
- RC3–RC5: tests recompute EXPECTED; no golden report under environment/.
- RC6/GX9/GX10: symptoms-only; no answer triples; no polarity contradictions.
- RC7: oracle LOC well above 80 with tip bind + five seating rewrites.
- CR5: single build.rs rematerializes five distinct seating files (no twin modules).
- GX8: verifier avoids domain-primitive imports beyond pytest/stdlib.

### Initial Draft Commitments

- `instruction.md`, `task.toml`, `output_contract.toml`
- `build_helpers/gen_data.py`
- `environment/Dockerfile`, `environment/.dockerignore`, `environment/requirements.txt`
- `environment/eng/{Cargo.toml,Cargo.lock,build.rs,stub_main.rs}`
- `environment/eng/seeds/s1.rs.in` … `s5.rs.in`
- `environment/eng/src/{main.rs,base.rs,decoy_p.rs,decoy_q.rs,pipe_a.rs,pipe_b.rs}`
- `environment/{seat/knit_b.rs,flag/xv_c.rs,mix/ward_d.rs,score/helm_e.rs,gate/emit_f.rs}`
- `environment/calib/{trial_pref.toml,trace_pref.toml}`
- `environment/data/series/w_{alpha,beta,gamma,delta,epsilon}.json`
- `environment/data/splits/{windows.toml,walk_forward.toml}`
- `environment/data/feature_registry/{tip_journal.jsonl,retired_tips.jsonl}`
- `environment/data/fixtures/surface_ok.json`
- `environment/data/ledger/journal.jsonl`
- `environment/data/fixtures.sha256`
- `environment/docs/{forecast_bands.md,desk_notes.md,report_schema.md}`
- `environment/scripts/{run_forecast_eval.sh,verify_fixtures.sh}`
- `environment/tools/{fcprobe,probe_calc.py}`
- `solution/solve.sh`, `tests/{test.sh,test_outputs.py}`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: seat/knit_b.rs
  symbol: pick_t
  kind: function
  signature: fn pick_t(a: &str, b: &str, c: &str) -> TipPick
  purpose: returns one tip row selected from journal materials

- path: flag/xv_c.rs
  symbol: bit_z
  kind: function
  signature: fn bit_z(a: &str, b: i64, c: &str) -> String
  purpose: returns the scaler label string used for a window row

- path: mix/ward_d.rs
  symbol: mix_w
  kind: function
  signature: fn mix_w(base: f64, causal: f64, leak: f64, shift: f64, epoch: i64) -> f64
  purpose: returns the smape contribution for a window

- path: score/helm_e.rs
  symbol: score_u
  kind: function
  signature: fn score_u(base: f64, causal: f64, leak: f64, shift: f64, horizon: i64) -> f64
  purpose: returns the mase contribution for a window

- path: gate/emit_f.rs
  symbol: gate_y
  kind: function
  signature: fn gate_y(smapes: &[f64], mases: &[f64], scalers: &[String], rows_ok: bool) -> bool
  purpose: returns whether the published eval_ok flag should be true
```

#### flipping_point_contract

```
locations:
  - id: A
    path: seat/knit_b.rs
    controls_tests: [test_c1_biotite, test_d9_epidote, test_h2_horizon]
  - id: B
    path: flag/xv_c.rs
    controls_tests: [test_e2_scoria, test_i6_marl]
  - id: C
    path: mix/ward_d.rs
    controls_tests: [test_f5_dolomite, test_g8_feldspar]
  - id: D
    path: score/helm_e.rs
    controls_tests: [test_f5_dolomite, test_l7_dunite]
  - id: E
    path: gate/emit_f.rs
    controls_tests: [test_g8_feldspar, test_j0_schist]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: eng/src/decoy_p.rs
  kind: helper
  rhymes_with: pick_t
  non_fix_purpose: rolls a display histogram over smape values for desk logs

- path: eng/src/decoy_q.rs
  kind: helper
  rhymes_with: score_u
  non_fix_purpose: archives a rolling mean of mase values unused by grading

- path: eng/src/pipe_a.rs
  kind: helper
  rhymes_with: bit_z
  non_fix_purpose: wires tip pick into the emitter without owning resolution policy

- path: eng/src/pipe_b.rs
  kind: helper
  rhymes_with: mix_w
  non_fix_purpose: calls mix/score seating for each window row
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [forecast, backtest, leakage, eval, windows, smape, mase, horizon, split, tip, scaler, causal, bands, series, splits, probe, report, rebuild, walk, forward, train, durable, live, schema, output, scripts, tools, features, boundary, preference, selection, serving, trial, registry, journal, retired, metrics, error, inference]
```
