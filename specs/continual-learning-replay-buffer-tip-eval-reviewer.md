### Decision
GO — Attempt 1. Machine-learning continual-learning replay-buffer tip
evaluation with five coupled loci (journal-resolved sealed replay tip,
durable-preference propagation, durable-vs-overflow buffer scoring,
peak-relative forgetting, deep eval gate) plus a build-script rematerialize
authority (`eng/build.rs` + `eng/seeds/` + `calib/` trial preference and
tip binding). Plausible-wrong module bodies replace textbook stubs;
stale-mirror and live-overflow fixture baits; a bait "healthy" report;
verifier rebuild + novel sealed-tip inject.

### Metadata
- Task name: continual-learning-replay-buffer-tip-eval
- Title: Continual-Learning Replay-Buffer Tip Evaluation
- Category: machine-learning
- Languages: [rust, bash]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [continual-learning, replay-buffer, forgetting, tip-epoch, accuracy-bands, inference-eval]
- Milestones: 0

### Discovery budget
- Discovery: The durable replay tip resolves from the sealed-and-not-retired
  max-epoch entry of the tip journal (`tip_g7`, epoch 4, fraction 0.40); the
  mirror sheet (`durable.toml`) is stale and the live sheet (`live.toml`)
  carries a newer, unsealed epoch — both are traps for plausible resolution
  rules, and the sealed-max entry itself (`tip_g9`, epoch 7) is retired.
  Planned location: `/app/data/replay/tip_journal.jsonl` +
  `retired_tips.jsonl` vs `durable.toml` / `live.toml`; resolution in
  `seat/knit_b.rs`
  Why instruction must not reveal it: Docs state the sealed/non-retired
  outcome; pasting the resolution rule beside the fix path would collapse
  tip seating to transcription.

- Discovery: The resolved replay fraction must be propagated through the
  durable-preference check in `flag/xv_c.rs` rather than short-circuited to
  a fast-path zero; the fast path looks plausible because it type-checks
  and produces a valid (but wrong) number.
  Planned location: `flag/xv_c.rs` + `seat/knit_b.rs` output
  Why instruction must not reveal it: Naming "fast path" or "zero
  short-circuit" would point directly at the diff; docs describe the
  outcome (durable preference must propagate) only.

- Discovery: Per-task accuracy blends a task's baseline with the
  *durable* buffer-affinity hit scaled by the resolved replay fraction, not
  the live-overflow affinity hit; the overflow hit is negative and
  disproportionately harms early-curriculum tasks, so a wrong polarity is
  visible as multiple early tasks dropping out of band together.
  Planned location: `/app/data/tasks/*.json` (`durable_hit` vs
  `overflow_hit`) + `mix/ward_d.rs`
  Why instruction must not reveal it: The blend formula must be
  reverse-derived from fixtures and band behavior, not transcribed.

- Discovery: Forgetting is peak-relative per task (`peak - accuracy`,
  floored at zero), not a flat `1 - accuracy` proxy; the two formulas agree
  only near `accuracy == peak`, so most tasks expose the polarity.
  Planned location: `/app/data/tasks/*.json` (`peak` field) +
  `score/helm_e.rs`
  Why instruction must not reveal it: Stating the exact formula would let
  agents transcribe it without checking it against the fixtures.

- Discovery: Engine builds rematerialize the five seating surfaces from
  `eng/seeds/` until `calib/trial_pref.toml` selection is "serving" and
  `calib/tip_bind.accept` matches the journal-resolved tip fields. One-pass
  module flips are undone by the verifier rebuild.
  Planned location: `eng/build.rs` + `calib/`
  Why instruction must not reveal it: Instruction/docs state the trial-mode
  refresh and the binding format as outcomes; the coupling to the journal
  resolution is the discovery.

- Discovery: `clprobe` reports a stable-looking status derived from a
  coarse last-task heuristic; `eval_ok` must encode per-task band, forgetting,
  and fraction invariants, not the probe heuristic.
  Planned location: `/app/tools/clprobe` + `/app/tools/probe_calc.py` +
  `gate/emit_f.rs`
  Why instruction must not reveal it: Spelling the probe formula lets
  agents hardcode `eval_ok=true` without discovering the deep-gate
  coupling.

### Anti-trivialization verdict
1 Disclosure-collapse: PASS — outcomes documented; tip/durable/forgetting
  algebra not.
