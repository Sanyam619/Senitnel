### Decision
GO — Attempt 1. Machine-learning continual-learning replay-buffer tip
evaluation with five coupled loci (journal-resolved sealed replay tip,
durable-preference propagation, durable-vs-overflow buffer scoring,
peak-relative forgetting, deep eval gate) plus a build-script rematerialize
authority: engine builds refresh the seating surfaces from `eng/seeds/`
until the desk trial preference is cleared and `calib/tip_bind.accept`
binds the journal-resolved tip. Mirrors the SoftHSM-class coupling of
`moe-router-load-balance-eval`, rethemed to continual-learning replay-buffer
tip evaluation. Plausible-wrong bodies (no textbook stubs); stale-mirror
and live-overflow fixture baits; a bait "healthy" report under
`data/fixtures/`; verifier rebuild + novel sealed-tip inject; goal-first ML
framing (no repair/debug lead-in).

### Metadata
- version: 2
- Task name: continual-learning-replay-buffer-tip-eval
- Title: Continual-Learning Replay-Buffer Tip Evaluation
- Category: machine-learning
- Languages: [rust, bash]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: [continual-learning, replay-buffer, forgetting, tip-epoch, accuracy-bands, inference-eval]
- Milestones: 0

## Authoring Brief

### Public contract

Seat the continual-learning evaluation so `/app/scripts/run_cl_eval.sh`
rebuilds the engine under `/app/eng` and writes `/output/cl-eval.json` with:

- `schema_tag` (string) — must be `cl-eval-v1`
- `tasks` (array, curriculum order `t_alpha, t_beta, t_gamma, t_delta`) —
  objects with `id` (string), `accuracy` (number), `forgetting` (number),
  `replay_frac` (number), `tip_epoch` (integer)
- `eval_ok` (boolean)

Materials under `/app/data/tasks/` and `/app/data/replay/` are frozen.
Numeric bands live in `/app/docs/cl_bands.md`. Every task's `replay_frac`
and `tip_epoch` must match the sealed, non-retired, journal-resolved tip;
every task's `accuracy` must land in its documented band; `forgetting`
must never be negative. `/app/tools/clprobe` may still print a
plausible-looking status line when deep evaluation is unhealthy. The
verifier rebuilds from `/app/eng` and re-invokes the eval; hand-written
reports fail. Two consecutive runs must be byte-identical.

### Failure topology

Cluster A (`seat/knit_b.rs::pick_t`): tip resolution ignores the retired
list and picks the newest sealed epoch on disk (`tip_g9`, epoch 7,
retired) instead of the journal-resolved sealed-and-not-retired tip
(`tip_g7`, epoch 4). Cluster B (`flag/xv_c.rs::bit_z`): the durable
preference fast path always returns `0.0` instead of propagating the
resolved replay fraction. Cluster C (`mix/ward_d.rs::mix_w`): scoring
always applies the live-overflow affinity (`overflow_hit`) instead of the
durable buffer affinity (`durable_hit`) keyed by the resolved tip epoch.
Cluster D (`score/helm_e.rs::score_u`): forgetting is computed as
`1.0 - accuracy` instead of `peak - accuracy` (clamped at zero) using the
task's own peak accuracy fixture. Cluster E (`gate/emit_f.rs::gate_y`):
`eval_ok` follows a probe-like "last task in a coarse band" heuristic
instead of checking every task's band membership plus forgetting and
replay-fraction invariants. Cluster F (authority): `eng/build.rs`
rematerializes all five seating surfaces from `eng/seeds/` on every build
while `calib/trial_pref.toml` stays armed or `calib/tip_bind.accept` does
not match the journal-resolved tip — so a one-pass "flip the five modules"
strategy is undone by the verifier rebuild.

These interact: module fixes without the calib binding are clobbered on
rebuild (test_j0_schist); the binding without module fixes leaves broken
metrics; a wrong tip epoch (Cluster A) shifts the resolved replay fraction
that Clusters B/C/D consume; the overflow-vs-durable polarity (Cluster C)
disproportionately drags down early-curriculum tasks whose `overflow_hit`
magnitude is largest; the novel sealed-tip inject moves epoch, fraction,
and every accuracy together, killing hardcodes.

### Environment shape

- **`environment/eng/`** — Rust continual-learning eval engine (opaque
  modules; rebuildable offline) + `build.rs` rematerialize gate + `seeds/`
  seed set.
- **`environment/calib/`** — mutable evaluation state: armed
  `trial_pref.toml`; agents write `tip_bind.accept`.
- **`environment/data/tasks/`** — frozen per-task fixtures (`base`, `peak`,
  `durable_hit`, `overflow_hit`, curriculum `seq`) + `audit/` calibration
  sample.
- **`environment/data/replay/`** — tip journal (authority), retired-tip
  list, stale mirror + live overflow sheets (baits).
- **`environment/data/fixtures/`** — bait "healthy" report.
- **`environment/data/ledger/`** — leftover pre-migration export, not
  authority.
- **`environment/docs/`** — bands + calibration/trial-mode outcomes (not
  fix recipes).
