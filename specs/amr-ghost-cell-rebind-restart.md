### Decision
GO — Attempt 1. Symptoms-only public contract; distributed fix across forge/ledger/mesh roots; opaque symbol table; eight verifier slices with no instruction-noun leakage in test names.

### Metadata
- version: 2
- Task name: amr-ghost-cell-rebind-restart
- Title: AMR Ghost-Cell Rebind Restart
- Category: scientific-computing
- Languages: [C]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: [amr, checkpoint, hydrodynamics, c, restart, numerical]
- Milestones: 0

## Authoring Brief

### Public contract

The agent receives a compact C hydrodynamics codebase with adaptive refinement that archives hierarchical block state each cycle. Operations have already merged an archived snapshot into a newer layout directive; the bundled restart driver runs to completion but face-adjacent layer magnitudes disagree with frozen reference traces while interior cells look plausible. The solver kernels are not broken.

The agent must drive the existing recovery workflow (not rewrite physics) so that all bundled scenarios produce layout-consistent recovered fields and emit `/output/restart-summary.json` with:

- `schema_tag` (string, fixed value documented in `/app/docs/summary-schema.md`)
- `scenarios` (array) — one object per bundled scenario name with:
  - `label` (string)
  - `block_tally` (integer)
  - `face_l2` (float) — L2 norm of the outer halo layer along shared faces vs reference slice
- `mass_drift` (float) — global volume integral drift vs reference (must be below documented epsilon)
- `tree_depth` (integer) — max refinement depth after recovery (must match policy table)

Grading replays every fixture under `/app/data/fixtures/` plus writes field dumps under `/output/fields/<scenario>/` for two timesteps. Tests compare computed face-layer L2, mass drift, tree depth, and summary schema — not log text or exit codes alone.

### Failure topology

Symptom cluster A: restart completes with healthy interior fields but face-adjacent layers diverge from reference — indicates stale neighbor mapping or wrong halo source, not a flux kernel bug. Symptom cluster B: block tallies and tree depth disagree with the adopted layout directive — indicates the recovery path bound the wrong archived generation or applied layout reconciliation out of order. Symptom cluster C: mass drift within tolerance on one scenario but face L2 fails on another — indicates partial refresh (intra-level tables updated without cross-level reconciliation).

These clusters interact: choosing the wrong archived generation makes layout reconciliation appear successful while neighbor maps still encode the pre-merge topology; running neighbor refresh before layout reconciliation produces locally consistent halos that violate the policy depth ladder. The agent must trace the multi-phase recovery driver, identify which persisted generation is canonical for the merged directive, and execute dependent phases in an order that preserves both topology invariants and halo orientation conventions.

### Environment shape

- **`environment/src/hydro/`** — explicit hydro stepping and Riemann flux kernels (working; not the fix surface).
- **`environment/src/mesh/`** — block tree, refinement policy reader, and neighbor link materialization.
- **`environment/src/forge/`** — checkpoint blob I/O and multi-phase recovery driver orchestration.
- **`environment/src/ledger/`** — archived generation catalog and layout-directive merge metadata.
- **`environment/src/couple/`** — face packing and halo fill routines consumed by the hydro stepper.
- **`environment/scripts/`** — CLI restart entrypoints the agent invokes.
- **`environment/data/`** — policy tables, archived blobs, scenario params, and reference face slices (reference slices are test inputs only; expected values are embedded in verifier code per RC5).
- **`environment/include/`** — shared headers across the above roots.
- **`/app/docs/summary-schema.md`** — normative output schema (solver-visible).

### Required artifacts

- `tasks/amr-ghost-cell-rebind-restart/instruction.md` — symptoms-only prose per Public contract.
- `tasks/amr-ghost-cell-rebind-restart/task.toml` — edition_2 standard task; `[environment] allow_internet = false`.
- `tasks/amr-ghost-cell-rebind-restart/environment/Dockerfile` — build toolchain + verifier deps.
- `tasks/amr-ghost-cell-rebind-restart/environment/.dockerignore`
- `tasks/amr-ghost-cell-rebind-restart/tests/test.sh` — canonical template.
- `tasks/amr-ghost-cell-rebind-restart/tests/test_outputs.py` — ≥8 tests per Test plan.
- `tasks/amr-ghost-cell-rebind-restart/solution/solve.sh` — oracle touching construction manifest symbols only.
- Full `environment/` tree per Initial Draft Commitments (35+ substantive files).

### Test plan

1. **test_emit_json_contract** — summary file exists, `schema_tag` correct, required keys only.
2. **test_slice_l2_alpha** — scenario alpha `face_l2` within tight tolerance vs recomputed reference slice.
3. **test_slice_l2_beta** — scenario beta `face_l2` within tolerance (different refinement pattern).
4. **test_volume_sum_alpha** — global mass integral drift below epsilon for alpha.
5. **test_volume_sum_beta** — mass drift for beta (catches partial halo refresh).
6. **test_depth_alpha** — `tree_depth` and `block_tally` match policy for alpha.
7. **test_depth_beta** — depth/tally for beta (distinct ladder).
8. **test_secondary_gamma** — third scenario chain-dependent: fails if recovery order wrong even when alpha passes.

Multiple valid orderings may pass if invariants hold; tests check outcomes not CLI flags.

### Drafting guardrails

