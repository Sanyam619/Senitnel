### Decision
GO — Attempt 1 (hardened after platform TRIVIAL 100%/100%). Machine-learning MoE inference/eval seating desk with five coupled loci (journal-resolved durable tip, epoch-windowed hold ledger, capacity-weighted load renormalization, natural-log scoring, deep eval gate) plus a build-script rematerialize authority: engine builds refresh the seating surfaces from `eng/seeds/` until the desk trial preference is cleared and `calib/tip_bind.accept` binds the journal-resolved tip. Plausible-wrong bodies (no textbook stubs); stale-mirror and overstated-roster fixture baits; capacity blend discoverable only from an archived healthy seating sample; verifier rebuild + novel-slice + novel-journal injects; goal-first ML framing (no repair/debug lead-in).

### Metadata
- version: 2
- Task name: moe-router-load-balance-eval
- Title: MoE Router Eval Desk
- Category: machine-learning
- Languages: [rust, bash]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: [mixture-of-experts, router, load-balance, perplexity, inference-eval, held-expert]
- Milestones: 0

## Authoring Brief

### Public contract

Seat the mixture-of-experts inference desk so `/app/scripts/run_moe_eval.sh` rebuilds the engine under `/app/eng` and writes `/output/moe-eval.json` with:

- `schema_tag` (string) — must be `moe-eval-v1`
- `experts` (array) — objects with `id` (string), `load_share` (number), `active` (boolean)
- `slices` (array) — objects with `id` (string), `perplexity` (number), `expert_entropy` (number), `router_temp` (number)
- `eval_ok` (boolean)

Materials under `/app/data/experts/`, `/app/data/routers/`, and `/app/data/eval/` are frozen. Numeric bands and micro-tolerances live in `/app/docs/moe_bands.md`. Active experts' load shares must sum to one within the documented micro-tolerance; held experts must be inactive with zero load_share; each slice's `router_temp` must match the durable router tip; each slice perplexity must land in its documented band. `/app/tools/moeprobe` may still print balanced when deep evaluation is unhealthy. The verifier rebuilds from `/app/eng` and re-invokes eval; hand-written reports fail. Two consecutive runs must be byte-identical.

### Failure topology

Cluster A: tip resolution prefers the newest-epoch on-disk sheet (live bait, 2.0) over the journal-resolved sealed tip (0.75 at epoch 4); the stale mirror (0.8) is a second trap that lands 3/4 slices in band but fails exact entropy and one band cell. Cluster B: holds are read from the overstated flat roster (`hold.json` lists e1,e3,e4) instead of the epoch-windowed ledger resolved at the tip epoch (held {e1,e3}; e4's hold is at epoch 7 > 4; e1's release at 9 is also out of window). The tip epoch and the hold window are coupled: a wrong epoch moves the hold set. Cluster C: seating ignores expert capacity — the correct blend (capacity × routed softmax, renormalized post-hold) is only recoverable from the archived healthy seating sample under `data/eval/audit/`. Cluster D: entropy is computed in log2 while perplexity exponentiates with e (mismatched base). Cluster E: `eval_ok` follows a probe-like spread heuristic. Cluster F (authority): `eng/build.rs` rematerializes all five seating surfaces from `eng/seeds/` on every build while `calib/trial_pref.toml` stays armed or `calib/tip_bind.accept` does not match the journal-resolved tip — so the one-pass "flip the five modules" strategy is undone by the verifier rebuild.

These interact: module fixes without the calib binding are clobbered on rebuild (test_h1_slate); the binding without module fixes leaves broken metrics; a wrong tip epoch shifts the hold window and distant load/entropy cells; capacity omission passes unit-mass checks but fails exact loads and two band cells; the novel-journal inject moves tip and hold window together, killing hardcodes.

### Environment shape