- **`environment/scripts/`** — `run_cl_eval.sh` driver + fixture verify.
- **`environment/tools/`** — `clprobe` surface status probe +
  `probe_calc.py` (last-task heuristic bait).

### Required artifacts

- `instruction.md` — goal-first continual-learning framing; symptoms
  secondary; no repair/debug lead-in; no algorithm dump.
- `task.toml` — `category = "machine-learning"`,
  `languages = ["rust", "bash"]`, `allow_internet = false`
- `output_contract.toml`
- `environment/Dockerfile` + `.dockerignore` + hashed `requirements.txt`
- `tests/test.sh` + `test_outputs.py` (≥10 hard domain tests)
- `solution/solve.sh` (substantive multi-locus rewrite)
- Full environment tree per Initial Draft Commitments (20+ substantive
  files excl. Dockerfile)

### Test plan

1. **test_a3_garnet** — `/app/data` matches `fixtures.sha256`.
2. **test_b7_zircon** — report exists; `schema_tag == cl-eval-v1`;
   curriculum order; required row keys present.
3. **test_c1_biotite** — every `tip_epoch` equals the sealed,
   non-retired journal resolution.
4. **test_d9_epidote** — resolved `tip_epoch` is neither the retired
   sealed-max nor a live-overflow epoch.
5. **test_e2_scoria** — every `replay_frac` equals the durable
   resolution, never the fast-path `0.0`.
6. **test_f5_dolomite** — per-task `accuracy`/`forgetting` match the
   durable-hit engine semantics recomputed from fixtures.
7. **test_g8_feldspar** — every task inside its published band;
   `eval_ok` true.
8. **test_h4_gneiss** — the real report is not the `surface_ok.json` bait.
9. **test_i6_marl** — the earliest task's accuracy stays in band and
   differs from the overflow-path value.
10. **test_j0_schist** — cargo rebuild from `/app/eng` + re-eval matches
    the standing report (fails while trial mode still rematerializes
    seeds).
11. **test_k3_pumice** — two consecutive runs produce byte-identical JSON.
12. **test_l7_dunite** — verifier-owned novel sealed journal entry shifts
    `tip_epoch`, `replay_frac`, and every accuracy together.

### Drafting guardrails

Instruction leads with continual-learning/forgetting/replay outcomes and
ML tags — never "fix the Rust project," cutover, or `/app/ops/`. Fix-path
symbols stay opaque against instruction nouns. No intent comments on fix
modules. No exact expected accuracy table in instruction. Bands live in
docs; expected-value recomputation lives only in tests. Decoys rhyme with
fix symbols but do non-fix work.

### Triviality Ledger

- One-pass "grep the five modules and flip them" fails: `eng/build.rs`
  rematerializes all five surfaces from `eng/seeds/` on the verifier
  rebuild while trial mode is armed.
- Arming the calib binding without the algorithmic fixes leaves broken
  metrics.
- Reading the retired sealed-max tip (`tip_g9`) or the live-overflow sheet
  for replay fraction fails every band and the retired/live discrimination
  test.
- Plain overflow-path scoring drags every task below band; the durable
  path is only confirmed by fixture recomputation.
- Hardcoding tip `tip_g7` / epoch 4 / fraction 0.40 / any accuracy table
  fails the novel-journal inject.
- Hand-writing `/output/cl-eval.json` fails verifier rebuild.

### Per-gate Pitfall Inventory

- RC1 — Oracle must rewrite substantive resolution/propagation/scoring
  bodies, not delete markers.
- RC2 — No broken_/golden_/expected_ path tokens; opaque module names.
- RC3 — Tests recompute accuracy/forgetting from frozen fixtures; not
  schema-only.
- RC4/RC5 — Expected values only in tests; no golden report under
  environment/.
- RC6 — Symptoms/outcomes instruction; bands referenced via docs path, not
  per-task answer recital.
- RC7 — solve.sh ≥80 LOC across five modules.
- GX9/GX10 — Do not list per-task expected accuracies in instruction;
  avoid polarity contradictions on `eval_ok`.
- Static — hashed requirements; PLW1510 `check=` on subprocess;
  `allow_internet=false`; `.dockerignore`; ML-first tags/languages.

### Initial Draft Commitments

