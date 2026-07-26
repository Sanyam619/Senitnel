### Decision
GO — Attempt 1. Machine-learning structured-pruning recovery desk with six scenarios over two start points and three calibration/eval domain mixes. Seven coupled loci: registry-resolved roster generation, geometry propagation, classifier column gathering, per-channel statistics on the surviving stack, classifier scale/offset recovery against the recorded location and spread, per-scenario seating (bound roster, all slice domains, no carried statistics on resume), and the acceptance receipt that disarms two `build.rs` seating gates. Plausible-wrong bodies (no textbook stubs); overlay/retired/legacy/captured-sweep baits; verifier rebuild + novel-generation inject; goal-first ML framing.

### Metadata
- Task name: structured-prune-recovery-eval
- Title: Structured-Pruning Sparsity Recovery Eval
- Category: machine-learning
- Languages: [rust]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [pruning, sparsity, mask-tip, flops, checkpoint-resume, inference-eval]
- Milestones: 0

### Discovery budget
- Discovery: The scoring roster generation is the one the registry resolves — the newest durable generation that has not been rolled back. The staged live overlay sheet carries the newest generation number of any state, and the newest durable row is retired after the fact.
  Planned location: `/app/data/mask_registry/tip_journal.jsonl` + `retired_tips.jsonl` vs `/app/data/masks/overlay.txt` and `m_g9.txt`; resolution in `eng/rank/src/tip.rs`.
  Why instruction must not reveal it: Docs describe the states and the rollback ledger as outcomes; naming the resolved generation would turn roster seating into transcription and let the agent hardcode a generation number.

- Discovery: Dropping a channel also removes the columns its downstream consumers and the classifier spent on it, so geometry has to propagate through the surviving stack rather than read the dense layout.
  Planned location: `/app/data/arch/topology.txt` + `eng/core/src/span.rs`.
  Why instruction must not reveal it: The propagation rule is the graded reasoning; pasting it beside the geometry body is an answer key (the SPH Shepard-algebra collapse class).

- Discovery: Re-fitting is two things, not one — per-channel statistics measured on the stack that survives, and a per-class scale/offset that lands the class responses on both the recorded location and the recorded spread. Applying the roster alone greens sparsity and multiply share and still fails accuracy.
  Planned location: `eng/gauge/src/lib.rs` + `eng/gauge/src/head.rs`, recorded anchors in `/app/data/dense/*.ckpt`.
  Why instruction must not reveal it: The moment algebra and the scale ratio must be derived from the recorded anchors and observed band misses, not transcribed.

- Discovery: A resume start is a starting point only. Its snapshot stamps a generation and carries the dense statistics of the run it was taken from; using either breaks partner agreement. Calibration also has to cover every domain the slice draws from, which is what separates the mixed cells from the single-domain cells.
  Planned location: `/app/data/dense/resume.ckpt` + `/app/data/eval/slice_*.txt` + `eng/rank/src/seat.rs`.
  Why instruction must not reveal it: Docs state that those snapshot fields describe that dense run; the seating consequence is the discovery.

- Discovery: The workspace re-seats parts of itself from its own seed material on every rebuild until the recorded pass is the scoring pass and the receipt describes the generation the registry resolves. One-pass source edits are undone by the verifier's rebuild.
  Planned location: `eng/core/build.rs` + `eng/rank/build.rs` + `calib/eval_pass.toml` + `calib/mask_bind.accept`.
  Why instruction must not reveal it: Desk notes state the re-seating and what the receipt names as outcomes; the coupling to the registry resolution is the discovery.

### Anti-trivialization verdict
1 Disclosure-collapse: PASS — outcomes documented; propagation, moment and receipt algebra not.
2 Hidden-instance: PASS — six-scenario matrix over two starts × three domain mixes.
3 Single-artifact: PASS — seven coupled loci across four crates plus desk state.
4 Generalization: PASS — novel durable generation inject moves geometry and accuracy together.
5 Prompt-honesty: PASS — symptoms and outcomes, no fix-site naming.
6 Cheating-vs-difficulty: PASS — rebuild and byte-identical republish are anti-cheat beside real recovery work.
7 Mechanical-fix: PASS.
8 Localized-fix: PASS — measured single-locus regressions all score 0.
9 Oracle-locality: PASS — four crates + two desk files.
10 Small declarative-cluster: PASS — engine numerics dominate; the receipt alone leaves 9/13 failing.
11 Grep-collapse: PASS — `budget`/`tally`/`fit`/`refit`/`settled`/`run` carry no instruction stems.
12 Pre-factored-helper: PASS — decoys rhyme (`load.rs`, `legacy.ckpt`, `trace_pref.toml`); no correct idiom left in an unused helper.
13 Recipe-discount: PASS — structured pruning recovery with resume parity is not textbook CRUD.
14 Security-aura: N/A (ML).
15 Orthogonal-checklist: PASS — generation choice moves geometry, sparsity and accuracy together.
16 Harness-discount: PASS.
17 One-pass solvability: PASS — captured-sweep bait plus rebuild authority.
18 Hard-only: PASS (target).
19 Discovery budget: PASS (5).
20 Instruction specificity: symptoms-only (collapse_check RC6 PASS, 0 families).
21 Topology distribution: PASS (see below).

