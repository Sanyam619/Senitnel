
### Decision
GO — Attempt 1. Simulated host stack with Rust graph/merge helpers and Bash override merge; three coupled fix loci; all six unit names listed in instruction.

### Metadata
- version: 2
- Task name: systemd-unit-cascade-rollback
- Title: Stack Cutover Rollback
- Category: system-administration
- Languages: ["bash", "rust"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["host", "ops", "rust", "bash", "migration", "recovery"]
- Milestones: 0

## Authoring Brief

### Public contract
Symptoms-only instruction describing failed activation, depwalk After complaints, and ledger refusal. Agent must reconcile override merge precedence, Rust alias/bind resolution, and graph ordering, rebuild tools, bring stack up, emit `/output/rollback-report.json` version 1 with six named rows and fields `name`, `state`, `start_order`, `hard_deps`, `soft_deps`. Anchor under `/data/fixtures/stack-seed/` must remain untouched.

### Failure topology
Cutover applied override fragments and alias remapping inconsistently: merged relay bind may point at a retired name, topo ordering uses truncated After closure, and activation refuses until graph + merge + sequencing align. Observable via health script failure, depwalk stderr, and missing ledger.

### Environment shape
`/app/` hosts config notes, Bash wrappers, prebuilt Rust binaries, and rebuildable `/app` workspace. `/data/stack/` holds unit bodies, override drop-ins, and runtime state. Immutable anchor snapshots live under `/data/fixtures/stack-seed/`.

### Required artifacts
instruction.md, task.toml, output_contract.toml, Dockerfile, .dockerignore, Rust workspace + three binaries, Bash scripts, fixture builder, tests, solve.sh, construction_manifest.json.

### Test plan
- test_x3_active_bundle: all six names active
- test_f7_order_chain: After-respecting start_order
- test_j2_hard_requires: Requires/BindsTo in hard_deps
- test_n5_soft_wants: Wants only in soft_deps
- test_p1_shape_bundle: JSON schema
- test_r4_anchor_intact: seed checksums
- test_h8_tally_matches_runtime: report vs runtime files
- test_k2_relay_bind_resolved: merged bind + active relay

### Drafting guardrails
Do not name fix files in instruction; keep opaque Rust module names; tests use neutral ids; forbid instruction nouns in fix-path symbols.

### Triviality Ledger
- Fixing only merge sort passes bind test but leaves topo/order failures because graph fold still truncates After closure.
- Fixing only alias table passes bind resolution but stackarm still aborts on ordering until fold_after recurses.
- Reordering Bash stack-up without rebuild leaves stale binary behavior — tests require on-disk runtime rows matching rebuilt tools.

### Per-gate Pitfall Inventory
- RC6: instruction stays symptoms-only; schema fields named because they are output contract.
- CR2: three locations each control distinct test subsets per flipping_point_contract.
- GX9: instruction must not recite per-unit expected order integers.
- static checks: allow_internet=false; pytest in Dockerfile.

### Initial Draft Commitments
- instruction.md
- task.toml
- output_contract.toml
- environment/Dockerfile
- environment/.dockerignore
- environment/Cargo.toml
- environment/Cargo.lock
- environment/stack-core/** 
- environment/depwalk/**
- environment/stackarm/**
- environment/ledgersnap/**
- environment/config/field-notes.md
- environment/config/stack.toml
- environment/scripts/*.sh
- environment/data/build_fixtures.sh
- environment/data/fixtures/stack-seed/manifest.txt
- tests/test.sh
- tests/test_outputs.py
- solution/solve.sh
- construction_manifest.json

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

See construction_manifest.json generated with the task.
