### Decision

GO — Attempt 1. Machine-learning INT4 weight-only quantized-inference desk: six scenarios (two start points x four evaluation slices) must publish perplexity, top-1 agreement, the grouping width they were quantized under and the scale-bank generation they were bound to, all inside documented bands. Six coupled loci: registry-resolved sealed grouped generation, the calibration admission window that generation opens, activation-aware scale recomputation from those calibration rows, the grouping axis the weight quantizer reduces over, the resume start that re-binds the scale sheet stamped into its own snapshot, and the acceptance receipt that stops three `build.rs` seating gates from re-seating the workspace from seed material. Goal-first ML framing (bring the quantized eval into its bands), no repair/debug lead-in, no algebra in solver-visible docs.

### Metadata

- version: 1
- Task name: int4-weight-only-calibration-eval
- Title: Calibration-Aware INT4 Weight-Only Eval
- Category: machine-learning
- Languages: [rust]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: [int4, weight-only, group-size, scale-bank, tip-epoch, inference-eval]
- Milestones: 0

## Authoring Brief

### Public contract

Bring the INT4 weight-only evaluation engine under `/app/eng` into the documented bands so `/app/scripts/run_int4_eval.sh` publishes `/output/int4-eval.json` with:

- `schema_tag` (string)
- `scenarios` (array) — objects with `id` (string), `perplexity` (number), `top1` (number), `group_size` (integer), `tip_epoch` (integer)
- `bands_ok` (boolean)

Required scenario ids: `cold_a`, `resume_a`, `cold_b`, `resume_b`, `mix_c`, `mix_d`. Frozen materials: FP16 snapshots under `/app/data/fp16/`, captured scale banks under `/app/data/scales/`, calibration rows under `/app/data/calib/`, the quantization registry under `/app/data/quant_registry/`, grouping sheets under `/app/data/quant_grids/`, evaluation slices under `/app/data/eval/`, and the layer layout under `/app/data/arch/`. Bands live in `/app/docs/int4_bands.md`; the report shape in `/app/docs/report_schema.md`; desk outcomes in `/app/docs/quant_notes.md`.

Each cold scenario and its resume partner must agree to within `1e-4`; `group_size` must be the grouping width of the sealed grouped generation the registry resolves (not the live per-channel sheet); `tip_epoch` must be that generation's number; the per-input-channel scales must be recomputed from the calibration rows the bound generation admits, not read from a captured bank. `/app/data/fixtures/surface_ok.json` reports healthy numbers while the published report is out of band. The verifier rebuilds the workspace from `/app/eng` and re-runs the entrypoint, so a hand-written report does not survive; two consecutive runs must be byte-identical.

### Failure topology

Cluster A (`eng/pane/src/tip.rs`) — the scored generation is the newest journal row of any state, so the live per-channel sheet wins over the sealed grouped generation. Ignoring only retirement lands on a rolled-back generation; ignoring only the sheet kind lands on a sealed per-channel generation. Three shortcuts, three different wrong answers, all of which move `group_size`, `tip_epoch` and every metric together.

Cluster B (`eng/knit/src/admit.rs`) — every shard named in the calibration ledger is folded into the calibration set, ignoring the epoch window each shard is admitted over, so the scales are fit over rows that expired before the bound generation and rows that were not collected until after it.

Cluster C (`eng/knit/src/gains.rs`, `weave`) — the per-input-channel scales are read straight out of the captured bank the registry names for the bound generation instead of being measured on the admitted calibration rows. The captured banks are real captures from an earlier calibration revision, so they parse, look plausible, and are wrong.

Cluster D (`eng/core/src/fold.rs`) — the weight quantizer reduces its group extent over the output rows instead of the input channels, so each group's scale is shared by weights that are never summed together.

Cluster E (`eng/pane/src/seat.rs`) — a resume start is treated as a source of authority: it binds the scale sheet stamped into its own snapshot instead of the sheet the scoring pass measured, so resume partners disagree with their cold partners.

Cluster F (`serving/bind.accept`) — `core/build.rs`, `knit/build.rs` and `pane/build.rs` each re-seat their fix surfaces from `seeds/` on every rebuild until the acceptance receipt records a scoring pass and describes a generation the registry will actually score under (sealed, not retired, grouped, with the grouping width and group count its sheet implies).

