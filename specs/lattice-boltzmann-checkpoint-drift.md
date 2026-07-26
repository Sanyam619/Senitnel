### Decision
GO — Attempt 1. Symptoms-only scientific-computing contract; three coupled fix loci (policy authority, checkpoint halo packing, spatial reduction); opaque symbol table; hard macroscopic-invariant tests with no repair/debug framing.

### Metadata
- version: 2
- Task name: lattice-boltzmann-checkpoint-drift
- Title: Lattice Boltzmann Checkpoint Drift
- Category: scientific-computing
- Languages: [Go]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: [lbm, cfd, checkpoint, go, numerical, reduction]
- Milestones: 0

## Authoring Brief

### Public contract

A Go D2Q9 lattice-Boltzmann campaign runner under `/app` advances fluid cases with mid-run snapshots and multi-worker domain splits. Campaigns that resume from snapshots exit cleanly and look numerically stable, yet bulk fluid observables disagree with uninterrupted cold starts. The same physics config under different worker counts also shifts those observables.

The agent must bring the campaign runner to a state where, for every bundled case under `/app/data/cases/`, cold-start and resume paths agree on macroscopic quantities, and worker-count changes do not move those quantities beyond the documented relative band. Emit `/output/campaign-report.json` with:

- `schema_tag` (string) — value documented in `/app/docs/report-schema.md`
- `cases` (array) — one object per (label, workers, mode) run with fields `label`, `workers`, `mode`, `mean_rho`, `mom_x`, `mom_y`, `ke`, `mass`, `stable`
- `parity` (object) with `cold_resume_max_rel` and `worker_spread_max_rel` (floats)

Grading recomputes relative spreads from the report and asserts conservation / stability / cross-mode agreement. Bit-identical per-cell fields are not the success metric.

### Failure topology

Cluster A: resume vs cold disagree on momentum / kinetic energy while both remain finite — snapshot bytes encode a halo layout that does not match live partition exchange. Cluster B: worker count changes mean density / mass while physics config is unchanged — aggregate fold includes ghost strips or associates partials in partition order. Cluster C: both paths are stable but absolute momentum sits on the wrong attractor — collision relaxation is taken from the compile-time build meta instead of the run manifest.

These interact: fixing only packing can make resume match a cold start that still used the wrong relaxation; fixing only policy leaves worker-dependent mass; fixing only reduction leaves resume boundary layers wrong. The agent must coordinate all three authorities.

### Environment shape

- **`environment/cmd/campaign/`** — CLI entry that drives cold and resume campaigns.
- **`environment/internal/lattice/`** — collide / stream / init kernels (working physics primitives).
- **`environment/internal/partition/`** — domain strip splits and live halo exchange.
- **`environment/internal/snap/`** — snapshot encode/decode (fix locus B).
- **`environment/internal/policy/`** — run-manifest vs build-meta resolution (fix locus A).
- **`environment/internal/reduce/`** — macroscopic fold (fix locus C).
- **`environment/internal/report/`** — JSON emission.
- **`environment/internal/decoy/`** — genuine non-fix helpers that rhyme with fix symbols.
- **`environment/internal/buildmeta/`** — compile-time constants that disagree with manifests.
- **`environment/config/manifests/`** — per-case run manifests.
- **`environment/data/cases/`** — case grids / forcing params.
- **`environment/scripts/`** — campaign driver the agent invokes.
- **`environment/docs/`** — report schema.

### Required artifacts

- `tasks/lattice-boltzmann-checkpoint-drift/instruction.md`
- `tasks/lattice-boltzmann-checkpoint-drift/task.toml` — category `scientific-computing`, languages `["go"]`, `allow_internet = false`
- `tasks/lattice-boltzmann-checkpoint-drift/output_contract.toml`
- `tasks/lattice-boltzmann-checkpoint-drift/environment/Dockerfile` + `.dockerignore`
- `tasks/lattice-boltzmann-checkpoint-drift/tests/test.sh` + `test_outputs.py` (≥8 hard tests)
- `tasks/lattice-boltzmann-checkpoint-drift/solution/solve.sh`
- Full environment tree per Initial Draft Commitments (25+ substantive files)

### Test plan

1. **test_schema_surface** — report exists; schema_tag and required top-level keys; case row keys exact.
2. **test_pair_gap_mx** — per-label cold vs resume mom_x relative gap below band.
3. **test_pair_gap_ke** — cold vs resume kinetic energy relative gap below band.
4. **test_span_rho** — across workers 1/2/4, mean_rho relative spread below band.
5. **test_span_integral** — mass relative spread across workers below band.
6. **test_integral_closed** — |mass - nx*ny*rho0| relative error below conservation band for every row.
7. **test_finite_rows** — every row stable true; catches NaN paths without accepting wrong attractors alone.
8. **test_gap_block** — report.parity fields match recomputed max relative gaps.
9. **test_band_mx** — cavity case mom_x magnitude must sit in the manifest-governed band (not build-meta band).
10. **test_label_matrix** — poiseuille, cavity, couette each appear under cold and resume for workers 1,2,4.

