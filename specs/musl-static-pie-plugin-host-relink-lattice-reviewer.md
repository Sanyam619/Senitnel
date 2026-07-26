### Decision
GO — Attempt 1. Distributed fix across musl host link emission, Rust ABI slot packing, and Go cgo flag emission; opaque symbols; glibc-green / musl-red trap; three-language plugin lattice under static-PIE constraints.

### Metadata
- Task name: musl-static-pie-plugin-host-relink-lattice
- Title: Musl Static-PIE Relink
- Category: build-and-dependency-management
- Languages: ["C", "Rust", "Go"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: ["tool_specific"]
- Tags: ["musl", "static-pie", "cgo", "cdylib", "ffi", "linker"]
- Milestones: 0

### Discovery budget
- Discovery: `knit_xv_a` still emits initial-exec TLS and omits coherent static-PIE musl flags for the target lane, so hosts that finish the link step fail TLS init when loading plugins
  Planned location: `h4/mk/knit_xv_a.mk`
  Why instruction must not reveal it: Naming the TLS/PIE flag set collapses to a one-makefile rewrite.

- Discovery: `fold_slot_b` packs the shared frame under inverted feature polarity relative to `include/frame.h`, so C host and Go cgo stubs disagree with the cdylib layout even when symbols resolve
  Planned location: `p7/src/slot.rs`
  Why instruction must not reveal it: Naming the packing polarity becomes a single cfg flip recipe.

- Discovery: `emit_xv_c` still publishes CGO flags that pull the glibc include/link path, so supervisor cells stay green on the builder lane and red on the musl target lane
  Planned location: `g3/emit_xv.go`
  Why instruction must not reveal it: Pointing at the cgo emitter removes the cross-toolchain coupling the task tests.

### Anti-trivialization verdict
| # | Check | Verdict | Reasoning |
|---|-------|---------|-----------|
| 1 | Disclosure-collapse | PASS | Symptoms-only; omits TLS model, packing polarity, cgo flag path |
| 2 | Hidden-instance | PASS | Fixed multi-cell matrix topology, not hunt-one-file |
| 3 | Single-artifact repair | PASS | Requires host/Rust/Go three-root coordination |
| 4 | Generalization | PASS | Tests cover primary/alt/opt/supervisor cells + contract fields |
| 5 | Prompt-honesty | PASS | Honest prompt does not name knit_xv_a / fold_slot_b / emit_xv_c |
| 6 | Cheating-vs-difficulty | PASS | Offline musl/rust/go toolchain is harness realism |
| 7 | Mechanical-fix filter | PASS | Not deps/timeout-only |
| 8 | Localized-fix | PASS | Fix spans h4 / p7 / g3 roots |
| 9 | Oracle-locality | PASS | Oracle edits three distinct emission/packing sites |
| 10 | Small declarative-cluster | PASS | Not one config block; TLS/ABI/cgo interact nonlinearly |
| 11 | Grep-collapse | PASS | Opaque symbols; instruction nouns banned on fix path |
| 12 | Pre-factored-helper | PASS | Helpers named knit_xv_a/fold_slot_b/emit_xv_c, not validate/fix |
| 13 | Recipe-discount | PASS | Not single Cargo feature flip or Go-MVS-only |
| 14 | Security-aura discount | PASS | N/A build category |
| 15 | Orthogonal-checklist | PASS | Outcomes couple through shared TLS/ABI/cgo lattice |
| 16 | Harness-discount | PASS | Docker/musl toolchain is realism only |
| 17 | One-pass solvability | PASS | Glibc-green musl-red + three interacting loci block one-pass |
| 18 | Hard-only gate | PASS | Clearly hard multi-toolchain static-PIE plugin lattice |
| 19 | Discovery budget test | PASS | Three non-trivial discoveries committed |
| 20 | Instruction specificity test | PASS | symptoms-only level |
| 21 | Topology distribution test | PASS | Three topologies each with ≥3 coordinating locations |

### Topology enumeration (3 candidate fix topologies)
- T1 Host-first lattice: `h4/mk/knit_xv_a.mk`, `h4/src/loader.c`, `include/slot_api.h` — host flags alone still leave Rust packing and cgo flags wrong.
- T2 Packing-first lattice: `p7/src/slot.rs::fold_slot_b`, `include/frame.h`, `p7/Cargo.toml` features — packing-only fix leaves TLS init and supervisor lane red.
- T3 Cgo-first lattice: `g3/emit_xv.go::emit_xv_c`, `g3/main.go`, `config/profiles/target.toml` — cgo-only fix leaves host TLS and frame ABI mismatch.

### Rubric axes
- Verifiable: PASS — Deterministic musl/cargo/go builds, load outcomes, contract field checks.
- Well-specified: PASS — Matrix cells must load with status ok and plugin_abi/tls_model agreed.
- Solvable: PASS — Expert C/Rust/Go build engineer solvable in a few hours.
- Difficult: PASS — Multi-toolchain static-PIE + ABI lattice beyond undergrad labs.
- Interesting: PASS — Real sensor-gateway plugin ship work paid engineers do.
- Outcome-verified: PASS — Grades load matrix and contract agreement, not process.

### Hardness axes
- Discover: PASS — Solver must recover wrong TLS/PIE emission, inverted packing polarity, and glibc-shaped cgo flags from code/runtime.
- Synthesize: PASS — Host link, Rust cdylib packing, and Go cgo flags must agree as one lattice.
- Diagnose: PASS — Instruction reports load/TLS/symbol symptoms without naming causes.
- Navigate coupling: PASS — Fixing one toolchain leaves the other two cells red.
- Reason beyond training: PASS — Not Cargo-feature-only or Go-MVS-only; three languages under static-PIE constraints.

### Instruction completeness test
Cannot solve from instruction.md alone: must discover which authority wins for feature unification, whether failure is relocation vs TLS vs ABI layout, and that binary existence ≠ plugin load under PIE constraints.

## Reviewer Appendix

### Implementation plan
Environment contains a C musl static-PIE host (`h4`), Rust cdylib (`p7`/`k2`), Go cgo supervisor (`g3`), shared headers, ops matrix with an existence-only status decoy, and `lattice_probe` that builds every matrix cell and writes `/output/lattice-report.json`. Broken state: host flag emitter, Rust packing gate, and cgo flag writer disagree after a toolchain bump. Agent must reconcile all three so every cell loads with contract-matching `plugin_abi` and `tls_model`. Hardness is the glibc-green/musl-red trap plus cross-language ABI coupling.

### Proposed file inventory
Matches Authoring Brief Initial Draft Commitments (25+ non-Docker environment files): Dockerfile, .dockerignore, Cargo workspace, h4 host, p7/k2 crates, g3 module, include headers, ops/link/config/data, lattice_probe.

### Oracle notes
`solve.sh` patches `knit_xv_a` to emit musl static-PIE + global-dynamic TLS flags for the target lane; corrects `fold_slot_b` polarity so wide/narrow packing matches `frame.h` under the active feature; rewrites `emit_xv_c` to emit musl-oriented CGO_CFLAGS/LDFLAGS. Then runs `lattice_probe`. Substantive LOC ≥ 30 across three roots.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
Must retarget host TLS/PIE emission, invert Rust packing polarity correctly, and align cgo flags with the musl target lane — one-file patch cannot satisfy primary/alt/supervisor tests together.

Likely editable frontier:
- h4/mk/knit_xv_a.mk
- p7/src/slot.rs
- g3/emit_xv.go

Requirement-to-file map:
- musl static-PIE TLS load -> h4/mk/knit_xv_a.mk
- plugin_abi frame agreement -> p7/src/slot.rs
- supervisor musl lane -> g3/emit_xv.go

Oracle estimated complexity: 80–120 lines non-boilerplate logic

Red flags:
- none

Residual hardness:
Three-way TLS/ABI/cgo coupling plus existence-only status decoy remains after the tree is visible.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
gateway, tree, cutover, musl, static-PIE, host, Rust, plugins, Go, cgo, supervisor, profile, matrix, cells, binaries, load, symbol, resolution, TLS, init, startup, glibc, builder, lane, target, Ops, status, scripts, disk, link, line, plugin, ABI, surface, compile, flags, agreement, PIE, constraints, lattice-report, lattice_probe, cell, plugin_abi, tls_model, contract

**Renames during drafting:**
- [`host/` → `h4/`: Path token matched instruction noun host.]
- [`plugin/` → `p7/`: Path token matched instruction noun plugin.]
- [`supervisor/` → `g3/`: Path token matched instruction noun supervisor.]
- [`emit_tls_flags` → `knit_xv_a`: Symbol echoed TLS/link nouns.]
- [`gate_abi_pack` → `fold_slot_b`: Symbol echoed ABI noun.]
- [`write_cgo_flags` → `emit_xv_c`: Symbol echoed cgo/flags nouns.]
- [`test_host_musl_load` → `test_k2_tier_alpha_pass`: host/musl/load collided.]
- [`test_abi_match` → `test_w3_frame_match`: abi collided.]

**Test names audited:**
- test_k2_tier_alpha_pass
- test_m5_tier_beta_pass
- test_r8_mode_match
- test_w3_frame_match
- test_n4_opt_tier_pass
- test_j7_supv_pass

**Concentration math:**
- Total tests across `flipping_point_contract`: 6
- Per location:
  - L1 (`h4/mk/knit_xv_a.mk`): 2/6 = 0.333333
  - L2 (`p7/src/slot.rs`): 2/6 = 0.333333
  - L3 (`g3/emit_xv.go`): 2/6 = 0.333333
- Cap: 0.5. Max ratio observed: 0.333333. Status: PASS

### Per-test feasibility pre-check
- Test: test_k2_tier_alpha_pass — Checks primary cell status ok — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_m5_tier_beta_pass — Checks alt cell status ok — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_r8_mode_match — Checks tls_model vs contract — Valid approaches: 2+ — Chain-dependent: soft (needs build) — Feasibility risk: LOW
- Test: test_w3_frame_match — Checks plugin_abi vs contract — Valid approaches: 2+ — Chain-dependent: soft — Feasibility risk: LOW
- Test: test_n4_opt_tier_pass — Checks opt cell status ok — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_j7_supv_pass — Checks supervisor cell status ok — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