### Topology enumeration (3 candidate fix topologies)
1. Generation × geometry × seating (`tip.rs` / `span.rs` / `seat.rs`) — bands still fail without re-fitting.
2. Statistics × classifier recovery × classifier columns (`gauge/lib.rs` / `head.rs` / `draw.rs`) — sparsity, multiply share and reported generation still wrong.
3. Desk receipt × seeds (`calib/` + `seeds/`) — rebuild stops clobbering, but every metric stays broken.

### Rubric axes
- Verifiable: Pass — deterministic JSON, recomputed expectations, rebuild + republish.
- Well-specified: Pass — report schema and bands are documented; graded outcomes named.
- Solvable: Pass — expert estimate 150 min; finite Rust surface, no network.
- Difficult: Pass — coupled generation × geometry × re-fit × resume parity.
- Interesting: Pass — real pruned-model recovery evaluation.
- Outcome-verified: Pass — the published report is graded, not the process.

### Hardness axes
- Discover: which generation scores, that geometry propagates, that re-fitting is two operations, that a resume snapshot is not an authority, that rebuilds re-seat.
- Synthesize: registry + rosters + snapshots + calibration shards + slices + layout.
- Diagnose: bands and partner disagreement as symptoms, without cause names.
- Navigate coupling: a wrong generation moves geometry and accuracy; single-domain calibration only shows up in the mixed cells.
- Reason beyond training: structured-mask recovery with recorded-anchor classifier refitting, not a generic pruning tutorial.

### Instruction completeness test
No — the instruction alone does not name the resolved generation, the propagation rule, the two re-fitting operations, the resume-snapshot polarity, or the receipt coupling. The agent must read the frozen materials and observe desk behavior.

## Reviewer Appendix

### Implementation plan
Ship a Rust evaluation workspace (`core`/`gauge`/`rank`/`emit`) whose shipped bodies are plausible-wrong: geometry reads the dense layout for fan-in and the dense tail for the classifier width; the classifier gathers weight columns by compacted position; statistics are measured by forwarding the dense stack and slicing afterwards; classifier recovery matches the recorded location but not the recorded spread; roster resolution takes the newest non-retired row of any state; seating re-seats a resume scenario on its own snapshot stamp, reuses the statistics that snapshot carries, and calibrates on the first domain only. `core/build.rs` and `rank/build.rs` rematerialize those surfaces from `seeds/` on every build until `calib/eval_pass.toml` records the scoring pass and `calib/mask_bind.accept` matches the registry-resolved generation. The oracle resolves the generation from the registry, writes the pass and receipt, patches the two small-diff files, rewrites the four larger bodies, syncs the seeds, and re-runs the entrypoint.

### Proposed file inventory
Matches the authoring Initial Draft Commitments (53 environment files excluding Docker files).

### Oracle notes
`solve.sh` derives the bound generation, epoch and kept-channel count from `tip_journal.jsonl` / `retired_tips.jsonl` / the roster sheet; writes `calib/eval_pass.toml` and `calib/mask_bind.accept`; patches `core/src/draw.rs` and `rank/src/tip.rs` in place (small semantic diffs, kept out of whole-file rewrites for GX2); rewrites `core/src/span.rs`, `gauge/src/lib.rs`, `gauge/src/head.rs` and `rank/src/seat.rs`; copies the seated sources over the seed material; then runs `/app/scripts/run_prune_eval.sh`. Every step is idempotent, so ablation re-runs are safe.

### Collapse audit
Stage: pre-submission (Attempt 1)
Smallest plausible successful patch: resolve the generation, write pass + receipt, and correct geometry propagation, classifier column gathering, statistics fitting, classifier recovery and per-scenario seating (~56 lines of real semantic diff across six surfaces, or the equivalent rewrite of the seed material after discovering the rebuild authority).
Likely editable frontier: `eng/core/src/{span,draw}.rs`, `eng/gauge/src/{lib,head}.rs`, `eng/rank/src/{tip,seat}.rs` (or the four seed files) + `calib/`.
Requirement-to-file map: reported generation → `tip.rs`; sparsity/multiply share → `span.rs`; accuracy → `draw.rs` + `gauge/lib.rs` + `gauge/head.rs`; partner agreement and mixed cells → `seat.rs`; durability of any fix → `calib/` receipt + pass.
Oracle estimated complexity: 223 non-boilerplate transitive LOC; 56 lines of real added+removed diff across 6 targets.
Red flags: collapse_check WARNs — RC2 predictability 67% (domain-named directories `calib`/`gauge`/`rank`; no answer-shaped tokens), CR9 two orphan "fields" that are verifier-local variables (`published_raw`, `rebuilt_raw`), GX3 borderline 56 lines (polarity-class fixes are inherently compact; the frontier is coupling, not volume), GX7 six orphan literals that are verifier staging names deliberately kept out of solver-visible docs.
Measured strategy matrix: oracle 13/13 pass (harbor reward 1.000); NOP 0.000; correct sources + stale receipt 9/13 fail; receipt only 9/13 fail; single-locus regressions from the oracle tree — geometry 3 fail, classifier columns 8, statistics 8, classifier recovery 8, roster resolution 8, seating 9.
Residual hardness: registry resolution against overlay and retired baits; geometry propagation; two-part re-fitting; resume-snapshot polarity; domain coverage in mixed cells; rebuild re-seating authority; novel-generation generalization.
Collapse verdict: PASS with four justified WARNs.

