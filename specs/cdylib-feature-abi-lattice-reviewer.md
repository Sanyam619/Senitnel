### Decision
GO — Attempt 1. Distributed fix across version-map emission, export gating, and metadata roots; opaque symbols; link-green/load-red trap; dual crate-type + C host matrix.

### Metadata
- Task name: cdylib-feature-abi-lattice
- Title: Cdylib Feature ABI Lattice
- Category: build-and-dependency-management
- Languages: ["Rust", "C"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: ["tool_specific"]
- Tags: ["rust", "cdylib", "ffi", "cargo", "features", "linker"]
- Milestones: 0

### Discovery budget
- Discovery: emit_map_a still maps facet_a exports into NEXUS_1 instead of NEXUS_2 in the generated version script, so hosts that resolve at link time reject the .so at dlopen with versioned-symbol mismatch
  Planned location: q3/build.rs
  Why instruction must not reveal it: Naming the version tag would collapse to a one-string rewrite of the map emitter.

- Discovery: gate_sym_b exports facet_b symbols under the inverted cfg (present on default builds, omitted when facet_b is enabled), so alt hosts miss required no_mangle symbols
  Planned location: q3/src/exports.rs
  Why instruction must not reveal it: Naming the polarity bug becomes a single cfg flip recipe.

- Discovery: write_meta_c still publishes legacy soname and Libs that disagree with the cdylib release link line under release, so abi_probe/.pc agreement and release dlopen fail even when exports look right
  Planned location: k9/src/meta.rs
  Why instruction must not reveal it: Pointing at the .pc emitter removes the metadata/link coupling the task tests.

### Anti-trivialization verdict
All 21 checks PASS — see attempt-1 evidence JSON. Not disclosure-collapse, not hidden-instance, not single-artifact repair, not feature-flag table. Residual hardness is FFI ABI + dual crate-type + host linkage lattice.

### Topology enumeration (3 candidate fix topologies)
- T1 Version-map-first: q3/build.rs::emit_map_a, q3/Cargo.toml features, hosts/alpha — map-only insufficient for alt unresolved.
- T2 Export-gate-first: q3/src/exports.rs::gate_sym_b, k2 surface, hosts/beta — export-only insufficient for versioned primary dlopen.
- T3 Metadata-first: k9/src/meta.rs::write_meta_c, pkg template, .cargo rustflags — meta-only insufficient for map/export drift.

### Rubric axes
- Verifiable: PASS — deterministic builds/dlopen/readelf/JSON.
- Well-specified: PASS — status ok + soname/symbol_versions contract.
- Solvable: PASS — expert hours, not absurd scope.
- Difficult: PASS — beyond undergrad Cargo feature labs.
- Interesting: PASS — real plugin ABI cutover.
- Outcome-verified: PASS — grades results not process.

### Hardness axes
- Discover: PASS — three hidden couplings in map/export/meta.
- Synthesize: PASS — features × crate-type × version script × .pc × hosts.
- Diagnose: PASS — symptoms without causes.
- Navigate coupling: PASS — local flips break distant cells.
- Reason beyond training: PASS — not MVS/yank or single feature flip.

### Instruction completeness test
No — instruction alone does not reveal NEXUS_1→NEXUS_2 retarget, facet_b polarity inversion, or soname/.pc Libs drift. Solver must engage the workspace and runtime link/load behavior.

## Reviewer Appendix

### Implementation plan
Environment is a mid-cutover Cargo workspace producing `libnuclide.so` (cdylib) with optional facets, plus three C hosts. Baseline state compiles enough that some cells link, but version tags, export gates, and metadata disagree. Agent must reconcile the lattice so abi_probe reports all cells ok. Distinct from cargo-feature-lattice-cutover: C consumers, versioned ELF symbols, dual crate-type, .pc agreement — not proc-macro roster work.

### Proposed file inventory
Matches Initial Draft Commitments in the authoring spec (≥25 non-Docker env files): workspace crates q3/k2/n6/k9, hosts, ops, link, pkg, config, data, bin/abi_probe, Dockerfile, .dockerignore.

### Oracle notes
solve.sh patches emit_map_a to emit NEXUS_2 for facet_a, corrects gate_sym_b polarity so facet_b exports only when enabled, rewrites write_meta_c to publish soname `libnuclide.so.2` and matching Libs, aligns feature tables / crate-type if needed, clears conflicting rustflags, runs abi_probe.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
Must touch version-map emission, export gating, and metadata writer; one-file or single-manifest patch cannot clear all six tests.

Likely editable frontier:
- q3/build.rs
- q3/src/exports.rs
- k9/src/meta.rs
- q3/Cargo.toml / workspace features
- .cargo/config.toml

Requirement-to-file map:
- primary link+load -> q3/build.rs + hosts/alpha
- alt link+load -> q3/src/exports.rs + hosts/beta
- release/.pc -> k9/src/meta.rs

Oracle estimated complexity: 80–140 lines non-boilerplate

Red flags:
- none if instruction stays symptoms-only and symbols stay opaque

Residual hardness:
After the tree is visible, solvers still must reason about versioned dlopen vs link resolution and profile-specific metadata drift.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
plugin, workspace, shared-object, ABI, host, binaries, dual, crate-type, cutover, matrix, cells, link, load, unresolved, versioned, symbols, feature, sets, ABIs, release, profiles, Cargo, exported, symbol, set, build, graph, agreement, cell, ops, profile, abi-matrix, abi_probe, status, soname, symbol_versions, expectations

**Renames during drafting:**
- [`plugin/` → `q3/`: path matched instruction noun plugin]
- [`abi/` → `k9/`: path matched instruction noun ABI]
- [`emit_version_map` → `emit_map_a`: avoided version/symbol nouns]
- [`gate_exports` → `gate_sym_b`: avoided exported/symbols]
- [`write_pc_meta` → `write_meta_c`: avoided .pc intent telegraph]
- [`test_host_ship_load` → `test_r3_tier_alpha_ok`: avoided host/load nouns]

**Test names audited:**
- test_r3_tier_alpha_ok
- test_v7_tier_beta_ok
- test_j2_tagbag_alpha
- test_h5_tagbag_beta
- test_p6_opt_dlopen
- test_c8_meta_match

**Concentration math:**
- Total tests across `flipping_point_contract`: 6
- Per location:
  - L1 (`q3/build.rs`): 2/6 = 0.333
  - L2 (`q3/src/exports.rs`): 2/6 = 0.333
  - L3 (`k9/src/meta.rs`): 2/6 = 0.333
- Cap: 0.5. Max ratio observed: 0.333. Status: PASS

### Per-test feasibility pre-check
- Test: test_r3_tier_alpha_ok — Checks primary cell status ok — Valid approaches: 2+ — Chain-dependent: no (session fixture) — Feasibility risk: LOW
- Test: test_v7_tier_beta_ok — Checks alt cell status ok — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_j2_tagbag_alpha — Checks NEXUS_2 facet_a tags — Valid approaches: 2+ — Chain-dependent: soft on build — Feasibility risk: MEDIUM
- Test: test_h5_tagbag_beta — Checks facet_b tags without facet_a-only — Valid approaches: 2+ — Chain-dependent: soft on build — Feasibility risk: MEDIUM
- Test: test_p6_opt_dlopen — Checks release cell load — Valid approaches: 2+ — Chain-dependent: soft on meta — Feasibility risk: MEDIUM
- Test: test_c8_meta_match — Checks soname/symbol_versions vs /app/link/ — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