Multiple valid code approaches pass if macroscopic invariants hold; tests check outcomes not patch sites.

### Drafting guardrails

Instruction is symptoms-only and does not use repair/debug framing. No algorithm names (BGK, D2Q9), no file/function locations, no cause statements. Fix-path symbols use construction manifest names only. Test names avoid instruction nouns. Decoys compile and serve real non-fix paths. No golden answer JSON under environment/.

### Triviality Ledger

- Rerunning the stock campaign script alone leaves cold/resume and worker spreads failing because packing and fold stay wrong.
- Editing only the manifest omega passes attractor checks on cold starts but fails resume parity (halo packing) and worker mass (fold).
- Fixing only snapshot packing makes cold≈resume for worker=1 but fails worker_spread tests.
- Hand-writing campaign-report.json passes schema tests but fails recomputed parity and conservation checks embedded in the verifier.

### Per-gate Pitfall Inventory

- **RC1**: Oracle patches three Go bodies with substantive logic, not deletions.
- **RC2**: No broken_/buggy_/fix_me_/golden_ tokens in solver-visible names.
- **RC3**: Every numeric contract has a computed assertion (relative gaps, conservation, attractor band).
- **RC4/RC5**: Expected bands live in test code / docs schema constants, not agent-writable goldens.
- **RC6**: Instruction symptoms-only; no BGK/D2Q9/file paths for fixes.
- **RC7**: Oracle non-boilerplate LOC comfortably above 30 across three sites.
- **GX3/GX9/GX10**: No heredoc padding; no answer-key recital; no polarity contradictions.
- **static**: allow_internet=false; pytest in Dockerfile; 20+ env files; .dockerignore present.

### Initial Draft Commitments

- `environment/go.mod`
- `environment/.dockerignore`
- `environment/Dockerfile`
- `environment/cmd/campaign/main.go`
- `environment/internal/lattice/init.go`
- `environment/internal/lattice/collide.go`
- `environment/internal/lattice/stream.go`
- `environment/internal/lattice/moments.go`
- `environment/internal/partition/split.go`
- `environment/internal/partition/halo.go`
- `environment/internal/snap/encode.go`
- `environment/internal/snap/decode.go`
- `environment/internal/policy/pick.go`
- `environment/internal/reduce/fold.go`
- `environment/internal/report/emit.go`
- `environment/internal/buildmeta/const.go`
- `environment/internal/decoy/scan_a.go`
- `environment/internal/decoy/pack_probe.go`
- `environment/internal/decoy/fold_trace.go`
- `environment/config/manifests/poiseuille.toml`
- `environment/config/manifests/cavity.toml`
- `environment/config/manifests/couette.toml`
- `environment/data/cases/poiseuille/grid.json`
- `environment/data/cases/cavity/grid.json`
- `environment/data/cases/couette/grid.json`
- `environment/scripts/run_campaign.sh`
- `environment/scripts/inspect_snap.sh`
- `environment/docs/report-schema.md`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: environment/internal/policy/pick.go
  symbol: op_a
  kind: function
  signature: func op_a(m blobX, b blobX) blobX
  purpose: Selects the active mode blob from two candidate blobs.

- path: environment/internal/snap/encode.go
  symbol: pack_b
  kind: function
  signature: func pack_b(f []float64, nx, ny, g int, ax int) []float64
  purpose: Flattens field plus ghost strips into a byte-oriented float slice.

- path: environment/internal/reduce/fold.go
  symbol: fold_c
  kind: function
  signature: func fold_c(parts []PartY, nx, ny, g int) AggZ
  purpose: Combines per-strip partials into global macroscopic aggregates.
```
#### flipping_point_contract

```
locations:
  - id: A
    path: environment/internal/policy/pick.go
    controls_tests: [test_band_mx, test_pair_gap_mx, test_schema_surface]
  - id: B
    path: environment/internal/snap/encode.go
    controls_tests: [test_pair_gap_ke, test_gap_block, test_finite_rows]
  - id: C
    path: environment/internal/reduce/fold.go
    controls_tests: [test_span_rho, test_span_integral, test_integral_closed, test_label_matrix]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: environment/internal/decoy/scan_a.go
  kind: helper
  rhymes_with: op_a
  non_fix_purpose: Read-only manifest inventory for inspect_snap.sh diagnostics.

- path: environment/internal/decoy/pack_probe.go
  kind: helper
  rhymes_with: pack_b
  non_fix_purpose: Debug dump of strip bounds used by inspect tooling, not snapshot I/O.

- path: environment/internal/decoy/fold_trace.go
  kind: helper
  rhymes_with: fold_c
  non_fix_purpose: Optional verbose partial logging for smoke scripts.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [campaign, runner, fluid, cases, snapshots, worker, domain, splits, resume, cold, starts, bulk, observables, physics, config, macroscopic, quantities, report, schema, label, workers, mode, mean_rho, mom_x, mom_y, ke, mass, stable, parity, lattice, boltzmann, checkpoint, drift, halo, reduction, manifest, collision, streaming, viscosity, omega, attractor]
```
