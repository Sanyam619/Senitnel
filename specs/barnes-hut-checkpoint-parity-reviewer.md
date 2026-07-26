### Decision
GO — Attempt 1. Scientific-computing campaign-parity contract (Barnes–Hut N-body) with three coupled loci; opaque symbol table; hard macroscopic-invariant tests; goal-first framing for category alignment.

### Metadata
- Task name: barnes-hut-checkpoint-parity
- Title: Barnes Hut Campaign Parity
- Category: scientific-computing
- Languages: [Go, C]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [nbody, barnes-hut, conservation, checkpoint, reductions]
- Milestones: 0

### Discovery budget
- Discovery: Run-manifest opening angle / softening is overridden by compile-time buildmeta constants on the active path.
  Planned location: `environment/internal/policy/pick.go` + `environment/internal/buildmeta/const.go`
  Why instruction must not reveal it: Naming the authority split collapses diagnosis to a one-line precedence flip.

- Discovery: Snapshot encode packs ghost/owned strips on the orthogonal axis relative to live partition halo exchange, so resume remaps boundary particles incorrectly while interiors stay plausible.
  Planned location: `environment/internal/snap/encode.go` vs `environment/internal/partition/halo.go`
  Why instruction must not reveal it: Pointing at packing layout turns the task into a named-format repair.

- Discovery: Macroscopic fold includes ghost particles (or associates by worker id), so worker count changes mass/momentum_L2 even with identical physics.
  Planned location: `environment/internal/reduce/fold.go`
  Why instruction must not reveal it: Stating the fold defect removes the domain-decomposition reasoning the task measures.

### Anti-trivialization verdict
1 Disclosure-collapse: PASS — honest goal/band list still requires tracing three authorities.
2 Hidden-instance: PASS — every bundled case is affected by the same systemic couplings.
3 Single-artifact repair: PASS — three coordinated loci required.
4 Generalization: PASS — three cases × worker × mode matrix.
5 Prompt-honesty: PASS — goal-first / symptoms-only; no fix recipe.
6 Cheating-vs-difficulty: PASS — difficulty is numerical coupling, not anti-cheat.
7 Mechanical-fix filter: PASS — N/A at idea stage.
8 Localized-fix: PASS — distributed across policy/snap/reduce.
9 Oracle-locality: PASS — three files minimum.
10 Small declarative-cluster: PASS — not a config table fill.
11 Grep-collapse: PASS — opaque symbols; instruction nouns banned on fix path.
12 Pre-factored-helper: PASS — helpers named op_a/pack_b/fold_c.
13 Recipe-discount: PASS — not “implement Barnes–Hut from textbook.”
14 Security-aura: PASS — N/A.
15 Orthogonal-checklist: PASS — loci interact.
16 Harness-discount: PASS — Docker is realism only.
17 One-pass solvability: PASS — requires runtime experiments across worker/resume matrix.
18 Hard-only gate: PASS.
19 Discovery budget: PASS — three items above.
20 Instruction specificity: PASS — goal/symptoms-only planned (no θ algebra dump).
21 Topology distribution: PASS — three topologies below.

### Topology enumeration (3 candidate fix topologies)
1. **Authority-first**: policy pick + snap pack + reduce fold — chosen realization. No single locus sufficient because attractor, resume parity, and worker spread are separately gated.
2. **Exchange-first**: rewrite live halo to match broken pack + policy + fold — still ≥3 sites; matching broken pack into live exchange would break cold-start interiors unless pack is also corrected.
3. **Report-side compensation**: synthesize corrected macros in report emit + leave kernels wrong — fails conservation recomputation and package-driven parity tests; would still need snap/policy/reduce if report is honest.

### Rubric axes
1 Verifiable: Pass — deterministic JSON + numeric bands + rebuild-from-source.
2 Well-specified: Pass — schema in docs + instruction field list.
3 Solvable: Pass — expert HPC/astro numerics engineer in a few hours.
4 Difficult: Pass — coupled checkpoint×decomposition×reduction, not undergrad N-body homework.
5 Interesting: Pass — real campaign parity pain for tree codes.
6 Outcome-verified: Pass — macroscopic report, not process.