- **`environment/eng/`** — Rust MoE eval engine (opaque modules; rebuildable offline) + `build.rs` rematerialize gate + `seeds/` seed set.
- **`environment/calib/`** — mutable desk state: armed `trial_pref.toml`; agents write `tip_bind.accept`.
- **`environment/data/experts/`** — frozen expert capacity fixtures.
- **`environment/data/routers/`** — tip journal (authority), stale mirror + live sheet baits, hold ledger (authority), overstated roster bait.
- **`environment/data/eval/`** — frozen per-slice routing logits + `audit/seated_sample.json` (healthy seating reference for capacity discovery).
- **`environment/docs/`** — bands + journal/hold/trial-mode outcomes (not fix recipes).
- **`environment/scripts/`** — `run_moe_eval.sh` driver + fixture verify.
- **`environment/tools/`** — `moeprobe` surface balance probe + `probe_calc.py` (uniform-share bait).

### Required artifacts

- `instruction.md` — goal-first ML seating; symptoms secondary; no repair/debug lead-in; no algorithm dump.
- `task.toml` — `category = "machine-learning"`, `languages = ["rust", "bash"]`, `allow_internet = false`
- `output_contract.toml`
- `environment/Dockerfile` + `.dockerignore` + hashed `requirements.txt`
- `tests/test.sh` + `test_outputs.py` (≥8 hard domain tests)
- `solution/solve.sh` (substantive multi-locus rewrite)
- Full environment tree per Initial Draft Commitments (25+ substantive files excl. Dockerfile)

### Test plan

1. **test_n4_quartz** — report exists; `schema_tag == moe-eval-v1`; required top-level and row keys present.
2. **test_w7_beryl** — sum of load_share over active experts is 1.0 ± 1e-6; inactive shares are 0.
3. **test_k2_topaz** — held set resolves from the epoch ledger ({e1,e3}); roster-only baits (e4) must stay active with positive load.
4. **test_m9_jade** — every slice router_temp equals the journal-resolved sealed tip; differs from live and mirror sheets.
5. **test_r6_onyx** — every slice perplexity inside `/app/docs/moe_bands.md` band.
6. **test_p3_flint** — expert_entropy equals the fixture-derived seated distribution entropy (1e-6), not uniform bait.
7. **test_c8_coral** — eval_ok is true only when deep invariants hold (probe balanced alone is insufficient).
8. **test_v5_mica** — exact capacity-weighted hold-aware loads (1e-6); moeprobe must not print balanced.
9. **test_h1_slate** — cargo rebuild from `/app/eng` + re-eval matches agent report (fails while trial mode still rematerializes seeds).
10. **test_u4_basalt** — two consecutive runs produce byte-identical JSON.
11. **test_y2_chert** — verifier-owned novel slice under a temp data root scores under independently computed metrics.
12. **test_j3_pyrite** — verifier-owned novel sealed journal entry (epoch 8, temp 0.6) shifts tip and hold window together; engine must track both.
13. **test_g6_shale** — `/app/data` matches fixtures.sha256.

### Drafting guardrails

Instruction leads with MoE inference/eval outcomes and ML tags — never “fix the Rust project,” cutover, or `/app/ops/`. Fix-path symbols stay opaque against instruction nouns. No intent comments on fix modules. No exact expected load tables in instruction. Bands live in docs; EXPECTED recomputation lives only in tests. Decoys rhyme with fix symbols but do non-fix work. Do not ship answer-key closed-form softmax algebra in solver-visible runbooks.

### Triviality Ledger

- One-pass "grep the five modules and flip them" (the prior platform-TRIVIAL trajectory) now fails: `eng/build.rs` rematerializes all five surfaces from `eng/seeds/` on the verifier rebuild while trial mode is armed — measured 8/13 tests fail under that strategy.
- Arming the calib binding without the algorithmic fixes leaves broken metrics (measured 8/13 fail).
- Reading `durable.toml` (stale mirror) or `live.toml` (newest epoch) for the tip fails exact entropy everywhere and at least one band; only journal sealed-max resolution matches.
- Trusting `hold.json` holds e4 (out-of-window) and fails k2/v5/bands; the ledger must be windowed by the resolved tip epoch.
- Plain softmax without capacity passes unit-mass but fails exact loads and two band cells; the blend is only recoverable from the audit sample.
- Hardcoding tip 0.75 / held {e1,e3} / any load table fails the novel-journal inject (tip 0.6 at epoch 8 flips the hold window to {e1,e3,e4}).
- Hand-writing `/output/moe-eval.json` fails verifier rebuild + both injects.