2 Hidden-instance: PASS — multi-task matrix, not one broken file hunt.
3 Single-artifact: PASS — ≥4 coupled modules plus a data-authority locus.
4 Generalization: PASS — novel sealed-tip inject.
5 Prompt-honesty: PASS — symptoms/outcomes without naming fix modules.
6 Cheating-vs-difficulty: PASS — rebuild/idempotence are anti-cheat beside
  real CL seating.
7 Mechanical-fix: PASS.
8 Localized-fix: PASS — five loci plus authority gate.
9 Oracle-locality: PASS — multi-file rewrite.
10 Small declarative-cluster: PASS — engine math, not config-only.
11 Grep-collapse: PASS — opaque symbols vs instruction nouns.
12 Pre-factored-helper: PASS — decoys rhyme; fix names opaque.
13 Recipe-discount: PASS — tip-resolve × durable-vs-overflow × peak-relative
  forgetting is not textbook CRUD.
14 Security-aura: N/A (ML).
15 Orthogonal-checklist: PASS — coupled clusters (tip epoch feeds both
  fraction and scoring).
16 Harness-discount: PASS.
17 One-pass solvability: PASS — probe bait + rematerialize authority defeat
  a single grep-and-flip pass.
18 Hard-only: PASS (target).
19 Discovery budget: PASS (6 ≥ 3).
20 Instruction specificity: symptoms-only / outcomes.
21 Topology distribution: PASS (see below).

### Topology enumeration (3 candidate fix topologies)
1. Tip×propagation×scoring in knit_b / xv_c / ward_d — no single module
   greens tip_epoch + replay_frac + band accuracy together.
2. Tip×scoring×gate in knit_b / ward_d / emit_f — forgetting and eval_ok
   still fail without the durable propagation fix.
3. Propagation×forgetting×gate in xv_c / helm_e / emit_f — tip_epoch still
   fails (retired/live polarity) without the journal-resolution fix.

### Rubric axes
- Verifiable: Pass — deterministic JSON + rebuild.
- Well-specified: Pass — schema + docs bands.
- Solvable: Pass — expert hours, finite Rust loci.
- Difficult: Pass — coupled tip×fraction×scoring×gate beyond training stubs.
- Interesting: Pass — real continual-learning replay-buffer eval work.
- Outcome-verified: Pass — grade report metrics, not process.

### Hardness axes
- Discover: tip polarity (retired vs live vs sealed-serving), durable
  propagation, durable-vs-overflow scoring, peak-relative forgetting,
  probe non-authority.
- Synthesize: task fixtures + replay journal + engine modules.
- Diagnose: symptoms (bands/forgetting/eval_ok) without cause names.
- Navigate coupling: a wrong tip epoch shifts the fraction every module
  consumes; a wrong scoring polarity moves multiple tasks out of band at
  once.
- Reason beyond training: sealed/non-retired journal resolution × durable
  buffer affinity × peak-relative forgetting × deep gate, not a generic
  replay-buffer tutorial.

### Instruction completeness test
No — instruction alone does not name the retired/live/durable resolution
rule, the durable-vs-overflow blend, the forgetting formula, or the
`eval_ok` predicate; the agent must read materials and engine behavior.

## Reviewer Appendix

### Implementation plan
Ship a Rust continual-learning eval engine that (broken) resolves the tip
by newest sealed epoch on disk ignoring retirement (`tip_g9`), always
returns replay fraction `0.0` from the durable-preference check, scores
every task against the live-overflow affinity instead of the durable
affinity, computes forgetting as `1.0 - accuracy`, and gates `eval_ok` on
a coarse last-task-only heuristic. `eng/build.rs` rematerializes all five
surfaces from `eng/seeds/` on every build while trial mode is armed or the
tip binding does not match the journal. Oracle clears
`calib/trial_pref.toml`, writes `calib/tip_bind.accept` from the journal
(python one-shot resolving sealed ∧ ¬retired max epoch), and overwrites
`pick_t` / `bit_z` / `mix_w` / `score_u` / `gate_y` bodies with journal-
resolve / propagation / durable-blend / peak-relative-forgetting / deep-
gate implementations, then runs `run_cl_eval.sh`.

### Proposed file inventory
Matches authoring Initial Draft Commitments (20+ env files).

