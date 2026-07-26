### Decision
GO — Attempt 1. Distributed fix across profile authority, Rust stamp forward, C ABI header forge, and cgo/OBJECT packing; opaque symbols; observation-only probe; verifier-owned EXPECTED; locally-green distant-fail traps.

### Metadata
- version: 2
- Task name: triple-toolchain-abi-unify-lattice
- Title: Triple Toolchain ABI Unify
- Category: build-and-dependency-management
- Languages: ["Rust", "Go", "C"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: ["tool_specific"]
- Tags: ["cmake", "cdylib", "cgo", "ffi", "features", "profiles"]
- Milestones: 0

## Authoring Brief

### Public contract

A plugin host under `/app/` must publish one shared C ABI header and link three language surfaces into each matrix cell under `/app/ops/matrix.toml`: a Rust cdylib, a Go cgo archive, and CMake OBJECT libraries. After a profile cutover, cells often look locally green on a single toolchain stamp while distant cells fail unification.

**Symptoms the agent sees (instruction.md level):**
- Locally green stamps on one toolchain while distant cells fail.
- Generated headers disagree with runtime packing.
- Selected feature sets never reach every language surface.
- Profile-driven configuration disagrees with what the live lattice applies.

**Required outcomes:**
- Every cell in `/app/ops/matrix.toml` reports a successful unify outcome.
- `/output/unify-report.json` is produced via `/app/bin/unify_probe` (not hand-written).
- Each cell reports `status` `ok`, with `abi_stamp` and `pack_width` agreeing across the three language surfaces for that cell's declared profile and feature set.

**Constraints:**
- `[environment] allow_internet = false`; verifier deps in Dockerfile.
- Leave `/app/bin/unify_probe` and `/app/ops/matrix.toml` unchanged.
- No multi-container layout.
- Languages: Rust + Go + C (CMake OBJECT libs).
- Frame as cutover/unification coherence — not repair/debug.

### Failure topology

Four cutover remnants interact under profile-conditional wrongness. First, `lane_m2` still resolves every profile name to the ship path, so fleet cells inherit ship pack widths. Second, `op_q7` drops the facet_x stamp bit on ship-only cells. Third, `hdr_n3` hardcodes pack width 8 whenever facet_y is set instead of honoring the live profile width. Fourth, `cg_p9` mirrors that broken width into cgo/OBJECT flags so header and packing look locally green together until one side is corrected.

The task is hard because greening one stamp fails another matrix cell, the probe is observation-only (no EXPECTED predicates in source), and EXPECTED values live only in tests.

### Environment shape

- `environment/Dockerfile` + `.dockerignore` — Rust + Go + cmake/gcc, offline caches, pytest.
- `environment/r8/` — Rust cdylib + `fwd.rs` stamp forward.
- `environment/g4/` — Go cgo module (auth + packing + emit).
- `environment/c6/` — CMake OBJECT libraries.
- `environment/gen/` — header forge binary sources.
- `environment/host/` — final link of all three surfaces.
- `environment/ops/` — matrix + status script + runbook (discovery only).
- `environment/config/profiles/` — ship/fleet/field (field is decoy-looking).
- `environment/link/` — surface notes (not answer key).
- `environment/tools/unify_probe/` — observation-only compiled runner → `/app/bin/unify_probe`.
- `environment/.cargo/config.toml` — rustflags decoy surface.

### Required artifacts

- `tasks/triple-toolchain-abi-unify-lattice/task.toml` with `allow_internet = false`.
- `tasks/triple-toolchain-abi-unify-lattice/instruction.md` — symptoms-only cutover prose (not repair/debug framing; do not name the four loci).
- `tasks/triple-toolchain-abi-unify-lattice/tests/test.sh`, `tests/test_outputs.py` — eight hard tests; session-cached builds; verifier-owned EXPECTED.
- `tasks/triple-toolchain-abi-unify-lattice/solution/solve.sh` — oracle patches ≥4 loci (≥30 LOC substantive).
- `tasks/triple-toolchain-abi-unify-lattice/environment/**` — 25+ non-Docker files per Initial Draft Commitments.

### Test plan

- `test_k3_tier_alpha_ok` — Ship-only facet_x cell unifies (`status` `ok`).
- `test_w9_tier_beta_ok` — Fleet dual-feature cell unifies.
- `test_m4_mark_alpha` — Alpha `abi_stamp` matches verifier EXPECTED and agrees across surfaces.
- `test_z2_mark_beta` — Beta `abi_stamp` matches EXPECTED and agrees across surfaces.
- `test_t6_span_gamma` — Fleet facet_y release cell has correct `pack_width`.
- `test_n8_span_delta` — Ship+facet_y cell packing agrees with header.
- `test_y1_tri_agree_beta` — Beta header/rust/go/c pack_width and stamps all agree.
- `test_f5_reentry_gamma` — Re-running unify_probe keeps gamma coherent (anti hand-write).

Chain-dependent: stamp/pack tests need successful builds; session fixture builds once. Multiple valid approaches exist (any coherent authority/forward/header/packing reconciliation).

### Drafting guardrails

Do not embed instruction nouns in fix-path function names, parameters, or test names. Instruction uses standard build/FFI language freely. Do not frame as bug-hunt or repair checklist — cutover/build-graph unification only. Do not ship a readable probe that compares against EXPECTED stamp strings. Do not leave all-branches-identical-wrong tables. No HINT/STEP walkthroughs in environment/.

### Triviality Ledger

- Greening only the Rust stamp on alpha fails fleet beta/gamma because authority still returns ship and facet_y pack widths stay hardcoded.
- Fixing header pack width alone leaves cgo/OBJECT still at 8 — locally green pair becomes a distant disagree.
- Fixing packing alone while authority returns ship still feeds wrong pack_from_profile into the forge for fleet cells.
- Fixing authority alone still leaves ship-only facet_x stamp drop and facet_y hardcodes.
- Hand-writing `/output/unify-report.json` fails harness integrity and rebuild/reentry checks.
- Enabling all features globally greens naive compiles but fails per-cell EXPECTED stamps/widths.

### Per-gate Pitfall Inventory

- RC1: Oracle must reconcile authority/forward/header/packing — not delete one hardcode or copy a golden JSON.
- RC3: Tests assert status, abi_stamp, pack_width agreement — not file existence alone.
- RC5: EXPECTED values live in test code only; probe is observation-only.
- RC6: Instruction stays symptoms-only — do not name `op_q7`, `lane_m2`, `hdr_n3`, or `cg_p9`, and do not list the four loci as a checklist.
- RC7: `solve.sh` edits ≥4 loci with substantive logic ≥30 LOC.
- CR1/CR2: Use construction manifest symbols verbatim; flipping-point 2+2+2+2.
- CR7/GX9: Field names `status`/`abi_stamp`/`pack_width` appear in instruction; do not recite per-cell answer triples beyond the contract.
- Static checks: `allow_internet = false`, `.dockerignore`, `.cargo/` COPY present, absolute paths, timeout coherence.

### Initial Draft Commitments

- `tasks/triple-toolchain-abi-unify-lattice/task.toml`
- `tasks/triple-toolchain-abi-unify-lattice/instruction.md`
- `tasks/triple-toolchain-abi-unify-lattice/output_contract.toml`
- `tasks/triple-toolchain-abi-unify-lattice/tests/test.sh`
- `tasks/triple-toolchain-abi-unify-lattice/tests/test_outputs.py`
- `tasks/triple-toolchain-abi-unify-lattice/solution/solve.sh`
- `tasks/triple-toolchain-abi-unify-lattice/environment/Dockerfile`
- `tasks/triple-toolchain-abi-unify-lattice/environment/.dockerignore`
- `tasks/triple-toolchain-abi-unify-lattice/environment/Cargo.toml`
- `tasks/triple-toolchain-abi-unify-lattice/environment/Cargo.lock`
- `tasks/triple-toolchain-abi-unify-lattice/environment/.cargo/config.toml`
- `tasks/triple-toolchain-abi-unify-lattice/environment/ops/matrix.toml`
- `tasks/triple-toolchain-abi-unify-lattice/environment/ops/status_check.sh`
- `tasks/triple-toolchain-abi-unify-lattice/environment/ops/runbooks/ctl_usage.md`
- `tasks/triple-toolchain-abi-unify-lattice/environment/link/surface.toml`
- `tasks/triple-toolchain-abi-unify-lattice/environment/link/legacy.toml`
- `tasks/triple-toolchain-abi-unify-lattice/environment/config/profiles/ship.toml`
- `tasks/triple-toolchain-abi-unify-lattice/environment/config/profiles/fleet.toml`
- `tasks/triple-toolchain-abi-unify-lattice/environment/config/profiles/field.toml`
- `tasks/triple-toolchain-abi-unify-lattice/environment/data/fixtures/seed.json`
- `tasks/triple-toolchain-abi-unify-lattice/environment/r8/Cargo.toml`
- `tasks/triple-toolchain-abi-unify-lattice/environment/r8/build.rs`
- `tasks/triple-toolchain-abi-unify-lattice/environment/r8/src/lib.rs`
- `tasks/triple-toolchain-abi-unify-lattice/environment/r8/src/fwd.rs`
- `tasks/triple-toolchain-abi-unify-lattice/environment/r8/src/slot.rs`
- `tasks/triple-toolchain-abi-unify-lattice/environment/r8/src/map_legacy.rs`
- `tasks/triple-toolchain-abi-unify-lattice/environment/g4/go.mod`
- `tasks/triple-toolchain-abi-unify-lattice/environment/g4/auth.go`
- `tasks/triple-toolchain-abi-unify-lattice/environment/g4/pack.go`
- `tasks/triple-toolchain-abi-unify-lattice/environment/g4/emit.go`
- `tasks/triple-toolchain-abi-unify-lattice/environment/g4/preview.go`
- `tasks/triple-toolchain-abi-unify-lattice/environment/g4/main.go`
- `tasks/triple-toolchain-abi-unify-lattice/environment/c6/CMakeLists.txt`
- `tasks/triple-toolchain-abi-unify-lattice/environment/c6/src/obj_a.c`
- `tasks/triple-toolchain-abi-unify-lattice/environment/c6/src/obj_b.c`
- `tasks/triple-toolchain-abi-unify-lattice/environment/c6/include/obj_api.h`
- `tasks/triple-toolchain-abi-unify-lattice/environment/gen/CMakeLists.txt`
- `tasks/triple-toolchain-abi-unify-lattice/environment/gen/hdr_n3.c`
- `tasks/triple-toolchain-abi-unify-lattice/environment/gen/preview_hdr.c`
- `tasks/triple-toolchain-abi-unify-lattice/environment/gen/main.c`
- `tasks/triple-toolchain-abi-unify-lattice/environment/host/CMakeLists.txt`
- `tasks/triple-toolchain-abi-unify-lattice/environment/host/main.c`
- `tasks/triple-toolchain-abi-unify-lattice/environment/tools/unify_probe/go.mod`
- `tasks/triple-toolchain-abi-unify-lattice/environment/tools/unify_probe/main.go`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: r8/src/fwd.rs
  symbol: op_q7
  kind: function
  signature: fn op_q7(a: u8, b: u8) -> u32
  purpose: Computes the Rust-side ABI stamp contribution from facet bit probes.

- path: g4/auth.go
  symbol: lane_m2
  kind: function
  signature: func lane_m2(a string) string
  purpose: Resolves a profile name to a filesystem path under config/profiles.

- path: gen/hdr_n3.c
  symbol: hdr_n3
  kind: function
  signature: void hdr_n3(int a, int b, int w, const char *path)
  purpose: Writes the shared C ABI header macros for stamp and pack width.

- path: g4/pack.go
  symbol: cg_p9
  kind: function
  signature: func cg_p9(a int, b int, w int) int
  purpose: Selects cgo/OBJECT packing width written into build flags for the cell.

- path: r8/build.rs
  symbol: main
  kind: function
  signature: fn main()
  purpose: Cargo build script that probes env facets and emits cfg for the cdylib.

- path: g4/emit.go
  symbol: writeFlags
  kind: function
  signature: func writeFlags(path string, width int) error
  purpose: Persists packing flags consumed by the CMake OBJECT lane.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: r8/src/fwd.rs
    controls_tests: [test_k3_tier_alpha_ok, test_m4_mark_alpha]
  - id: B
    path: g4/auth.go
    controls_tests: [test_w9_tier_beta_ok, test_z2_mark_beta]
  - id: C
    path: gen/hdr_n3.c
    controls_tests: [test_t6_span_gamma, test_y1_tri_agree_beta]
  - id: D
    path: g4/pack.go
    controls_tests: [test_n8_span_delta, test_f5_reentry_gamma]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: r8/src/map_legacy.rs
  kind: helper
  rhymes_with: op_q7
  non_fix_purpose: Pretty-prints historical stamp fragments for ops docs; not invoked by release cdylib builds.

- path: g4/preview.go
  kind: helper
  rhymes_with: lane_m2
  non_fix_purpose: Lists profile filenames for status_check.sh; does not resolve the live path.

- path: gen/preview_hdr.c
  kind: helper
  rhymes_with: hdr_n3
  non_fix_purpose: Emits a human-readable dump of header macros for ops; unused by unify_probe.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [plugin, host, shared, ABI, header, language, surfaces, matrix, cell, Rust, cdylib, Go, cgo, archive, CMake, OBJECT, libraries, profile, cutover, toolchain, stamp, unification, generated, packing, feature, sets, configuration, lattice, coherence, unify, outcome, report, probe, status, abi_stamp, pack_width, ops, cells]
```