### Per-gate Pitfall Inventory

- RC1 — Oracle must rewrite substantive routing/hold/renorm bodies, not delete markers.
- RC2 — No broken_/golden_/expected_ path tokens; opaque module names.
- RC3 — Tests recompute load/entropy/perplexity from frozen fixtures; not schema-only.
- RC4/RC5 — EXPECTED only in tests; no golden report under environment/.
- RC6 — Symptoms/outcomes instruction; bands referenced via docs path, not per-slice answer recital.
- RC7 — solve.sh ≥80 LOC across three modules.
- GX9/GX10 — Do not list per-slice expected perplexities in instruction; avoid polarity contradictions on eval_ok.
- Static — hashed requirements; PLW1510 check= on subprocess; allow_internet=false; .dockerignore; ML-first tags/languages.

### Initial Draft Commitments

- `tasks/moe-router-load-balance-eval/instruction.md`
- `tasks/moe-router-load-balance-eval/task.toml`
- `tasks/moe-router-load-balance-eval/output_contract.toml`
- `tasks/moe-router-load-balance-eval/environment/Dockerfile`
- `tasks/moe-router-load-balance-eval/environment/.dockerignore`
- `tasks/moe-router-load-balance-eval/environment/requirements.txt`
- `tasks/moe-router-load-balance-eval/environment/eng/Cargo.toml`
- `tasks/moe-router-load-balance-eval/environment/eng/Cargo.lock`
- `tasks/moe-router-load-balance-eval/environment/seat/knit_b.rs`
- `tasks/moe-router-load-balance-eval/environment/flag/xv_c.rs`
- `tasks/moe-router-load-balance-eval/environment/mix/ward_d.rs`
- `tasks/moe-router-load-balance-eval/environment/score/helm_e.rs`
- `tasks/moe-router-load-balance-eval/environment/gate/emit_f.rs`
- `tasks/moe-router-load-balance-eval/environment/eng/src/main.rs`
- `tasks/moe-router-load-balance-eval/environment/eng/src/base.rs`
- `tasks/moe-router-load-balance-eval/environment/eng/src/pipe_a.rs`
- `tasks/moe-router-load-balance-eval/environment/eng/src/pipe_b.rs`
- `tasks/moe-router-load-balance-eval/environment/eng/src/decoy_p.rs`
- `tasks/moe-router-load-balance-eval/environment/eng/src/decoy_q.rs`
- `tasks/moe-router-load-balance-eval/environment/data/experts/e0.json`
- `tasks/moe-router-load-balance-eval/environment/data/experts/e1.json`
- `tasks/moe-router-load-balance-eval/environment/data/experts/e2.json`
- `tasks/moe-router-load-balance-eval/environment/data/experts/e3.json`
- `tasks/moe-router-load-balance-eval/environment/data/experts/e4.json`
- `tasks/moe-router-load-balance-eval/environment/data/routers/tip_journal.jsonl`
- `tasks/moe-router-load-balance-eval/environment/data/routers/hold_ledger.jsonl`
- `tasks/moe-router-load-balance-eval/environment/data/routers/durable.toml`
- `tasks/moe-router-load-balance-eval/environment/data/routers/live.toml`
- `tasks/moe-router-load-balance-eval/environment/data/routers/hold.json`
- `tasks/moe-router-load-balance-eval/environment/data/eval/audit/seated_sample.json`
- `tasks/moe-router-load-balance-eval/environment/calib/trial_pref.toml`
- `tasks/moe-router-load-balance-eval/environment/eng/build.rs`
- `tasks/moe-router-load-balance-eval/environment/eng/seeds/s1.rs.in`
- `tasks/moe-router-load-balance-eval/environment/eng/seeds/s2.rs.in`
- `tasks/moe-router-load-balance-eval/environment/eng/seeds/s3.rs.in`
- `tasks/moe-router-load-balance-eval/environment/eng/seeds/s4.rs.in`
- `tasks/moe-router-load-balance-eval/environment/eng/seeds/s5.rs.in`
- `tasks/moe-router-load-balance-eval/environment/tools/probe_calc.py`
- `tasks/moe-router-load-balance-eval/environment/data/eval/s_alpha.json`
- `tasks/moe-router-load-balance-eval/environment/data/eval/s_beta.json`
- `tasks/moe-router-load-balance-eval/environment/data/eval/s_gamma.json`
- `tasks/moe-router-load-balance-eval/environment/data/eval/s_delta.json`
- `tasks/moe-router-load-balance-eval/environment/data/fixtures.sha256`
- `tasks/moe-router-load-balance-eval/environment/docs/moe_bands.md`
- `tasks/moe-router-load-balance-eval/environment/docs/desk_notes.md`
- `tasks/moe-router-load-balance-eval/environment/scripts/run_moe_eval.sh`
- `tasks/moe-router-load-balance-eval/environment/scripts/verify_fixtures.sh`
- `tasks/moe-router-load-balance-eval/environment/tools/moeprobe`
- `tasks/moe-router-load-balance-eval/tests/test.sh`
- `tasks/moe-router-load-balance-eval/tests/test_outputs.py`
- `tasks/moe-router-load-balance-eval/solution/solve.sh`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: seat/knit_b.rs
  symbol: pick_t
  kind: function
  signature: pub fn pick_t(a: &str, b: &str, c: &str) -> (f64, i64)
  purpose: resolve a scalar and generation index from journal/mirror/live sources

