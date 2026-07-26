### Decision
GO — Attempt 1. Distributed Rust rollover validation task.

### Metadata
- version: 2
- Task name: dnssec-chain-trust-reconstruction
- Title: Signed Rollover Audit
- Category: security
- Languages: ["rust", "bash"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: ["security", "rust", "protocol", "validation"]
- Milestones: 0

## Authoring Brief
This file is the only drafting input for Step 2b. Do NOT include reviewer-only analysis, oracle steps, exact patch sites, or an exhaustive file tree here.

### Public contract
Repair the Rust analyzer so it emits `/app/output/validation.json` and `/app/output/replayed.json` from `/app/data/queries.tsv`, choosing the per-instant chain and reporting stale-only routes.

### Failure topology
Mixed rollover captures accept stale proof routes or choose the wrong live route. Correct behavior couples parsing, temporal selection, chain assembly, and reporting.

### Environment shape
Single Rust crate, split fixture registries, decoy helpers, pytest verifier.

### Required artifacts
Standard task files with 20+ meaningful environment files.

### Test plan
Six tests cover primary overlap, stale-only rejection, secondary handoff, boundary instants, replay set equality, and missing material.

### Drafting guardrails
Instruction stays symptoms-only and avoids concrete record classes or algorithms.

### Triviality Ledger
- Naive active-window acceptance fails overlap and stale-only cases.
- One-file table editing fails chain and report coupling.
- Handwritten output requires reconstructing all fixture outcomes.

### Per-gate Pitfall Inventory
- RC1/RC7/GX3: oracle changes substantive Rust logic.
- RC2/CR7: opaque fix-path names.
- RC3/RC4/RC5: expected values only in tests.
- RC6/GX9/GX10: no answer recital or polarity contradiction.
- Static checks: offline standard layout.

### Initial Draft Commitments
- instruction.md
- task.toml
- output_contract.toml
- environment/.dockerignore
- environment/Dockerfile
- environment/Cargo.toml
- environment/src/main.rs
- environment/src/model.rs
- environment/src/io/mod.rs
- environment/src/io/wire.rs
- environment/src/io/scan.rs
- environment/src/core/mod.rs
- environment/core/phase.rs
- environment/core/atlas.rs
- environment/src/clock/mod.rs
- environment/clock/sieve.rs
- environment/src/report/mod.rs
- environment/report/emit.rs
- environment/src/ledger/mod.rs
- environment/src/ledger/notes.rs
- environment/src/util.rs
- environment/data/queries.tsv
- environment/data/registry/00-roots.txt
- environment/data/registry/10-example-keys.txt
- environment/data/registry/11-lab-keys.txt
- environment/data/registry/12-archive-keys.txt
- environment/data/registry/20-example-bridges.txt
- environment/data/registry/21-lab-bridges.txt
- environment/data/registry/22-archive-bridges.txt
- environment/data/registry/30-records-a.txt
- environment/data/registry/31-records-b.txt
- environment/data/registry/40-example-marks.txt
- environment/data/registry/41-lab-marks.txt
- environment/data/registry/42-archive-marks.txt
- environment/docs/catalog-notes.md
- environment/docs/operator-log.md
- environment/fixtures/window-alpha.txt
- environment/fixtures/window-beta.txt
- environment/fixtures/window-gamma.txt
- solution/solve.sh
- tests/test.sh
- tests/test_outputs.py

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table
- path: core/phase.rs
  symbol: phase_a
  kind: function
  signature: pub fn phase_a(data: &CaseData, q: &Query) -> Vec<Mark>
  purpose: Collects candidate marks.
- path: core/atlas.rs
  symbol: phase_b
  kind: function
  signature: pub fn phase_b<'a>(data: &'a CaseData, zone: &str, id: &str, t: i64) -> Option<&'a Node>
  purpose: Selects usable node.
- path: core/atlas.rs
  symbol: phase_f
  kind: function
  signature: pub fn phase_f<'a>(data: &'a CaseData, zone: &str, id: &str, t: i64) -> Option<&'a Node>
  purpose: Detects stale node.
- path: clock/sieve.rs
  symbol: fold_c
  kind: function
  signature: pub fn fold_c(data: &CaseData, q: &Query, mark: &Mark) -> Option<Vec<String>>
  purpose: Builds route text.
- path: report/emit.rs
  symbol: emit_d
  kind: function
  signature: pub fn emit_d(data: &CaseData) -> (String, String)
  purpose: Serializes outputs.

#### flipping_point_contract
locations:
  - id: A
    path: core/phase.rs
    controls_tests: [test_alpha, test_delta]
  - id: B
    path: clock/sieve.rs
    controls_tests: [test_charlie, test_delta]
  - id: C
    path: report/emit.rs
    controls_tests: [test_bravo, test_echo, test_foxtrot]
no_single_location_flips_majority: true
concentration_cap: 0.5

#### decoy_manifest
- path: src/ledger/notes.rs
  kind: helper
  rhymes_with: phase_a
  non_fix_purpose: Sorts strings.
- path: src/util.rs
  kind: helper
  rhymes_with: phase_b
  non_fix_purpose: Counts rows.

#### code_forbidden_tokens
code_forbidden_tokens: [analyzer, app, naming, catalog, credential, rollover, snapshots, lookups, proof, material, wall-clock, instant, Rust, project, output, validation, json, replayed, query, id, name, status, chain, reason, authorities, machine, time, inputs, files]