Instruction stays symptoms-only: no phase names, no table/module hints, no "ghost" or "rebind" vocabulary. Fix-path symbols use construction manifest opaque names only. Reference binaries under `data/ref_slices/` are inputs to verifier recomputation, not answer keys in `environment/` readable by tampering. Decoy modules in `ledger/` and `couple/` must compile and serve real non-fix paths. Do not name tests after instruction nouns.

### Triviality Ledger

- Naive "rerun default restart script" passes interior health checks but fails `test_slice_l2_*` because default path binds the pre-merge archived generation.
- Editing only the policy table passes `test_depth_*` but fails `test_slice_l2_*` because neighbor maps never refresh.
- Refreshing neighbor maps before layout reconciliation passes alpha locally but fails `test_secondary_gamma` cross-level ladder invariant.
- Setting summary JSON fields by hand passes `test_emit_json_contract` but fails field-dump recomputation embedded in slice tests.

### Per-gate Pitfall Inventory

- **RC1**: Oracle must implement multi-phase coordination in `solve.sh`, not delete buggy code.
- **RC2**: No `broken_*`, `ghost_*`, `rebind_*` in paths or test names.
- **RC3**: Every numeric field in summary schema has a computed assertion, not existence-only.
- **RC4**: Expected L2/mass values computed in `test_outputs.py` from fixture params + ref slices, not read from agent-writable golden files.
- **RC5**: No answer-shaped JSON under `environment/`; embed tolerances in tests.
- **RC6**: Instruction describes symptoms and output schema only — no recovery recipe.
- **RC7**: Oracle touches ≥3 manifest locations; flipping-point compliance required.
- **GX3**: Substantive C recovery logic in oracle, not comment-padding.
- **static checks**: `allow_internet = false`; pytest in Dockerfile; 20+ env files.

### Initial Draft Commitments

- `environment/Makefile`
- `environment/.dockerignore`
- `environment/src/main.c`
- `environment/src/hydro/step.c`
- `environment/src/hydro/flux.c`
- `environment/src/mesh/block_tree.c`
- `environment/src/mesh/refine_policy.c`
- `environment/src/mesh/link_refresh.c`
- `environment/src/forge/recover_phase.c`
- `environment/src/forge/checkpoint_io.c`
- `environment/src/ledger/epoch_pick.c`
- `environment/src/ledger/policy_merge.c`
- `environment/src/ledger/catalog_scan.c`
- `environment/src/couple/face_pack.c`
- `environment/src/couple/halo_fill.c`
- `environment/src/couple/stencil_probe.c`
- `environment/src/util/crc32.c`
- `environment/src/util/json_emit.c`
- `environment/include/hydro.h`
- `environment/include/mesh.h`
- `environment/include/forge.h`
- `environment/include/ledger.h`
- `environment/include/couple.h`
- `environment/scripts/run_restart.sh`
- `environment/scripts/inspect_archive.sh`
- `environment/docs/summary-schema.md`
- `environment/data/policy_v2.table`
- `environment/data/archive_cycle_17.blob`
- `environment/data/archive_cycle_21.blob`
- `environment/data/fixtures/alpha.params`
- `environment/data/fixtures/beta.params`
- `environment/data/fixtures/gamma.params`
- `environment/data/ref_slices/alpha_face.bin`
- `environment/data/ref_slices/beta_face.bin`
- `environment/data/ref_slices/gamma_face.bin`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: environment/src/forge/recover_phase.c
  symbol: apply_seq_a
  kind: function
  signature: int apply_seq_a(struct forge_ctx *ctx, int stage_mask)
  purpose: Runs numbered recovery stages in caller-supplied order mask.

- path: environment/src/ledger/epoch_pick.c
  symbol: select_src_b
  kind: function
  signature: int select_src_b(const struct ledger_ctx *ctx, uint32_t *out_gen)
  purpose: Chooses archived generation id from merge metadata and catalog.

- path: environment/src/mesh/link_refresh.c
  symbol: rebuild_map_c
  kind: function
  signature: int rebuild_map_c(struct mesh_ctx *m, uint32_t gen_id)
  purpose: Rebuilds neighbor link tables for the active generation id.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: environment/src/forge/recover_phase.c
    controls_tests: [test_emit_json_contract, test_slice_l2_alpha, test_slice_l2_beta]
  - id: B
    path: environment/src/ledger/epoch_pick.c
    controls_tests: [test_volume_sum_alpha, test_volume_sum_beta, test_depth_alpha]
  - id: C
    path: environment/src/mesh/link_refresh.c
    controls_tests: [test_depth_beta, test_secondary_gamma]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: environment/src/ledger/catalog_scan.c
  kind: helper
  rhymes_with: select_src_b
  non_fix_purpose: Read-only archive inventory for inspect_archive.sh diagnostics.

- path: environment/src/couple/stencil_probe.c
  kind: helper
  rhymes_with: rebuild_map_c
  non_fix_purpose: Debug halo stencil dumps used by inspect tooling, not recovery.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [hydrodynamics, adaptive, refinement, checkpoints, hierarchical, blocks, cycle, archived, checkpoint, layout, restart, conserved, face, layer, norms, reference, baseline, interior, states, solver, kernels, recovery, scenarios, output, summary, block, counts, boundary, error, driver, snapshot, directive, magnitudes, traces, cells, fields, timesteps, policy, merge, topology, ghost, rebind, exchange, halo, neighbor, epoch, fixture]
```
