### Decision
GO — Attempt 1. Original Go packlab task with three inconsistent bundle fixtures, distributed fix across chain/flatten/catalog modules, deterministic verifier via ref_bundle.py.

### Metadata
- version: 2
- Task name: overlay-image-layer-reconciliation
- Title: Overlay Layer Reconciliation
- Category: system-administration
- Languages: [go, bash]
- Difficulty: hard
- Codebase size: small
- Subcategories: [tool_specific]
- Tags: [containers, go, packaging, ops, storage, integrity]
- Milestones: 0

## Authoring Brief

### Public contract
Agent repairs `/app` Go sources and rebuilds `/app/bin/packctl`. Output: `/output/reconcile-report.json` with version 1, `bundles[]` each with `id`, bottom-to-top `stacks`, and `paths` maps. Three bundles under `/data/images/`. Do not modify bundle blobs; `anchor.sha256` guards inputs.

### Failure topology
Manifest row order disagrees with wire-id chains; stackview naively trusts publication order; packctl emits wrong stacks and merged path digests when tombstone/opq/alias semantics are incomplete or orphan manifest rows are included.

### Environment shape
Go module at `/app`, bundle fixtures at `/data/images/`, naive `stackview` and production `packctl` CLIs, QA reference script at `/app/ops/ref_bundle.py`, field notes under `/app/config/`.

### Required artifacts
instruction.md, task.toml, output_contract.toml, Dockerfile, .dockerignore, 35+ environment files, solve.sh, patches, test.sh, test_outputs.py.

### Test plan
- Schema and bundle id presence
- Per-bundle stacks match wire-id chain (x7, m4, k9)
- Per-bundle paths match reference flatten (x7, m4, k9)
- Anchor blob integrity

### Drafting guardrails
Symptoms-only instruction; opaque fix-path symbols (OpA, ReconcileB, ResolveC); no BUG comments in env.

### Triviality Ledger
- Naive manifest-order flatten passes x7 stacks test only when chain ordering is also wrong in the same direction — blocked by m4 opq and k9 alias/orphan tests.
- Trusting stackview output collapses on m4 stale siblings test.
- Patching only one of three modules leaves majority of path/stack tests failing.

### Per-gate Pitfall Inventory
- RC3: tests compare computed digests via ref_bundle, not format-only.
- GX7: no hardcoded golden SHA256 in tests.
- GX3: patch-based oracle with 64+ line edit distance across three files.
- GX8: verifier imports only stdlib/subprocess; derivation in env ref_bundle.py.

### Initial Draft Commitments
- tasks/overlay-image-layer-reconciliation/** (generated via scripts/gen_overlay_image_layer_reconciliation.py)
