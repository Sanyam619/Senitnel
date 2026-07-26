### Decision
GO — Attempt 1. Symptoms-only scientific-computing contract; three coupled fix loci; opaque symbol table; hard macroscopic-invariant tests with no repair/debug framing.

### Metadata
- Task name: lattice-boltzmann-checkpoint-drift
- Title: Lattice Boltzmann Checkpoint Drift
- Category: scientific-computing
- Languages: [Go]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [lbm, cfd, checkpoint, go, numerical, reduction]
- Milestones: 0

### Discovery budget
- Discovery: Run manifest omega/fold preference is overridden by compile-time buildmeta constants on the active path.
  Planned location: `environment/internal/policy/pick.go` + `environment/internal/buildmeta/const.go`
  Why instruction must not reveal it: Naming the authority split collapses diagnosis to a one-line precedence flip.

- Discovery: Snapshot encode packs ghost strips on the orthogonal axis relative to live partition halo exchange, so resume remaps boundary populations incorrectly while interiors stay plausible.
  Planned location: `environment/internal/snap/encode.go` vs `environment/internal/partition/halo.go`
  Why instruction must not reveal it: Pointing at packing layout turns the task into a named-format repair.

- Discovery: Macroscopic fold includes ghost cells (or associates by worker id), so worker count changes mass/mean_rho even with identical physics.
  Planned location: `environment/internal/reduce/fold.go`
  Why instruction must not reveal it: Stating the fold defect removes the domain-decomposition reasoning the task measures.

### Anti-trivialization verdict
1 Disclosure-collapse: PASS — honest symptom list still requires tracing three authorities.
2 Hidden-instance: PASS — every bundled case is affected by the same systemic couplings.
3 Single-artifact repair: PASS — three coordinated loci required.
4 Generalization: PASS — three cases × worker matrix.
5 Prompt-honesty: PASS — symptoms-only.
6 Cheating-vs-difficulty: PASS — difficulty is numerical coupling, not anti-cheat.
7 Mechanical-fix filter: PASS — N/A at idea stage.
8 Localized-fix: PASS — distributed across policy/snap/reduce.
9 Oracle-locality: PASS — three files minimum.
10 Small declarative-cluster: PASS — not a config table fill.
11 Grep-collapse: PASS — opaque symbols; instruction nouns banned on fix path.
12 Pre-factored-helper: PASS — helpers named op_a/pack_b/fold_c.
13 Recipe-discount: PASS — not textbook LBM implement-from-spec.
14 Security-aura: PASS — N/A.
15 Orthogonal-checklist: PASS — loci interact.
16 Harness-discount: PASS — Docker is realism only.
17 One-pass solvability: PASS — requires runtime experiments across worker/resume matrix.
18 Hard-only gate: PASS.
19 Discovery budget: PASS — three items above.
20 Instruction specificity: PASS — symptoms-only planned.
21 Topology distribution: PASS — three topologies below.

### Topology enumeration (3 candidate fix topologies)
1. **Authority-first**: policy pick + snap pack + reduce fold — chosen realization. No single locus sufficient because attractor, resume parity, and worker spread are separately gated.
2. **Exchange-first**: rewrite live halo to match broken pack + policy + fold — still ≥3 sites; matching broken pack into live exchange would break cold-start interiors unless pack is also corrected.
3. **Report-side compensation**: synthesize corrected macros in report emit + leave kernels wrong — fails conservation recomputation and field-driven parity tests; would still need snap/policy/reduce if report is honest.

### Rubric axes
1 Verifiable: Pass — deterministic JSON + numeric bands.
2 Well-specified: Pass — schema in docs + instruction.
3 Solvable: Pass — expert CFD/HPC engineer in a few hours.
4 Difficult: Pass — coupled numerical policies, not undergrad LBM homework.
5 Interesting: Pass — real checkpoint/resume CFD ops pain.
6 Outcome-verified: Pass — macroscopic report, not process.

### Hardness axes
- Discover: Must find manifest vs buildmeta conflict, pack axis mismatch, fold ghost inclusion from code/runtime.
- Synthesize: Policy, snapshot, and reduction must agree.
- Diagnose: Instruction states symptoms only.
- Navigate coupling: Fixing one locus leaves other test clusters red.
- Reason beyond training: Not "implement LBM from textbook"; checkpoint×decomposition×reduction coupling is out-of-distribution as a unit.

