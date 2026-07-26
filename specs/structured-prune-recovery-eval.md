### Decision
GO — Attempt 1. Machine-learning structured-pruning recovery desk: six scenarios (two start points × three calibration/eval domain mixes) must publish accuracy, sparsity, multiply share and the roster generation they were scored under, all inside documented bands. Seven coupled loci: registry-resolved durable roster generation, geometry propagation through the surviving stack, classifier column gathering on the compacted vector, per-channel statistics re-fitted on the surviving stack, classifier scale/offset recovery against the recorded location *and* spread, per-scenario seating (bound roster + all domains its slice draws from + no carried statistics on resume), and the acceptance receipt that stops two `build.rs` gates from re-seating the workspace from seed material. Goal-first ML framing (recover the published bands), no repair/debug lead-in, no algorithm dump in solver-visible docs.

### Metadata
- version: 2
- Task name: structured-prune-recovery-eval
- Title: Structured-Pruning Sparsity Recovery Eval
- Category: machine-learning
- Languages: [rust]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: [pruning, sparsity, mask-tip, flops, checkpoint-resume, inference-eval]
- Milestones: 0

## Authoring Brief

### Public contract

Bring the pruned-model evaluation desk under `/app/eng` into the documented bands so `/app/scripts/run_prune_eval.sh` publishes `/output/prune-eval.json` with:

- `schema_tag` (string)
- `scenarios` (array) — objects with `id` (string), `accuracy` (number), `sparsity` (number), `flops_frac` (number), `mask_tip` (integer)
- `bands_ok` (boolean)

Required scenario ids: `cold_a`, `resume_a`, `cold_b`, `resume_b`, `mix_c`, `mix_d`. Frozen materials: dense snapshots under `/app/data/dense/`, channel rosters under `/app/data/masks/`, the roster registry under `/app/data/mask_registry/`, calibration rows under `/app/data/calib/`, evaluation slices under `/app/data/eval/`, and the block layout under `/app/data/arch/`. Bands live in `/app/docs/prune_bands.md`; the report shape in `/app/docs/report_schema.md`; desk outcomes in `/app/docs/recovery_notes.md`.

Each cold scenario and its resume partner must agree to within `1e-4`; `sparsity` must be the sparsity of the durable roster generation (not the live overlay proposal); `flops_frac` must land inside its documented band; accuracy lands in band only when the durable structured roster is applied *and* the per-channel statistics plus the classifier are re-fitted. `/app/data/fixtures/surface_ok.json` reports healthy numbers while the published report is out of band. The verifier rebuilds the workspace from `/app/eng` and re-runs the entrypoint, so a hand-written report does not survive; two consecutive runs must be byte-identical.

### Failure topology

Cluster A (`eng/core/src/span.rs`) — geometry does not propagate: each block's fan-in is taken from the dense layout instead of what survived upstream, and the classifier's column count is read from the dense tail, so sparsity and multiply share describe a denser stack than the one being scored. Cluster B (`eng/core/src/draw.rs`) — the classifier gathers its weight columns by position in the compacted vector instead of by surviving channel id, which greens shapes and destroys accuracy. Cluster C (`eng/gauge/src/lib.rs`) — per-channel statistics are measured by forwarding the dense stack and slicing afterwards, so every surviving channel normalises against statistics from a stack it is not in. Cluster D (`eng/gauge/src/head.rs`) — classifier recovery lands on the recorded location but not the recorded spread (the per-class scale drops the sample divisor). Cluster E (`eng/rank/src/tip.rs`) — the roster generation is the newest non-retired row of any state, so the staged live overlay proposal wins over the durable generation the registry resolves. Cluster F (`eng/rank/src/seat.rs`) — a resume start is treated as a source of authority: it re-seats on the generation stamped in its own snapshot and reuses the dense statistics it was carrying, and calibration only covers the first domain a slice draws from, so resume partners disagree and the mixed-domain cells miss their bands. Cluster G (`calib/mask_bind.accept` + `calib/eval_pass.toml`) — `core/build.rs` and `rank/build.rs` rematerialize the seating surfaces from `seeds/` on every rebuild until the recorded pass is the scoring pass and the receipt describes the generation the registry resolves.