These interact. Source fixes without the receipt are undone by the verifier's rebuild; the receipt without the source fixes leaves every metric broken; a wrong generation moves the grouping width, the epoch, the admitted calibration window and every metric at once; recomputing scales without fixing the grouping axis (or the reverse) leaves every band missed; and the novel-generation inject moves the resolved generation under the agent, so a hardcoded grouping width or metric table fails.

### Environment shape

- **`environment/eng/`** — Rust evaluation workspace: `core` (loaders, forward pass, quantizer, likelihood) + `knit` (calibration admission, activation-aware scales) + `pane` (registry resolution, per-scenario seating) + `emit` (report), with three `build.rs` seating gates and `seeds/` seed material.
- **`environment/serving/bind.accept`** — mutable acceptance receipt, shipped stale (names the sealed per-channel generation, records a rehearsal pass).
- **`environment/calib/trace_pref.toml`** — decoy desk note.
- **`environment/data/fp16/`** — frozen cold + mid-run FP16 snapshots, plus a pre-freeze archive snapshot that is never scored.
- **`environment/data/quant_grids/`** — grouping sheets per generation, including the live per-channel bait and a sealed per-channel sheet.
- **`environment/data/quant_registry/`** — `tip_journal.jsonl` (out-of-order rows, mixed states) + `retired_tips.jsonl` (rolls back the newest sealed grouped generation).
- **`environment/data/scales/`** — captured per-input-channel banks from an earlier calibration revision.
- **`environment/data/calib/`** — calibration shards plus `admit_ledger.jsonl` giving each shard's epoch window.
- **`environment/data/eval/`, `environment/data/arch/`** — per-scenario slices with their domain lists, the scenario roster, and the layer layout.
- **`environment/data/fixtures/surface_ok.json`** — captured healthy sweep pinned to the live per-channel generation (false green).
- **`environment/docs/`** — bands, report schema, desk outcomes (no algebra, no fix recipes).
- **`environment/scripts/run_int4_eval.sh`** — rebuild + publish entrypoint.

### Required artifacts

- `instruction.md` — goal-first ML quantized-eval framing; symptoms secondary; no repair/debug lead-in; no per-scenario answer recital.
- `task.toml` — `category = "machine-learning"`, `languages = ["rust"]`, `allow_internet = false`.
- `output_contract.toml`.
- `environment/Dockerfile` + `.dockerignore` + hashed `requirements.txt`.
- `tests/test.sh` + `tests/test_outputs.py` (>=12 hard domain tests, expectations embedded in verifier code).
- `solution/solve.sh` (multi-locus rewrite across three crates plus the desk receipt).
- `build_helpers/` reference pipeline that generated the frozen fixtures — kept at the repo root, never inside the task directory, because it names the bound generation.

### Test plan (17 shipped)

1. **test_frozen_inputs_integrity** — `/app/data` and the published bands match `data.sha256`.
2. **test_report_schema_and_scenario_order** — schema tag, required ids in roster order, field types and ranges.
3. **test_group_size_is_the_resolved_grouped_generation** — every scenario reports the resolved grouping width, with a likelihood guard that the metric beside it could have come from that width.
4. **test_group_size_is_not_the_live_or_rolled_back_sheet** — the per-channel widths, the rolled-back generation's width and the staged width are rejected.
5. **test_tip_epoch_is_the_sealed_scale_bank_generation** — the resolved epoch, and none of the rolled-back / live / staged / older sealed epochs.
6. **test_first_domain_scenarios_match_faithful_pass** — `cold_a`/`resume_a` perplexity and top-1 equal a faithful pass.
7. **test_second_domain_scenarios_match_faithful_pass** — same for `cold_b`/`resume_b`.
8. **test_mixed_domain_scenarios_match_faithful_pass** — same for `mix_c`/`mix_d`.
9. **test_cold_and_resume_partners_agree** — partner perplexity and top-1 agree within `1e-4`.
10. **test_all_scenarios_inside_published_bands** — every metric inside `/app/docs/int4_bands.md`, and `bands_ok` true.
11. **test_published_numbers_are_not_the_captured_sweep** — the report is neither the healthy-looking fixture's numbers nor its grouping width.
12. **test_entrypoint_republish_is_byte_identical** — rebuild + two entrypoint runs reproduce the agent's report byte for byte.
13. **test_scales_do_not_come_from_the_captured_banks** — perturbing the captured bank the registry names must not move the report.
14. **test_unadmitted_calibration_rows_do_not_reach_the_scales** — perturbing a shard outside the admission window must not move the report.
15. **test_admitted_calibration_rows_reach_the_scales** — perturbing an admitted shard must move every scenario while partners keep agreeing.
16. **test_scales_track_the_admitted_calibration_window** — widening a shard's admission window must land every scenario on the numbers that window produces.
17. **test_novel_sealed_generation_moves_the_report** — a verifier-owned novel sealed grouped generation shifts the grouping width, the epoch and every metric together, and drops `bands_ok`.

