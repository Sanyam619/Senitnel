### Decision
GO — Attempt 1. Distributed fix across profile authority, Rust stamp forward, C ABI header forge, and cgo/OBJECT packing; opaque symbols; observation-only probe; verifier-owned EXPECTED; locally-green distant-fail traps.

### Metadata
- Task name: triple-toolchain-abi-unify-lattice
- Title: Triple Toolchain ABI Unify
- Category: build-and-dependency-management
- Languages: ["Rust", "Go", "C"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: ["tool_specific"]
- Tags: ["cmake", "cdylib", "cgo", "ffi", "features", "profiles"]
- Milestones: 0

### Discovery budget
- Discovery: lane_m2 always returns the ship profile path, so fleet cells inherit ship pack_width=8
  Planned location: g4/auth.go
  Why instruction must not reveal it: Naming the profile path picker collapses to a one-line string rewrite.
- Discovery: op_q7 drops the facet_x stamp bit on ship-only cells
  Planned location: r8/src/fwd.rs
  Why instruction must not reveal it: Naming the stamp-bit polarity becomes a single boolean flip recipe.
- Discovery: hdr_n3 hardcodes pack_width 8 whenever facet_y is set
  Planned location: gen/hdr_n3.c
  Why instruction must not reveal it: Pointing at the header forge removes the header/packing coupling.
- Discovery: cg_p9 mirrors broken width 8 under facet_y into cgo/OBJECT flags
  Planned location: g4/pack.go
  Why instruction must not reveal it: Naming the packing mirror removes the locally-green distant-fail trap.

### Anti-trivialization verdict
All 21 checks PASS. Key: not disclosure-collapse (symptoms-only), not single-artifact, not grep-collapse (opaque symbols), not one-pass (four coupled loci), discovery budget ≥3, topology distribution ≥3×3, hard-only gate PASS. Avoids musl collapse modes: no three-fix-noun checklist in instruction, no readable EXPECTED probe source, wrongness is lane/profile-conditional.

### Topology enumeration (3 candidate fix topologies)
- T1 Authority-first: g4/auth.go::lane_m2 + gen/hdr_n3.c::hdr_n3 + g4/pack.go::cg_p9 + r8/src/fwd.rs::op_q7 — authority alone insufficient.
- T2 Header/packing-first: hdr_n3 + cg_p9 + lane_m2 + op_q7 — aligned packing still fails under wrong pack_from_profile and alpha stamp drop.
- T3 Stamp-first: op_q7 + lane_m2 + hdr_n3 + c6/CMakeLists.txt — alpha-only repair leaves fleet cells failing.

### Rubric axes
- Verifiable: PASS — deterministic builds + JSON outcomes.
- Well-specified: PASS — status ok + agreeing abi_stamp/pack_width.
- Solvable: PASS — expert multi-toolchain engineer, few hours.
- Difficult: PASS — profile-conditional triple-toolchain lattice.
- Interesting: PASS — real plugin host ABI unification.
- Outcome-verified: PASS — grades report, not process.

### Hardness axes
- Discover: PASS — four discoveries not in instruction.
- Synthesize: PASS — Rust/Go/CMake/profile must agree.
- Diagnose: PASS — symptoms only.
- Navigate coupling: PASS — local green fails distant cells.
- Reason beyond training: PASS — not textbook Cargo flip.

### Instruction completeness test
No — instruction alone cannot reveal path resolution, stamp-bit drop, or pack-width hardcodes. Agent must engage codebase and matrix behavior.

## Reviewer Appendix

### Implementation plan
Ship a Go+Rust+CMake plugin host matrix. unify_probe builds each cell (generate header, build cdylib with facet env, build go cgo archive, build cmake OBJECT libs, link host) and records observed status/abi_stamp/pack_width per surface without EXPECTED comparisons. Broken defaults: lane_m2→ship always; op_q7 drops facet_x on ship-only; hdr_n3 and cg_p9 hardcode width 8 under facet_y. Oracle restores path resolution, stamp bit, and profile-honoring widths. Tests embed EXPECTED.

### Proposed file inventory
Matches Initial Draft Commitments in authoring spec (≥25 non-Docker environment files): Dockerfile, Cargo workspace r8, g4 go module, c6 cmake OBJECT, gen header forge, host linker, profiles, matrix, observation probe, decoys map_legacy/preview/preview_hdr, link notes, fixtures.

### Oracle notes
solve.sh patches: (1) op_q7 include 0x01 when a!=0 regardless of b; (2) lane_m2 return /app/config/profiles/{a}.toml; (3) hdr_n3 write w as pack width always; (4) cg_p9 return w (or 4 when b!=0 and w from profile). Rebuild not required in solve if probe rebuilds; ensure ≥30 LOC substantive.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
Must edit four loci — path resolution, stamp forward, header width, packing width — with profile-conditional behavior; single-file insufficient.

Likely editable frontier:
- r8/src/fwd.rs
- g4/auth.go
- gen/hdr_n3.c
- g4/pack.go

Requirement-to-file map:
- ship-only stamp -> r8/src/fwd.rs
- fleet authority -> g4/auth.go
- header pack width -> gen/hdr_n3.c
- cgo/OBJECT pack width -> g4/pack.go

Oracle estimated complexity: 60-90 lines non-boilerplate

Red flags:
- none if instruction avoids naming four loci and probe stays observation-only

Residual hardness:
After tree is visible, solver still must discover which profile is live, that header and packing are co-broken to look green, and that ship-only stamp polarity differs from dual-feature cells.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
plugin, host, shared, ABI, header, language, surfaces, matrix, cell, Rust, cdylib, Go, cgo, archive, CMake, OBJECT, libraries, profile, cutover, toolchain, stamp, unification, generated, packing, feature, sets, configuration, lattice, coherence, unify, outcome, report, probe, status, abi_stamp, pack_width, ops, cells

**Renames during drafting:**
- `resolve_profile` → `lane_m2`: matched profile
- `emit_header` → `hdr_n3`: matched header
- `pack_width_for` → `cg_p9`: matched packing
- `feature_stamp` → `op_q7`: matched feature/stamp

**Test names audited:**
- test_k3_tier_alpha_ok
- test_w9_tier_beta_ok
- test_m4_mark_alpha
- test_z2_mark_beta
- test_t6_span_gamma
- test_n8_span_delta
- test_y1_tri_agree_beta
- test_f5_reentry_gamma

**Concentration math:**
- Total tests across flipping_point_contract: 8
- Per location:
  - L1 (r8/src/fwd.rs): 2/8 = 0.25
  - L2 (g4/auth.go): 2/8 = 0.25
  - L3 (gen/hdr_n3.c): 2/8 = 0.25
  - L4 (g4/pack.go): 2/8 = 0.25
- Cap: 0.5. Max ratio observed: 0.25. Status: PASS

### Per-test feasibility pre-check
- Test: test_k3_tier_alpha_ok — Checks alpha status ok — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_w9_tier_beta_ok — Checks beta status ok — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_m4_mark_alpha — Checks alpha abi_stamp EXPECTED + agreement — Valid approaches: 2+ — Chain-dependent: yes on build — Feasibility risk: LOW
- Test: test_z2_mark_beta — Checks beta abi_stamp EXPECTED + agreement — Valid approaches: 2+ — Chain-dependent: yes on build — Feasibility risk: LOW
- Test: test_t6_span_gamma — Checks gamma pack_width EXPECTED — Valid approaches: 2+ — Chain-dependent: yes — Feasibility risk: LOW
- Test: test_n8_span_delta — Checks delta packing/header agree — Valid approaches: 2+ — Chain-dependent: yes — Feasibility risk: LOW
- Test: test_y1_tri_agree_beta — Checks beta tri-surface agreement — Valid approaches: 2+ — Chain-dependent: yes — Feasibility risk: MEDIUM
- Test: test_f5_reentry_gamma — Re-runs probe; gamma still coherent — Valid approaches: 2+ — Chain-dependent: yes — Feasibility risk: LOW