These interact. Source fixes without the receipt are undone by the verifier's rebuild; the receipt without the source fixes leaves every metric broken; a wrong roster generation moves geometry, sparsity and accuracy together; re-fitting statistics without the classifier recovery (or the reverse) leaves the mixed-domain cells outside band while the single-domain cells look close; and the novel-generation inject moves the resolved roster under the agent, so a hardcoded roster or metric table fails.

### Environment shape

- **`environment/eng/`** — Rust evaluation workspace: `core` (loaders, forward stack, geometry) + `gauge` (statistics, classifier recovery) + `rank` (registry resolution, per-scenario seating) + `emit` (report), with two `build.rs` seating gates and `seeds/` seed material.
- **`environment/calib/`** — mutable desk state: `eval_pass.toml` (rehearsal by default), `mask_bind.accept` (stale receipt naming the overlay generation), `trace_pref.toml` (decoy).
- **`environment/data/dense/`** — frozen cold + mid-run snapshots, plus a pre-freeze archive snapshot that is never scored.
- **`environment/data/masks/`** — six durable roster sheets + the staged live overlay bait.
- **`environment/data/mask_registry/`** — `tip_journal.jsonl` (out-of-order rows, mixed states) + `retired_tips.jsonl` (rolls back the newest durable generation).
- **`environment/data/calib/`, `environment/data/eval/`, `environment/data/arch/`** — frozen calibration shards, per-scenario slices with their domain lists, and the block layout.
- **`environment/data/fixtures/surface_ok.json`** — captured healthy sweep (false green).
- **`environment/docs/`** — bands, report schema, desk outcomes (no algebra, no fix recipes).
- **`environment/scripts/run_prune_eval.sh`** — rebuild + publish entrypoint.

### Required artifacts

- `instruction.md` — goal-first ML recovery framing; symptoms secondary; no repair/debug lead-in; no per-scenario answer recital.
- `task.toml` — `category = "machine-learning"`, `languages = ["rust"]`, `allow_internet = false`.
- `output_contract.toml`.
- `environment/Dockerfile` + `.dockerignore` + hashed `requirements.txt`.
- `tests/test.sh` + `tests/test_outputs.py` (≥8 hard domain tests, EXPECTED recomputed in the verifier).
- `solution/solve.sh` (multi-locus rewrite across four crates plus the desk receipt).
- `build_helpers/` reference pipeline that generated the frozen fixtures.

### Test plan

1. **test_frozen_inputs_integrity** — `/app/data` and the published bands match `data.sha256`.
2. **test_report_schema_and_scenario_order** — schema tag, required ids, field types.
3. **test_mask_tip_is_bound_durable_generation** — every scenario reports the registry-resolved durable generation.
4. **test_mask_tip_is_not_rolled_back_or_proposed_roster** — the retired generation and the staged overlay generation are both rejected.
5. **test_geometry_is_that_of_the_bound_roster** — sparsity and multiply share recomputed from the frozen layout and the resolved roster with propagation (1e-9).
6. **test_cold_and_resume_partners_agree** — partner accuracies agree within `1e-4` and are not both a degenerate constant.
7. **test_first_domain_scenarios_match_faithful_pass** — `cold_a`/`resume_a` accuracy equals the verifier's independent recovery pass.
8. **test_second_domain_scenarios_match_faithful_pass** — same for `cold_b`/`resume_b`.
9. **test_mixed_domain_scenarios_match_faithful_pass** — same for `mix_c`/`mix_d`, which only land when calibration covers every domain the slice draws from.
10. **test_all_scenarios_inside_published_bands** — every accuracy and both geometry figures inside `/app/docs/prune_bands.md`, and `bands_ok` true.
11. **test_published_numbers_are_not_the_captured_sweep** — the report is not the healthy-looking fixture.
12. **test_entrypoint_republish_is_byte_identical** — rebuild + two entrypoint runs reproduce the agent's report byte for byte.
13. **test_novel_durable_roster_moves_the_report** — a verifier-owned novel durable generation shifts geometry and accuracy together under an independently computed expectation.

### Drafting guardrails

Instruction leads with pruned-model evaluation outcomes and ML tags; never "fix the Rust project", cutover, ops, or `/app/ops/`. Fix-path symbols stay opaque against instruction nouns (`budget`, `tally`, `fit`, `refit`, `settled`, `run`). No intent comments on fix bodies. Bands live in docs; per-scenario expectations are recomputed only in the verifier. Docs describe outcomes (which generation scores, what re-fitting has to land on) and never the propagation formula, the moment algebra, or the receipt template. Decoys (`legacy.ckpt`, `overlay.txt`, `m_g9.txt`, `surface_ok.json`, `trace_pref.toml`, `load.rs`) rhyme with fix symbols but do non-fix work.

