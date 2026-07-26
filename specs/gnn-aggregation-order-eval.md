### Decision
GO — Attempt 1. SoftHSM-class GNN inference eval: durable agg tip × degree-norm preference × cold/resume parity × mix roster, gated by evaluation selection + tip bind rematerialize. Symptoms-only ML surface (no repair/debug framing). Five semantic seating loci plus dual calib across three roots; concentration ≤ 0.45.

### Metadata
- version: 2
- Task name: gnn-aggregation-order-eval
- Title: GNN Aggregation Eval
- Category: machine-learning
- Languages: ["rust", "bash"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: ["gnn", "aggregation", "message-passing", "tip-epoch", "checkpoint-resume", "inference-eval"]
- Milestones: 0

## Authoring Brief

### Public contract

- Entry point: `/app/scripts/run_gnn_eval.sh` rebuilds the engine under `/app/eng` and writes `/output/gnn-eval.json`.
- Report schema: `schema_tag` (string) = `gnn-eval-v2`; `scenarios` = array with exactly the ids `cold_a`, `resume_a`, `cold_b`, `resume_b`, `mix_c`, `mix_d` in that order; each entry carries `id` (string), `accuracy` (number), `macro_f1` (number), `agg` (string), `tip_epoch` (integer); `bands_ok` (boolean).
- Field layout and scenario set are documented in `/app/docs/report_schema.md`. Published metric bands live in `/app/docs/gnn_bands.md`. Desk notes live in `/app/ops/runbooks/eval_notes.md`. Evaluation selection and tip binding live under `/app/calib/`. Graphs under `/app/data/graphs/` and checkpoints under `/app/data/checkpoints/` are frozen.
- For each family, cold and resume `accuracy` and `macro_f1` must match within `1e-4`.
- Every scenario's `agg` must equal the durable aggregation tip (`mean` | `sum` | `max` | `pna` — not a live decoy). Every `tip_epoch` must equal the sealed journal tip generation the desk binds. Degree-normalized features must follow the durable preference for that tip.
- Every cell sits inside its published band and `bands_ok` is true only then.
- `/app/data/fixtures/surface_ok.json` may look healthy while `bands_ok` is false; reports that copy it fail.
- Hand-written reports fail: verification rebuilds from `/app/eng` and re-runs; values must match. Two consecutive entrypoint runs must be byte-identical. The verifier also injects a novel durable tip and expects `agg`, `tip_epoch`, and mix metrics to move with that tip.

Instruction is symptoms-only: band drift after restart, resume cells no longer matching cold twins, mix slices disagreeing with documentation, rows pinning the wrong aggregation generation. No module/config names beyond the public paths above; no per-cell expected numerics (GX9).

### Failure topology

Four seating defects plus a dual-crate build-authority gate interact. The ledger binder selects the newest tip of any state instead of the newest durable non-retired tip, so every cell reports the live tip's epoch and (because aggregation mode is keyed off the bound tip) also poisons `agg` toward a live max bait. Separately, the aggregation resolver can still read a PNA decoy sheet family even after epoch binding is corrected. Degree handling follows a live raw preference until the durable degree-normalized preference is restored, which silently shifts mix-slice accuracy when sum vs mean aggregators amplify unnormalized degrees. Resume checkpoints store block-packed classifier frames; unpacking that drops block scales breaks cold/resume parity. The composed-slice assembler concatenates every on-disk graph instead of the tip's mix roster, so mix cells miss bands even when upstream seating is fixed. While evaluation selection stays on trial or the tip-bind receipt does not match the registry-resolved tip, both build scripts rematerialize all seating surfaces from broken seeds on every cargo build — source-only patches do not survive the verifier rebuild. Greening `cold_a` alone fails tip/resume/mix cells.

### Environment shape

- `core/` — Rust crate: graph IO, checkpoint decode, degree handling, message-passing score, mix assembly; build script rematerializes lens/weave/braid seeds.
- `rank/` — Rust crate: tip binding and aggregation-mode resolution; build script rematerializes knot/facet seeds.
- `emit/` — Rust binary crate (`loam`): eval subcommand emitting deterministic JSON.
- Workspace under `/app/eng`; `calib/` holds evaluation selection + tip bind; `data/feature_registry/` holds tip journal + retired tips; `data/sched/` holds agg sheet families (committed + PNA decoy); frozen graphs/checkpoints; bait `surface_ok.json`; leftover `data/ledger/` decoy.
- `docs/` bands + schema; `ops/runbooks/eval_notes.md` scenario prose; `scripts/run_gnn_eval.sh`.

### Required artifacts

- Standard single-step layout: instruction, task.toml, output_contract.toml, Dockerfile with stub-free but cache-friendly COPY of calib+data before build, hashed requirements.txt, `.dockerignore`, tests, solve.sh, 20+ environment files, `build_helpers/gen_data.py` (not in image).

### Test plan

1. `test_j2_pyrite` — frozen graphs/checkpoints/registry/sched/bands hash-match.
2. `test_k4_agate` — schema, six ids/order, typed fields, finite metrics.
3. `test_p7_jasper` — cold/resume accuracy and macro_f1 parity within 1e-4.
4. `test_r3_garnet` — family-a cells inside bands / match EXPECTED.
5. `test_t6_beryl` — family-b cells inside bands / match EXPECTED.
6. `test_m5_onyx` — mix cells match EXPECTED and sit in bands.
7. `test_w1_topaz` — every `agg` equals durable tip aggregation (`mean`), not live max / retired pna.
8. `test_v8_lazuli` — every `tip_epoch` equals durable non-retired journal generation.
9. `test_d9_quartz` — two consecutive entrypoint runs byte-identical.
10. `test_e2_opal` — entrypoint republish equals shipped report (rematerialize killer).
11. `test_g6_flint` — `bands_ok` true and metrics ≠ surface_ok bait.
12. `test_n8_umber` — tip_epoch not retired/live generations.
13. `test_s4_coral` — novel durable tip inject moves agg + tip_epoch + mix metrics together.

### Drafting guardrails

No instruction noun on fix-path symbols/paths/test names; no intent comments; bands are ranges only; runbook is outcomes not recipes; seeds comment-free; decoys do real work; ML vocabulary (`calib/`, feature registry, evaluation selection) — never ops cutover / bind-as-commit SE aura beyond the existing SoftHSM `calib/` + runbook pattern already accepted on sibling ML desks.

### Triviality Ledger

- Hardcoding six cells fails republish + novel-tip inject.
- Patching seating sources without serving+bind fails verifier rebuild rematerialize.
- Flipping calib alone leaves broken seeds in place — bands stay red.
- Copying surface_ok fails flint and republish.
- Fixing tip but not degree-norm / mix leaves mix cells out of band; fixing resume alone greens parity but not tip/agg cells.
- Grep-for-nouns blocked by opaque symbol table.

### Per-gate Pitfall Inventory

- RC1: oracle body-edits only at contract sites.
- RC2: decoys braid/dial/pin/ledger/surface_ok/PNA sheet.
- RC3: EXPECTED + bands + novel inject + republish.
- RC4: rebuild equality + frozen sha256.
- RC5: no golden report in environment.
- RC6: symptoms-only instruction.
- RC7: ≥30 LOC oracle (five seating rewrites + calib).
- CR1–CR9 / GX9 / GX10 / PLW1510 / PLR0124 / hashed pip: as Required artifacts.

### Initial Draft Commitments

- instruction.md
- task.toml
- output_contract.toml
- construction_manifest.json
- environment/Dockerfile
- environment/.dockerignore
- environment/requirements.txt
- environment/Cargo.toml
- environment/Cargo.lock
- environment/core/Cargo.toml
- environment/core/build.rs
- environment/core/src/lib.rs
- environment/core/src/base.rs
- environment/core/src/lens.rs
- environment/core/src/weave.rs
- environment/core/src/braid.rs
- environment/core/src/gauge.rs
- environment/core/seeds/lens_seed.rs.in
- environment/core/seeds/weave_seed.rs.in
- environment/core/seeds/braid_seed.rs.in
- environment/rank/Cargo.toml
- environment/rank/build.rs
- environment/rank/src/lib.rs
- environment/rank/src/knot.rs
- environment/rank/src/facet.rs
- environment/rank/src/dial.rs
- environment/rank/src/lace.rs
- environment/rank/seeds/knot_seed.rs.in
- environment/rank/seeds/facet_seed.rs.in
- environment/emit/Cargo.toml
- environment/emit/src/main.rs
- environment/calib/trial_pref.toml
- environment/calib/tip_bind.accept
- environment/calib/trace_pref.toml
- environment/ops/pin.toml
- environment/ops/runbooks/eval_notes.md
- environment/scripts/run_gnn_eval.sh
- environment/docs/gnn_bands.md
- environment/docs/report_schema.md
- environment/data/feature_registry/tip_journal.jsonl
- environment/data/feature_registry/retired_tips.jsonl
- environment/data/sched/table_a7.toml
- environment/data/sched/table_w2.toml
- environment/data/graphs/graph_01.gbin
- environment/data/graphs/graph_02.gbin
- environment/data/graphs/graph_03.gbin
- environment/data/graphs/graph_04.gbin
- environment/data/graphs/graph_05.gbin
- environment/data/graphs/graph_06.gbin
- environment/data/graphs/graph_07.gbin
- environment/data/graphs/graph_08.gbin
- environment/data/checkpoints/cold_a.ckpt
- environment/data/checkpoints/resume_a.ckpt
- environment/data/checkpoints/cold_b.ckpt
- environment/data/checkpoints/resume_b.ckpt
- environment/data/fixtures/surface_ok.json
- environment/data/ledger/journal.jsonl
- build_helpers/gen_data.py
- tests/test.sh
- tests/test_outputs.py
- tests/data.sha256
- solution/solve.sh

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: rank/src/knot.rs
  symbol: knot_r
  kind: function
  signature: pub fn knot_r(marks: &[Mark], retired: &HashSet<String>) -> u32
  purpose: Selects the journal generation the emission binds to.
- path: rank/src/facet.rs
  symbol: facet_q
  kind: function
  signature: pub fn facet_q(idx: u32, root: &Path) -> String
  purpose: Resolves the aggregation mode string for a bound generation.
- path: core/src/lens.rs
  symbol: lens_unfold
  kind: function
  signature: pub fn lens_unfold(blob: &[u8]) -> Vec<Vec<f32>>
  purpose: Decodes classifier weight rows from a checkpoint blob.
- path: core/src/braid.rs
  symbol: braid_n
  kind: function
  signature: pub fn braid_n(rows: &[Vec<f32>], deg: &[f32], pref: &str) -> Vec<Vec<f32>>
  purpose: Applies feature seating under the bound preference token.
- path: core/src/weave.rs
  symbol: weave_m
  kind: function
  signature: pub fn weave_m(marks: &[Mark], lots: &[Lot], retired: &HashSet<String>) -> Vec<Lot>
  purpose: Assembles the two composed graph collections from the tip roster.
- path: calib/trial_pref.toml
  symbol: SELECTION
  kind: constant
  signature: [evaluation] selection = "trial" | "serving"
  purpose: Evaluation selection consumed by both build scripts.
- path: calib/tip_bind.accept
  symbol: TIP_BIND
  kind: constant
  signature: tip id receipt string
  purpose: Tip bind receipt compared to registry-resolved tip.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: calib/trial_pref.toml
    controls_tests: [test_e2_opal, test_d9_quartz, test_s4_coral]
  - id: B
    path: calib/tip_bind.accept
    controls_tests: [test_e2_opal, test_v8_lazuli, test_n8_umber]
  - id: C
    path: rank/src/knot.rs
    controls_tests: [test_v8_lazuli, test_n8_umber, test_s4_coral]
  - id: D
    path: rank/src/facet.rs
    controls_tests: [test_w1_topaz, test_r3_garnet, test_s4_coral]
  - id: E
    path: core/src/lens.rs
    controls_tests: [test_p7_jasper, test_t6_beryl, test_g6_flint]
  - id: F
    path: core/src/braid.rs
    controls_tests: [test_m5_onyx, test_r3_garnet, test_g6_flint]
  - id: G
    path: core/src/weave.rs
    controls_tests: [test_m5_onyx, test_s4_coral, test_g6_flint]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: core/src/gauge.rs
  kind: helper
  rhymes_with: braid_n
  non_fix_purpose: Scores accuracy and macro_f1 after message passing.
- path: rank/src/dial.rs
  kind: helper
  rhymes_with: knot_r
  non_fix_purpose: Trace-mode stride reader from calib/trace_pref.toml.
- path: ops/pin.toml
  kind: config-reader
  rhymes_with: SELECTION
  non_fix_purpose: Legacy pin ignored by eval path.
- path: data/sched/table_w2.toml
  kind: config-reader
  rhymes_with: facet_q
  non_fix_purpose: Live/PNA decoy sheet family.
- path: data/fixtures/surface_ok.json
  kind: helper
  rhymes_with: weave_m
  non_fix_purpose: Stale surface sweep report bait.
- path: data/ledger/journal.jsonl
  kind: helper
  rhymes_with: knot_r
  non_fix_purpose: Leftover sweep ledger, not feature-registry authority.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [aggregation, message, passing, tip, epoch, checkpoint, resume, accuracy, macro, degree, bands, scenario, evaluation, graph, durable, live, mean, sum, max, pna, norm, journal, retired, serving, trial, bind, cold, mix, report, schema, engine, rebuild]
```