### Hardness axes
- Discover: Must find manifest vs buildmeta conflict, pack axis mismatch, fold ghost inclusion from code/runtime.
- Synthesize: Policy, snapshot, and reduction must agree.
- Diagnose: Instruction states goal/bands, not causes.
- Navigate coupling: Fixing one locus leaves other test clusters red.
- Reason beyond training: Not “implement Barnes–Hut from a textbook”; checkpoint×decomposition×reduction coupling is out-of-distribution as a unit.

### Instruction completeness test
No — instruction.md alone does not name which authority wins, how snapshot bytes are laid out, or how folds must associate. The agent must read and experiment on the Go/C tree.

## Reviewer Appendix

### Implementation plan
Ship a compact Barnes–Hut N-body campaign in Go with a small C force kernel (cgo), strip domain decomposition, mid-run snapshot, and campaign driver producing `/output/campaign-report.json`. Seed three intentional divergences: `op_a` prefers buildmeta over manifest; `pack_b` packs the orthogonal halo axis; `fold_c` sums ghost particles. Oracle rewrites those three bodies. Verifier asserts cold/resume and cross-worker macroscopic agreement, mass closure, attractor band, and parity block consistency, rebuilding from source each time.

### Proposed file inventory
Matches authoring Initial Draft Commitments (≥28 environment files excl. Dockerfile). Distinct from `lattice-boltzmann-checkpoint-drift` (tree/particles/C kernel vs D2Q9 lattice).

### Oracle notes
`solve.sh` patches `op_a` to prefer manifest blob when fields disagree; rewrites `pack_b` to pack along the live partition axis (`ax`); rewrites `fold_c` to sum only interior particles in stable global order. Rebuilds and runs `run_campaign.sh`.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
Coordinate three non-local functions so manifest physics, snapshot halo layout, and interior-only fold agree — not a one-liner.

Likely editable frontier:
- internal/policy/pick.go
- internal/snap/encode.go
- internal/reduce/fold.go
- possibly decode.go if pack/decode pairing must match

Requirement-to-file map:
- wrong attractor / energy band -> policy/pick.go
- cold/resume gap -> snap/encode.go
- worker spread / mass -> reduce/fold.go

Oracle estimated complexity: 80–140 non-boilerplate lines across solve.sh patches

Red flags:
- Do not clone LBM instruction symptom-first lead (“disagree… shifts…”) — use goal-first conservation/agreement lead for category_classifier
- Keep distinct case names/physics from LBM to avoid Similarity collision

Residual hardness:
Even with the tree visible, the solver must determine which of several similar-looking policy/pack/fold helpers is authoritative and how they couple under resume×workers.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
n-body, barnes, hut, campaign, multipole, treecode, mid-run, snapshots, multi-worker, domain, splits, conserved, observables, numerical, agreement, bands, checkpoint, resume, worker, counts, force, accuracy, reduction, ordering, cases, macroscopic, quantities, cold, resumed, modes, report, schema_tag, label, workers, mode, energy, momentum_L2, mass, stable, parity, cold_resume_max_rel, worker_spread_max_rel, manifests, compile-time, defaults, opening, angle, softening

**Renames during drafting:**
- `ModeBlob` → `blobX`: instruction noun "mode"
- `Partial` → `PartY`: avoid domain jargon telegraph
- `Aggregate` → `AggZ`: avoid "mass" clustering on fix path
- ghost width param → `g`: keep params opaque
- axis → `ax`: avoid partition-axis telegraph

**Test names audited:**
- test_schema_surface
- test_pair_gap_energy
- test_pair_gap_mom
- test_span_mass
- test_span_mom
- test_integral_closed
- test_finite_rows
- test_gap_block
- test_band_energy
- test_label_matrix