### Triviality Ledger

- One-pass "grep the crates and flip the obvious polarities" fails: both `core/build.rs` and `rank/build.rs` rematerialize the seating surfaces from `seeds/` on the verifier's rebuild while the pass is rehearsal or the receipt names the wrong generation (measured: 9/13 tests fail with correct sources and a stale receipt).
- Writing the receipt without the source fixes leaves every metric broken (measured: 9/13 fail).
- Single-locus regressions from the oracle tree all score 0: geometry 3 failed, classifier columns 8, statistics 8, classifier recovery 8, roster resolution 8, seating 9.
- Applying the roster without re-fitting greens sparsity and multiply share but fails accuracy and the mixed-domain cells — the documented "harder" axis of the idea.
- Reading the newest non-retired registry row picks the staged overlay proposal; reading the newest durable row picks the rolled-back generation. Only the registry resolution passes.
- Calibrating on the first domain only leaves `mix_c`/`mix_d` outside band while single-domain cells look close.
- Hardcoding the generation number, the sparsity, or any accuracy table fails the novel-generation inject.
- Hand-writing `/output/prune-eval.json` fails the rebuild + republish test.

### Per-gate Pitfall Inventory

- RC1 — oracle rewrites substantive geometry/statistics/seating bodies; net simplification, not marker deletion.
- RC2 — crate and module names carry no `broken_`/`golden_`/`expected_` tokens; predictability WARN is inherent to domain-named directories (`calib`, `gauge`, `rank`) and is justified, not answer-shaped.
- RC3 — tests recompute accuracy, sparsity and multiply share from frozen fixtures; schema checks are a minority.
- RC4/RC5 — no golden report under `environment/`; EXPECTED lives only in the verifier.
- RC6 — symptoms-only instruction; scenario ids are not enumerated in `instruction.md` (they live in the shipped roster and the report schema doc).
- RC7/GX3 — oracle spans four crates plus two desk files; real diff must stay above the trivial floor while GX2 forbids hiding a tiny fix inside a whole-file rewrite (small-diff files are patched, larger-diff files rewritten).
- CR1/CR7 — every oracle-touched symbol declared and renamed off instruction stems (`share`→`budget`, `Bands`→`Norms`, `sweep`→`drive`, `recover`→`refit`, `snapshot`→`start_ckpt`).
- GX7 — verifier staging names (`/logs/verifier`, `prune-eval-*.json`, `data.sha256`) stay out of solver-visible docs by policy; that orphan set is a justified WARN.
- GX9/GX10 — no per-scenario (id, key, value) triples in the instruction; no both-polarity statements about `bands_ok`.
- Static — hashed `requirements.txt` with `--require-hashes`, separate `RUN rm`, `check=` on every verifier `subprocess.run`, no `v == v` finite checks, `.dockerignore` present, ML-first tags.

### Initial Draft Commitments