### Naming-pass record

**Instruction nouns extracted:**
recover, pruned, model, published, bands, evaluation, desk, scores, classifier, accuracy, sparsity, reaches, multiply, share, geometry, denser, stack, scenarios, roster, schema_tag, scenarios, bands_ok, fields, band, cold, resume, partner, generation, snapshots, masks, registry, calibration, slices, inputs, outputs, workspace, rebuilt, entrypoint, report, byte-identical, captured, sweep, healthy

**Renames during drafting:**
- `span::share` → `span::reach` → `span::budget`: `share` and then `reaches` collide with instruction nouns.
- `gauge::Bands` → `gauge::Norms`: avoid instruction noun `bands`.
- `gauge::sweep` → `gauge::drive`: avoid instruction noun `sweep`.
- `gauge::head::recover` → `gauge::head::refit`: avoid instruction verb `recover`.
- `rank::seat::snapshot` → `rank::seat::start_ckpt`: avoid instruction noun `snapshots`.
- `rank::seat::held_bands` → `rank::seat::held_norms`: avoid instruction noun `bands` (removed entirely by the oracle).

**Test names audited:**
- test_frozen_inputs_integrity
- test_report_schema_and_scenario_order
- test_mask_tip_is_bound_durable_generation
- test_mask_tip_is_not_rolled_back_or_proposed_roster
- test_geometry_is_that_of_the_bound_roster
- test_cold_and_resume_partners_agree
- test_first_domain_scenarios_match_faithful_pass
- test_second_domain_scenarios_match_faithful_pass
- test_mixed_domain_scenarios_match_faithful_pass
- test_all_scenarios_inside_published_bands
- test_published_numbers_are_not_the_captured_sweep
- test_entrypoint_republish_is_byte_identical
- test_novel_durable_roster_moves_the_report

**Concentration math:**
- Total tests: 13
- A `span.rs`: 3/13 = 0.23
- B `draw.rs`: 3/13 = 0.23
- C `gauge/lib.rs`: 2/13 = 0.15
- D `gauge/head.rs`: 2/13 = 0.15
- E `tip.rs`: 3/13 = 0.23
- F `seat.rs`: 3/13 = 0.23
- G `calib/mask_bind.accept`: 2/13 = 0.15 (required transitively by every metric test via the rebuild)
- Cap: 0.5. Max ratio observed: 0.23. Status: PASS

### Per-test feasibility pre-check
- test_frozen_inputs_integrity — checksum of frozen inputs — 1 approach — no ambiguity — LOW
- test_report_schema_and_scenario_order — schema keys and ids — 2+ — no — LOW
- test_mask_tip_is_bound_durable_generation — registry resolution equality — 2+ — documented states — MEDIUM
- test_mask_tip_is_not_rolled_back_or_proposed_roster — rejects retired and staged generations — 2+ — documented rollback ledger — MEDIUM
- test_geometry_is_that_of_the_bound_roster — recomputed propagation (1e-9) — 2+ — propagation is the discovery — MEDIUM
- test_cold_and_resume_partners_agree — 1e-4 partner agreement plus non-degeneracy — 2+ — documented tolerance — MEDIUM
- test_first_domain_scenarios_match_faithful_pass — independent recovery pass — 2+ — anchors shipped in the snapshot — MEDIUM
- test_second_domain_scenarios_match_faithful_pass — same on the second domain — 2+ — no — MEDIUM
- test_mixed_domain_scenarios_match_faithful_pass — same on mixed slices — 2+ — slice domain lists shipped — MEDIUM
- test_all_scenarios_inside_published_bands — band membership + `bands_ok` — 2+ — bands documented — MEDIUM
- test_published_numbers_are_not_the_captured_sweep — anti-copy of the healthy fixture — 1 — no — LOW
- test_entrypoint_republish_is_byte_identical — rebuild + two runs — 2+ — documented — MEDIUM
- test_novel_durable_roster_moves_the_report — verifier-owned novel generation — 2+ — documented that an unseen generation must move the report — MEDIUM
