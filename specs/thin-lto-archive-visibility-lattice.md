### Decision
GO — Attempt 1. Thin-LTO archive visibility lattice under build-and-dependency-management with four coupled loci (Cargo digest/epoch forward, C visibility forge, Go cgo membership, profile authority). Symptoms-only instruction; observation-only probe; verifier-owned EXPECTED; probe ok requires profile-declared bitcode_epoch (not mutual agreement).

### Metadata
- version: 2
- Task name: thin-lto-archive-visibility-lattice
- Title: Thin-LTO Archive Lattice
- Category: build-and-dependency-management
- Languages: ["C", "Rust", "Go"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["tool_specific"]
- Tags: ["thin-lto", "staticlib", "cgo", "visibility", "archives", "profiles"]
- Milestones: 0

## Authoring Brief

### Public contract
Bring every matrix cell under `/app/ops/matrix.toml` into a coherent lattice outcome across a C static archive, Rust staticlib, and Go cgo archive. Write `/output/lattice-report.json` via `/app/bin/lattice_probe` (not by hand). Leave `/app/bin/lattice_probe` and `/app/ops/matrix.toml` unchanged. Report fields: per-cell `status`, `bitcode_epoch`, `vis_digest`, `archive_members`. Profile bitcode epochs live under `/app/config/profiles` (ship=3, fleet=7). Success requires cross-archive agreement on epoch+digest+members AND match to the cell's declared profile epoch, feature-matched digest, and profile packing count. Mutual agreement on the wrong epoch is not success. A surface link-ok path may green on agreement alone and must not be treated as authority.

### Failure topology
After profile cutover, single-language digests look locally coherent while distant cells disagree on thin-LTO bitcode epoch and exported-symbol visibility. Profile authority can feed ship epochs into fleet cells; Rust forward can drop a strand bit; visibility forge can hardcode ship epoch under strand_b; cgo packing can mirror that wrong ship membership so forge+packing look locally green together. Forcing thin-LTO everywhere breaks ship archive membership. Greening one toolchain stamp fails distant matrix cells.

### Environment shape
- `config/profiles/` — ship/fleet/field bitcode_epoch and archive_members declarations
- `r7/` — Rust staticlib with strand cfg and opaque digest forward
- `g5/` — Go ctl for profile resolve, membership packing, flag emit
- `vis/` — C visibility map emitter
- `c9/` — C archive object sources
- `host/` — observation binary that reads archives and prints digests
- `ops/matrix.toml` — multi-cell layout matrix
- `ops/status_check.sh` — surface link-ok bait (agreement-only)
- `tools/lattice_probe/` — observation runner (compiled; not editable for credit)
- `link/`, `data/fixtures/` — supporting surfaces

### Required artifacts
Standard task layout: `instruction.md`, `task.toml`, `output_contract.toml`, `environment/` (20+ files, Dockerfile, `.dockerignore`, non-hidden cargo config seed), `solution/solve.sh`, `tests/{test.sh,test_outputs.py,ledgers/harness.sha256}`. Never `COPY` hidden `.cargo/` from build context — materialize from `config/rust/cargo_config.toml`.

### Test plan
- `test_k3_tier_alpha_ok` — ship strand_a cell status ok (multiple approaches; not chain-dependent)
- `test_w9_tier_beta_ok` — fleet dual-feature cell at EXPECTED epoch/digest
- `test_m4_mark_alpha` — alpha EXPECTED + cross-surface agree
- `test_z2_mark_beta` — beta EXPECTED + cross-surface agree
- `test_t6_span_gamma` — fleet strand_b release cell epoch/digest
- `test_n8_span_delta` — fleet strand_b packing + digest agreement
- `test_y1_tri_agree_beta` — deep rust/go/c/header agreement at EXPECTED
- `test_f5_reentry_gamma` — re-run probe (anti hand-write)
- `test_p7_quota_alpha` — ship packing count on alpha
- `test_h2_quota_beta` — fleet packing count on beta

### Drafting guardrails
Symptoms-only instruction; do not name knit_v4/lane_k1/emit_q3/cg_n5; opaque fix-path symbols; no answer-shaped probe predicates; no three-toolchain repair checklist; probe ok requires declared profile epoch; surface status_check is bait; EXPECTED only in tests; no `.cargo/` COPY.

### Triviality Ledger
- Mutual-agreement-only probe ok → blocked: probe requires profile-declared bitcode_epoch + feature digest + membership
- Force `-flto=thin` everywhere → blocked: ship membership packing fails under strand-conditional cg_n5 / profile members
- Readable probe as answer key → blocked: observation-only compiled probe; EXPECTED in tests
- One-locus polarity flip → blocked: four coupled loci; greening one fails distant cells
- Surface link-ok greening → blocked: tests grade lattice_probe report, not status_check

### Per-gate Pitfall Inventory
- RC1: Oracle must rewrite bodies with correct logic, not delete BUG markers
- RC2: Opaque symbols; no broken_/fix_me_ names; opaque test names
- RC3: Tests assert EXPECTED epoch/digest/members, not JSON existence
- RC4/RC5: EXPECTED embedded in test_outputs.py; harness.sha256 over probe sources + matrix
- RC6: Symptoms-only; profile epochs named for sufficiency (not fix recipe)
- RC7: Oracle LOC substantive across four files (≥30 non-boilerplate)
- GX9: Do not enumerate per-cell EXPECTED triples in instruction
- GX10: Do not put both ok/fail polarities for one cell in one sentence
- Static: allow_internet=false; verifier deps in Dockerfile; absolute /app paths in harness ledger

### Initial Draft Commitments
- instruction.md
- task.toml
- output_contract.toml
- environment/Dockerfile
- environment/.dockerignore
- environment/Cargo.toml
- environment/Cargo.lock
- environment/config/rust/cargo_config.toml
- environment/config/profiles/ship.toml
- environment/config/profiles/fleet.toml
- environment/config/profiles/field.toml
- environment/r7/Cargo.toml
- environment/r7/build.rs
- environment/r7/src/lib.rs
- environment/r7/src/knit.rs
- environment/r7/src/slot.rs
- environment/r7/src/map_legacy.rs
- environment/g5/go.mod
- environment/g5/main.go
- environment/g5/auth.go
- environment/g5/pack.go
- environment/g5/emit.go
- environment/g5/preview.go
- environment/vis/CMakeLists.txt
- environment/vis/emit_q3.c
- environment/vis/main.c
- environment/vis/preview_vis.c
- environment/c9/CMakeLists.txt
- environment/c9/include/obj_api.h
- environment/c9/src/obj_a.c
- environment/c9/src/obj_b.c
- environment/host/CMakeLists.txt
- environment/host/main.c
- environment/ops/matrix.toml
- environment/ops/status_check.sh
- environment/ops/runbooks/ctl_usage.md
- environment/link/legacy.toml
- environment/link/surface.toml
- environment/data/fixtures/seed.json
- environment/tools/lattice_probe/go.mod
- environment/tools/lattice_probe/main.go
- solution/solve.sh
- tests/test.sh
- tests/test_outputs.py
- tests/ledgers/harness.sha256

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table
```
- path: r7/src/knit.rs
  symbol: knit_v4
  kind: function
  signature: fn knit_v4(a: u8, b: u8, e: u8) -> u32
  purpose: Computes the Rust-side visibility digest contribution from strand bit probes and live epoch.
- path: g5/auth.go
  symbol: lane_k1
  kind: function
  signature: func lane_k1(a string) string
  purpose: Resolves a profile name to a filesystem path under config/profiles.
- path: vis/emit_q3.c
  symbol: emit_q3
  kind: function
  signature: void emit_q3(int a, int b, int e, const char *path)
  purpose: Writes the shared visibility map macros for digest and bitcode epoch.
- path: g5/pack.go
  symbol: cg_n5
  kind: function
  signature: func cg_n5(a int, b int, m int) int
  purpose: Selects cgo archive membership count written into build flags for the cell.
- path: g5/xv_q2.go
  symbol: xv_q2
  kind: function
  signature: func xv_q2(a, b, e int) uint32
  purpose: Computes the Go-side visibility contribution from strand probes and epoch.
- path: r7/build.rs
  symbol: fold_e
  kind: function
  signature: fn fold_e(live: String) -> String
  purpose: Selects the epoch env value for the staticlib; must pass live BITCODE_EPOCH rather than sealed archive_epoch.
- path: g5/emit.go
  symbol: writeFlags
  kind: function
  signature: func writeFlags(path string, members int) error
  purpose: Persists packing flags consumed by the C archive lane.
```

#### flipping_point_contract
```
locations:
  - id: A
    path: r7/src/knit.rs
    controls_tests: [test_k3_tier_alpha_ok, test_m4_mark_alpha]
  - id: B
    path: g5/auth.go
    controls_tests: [test_w9_tier_beta_ok, test_z2_mark_beta]
  - id: C
    path: vis/emit_q3.c
    controls_tests: [test_t6_span_gamma, test_y1_tri_agree_beta]
  - id: D
    path: g5/pack.go
    controls_tests: [test_n8_span_delta, test_f5_reentry_gamma, test_p7_quota_alpha, test_h2_quota_beta]
  - id: E
    path: r7/build.rs
    controls_tests: [test_w9_tier_beta_ok, test_t6_span_gamma, test_n8_span_delta]
  - id: F
    path: g5/xv_q2.go
    controls_tests: [test_y1_tri_agree_beta, test_z2_mark_beta]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest
```
- path: r7/src/map_legacy.rs
  kind: helper
  rhymes_with: knit_v4
  non_fix_purpose: Pretty-prints historical digest fragments for ops docs; not invoked by release staticlib builds.
- path: g5/preview.go
  kind: helper
  rhymes_with: lane_k1
  non_fix_purpose: Lists profile filenames for status_check.sh; does not resolve the live path.
- path: vis/preview_vis.c
  kind: helper
  rhymes_with: emit_q3
  non_fix_purpose: Emits a human-readable dump of visibility macros for ops; unused by lattice_probe.
```

#### code_forbidden_tokens
```
code_forbidden_tokens: [fleet, product, static, archive, Rust, staticlib, Go, cgo, layout, cell, matrix, profile, cutover, observation, digests, language, surface, thin-LTO, bitcode, epoch, exported-symbol, visibility, link-ok, success, lattice, outcome, report, probe, status, bitcode_epoch, vis_digest, archive_members, ship, feature, packing, membership, archives]
```
