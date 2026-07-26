### Decision
GO — Attempt 1. Same decision line as the authoring spec.

### Metadata
- Task name: diffusion-cfg-sampler-tip-recalibration
- Title: Diffusion CFG Recalibration
- Category: machine-learning
- Languages: ["rust"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["diffusion", "cfg-scale", "sampler", "checkpoint-resume", "fid", "clip-score"]
- Milestones: 0

### Discovery budget
- Discovery: Resolved serving tip is tip_g7 (idx 6), not newest durable tip_g9 (retired) or newest-any tip_live (idx 9).
  Planned location: data/feature_registry/{tip_journal,retired_tips}.jsonl + knot_r
  Why instruction must not reveal it: naming the tip id collapses tip resolution to transcription.
- Discovery: Durable schedule sheet is a7 with cfg=7.5 / sampler=dpmpp_2m; live sheet w2 seats euler_short.
  Planned location: data/sched/table_{a7,w2}.toml + facet_q sheet family selection
  Why instruction must not reveal it: would turn CFG/sampler into a checklist paste.
- Discovery: Trial selection or mismatched tip_bind rematerializes all four seating surfaces on cargo build.
  Planned location: calib/trial_pref.toml + tip_bind.accept + dual build.rs
  Why instruction must not reveal it: naming the gate files as the fix collapses SoftHSM hardness.
- Discovery: Resume CKP2 VAE block coefficients must always scale rows (not only when coef > 1).
  Planned location: core/src/lens.rs
  Why instruction must not reveal it: cause-revealing; instruction states resume parity symptom only.
- Discovery: Mix cells honor tip weft_c/weft_d rosters, not fold-all.
  Planned location: core/src/weave.rs + journal weft fields
  Why instruction must not reveal it: would map mix failures to one function.

### Anti-trivialization verdict
Checks 1–21 pass under SoftHSM dual rematerialize + multi-step tip + coupled CFG×sampler×VAE×mix. Discovery budget ≥3; topology ≥3; symptoms-only instruction; hard-only gate PASS.

### Topology enumeration (3 candidate fix topologies)
1. Calib-first: clear selection+bind, then fix knot/facet/lens/weave — no single location greens majority.
2. Metrics-first: fix lens+weave for parity/mix, still fail tip/cfg until knot+facet+calib.
3. Schedule-first: fix facet CFG/sampler, still fail tip_epoch/parity/mix/republish without knot/lens/weave/calib.

### Rubric axes
Verifiable Pass; Well-specified Pass; Solvable Pass; Difficult Pass; Interesting Pass; Outcome-verified Pass.

### Hardness axes
Discover/Synthesize/Diagnose/Navigate coupling/Reason beyond training — all satisfied via tip lattice × schedule × VAE × mix × rematerialize.

### Instruction completeness test
No — instruction alone does not name tip_g7, schedule values, VAE coef rule, or rematerialize gate files; agent must engage the codebase.

## Reviewer Appendix

### Implementation plan
Rust diffusion eval desk under /app/eng with SoftHSM calib gate; broken seating seeds; ML eval framing under calib/eval.

### Proposed file inventory
Matches Initial Draft Commitments in authoring spec (≥20 environment files).

### Oracle notes
Set selection=serving, tip_bind=tip_g7; rewrite lens/knot/facet/weave bodies; run entrypoint.

### Collapse audit
Stage: implementation-plan
Smallest plausible successful patch: five coordinated edits (calib pair + four seating bodies).
Likely editable frontier: knot, facet, lens, weave, calib.
Requirement-to-file map: tip→knot; cfg/sampler→facet; resume→lens; mix→weave; republish durability→calib+build.rs.
Oracle estimated complexity: ~120 non-boilerplate lines.
Red flags: none if rematerialize covers all four surfaces.
Residual hardness: multi-step tip + schedule sheet family + VAE + mix + gate.
Collapse verdict: PASS

### Naming-pass record
**Instruction nouns extracted:** (see code_forbidden_tokens)
**Renames during drafting:** None — first-pass naming used opaque knot/facet/lens/weave.
**Test names audited:** test_j2_pyrite, test_k4_agate, test_p7_jasper, test_w1_topaz, test_v8_lazuli, test_q1_flint, test_r3_garnet, test_t6_beryl, test_m5_onyx, test_g6_coral, test_h3_umber, test_d9_quartz, test_n8_zircon
**Concentration math:** Total graded controls ~13; max location share ≤0.4; Cap 0.5 PASS.

### Per-test feasibility pre-check
All mineral tests: valid approaches 1–2; chain-dependent only where noted; feasibility LOW–MEDIUM.