**Concentration math:**
- Total tests across `flipping_point_contract`: 10
- Per location:
  - L1 (`environment/internal/policy/pick.go`): 3/10 = 0.30
  - L2 (`environment/internal/snap/encode.go`): 3/10 = 0.30
  - L3 (`environment/internal/reduce/fold.go`): 4/10 = 0.40
- Cap: 0.5. Max ratio observed: 0.40. Status: PASS

### Per-test feasibility pre-check
- test_schema_surface: schema keys — 2+ approaches — not chain-dependent — LOW
- test_pair_gap_energy: cold/resume energy — 2+ — no — MEDIUM
- test_pair_gap_mom: cold/resume momentum — 2+ — no — MEDIUM
- test_span_mass: worker mass — 2+ — no — MEDIUM
- test_span_mom: worker momentum — 2+ — no — MEDIUM
- test_integral_closed: conservation — 2+ — no — LOW
- test_finite_rows: stable flags — 2+ — no — LOW
- test_gap_block: parity recompute — 2+ — depends on report honesty — MEDIUM
- test_band_energy: attractor band — 2+ — no — HIGH if band too tight (set from manifest-vs-buildmeta separation)
- test_label_matrix: coverage — 2+ — no — LOW

### Draft instruction.md (Step 2b must humanize; keep goal-first)

```
Complete an N-body Barnes-Hut campaign so its conserved observables satisfy documented numerical-agreement bands across checkpoint/resume and across domain-split worker counts. The campaign under /app advances bundled cases with a multipole treecode, mid-run snapshots, and parallel domain decomposition; correctness means energy, total momentum, and mass closure stay within the bands in /app/docs/report-schema.md whether a case runs cold, resumes from a snapshot, or is split across 1, 2, or 4 workers (force accuracy and reduction ordering must keep results worker-independent).

Drive /app/scripts/run_campaign.sh over every case in /app/data/cases/ and write /output/campaign-report.json with schema_tag nbody-campaign-v1: one row per (case, workers, mode) carrying label, workers, mode, energy, momentum_L2, mass, and stable, plus a parity object with cold_resume_max_rel and worker_spread_max_rel. The verifier rebuilds /app/cmd/campaign from source and re-invokes internal packages with its own inputs, so reports must come from the real solver. When run manifests under /app/config/manifests/ and compile-time defaults disagree on a physics knob, the manifest is authoritative for the observables you report.
```

### Form paste (Idea Proposal — already cleared / for handoff)

**Idea Category:** Scientific Computing

Task Idea Summary:
```
Complete an N-body Barnes-Hut campaign so its conserved observables satisfy documented numerical-agreement bands across checkpoint/resume and across domain-split worker counts. The campaign under /app advances bundled cases with a multipole treecode, mid-run snapshots, and parallel domain decomposition; correctness means energy, total momentum, and mass closure stay within the bands in /app/docs/report-schema.md whether a case runs cold, resumes from a snapshot, or is split across 1, 2, or 4 workers (force accuracy and reduction ordering must keep results worker-independent). Drive /app/scripts/run_campaign.sh over every case in /app/data/cases/ and write /output/campaign-report.json with schema_tag nbody-campaign-v1: one row per (case, workers, mode) carrying label, workers, mode, energy, momentum_L2, mass, and stable, plus a parity object with cold_resume_max_rel and worker_spread_max_rel. The verifier rebuilds /app/cmd/campaign from source and re-invokes internal packages with its own inputs, so reports must come from the real solver. When run manifests under /app/config/manifests/ and compile-time defaults disagree on a physics knob, the manifest is authoritative for the observables you report.
```

Associated Skills:
```
Barnes-Hut treecodes; multipole acceptance criteria; N-body energy/momentum conservation; checkpoint/resume fidelity; domain-decomposition reductions and floating-point associativity; numerical agreement bands; scientific campaign reports
```

Task Tags:
```
nbody, barnes-hut, conservation, checkpoint, reductions
```