### Oracle notes
`solve.sh` resolves the tip in Python from `tip_journal.jsonl` and
`retired_tips.jsonl` (sealed ∧ ¬retired, max epoch), writes
`calib/trial_pref.toml` selection `serving` and `calib/tip_bind.accept`
with `tip=`/`epoch=`/`replay=` fields, rewrites the five Rust seating
surfaces with correct bodies, then runs `run_cl_eval.sh`.

### Collapse audit
Stage: Attempt 1 (pre-platform, hardened from moe lineage lessons)
Smallest plausible successful patch: clear trial preference + journal-
matched tip binding + rewrite the five coupled seating functions (~90+
LOC), or equivalently rewrite the five seed files after discovering the
rematerialize authority.
Likely editable frontier: seat/flag/mix/score/gate modules (or
`eng/seeds/*.rs.in`) + `calib/`
Requirement-to-file map: journal tip → knit_b; fraction propagation →
xv_c; durable-vs-overflow scoring → ward_d; forgetting → helm_e; eval_ok →
emit_f; durability → calib gate
Oracle estimated complexity: 90+ non-boilerplate LOC across 6 surfaces
Red flags: none if opaque naming held; NOP expected to fail the majority
of tests (tip retired, fraction zero, overflow scoring, wrong forgetting,
coarse gate); module-only (calib untouched) expected to fail rebuild
parity; calib-only (modules untouched) expected to leave broken metrics
Residual hardness: retired-vs-live-vs-serving tip polarity; durable
propagation vs fast-path zero; durable-vs-overflow blend reverse-
derivation from fixtures/bands; rematerialize authority discovery; novel
sealed-tip generalization
Collapse verdict: PASS (pending local static/collapse gate + oracle/NOP
evidence — not yet claimed in this attempt)

### Naming-pass record

**Instruction nouns extracted:**
continual, learning, replay, buffer, curriculum, task, accuracy,
forgetting, peak, band, calibration, calib, seating, surfaces, engine,
tip, epoch, sealed, retired, durable, overflow, live, journal, trial,
binding, probe, healthy, status, eval, schema, report

**Renames during drafting:**
- kept moe's opaque symbol names (`pick_t`, `bit_z`, `mix_w`, `score_u`,
  `gate_y`) verbatim since none substring-match the CL instruction noun
  list above.
- `ops/` vocabulary avoided throughout; `calib/` chosen to keep an
  ML-flavored desk vocabulary instead of an ops-cutover aura.

**Test names audited:**
- test_a3_garnet
- test_b7_zircon
- test_c1_biotite
- test_d9_epidote
- test_e2_scoria
- test_f5_dolomite
- test_g8_feldspar
- test_h4_gneiss
- test_i6_marl
- test_j0_schist
- test_k3_pumice
- test_l7_dunite

**Concentration math:**
- Total tests: 12
- A knit_b: 3/12 = 0.25
- B xv_c: 3/12 = 0.25
- C ward_d: 3/12 = 0.25
- D helm_e: 2/12 = 0.17
- E emit_f: 2/12 = 0.17
- F calib gate: 1/12 = 0.08 (also required transitively by every metric
  test via rebuild)
- Cap: 0.5. Max ratio observed: 0.25. Status: PASS

### Per-test feasibility pre-check
- test_a3_garnet — checksum — 1 — no — LOW
- test_b7_zircon — schema keys + order — 2+ approaches — no — LOW
- test_c1_biotite — journal-resolved tip_epoch equality — 2+ — no — MEDIUM
- test_d9_epidote — tip_epoch not retired/live — 2+ — no — MEDIUM
- test_e2_scoria — replay_frac equals durable resolution — 2+ — no — MEDIUM
- test_f5_dolomite — exact accuracy/forgetting (fixture-derived) — 2+ — no — MEDIUM
- test_g8_feldspar — band membership + eval_ok — 2+ — weak chain on tip — MEDIUM
- test_h4_gneiss — report ≠ bait — 1 — no — LOW
- test_i6_marl — earliest-task band + overflow divergence — 2+ — no — MEDIUM
- test_j0_schist — rebuild parity under rematerialize gate — 1 (rebuild) — no — MEDIUM
- test_k3_pumice — bytes — 2+ — no — LOW
- test_l7_dunite — novel sealed-tip inject shifts epoch/fraction/accuracy — 2+ — no — MEDIUM
