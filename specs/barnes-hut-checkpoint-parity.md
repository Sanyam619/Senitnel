### Decision
GO — Attempt 1. Scientific-computing campaign-parity contract (Barnes–Hut N-body) with three coupled loci (manifest physics authority, checkpoint domain packing, interior-only reduction); opaque symbols; macroscopic conservation/parity tests; goal-first framing so the category classifier stays on scientific-computing (not debugging).

### Metadata
- version: 2
- Task name: barnes-hut-checkpoint-parity
- Title: Barnes Hut Campaign Parity
- Category: scientific-computing
- Languages: [Go, C]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: [nbody, barnes-hut, conservation, checkpoint, reductions]
- Milestones: 0

## Authoring Brief

### Public contract

An N-body Barnes–Hut campaign under `/app` advances bundled cases with a multipole treecode, mid-run snapshots, and multi-worker domain splits. The solver-visible goal is that conserved observables satisfy documented numerical-agreement bands across checkpoint/resume and across domain-split worker counts (force accuracy and reduction ordering must keep results worker-independent).

Drive `/app/scripts/run_campaign.sh` so every case under `/app/data/cases/` produces agreeing macroscopic quantities for cold vs resumed modes and for worker counts 1, 2, and 4. Write `/output/campaign-report.json` with:

- `schema_tag` (string) — must be `nbody-campaign-v1`
- `cases` (array) — one object per `(label, workers, mode)` with fields:
  - `label` (string)
  - `workers` (int)
  - `mode` (string: `cold` or `resume`)
  - `energy` (float)
  - `momentum_L2` (float)
  - `mass` (float)
  - `stable` (bool)
- `parity` (object) with:
  - `cold_resume_max_rel` (float) — max relative deviation of observables between cold and resumed runs for the same label/workers
  - `worker_spread_max_rel` (float) — max relative spread of observables across worker counts for the same label/mode

Exact numeric bands and physical bounds live in `/app/docs/report-schema.md`. Per-particle bit identity is not required; macroscopic agreement, mass closure, and finite/stable rows are.

The verifier rebuilds `/app/cmd/campaign` from current sources before grading and also invokes internal packages with verifier-owned inputs (config selection, snapshot round-trip including domain halos, interior-only reductions). Hand-written or hardcoded reports fail. When run manifests under `/app/config/manifests/` and compile-time defaults disagree on a physics knob (e.g. opening angle / softening), the manifest is authoritative for reported observables.

### Failure topology

Cluster A: cold and resume both finish finite/stable, but energy and momentum sit on the wrong attractor — active treecode / softening knobs are taken from compile-time build meta instead of the per-case run manifest. Cluster B: cold≈resume for worker=1 but resume remaps boundary particles wrong under multi-worker splits — snapshot packing of domain-owned particles/ghosts disagrees with live partition exchange. Cluster C: worker count changes mass / momentum_L2 under identical physics — macroscopic fold includes ghost/halo particles or associates partials in partition-id order.

These interact: correcting only packing can make resume match a cold start that still used the wrong opening angle; correcting only policy leaves worker-dependent mass; correcting only reduction leaves resume boundary layers wrong. The agent must coordinate all three authorities.

### Environment shape

- **`environment/cmd/campaign/`** — Go CLI that drives cold and resume campaigns and emits the report.
- **`environment/internal/tree/`** — Barnes–Hut build / walk (working multipole primitives; not the primary fix locus).
- **`environment/native/`** — small C force kernel called from Go (cgo); correct physics primitive.
- **`environment/internal/partition/`** — domain splits and live halo exchange for particles.
- **`environment/internal/snap/`** — snapshot encode/decode (fix locus B).
- **`environment/internal/policy/`** — run-manifest vs build-meta resolution (fix locus A).
- **`environment/internal/reduce/`** — macroscopic fold (fix locus C).
- **`environment/internal/report/`** — JSON emission.
- **`environment/internal/decoy/`** — genuine non-fix helpers that rhyme with fix symbols.
- **`environment/internal/buildmeta/`** — compile-time constants that disagree with manifests.
- **`environment/config/manifests/`** — per-case run manifests (theta, softening, steps, …).
- **`environment/data/cases/`** — particle ICs / case params.
- **`environment/scripts/`** — campaign driver the agent invokes.
- **`environment/docs/`** — report schema and numeric bands.

### Required artifacts

- `tasks/barnes-hut-checkpoint-parity/instruction.md` — goal-first scientific framing (agreement/conservation bands); symptoms allowed as secondary clauses; no repair/debug lead-in; no algorithm dump of Barnes–Hut criterion algebra.
- `tasks/barnes-hut-checkpoint-parity/task.toml` — category `scientific-computing`, languages `["go","c"]`, `allow_internet = false`
- `tasks/barnes-hut-checkpoint-parity/output_contract.toml`
- `tasks/barnes-hut-checkpoint-parity/environment/Dockerfile` + `.dockerignore`
- `tasks/barnes-hut-checkpoint-parity/tests/test.sh` + `test_outputs.py` (≥8 hard tests) + optional Go checker if mirroring LBM
- `tasks/barnes-hut-checkpoint-parity/solution/solve.sh`
- Full environment tree per Initial Draft Commitments (25+ substantive files excl. Dockerfile)

### Test plan