### Drafting guardrails

Instruction leads with quantized-inference evaluation outcomes and ML tags; never "fix the Rust project", cutover, ops, or `/app/ops/`. Fix-path symbols stay opaque against instruction nouns (`settled`, `run`, `rows`, `sheet`, `pack`). No intent comments on fix bodies. Bands live in docs; per-scenario expectations live only in the verifier. Docs describe outcomes (which generation scores, where the scales have to be measured) and never the scale formula, the quantizer algebra, the admission window arithmetic or the receipt template. Decoys (`archive.ckpt`, `grid_live.txt`, `grid_g9.txt`, `grid_g11.txt`, `surface_ok.json`, `trace_pref.toml`, `load.rs`) rhyme with fix symbols but do non-fix work.

### Triviality Ledger

- One-pass "grep the crates and flip the obvious polarities" fails: `core/build.rs`, `knit/build.rs` and `pane/build.rs` all re-seat their fix surfaces from `seeds/` on the verifier's rebuild while the receipt records a rehearsal pass or names a generation the registry will not score under.
- "Write the receipt and stop" fails: the receipt only gates re-seating; every metric still comes from the five source loci.
- "Read the answer off the health fixture" fails: `surface_ok.json` is pinned to the live per-channel generation and its numbers are more than the copy gap away from a faithful pass on every scenario.
- "Copy the captured bank the registry names" fails: `test_scales_do_not_come_from_the_captured_banks` perturbs that bank and requires the report not to move.
- "Hardcode the grouping width / epoch / metric table" fails: the novel-generation inject moves all three under the agent.
- "Fit scales over every shard in the ledger" fails: `test_scales_track_the_admitted_calibration_window` and the faithful-pass cells both discriminate the window.
- "Green the single-domain cells and stop" fails: the mixed-domain cells and the pair-agreement cell are scored separately.

### Per-gate Pitfall Inventory

- **RC1** — `solve.sh` rewrites five module bodies and derives the receipt from the registry; nothing is a revert.
- **RC2** — no `broken_*` / `golden_*` / `expected_*` tokens; crate and module names (`core`, `knit`, `pane`, `emit`, `fold`, `gains`, `admit`, `tip`, `seat`) do not encode the contract.
- **RC3** — every test asserts computed domain values (perplexity, top-1, grouping width, epoch) rather than shape alone.
- **RC4** — expectations are literals in `tests/test_outputs.py`; the frozen inputs are SHA-256 pinned.
- **RC5** — the only fixture that looks like an answer is `surface_ok.json`, which is poisoned onto the live per-channel generation.
- **RC6** — instruction is symptoms-only: no formula, no file locations, no numeric thresholds beyond the published pair tolerance the contract itself needs.
- **RC7** — oracle is a multi-hundred-line rewrite across three crates plus receipt derivation.
- **CR2** — five source locations plus the receipt; the largest single location controls fewer than half the tests.
- **CR6** — fix bodies carry mechanical comments only.
- **CR7** — instruction nouns (report, scenario, calibration, generation, grouping, scale, slice, snapshot) do not appear as fix-path symbols.
- **GX9** — the instruction names no per-scenario metric value; bands live in the docs table.