- `tasks/continual-learning-replay-buffer-tip-eval/instruction.md`
- `tasks/continual-learning-replay-buffer-tip-eval/task.toml`
- `tasks/continual-learning-replay-buffer-tip-eval/output_contract.toml`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/Dockerfile`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/.dockerignore`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/requirements.txt`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/eng/Cargo.toml`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/eng/Cargo.lock`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/seat/knit_b.rs`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/flag/xv_c.rs`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/mix/ward_d.rs`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/score/helm_e.rs`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/gate/emit_f.rs`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/eng/src/main.rs`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/eng/src/base.rs`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/eng/src/pipe_a.rs`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/eng/src/pipe_b.rs`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/eng/src/decoy_p.rs`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/eng/src/decoy_q.rs`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/data/tasks/t_alpha.json`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/data/tasks/t_beta.json`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/data/tasks/t_gamma.json`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/data/tasks/t_delta.json`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/data/tasks/audit/sample_eval.json`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/data/replay/tip_journal.jsonl`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/data/replay/retired_tips.jsonl`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/data/replay/durable.toml`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/data/replay/live.toml`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/data/fixtures/surface_ok.json`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/data/ledger/journal.jsonl`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/calib/trial_pref.toml`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/eng/build.rs`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/eng/seeds/s1.rs.in`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/eng/seeds/s2.rs.in`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/eng/seeds/s3.rs.in`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/eng/seeds/s4.rs.in`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/eng/seeds/s5.rs.in`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/data/fixtures.sha256`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/docs/cl_bands.md`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/docs/desk_notes.md`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/docs/report_schema.md`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/scripts/run_cl_eval.sh`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/scripts/verify_fixtures.sh`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/tools/clprobe`
- `tasks/continual-learning-replay-buffer-tip-eval/environment/tools/probe_calc.py`
- `tasks/continual-learning-replay-buffer-tip-eval/tests/test.sh`
- `tasks/continual-learning-replay-buffer-tip-eval/tests/test_outputs.py`
- `tasks/continual-learning-replay-buffer-tip-eval/solution/solve.sh`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: seat/knit_b.rs
  symbol: pick_t
  kind: function
  signature: pub fn pick_t(a: &str, b: &str, c: &str) -> (f64, i64)
  purpose: resolve a replay fraction and epoch from journal/mirror/live sources

- path: flag/xv_c.rs
  symbol: bit_z
  kind: function
  signature: pub fn bit_z(a: f64, b: i64, c: &str) -> f64
  purpose: propagate (or drop) the resolved replay fraction through a durable-preference check

- path: mix/ward_d.rs
  symbol: mix_w
  kind: function
  signature: pub fn mix_w(base: f64, durable_hit: f64, overflow_hit: f64, frac: f64, epoch: i64) -> f64
  purpose: turn a task's baseline and buffer-affinity hits into a scored accuracy

- path: score/helm_e.rs
  symbol: score_u
  kind: function
  signature: pub fn score_u(acc: f64, peak: f64) -> f64
  purpose: derive a forgetting scalar from scored accuracy and a task's peak accuracy

- path: gate/emit_f.rs
  symbol: gate_y
  kind: function
  signature: pub fn gate_y(accs: &[f64], forgettings: &[f64], fracs: &[f64], rows_ok: bool) -> bool
  purpose: combine per-task accuracy/forgetting/fraction invariants and row-band status into a single boolean

- path: eng/build.rs
  symbol: seated
  kind: build-script gate
  signature: fn seated(root: &Path) -> bool
  purpose: rematerialize seating surfaces from eng/seeds unless calib binding matches the resolved journal tip
```

#### flipping_point_contract

```
locations:
  - id: A
    path: seat/knit_b.rs
    controls_tests: [test_c1_biotite, test_d9_epidote, test_l7_dunite]
  - id: B
    path: flag/xv_c.rs
    controls_tests: [test_e2_scoria, test_f5_dolomite, test_l7_dunite]
  - id: C
    path: mix/ward_d.rs
    controls_tests: [test_f5_dolomite, test_g8_feldspar, test_i6_marl]
  - id: D
    path: score/helm_e.rs
    controls_tests: [test_f5_dolomite, test_g8_feldspar]
  - id: E
    path: gate/emit_f.rs
    controls_tests: [test_g8_feldspar, test_h4_gneiss]
  - id: F
    path: calib/ (trial_pref.toml removal + tip_bind.accept)
    controls_tests: [test_j0_schist]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: eng/src/decoy_p.rs
  kind: helper
  rhymes_with: pick_t
  non_fix_purpose: computes a decorative accuracy rollup for calibration logging; unused by graded path

- path: eng/src/decoy_q.rs
  kind: helper
  rhymes_with: mix_w
  non_fix_purpose: computes a decorative histogram string for operator logs

- path: data/replay/durable.toml
  kind: fixture
  rhymes_with: tip_journal.jsonl
  non_fix_purpose: stale mirror replay-fraction sheet; reading it yields an out-of-band fraction

- path: data/replay/live.toml
  kind: fixture
  rhymes_with: tip_journal.jsonl
  non_fix_purpose: newest-epoch unsealed overflow sheet; reading it yields an out-of-band fraction

- path: data/ledger/journal.jsonl
  kind: fixture
  rhymes_with: tip_journal.jsonl
  non_fix_purpose: leftover pre-migration replay export; not read by the engine

- path: data/fixtures/surface_ok.json
  kind: fixture
  rhymes_with: cl-eval.json
  non_fix_purpose: pre-baked "healthy-looking" report that a copied answer would match
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [continual, learning, replay, buffer, curriculum, task, accuracy, forgetting, peak, band, calibration, calib, seating, surfaces, engine, tip, epoch, sealed, retired, durable, overflow, live, journal, trial, binding, probe, healthy, status, eval, schema, report]
```