1. **test_schema_surface** — report exists; `schema_tag == nbody-campaign-v1`; required top-level and row keys present.
2. **test_pair_gap_energy** — per-label cold vs resume `energy` relative gap below band.
3. **test_pair_gap_mom** — cold vs resume `momentum_L2` relative gap below band.
4. **test_span_mass** — across workers 1/2/4, `mass` relative spread below band.
5. **test_span_mom** — `momentum_L2` relative spread across workers below band.
6. **test_integral_closed** — |mass − sum(particle masses)| relative error below conservation band for every row.
7. **test_finite_rows** — every row `stable == true`; all math fields finite.
8. **test_gap_block** — `parity.*` fields match recomputed max relative gaps from `cases`.
9. **test_band_energy** — one designated case’s `energy` magnitude sits in the manifest-governed band (not build-meta band).
10. **test_label_matrix** — `plummer`, `binary`, `collapse` each appear under cold and resume for workers 1, 2, 4.

Multiple valid code approaches pass if macroscopic invariants hold; tests check outcomes not patch sites. Not chain-dependent on full solution for schema/finite/matrix coverage tests.

### Drafting guardrails

Instruction leads with the numerical goal (agreement/conservation bands), not “disagree / drift / fix.” No named Barnes–Hut opening-angle formula, no fix-file paths, no cause statements (“because ghosts are included”). Fix-path symbols use construction manifest names only. Test names avoid instruction nouns as substrings where the naming-pass requires it. Decoys compile and serve real non-fix paths. No golden answer JSON under `environment/`. Do not copy LBM filenames/symbols verbatim — this is a distinct n-body tree campaign.

### Triviality Ledger

- Rerunning the stock campaign script alone leaves cold/resume and worker spreads failing because packing and fold stay wrong.
- Editing only the manifest theta/softening passes attractor checks on cold starts but fails resume parity (domain packing) and worker mass (fold).
- Fixing only snapshot packing makes cold≈resume for worker=1 but fails worker_spread tests.
- Hand-writing `/output/campaign-report.json` passes schema smoke but fails recomputed parity, conservation, and verifier-owned package probes.
- Replacing `/app/cmd/campaign` with a bash emitter of fixed numbers fails the fresh-source rebuild path.

### Per-gate Pitfall Inventory

- **RC1**: Oracle patches three substantive bodies (policy/snap/reduce), not deletions or comment flips.
- **RC2**: No `broken_`/`buggy_`/`fix_me_`/`golden_` tokens in solver-visible names.
- **RC3**: Every numeric contract has a computed assertion (relative gaps, conservation, attractor band).
- **RC4/RC5**: Expected bands live in test code / `report-schema.md` constants, not agent-writable goldens under `environment/`.
- **RC6**: Instruction symptoms/goal-only; no closed-form θ criterion dump; no fix-site paths.
- **RC7**: Oracle non-boilerplate LOC comfortably above 30 across three sites.
- **GX1/GX3**: No heredoc/comment padding in `solve.sh`.
- **GX9/GX10**: Do not recite per-row expected energy values in instruction; no polarity contradictions on `stable`/mode.
- **static**: `allow_internet=false`; pytest deps in Dockerfile; ≥20 env files; `.dockerignore` present; no `COPY` of hidden dotdirs from context.

### Initial Draft Commitments

- `environment/go.mod`
- `environment/.dockerignore`
- `environment/Dockerfile`
- `environment/cmd/campaign/main.go`
- `environment/native/force.c`
- `environment/native/force.h`
- `environment/internal/tree/build.go`
- `environment/internal/tree/walk.go`
- `environment/internal/tree/cgo_force.go`
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
- `environment/config/manifests/plummer.toml`
- `environment/config/manifests/binary.toml`
- `environment/config/manifests/collapse.toml`
- `environment/data/cases/plummer/particles.json`
- `environment/data/cases/binary/particles.json`
- `environment/data/cases/collapse/particles.json`
- `environment/scripts/run_campaign.sh`
- `environment/scripts/inspect_snap.sh`
- `environment/docs/report-schema.md`
- `instruction.md`
- `task.toml`
- `output_contract.toml`
- `tests/test.sh`
- `tests/test_outputs.py`
- `solution/solve.sh`

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
  signature: func pack_b(state []float64, n int, g int, ax int) []float64
  purpose: Flattens particle state plus ghost strips into a durable float slice.

- path: environment/internal/reduce/fold.go
  symbol: fold_c
  kind: function
  signature: func fold_c(parts []PartY, n int, g int) AggZ
  purpose: Combines per-strip partials into global macroscopic aggregates.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: environment/internal/policy/pick.go
    controls_tests: [test_band_energy, test_pair_gap_energy, test_schema_surface]
  - id: B
    path: environment/internal/snap/encode.go
    controls_tests: [test_pair_gap_mom, test_gap_block, test_finite_rows]
  - id: C
    path: environment/internal/reduce/fold.go
    controls_tests: [test_span_mass, test_span_mom, test_integral_closed, test_label_matrix]
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
code_forbidden_tokens: [campaign, barnes, hut, nbody, particle, particles, treecode, multipole, opening, angle, softening, checkpoint, resume, cold, worker, workers, domain, split, splits, parity, energy, momentum, mass, stable, manifest, reduction, halo, ghost, observables, conservation, agreement, plummer, binary, collapse, schema, report]
```