- `tasks/structured-prune-recovery-eval/instruction.md`
- `tasks/structured-prune-recovery-eval/task.toml`
- `tasks/structured-prune-recovery-eval/output_contract.toml`
- `tasks/structured-prune-recovery-eval/environment/Dockerfile`
- `tasks/structured-prune-recovery-eval/environment/.dockerignore`
- `tasks/structured-prune-recovery-eval/environment/requirements.txt`
- `tasks/structured-prune-recovery-eval/environment/eng/Cargo.toml`
- `tasks/structured-prune-recovery-eval/environment/eng/Cargo.lock`
- `tasks/structured-prune-recovery-eval/environment/eng/core/Cargo.toml`
- `tasks/structured-prune-recovery-eval/environment/eng/core/build.rs`
- `tasks/structured-prune-recovery-eval/environment/eng/core/src/lib.rs`
- `tasks/structured-prune-recovery-eval/environment/eng/core/src/load.rs`
- `tasks/structured-prune-recovery-eval/environment/eng/core/src/draw.rs`
- `tasks/structured-prune-recovery-eval/environment/eng/core/src/span.rs`
- `tasks/structured-prune-recovery-eval/environment/eng/core/seeds/draw_seed.rs.in`
- `tasks/structured-prune-recovery-eval/environment/eng/core/seeds/span_seed.rs.in`
- `tasks/structured-prune-recovery-eval/environment/eng/gauge/Cargo.toml`
- `tasks/structured-prune-recovery-eval/environment/eng/gauge/src/lib.rs`
- `tasks/structured-prune-recovery-eval/environment/eng/gauge/src/head.rs`
- `tasks/structured-prune-recovery-eval/environment/eng/rank/Cargo.toml`
- `tasks/structured-prune-recovery-eval/environment/eng/rank/build.rs`
- `tasks/structured-prune-recovery-eval/environment/eng/rank/src/lib.rs`
- `tasks/structured-prune-recovery-eval/environment/eng/rank/src/tip.rs`
- `tasks/structured-prune-recovery-eval/environment/eng/rank/src/seat.rs`
- `tasks/structured-prune-recovery-eval/environment/eng/rank/seeds/tip_seed.rs.in`
- `tasks/structured-prune-recovery-eval/environment/eng/rank/seeds/seat_seed.rs.in`
- `tasks/structured-prune-recovery-eval/environment/eng/emit/Cargo.toml`
- `tasks/structured-prune-recovery-eval/environment/eng/emit/src/main.rs`
- `tasks/structured-prune-recovery-eval/environment/calib/eval_pass.toml`
- `tasks/structured-prune-recovery-eval/environment/calib/mask_bind.accept`
- `tasks/structured-prune-recovery-eval/environment/calib/trace_pref.toml`
- `tasks/structured-prune-recovery-eval/environment/data/arch/topology.txt`
- `tasks/structured-prune-recovery-eval/environment/data/dense/cold.ckpt`
- `tasks/structured-prune-recovery-eval/environment/data/dense/resume.ckpt`
- `tasks/structured-prune-recovery-eval/environment/data/dense/legacy.ckpt`
- `tasks/structured-prune-recovery-eval/environment/data/masks/m_g2.txt`
- `tasks/structured-prune-recovery-eval/environment/data/masks/m_g3.txt`
- `tasks/structured-prune-recovery-eval/environment/data/masks/m_g4.txt`
- `tasks/structured-prune-recovery-eval/environment/data/masks/m_g5.txt`
- `tasks/structured-prune-recovery-eval/environment/data/masks/m_g7.txt`
- `tasks/structured-prune-recovery-eval/environment/data/masks/m_g9.txt`
- `tasks/structured-prune-recovery-eval/environment/data/masks/overlay.txt`
- `tasks/structured-prune-recovery-eval/environment/data/mask_registry/tip_journal.jsonl`
- `tasks/structured-prune-recovery-eval/environment/data/mask_registry/retired_tips.jsonl`
- `tasks/structured-prune-recovery-eval/environment/data/calib/shard_a.txt`
- `tasks/structured-prune-recovery-eval/environment/data/calib/shard_b.txt`
- `tasks/structured-prune-recovery-eval/environment/data/eval/roster.txt`
- `tasks/structured-prune-recovery-eval/environment/data/eval/slice_a.txt`
- `tasks/structured-prune-recovery-eval/environment/data/eval/slice_b.txt`
- `tasks/structured-prune-recovery-eval/environment/data/eval/slice_c.txt`
- `tasks/structured-prune-recovery-eval/environment/data/eval/slice_d.txt`
- `tasks/structured-prune-recovery-eval/environment/data/fixtures/surface_ok.json`
- `tasks/structured-prune-recovery-eval/environment/docs/prune_bands.md`
- `tasks/structured-prune-recovery-eval/environment/docs/report_schema.md`
- `tasks/structured-prune-recovery-eval/environment/docs/recovery_notes.md`
- `tasks/structured-prune-recovery-eval/environment/scripts/run_prune_eval.sh`
- `tasks/structured-prune-recovery-eval/tests/test.sh`
- `tasks/structured-prune-recovery-eval/tests/test_outputs.py`
- `tasks/structured-prune-recovery-eval/tests/data.sha256`
- `tasks/structured-prune-recovery-eval/solution/solve.sh`
- `tasks/structured-prune-recovery-eval/build_helpers/reference_model.py`
- `tasks/structured-prune-recovery-eval/build_helpers/gen_data.py`