### Instruction completeness test
No — instruction.md alone does not name which authority wins, how bytes are laid out, or how folds must associate. The agent must read and experiment on the Go tree.

## Reviewer Appendix

### Implementation plan
Ship a compact D2Q9 BGK solver in Go with strip domain decomposition, mid-run snapshot, and campaign driver producing `/output/campaign-report.json`. Seed three intentional divergences: `op_a` prefers buildmeta over manifest; `pack_b` packs the orthogonal halo axis; `fold_c` sums ghost cells. Oracle rewrites those three bodies. Verifier asserts cold/resume and cross-worker macroscopic agreement, mass closure, attractor band, and parity block consistency.

### Proposed file inventory
Matches authoring Initial Draft Commitments (28 environment files excl. Dockerfile).

### Oracle notes
`solve.sh` patches `op_a` to prefer manifest blob when fields disagree; rewrites `pack_b` to pack along the live partition axis (ax); rewrites `fold_c` to sum only interior cells in global raster order. Rebuilds and runs `run_campaign.sh`.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
Coordinate three non-local Go functions so manifest physics, snapshot halo layout, and interior-only spatial fold agree — not a one-liner.

Likely editable frontier:
- internal/policy/pick.go
- internal/snap/encode.go
- internal/reduce/fold.go
- possibly decode.go if pack/decode pairing must match

Requirement-to-file map:
- wrong attractor -> policy/pick.go
- cold/resume gap -> snap/encode.go
- worker spread / mass -> reduce/fold.go

Oracle estimated complexity: 80–140 non-boilerplate lines across solve.sh patches

Red flags:
- none if opaque naming held

Residual hardness:
Even with the tree visible, the solver must determine which of several similar-looking policy/pack/fold helpers is authoritative and how they couple under resume×workers.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
lattice, fluid, campaign, bundled, cases, mid-run, snapshots, multi-worker, domain, splits, resumed, campaigns, bulk, observables, uninterrupted, cold, starts, physics, config, worker, count, macroscopic, quantities, report, schema_tag, cases, parity, label, workers, mode, mean_rho, mom_x, mom_y, ke, mass, stable, cold_resume_max_rel, worker_spread_max_rel, agreement, closure, bit, identity, cell

**Renames during drafting:**
- `ModeBlob` → `blobX`: instruction noun "mode"
- `Partial` → `partY`: avoid domain jargon telegraph
- `Aggregate` → `aggZ`: avoid "mass" field clustering on fix path
- `ghost` param → `g`: instruction may mention boundary layers; keep params opaque
- `axis` → `ax`: avoid partition-axis telegraph

**Test names audited:**
- test_schema_surface
- test_cold_resume_mom
- test_cold_resume_ke
- test_worker_rho_spread
- test_worker_mass_spread
- test_mass_closed
- test_stable_all_rows
- test_parity_block
- test_wrong_attractor_rejected
- test_all_labels_present

Note: several test names contain instruction nouns (cold, resume, worker, mass, parity). Rename before ship to:
- test_schema_surface
- test_pair_gap_mx
- test_pair_gap_ke
- test_span_rho
- test_span_integral
- test_integral_closed
- test_finite_rows
- test_gap_block
- test_band_mx
- test_label_matrix

**Concentration math:**
- Total distinct tests in flipping_point_contract union: 8 unique (schema/finite/label_matrix may be uncontrolled by A/B/C — attach schema to A lightly or leave as always-on smoke). Adjust contract so union covers all graded tests and no location >50%.
- Recheck at construction: A≤3/10, B≤3/10, C≤4/10.

### Per-test feasibility pre-check
- test_schema_surface: schema keys — 2+ approaches — not chain-dependent — LOW
- test_pair_gap_mx: cold/resume mom — 2+ — no — MEDIUM
- test_pair_gap_ke: cold/resume ke — 2+ — no — MEDIUM
- test_span_rho: worker rho — 2+ — no — MEDIUM
- test_span_integral: worker mass — 2+ — no — MEDIUM
- test_integral_closed: conservation — 2+ — no — LOW
- test_finite_rows: stable flags — 2+ — no — LOW
- test_gap_block: parity recompute — 2+ — depends on report honesty — MEDIUM
- test_band_mx: attractor band — 2+ — no — HIGH if band too tight
- test_label_matrix: coverage — 2+ — no — LOW