- path: flag/xv_c.rs
  symbol: bit_z
  kind: function
  signature: pub fn bit_z(a: &[String], b: &[(String, String, i64)], ids: &[String], g: i64) -> Vec<bool>
  purpose: map roster summary and epoch-carrying entries onto per-id boolean flags

- path: mix/ward_d.rs
  symbol: mix_w
  kind: function
  signature: pub fn mix_w(raw: &[f64], caps: &[f64], flags: &[bool], scale: f64) -> Vec<f64>
  purpose: turn raw scores, per-id scalars, and flags into a unit-mass weight vector

- path: score/helm_e.rs
  symbol: score_u
  kind: function
  signature: pub fn score_u(weights: &[f64], scale: f64) -> (f64, f64)
  purpose: derive two scalar metrics from a weight vector and scale

- path: gate/emit_f.rs
  symbol: gate_y
  kind: function
  signature: pub fn gate_y(shares: &[f64], flags: &[bool], rows_ok: bool) -> bool
  purpose: combine share/flag/row predicates into a single boolean

- path: eng/build.rs
  symbol: seated
  kind: build-script gate
  signature: fn seated(root: &Path) -> bool
  purpose: rematerialize seating surfaces from eng/seeds unless calib binding matches the resolved journal generation
```

#### flipping_point_contract

```
locations:
  - id: A
    path: seat/knit_b.rs
    controls_tests: [test_m9_jade, test_r6_onyx, test_j3_pyrite]
  - id: B
    path: flag/xv_c.rs
    controls_tests: [test_k2_topaz, test_w7_beryl, test_j3_pyrite]
  - id: C
    path: mix/ward_d.rs
    controls_tests: [test_w7_beryl, test_v5_mica, test_c8_coral]
  - id: D
    path: score/helm_e.rs
    controls_tests: [test_r6_onyx, test_p3_flint, test_y2_chert]
  - id: E
    path: gate/emit_f.rs
    controls_tests: [test_c8_coral, test_v5_mica]
  - id: F
    path: calib/ (trial_pref.toml removal + tip_bind.accept)
    controls_tests: [test_h1_slate]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: eng/src/decoy_p.rs
  kind: helper
  rhymes_with: pick_t
  non_fix_purpose: formats capacity summaries for desk notes; unused by graded path

- path: eng/src/decoy_q.rs
  kind: helper
  rhymes_with: mix_w
  non_fix_purpose: computes a decorative histogram string for logging
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [mixture, experts, inference, desk, schema, load, share, active, slices, perplexity, entropy, router, temp, eval, materials, routers, band, durable, tip, held, probe, balanced, reports, engine, softmax, renormal, hold, mask, temperature, logit, journal, capacity, trial, binding]
```
