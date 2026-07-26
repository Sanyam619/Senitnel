### Decision
GO — Attempt 1. Distributed fix across musl host link emission, Rust ABI slot packing, and Go cgo flag emission; opaque symbols; glibc-green / musl-red trap; three-language plugin lattice under static-PIE constraints.

### Metadata
- version: 2
- Task name: musl-static-pie-plugin-host-relink-lattice
- Title: Musl Static-PIE Relink
- Category: build-and-dependency-management
- Languages: ["C", "Rust", "Go"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: ["tool_specific"]
- Tags: ["musl", "static-pie", "cgo", "cdylib", "ffi", "linker"]
- Milestones: 0

## Authoring Brief

### Public contract

A sensor gateway under `/app/` ships a musl static-PIE C host, Rust cdylib plugins, and a Go cgo supervisor. After a toolchain bump, CI-green artifacts still fail under the profile matrix in `/app/ops/matrix.toml`: some cells refuse plugin load, others fail symbol resolution or TLS init at startup, and the glibc builder lane stays green while the musl target lane does not. Ops status scripts only confirm binaries exist on disk.

**Symptoms the agent sees (instruction.md level):**
- Matrix cells produce binaries that never load plugins.
- Other cells fail symbol resolution or TLS init at startup.
- Glibc builder lane looks fine; musl target lane does not.
- Status scripts only check that binaries exist.

**Required outcomes:**
- Every cell in `/app/ops/matrix.toml` loads plugins under the host's PIE constraints.
- `/output/lattice-report.json` is produced via `/app/tools/lattice_probe` (not hand-written).
- Each cell reports `status` `ok`, with `plugin_abi` and `tls_model` matching `/app/link/contract.toml`.

**Constraints:**
- `[environment] allow_internet = false`; verifier deps in Dockerfile.
- No multi-container layout.
- Agent reconciles host link emission, Rust plugin ABI surface, and Go cgo compile flags — not a golden JSON rewrite.
- Languages: C, Rust, Go.

### Failure topology

Three cutover remnants interact across toolchains. First, `knit_xv_a` in the C host makefile fragment still emits a glibc-shaped TLS model and omits coherent static-PIE flags for the musl target lane, so hosts that "link" still fail TLS init when loading plugins. Second, `fold_slot_b` in the Rust cdylib still packs the shared frame under the wrong feature polarity, so C headers and Go cgo stubs disagree with the loaded object even when symbols resolve. Third, `emit_xv_c` in the Go supervisor still publishes CGO flags that pull the glibc include/link path, so supervisor cells green on the builder lane and red on the musl target lane.

The task is hard because binary existence is a false acceptance signal, glibc-linked success masks musl/static-PIE issues, and fixing one toolchain breaks another when ABI layout and TLS/relocation constraints disagree.

### Environment shape

- `environment/Dockerfile` + `.dockerignore` — musl-gcc, Rust (musl target), Go with cgo, pytest.
- `environment/h4/` — C static-PIE host sources and makefile fragment (`knit_xv_a`).
- `environment/p7/` — Rust cdylib workspace (core + plugin crate with `fold_slot_b`).
- `environment/g3/` — Go cgo supervisor (`emit_xv_c`).
- `environment/include/` — shared C ABI headers consumed by host and cgo.
- `environment/ops/` — matrix, status decoy script, runbook.
- `environment/link/` — contract.toml (authoritative) + legacy decoy notes.
- `environment/config/profiles/` — builder vs target profile TOMLs.
- `environment/data/fixtures/` — seed/attestation fixtures.
- `environment/tools/lattice_probe` — builds matrix and writes `/output/lattice-report.json`.

### Required artifacts

- `tasks/musl-static-pie-plugin-host-relink-lattice/task.toml` with `allow_internet = false`.
- `tasks/musl-static-pie-plugin-host-relink-lattice/instruction.md` — symptoms-only cutover prose (not repair/debug framing).
- `tasks/musl-static-pie-plugin-host-relink-lattice/tests/test.sh`, `tests/test_outputs.py` — six hard tests; session-cached builds.
- `tasks/musl-static-pie-plugin-host-relink-lattice/solution/solve.sh` — oracle patches ≥3 loci (≥30 LOC substantive).
- `tasks/musl-static-pie-plugin-host-relink-lattice/environment/**` — 25+ non-Docker files per Initial Draft Commitments.

### Test plan

- `test_k2_tier_alpha_pass` — Primary musl static-PIE matrix cell loads (`status` `ok`).
- `test_m5_tier_beta_pass` — Alt feature-set cell loads with coherent frame packing.
- `test_r8_mode_match` — Primary cell `tls_model` matches `/app/link/contract.toml`.
- `test_w3_frame_match` — Alt cell `plugin_abi` matches contract (C/Rust/Go layout agreement).
- `test_n4_opt_tier_pass` — Release/opt supervisor cell loads successfully.
- `test_j7_supv_pass` — Go cgo supervisor cell reports `status` `ok` on musl target lane.

Chain-dependent: mode/frame tests need successful builds; session fixture builds once. Multiple valid approaches exist (any coherent host/Rust/Go reconciliation that satisfies outcomes).

### Drafting guardrails

Do not embed instruction nouns in fix-path function names, parameters, or test names. Instruction uses standard musl/PIE/cgo language freely. Do not frame as bug-hunt or repair checklist — cutover/build-graph reconciliation only. Do not hide the operational contract in environment README files. No HINT/STEP walkthroughs in environment/.

### Triviality Ledger

- Making only the glibc builder lane green fails `test_k2_tier_alpha_pass` / `test_r8_mode_match` because musl static-PIE TLS emission remains wrong.
- Retargeting host TLS/PIE flags alone without Rust packing still fails `test_m5_tier_beta_pass` / `test_w3_frame_match`.
- Fixing Rust packing alone leaves supervisor cells red (`test_n4_opt_tier_pass` / `test_j7_supv_pass`) via glibc-shaped cgo flags.
- Fixing Go cgo flags alone leaves host TLS init and ABI frame mismatch red.
- Hand-writing `/output/lattice-report.json` without real host/plugin/supervisor artifacts fails rebuild-from-sources and contract field checks.
- Enabling all Rust features globally greens naive compiles but fails alt `plugin_abi` expectations.
- Relying on ops status scripts (existence-only) passes NOP-shaped checks but fails every lattice_probe outcome test.

### Per-gate Pitfall Inventory

- RC1: Oracle must reconcile host flags / Rust packing / cgo emission — not delete one line or copy a golden JSON.
- RC3: Tests assert load status, `tls_model`, and `plugin_abi` agreement — not file existence alone.
- RC5: Expected contract values live in test code and `/app/link/contract.toml` named by instruction; no golden JSON under environment/output.
- RC6: Instruction stays symptoms-only cutover language — do not name `knit_xv_a`, `fold_slot_b`, or `emit_xv_c`.
- RC7: `solve.sh` edits ≥3 loci with substantive logic ≥30 LOC.
- CR1/CR2: Use construction manifest symbols verbatim; flipping-point 2+2+2.
- CR7/GX9: Field names `status`/`plugin_abi`/`tls_model` appear in instruction; do not recite per-test answer triples beyond contract.
- Static checks: `allow_internet = false`, `.dockerignore`, absolute paths, timeout coherence with cached musl/cargo/go builds.

### Initial Draft Commitments

- `tasks/musl-static-pie-plugin-host-relink-lattice/task.toml`
- `tasks/musl-static-pie-plugin-host-relink-lattice/instruction.md`
- `tasks/musl-static-pie-plugin-host-relink-lattice/output_contract.toml`
- `tasks/musl-static-pie-plugin-host-relink-lattice/tests/test.sh`
- `tasks/musl-static-pie-plugin-host-relink-lattice/tests/test_outputs.py`
- `tasks/musl-static-pie-plugin-host-relink-lattice/tests/ledgers/harness.sha256`
- `tasks/musl-static-pie-plugin-host-relink-lattice/solution/solve.sh`
- `tasks/musl-static-pie-plugin-host-relink-lattice/environment/Dockerfile`
- `tasks/musl-static-pie-plugin-host-relink-lattice/environment/.dockerignore`
- `tasks/musl-static-pie-plugin-host-relink-lattice/environment/Cargo.toml`
- `tasks/musl-static-pie-plugin-host-relink-lattice/environment/Cargo.lock`
- `tasks/musl-static-pie-plugin-host-relink-lattice/environment/include/frame.h`
- `tasks/musl-static-pie-plugin-host-relink-lattice/environment/include/slot_api.h`
- `tasks/musl-static-pie-plugin-host-relink-lattice/environment/h4/Makefile`
- `tasks/musl-static-pie-plugin-host-relink-lattice/environment/h4/mk/knit_xv_a.mk`
- `tasks/musl-static-pie-plugin-host-relink-lattice/environment/h4/src/main.c`
- `tasks/musl-static-pie-plugin-host-relink-lattice/environment/h4/src/loader.c`
- `tasks/musl-static-pie-plugin-host-relink-lattice/environment/h4/src/preview_ld.c`
- `tasks/musl-static-pie-plugin-host-relink-lattice/environment/p7/Cargo.toml`
- `tasks/musl-static-pie-plugin-host-relink-lattice/environment/p7/src/lib.rs`
- `tasks/musl-static-pie-plugin-host-relink-lattice/environment/p7/src/slot.rs`
- `tasks/musl-static-pie-plugin-host-relink-lattice/environment/p7/src/map_legacy.rs`
- `tasks/musl-static-pie-plugin-host-relink-lattice/environment/k2/Cargo.toml`
- `tasks/musl-static-pie-plugin-host-relink-lattice/environment/k2/src/lib.rs`
- `tasks/musl-static-pie-plugin-host-relink-lattice/environment/g3/go.mod`
- `tasks/musl-static-pie-plugin-host-relink-lattice/environment/g3/go.sum`
- `tasks/musl-static-pie-plugin-host-relink-lattice/environment/g3/main.go`
- `tasks/musl-static-pie-plugin-host-relink-lattice/environment/g3/emit_xv.go`
- `tasks/musl-static-pie-plugin-host-relink-lattice/environment/g3/preview_cg.go`
- `tasks/musl-static-pie-plugin-host-relink-lattice/environment/ops/matrix.toml`
- `tasks/musl-static-pie-plugin-host-relink-lattice/environment/ops/status_check.sh`
- `tasks/musl-static-pie-plugin-host-relink-lattice/environment/ops/runbooks/ctl_usage.md`
- `tasks/musl-static-pie-plugin-host-relink-lattice/environment/link/contract.toml`
- `tasks/musl-static-pie-plugin-host-relink-lattice/environment/link/legacy_notes.toml`
- `tasks/musl-static-pie-plugin-host-relink-lattice/environment/config/profiles/builder.toml`
- `tasks/musl-static-pie-plugin-host-relink-lattice/environment/config/profiles/target.toml`
- `tasks/musl-static-pie-plugin-host-relink-lattice/environment/data/fixtures/seed.json`
- `tasks/musl-static-pie-plugin-host-relink-lattice/environment/tools/lattice_probe`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: h4/mk/knit_xv_a.mk
  symbol: knit_xv_a
  kind: function
  signature: knit_xv_a(a, b)
  purpose: Emits host CC/LD flag fragments from profile probes during the C host build.

- path: p7/src/slot.rs
  symbol: fold_slot_b
  kind: function
  signature: fn fold_slot_b(a: bool, b: bool) -> u32
  purpose: Selects which repr(C) frame packing arm is compiled for the cdylib export surface.

- path: g3/emit_xv.go
  symbol: emit_xv_c
  kind: function
  signature: func emit_xv_c(a string, b string) error
  purpose: Writes CGO_CFLAGS/LDFLAGS consumed by the supervisor build and lattice_probe.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: h4/mk/knit_xv_a.mk
    controls_tests: [test_k2_tier_alpha_pass, test_r8_mode_match]
  - id: B
    path: p7/src/slot.rs
    controls_tests: [test_m5_tier_beta_pass, test_w3_frame_match]
  - id: C
    path: g3/emit_xv.go
    controls_tests: [test_n4_opt_tier_pass, test_j7_supv_pass]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: h4/src/preview_ld.c
  kind: helper
  rhymes_with: knit_xv_a
  non_fix_purpose: Pretty-prints historical LD fragments for ops docs; not invoked by release host builds.

- path: p7/src/map_legacy.rs
  kind: helper
  rhymes_with: fold_slot_b
  non_fix_purpose: Formats legacy packing notes for docs; not linked into the release cdylib.

- path: g3/preview_cg.go
  kind: helper
  rhymes_with: emit_xv_c
  non_fix_purpose: Dry-run CGO flag printer for local docs; not consumed by lattice_probe.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [gateway, tree, cutover, musl, static-PIE, host, Rust, plugins, Go, cgo, supervisor, profile, matrix, cells, binaries, load, symbol, resolution, TLS, init, startup, glibc, builder, lane, target, Ops, status, scripts, disk, link, line, plugin, ABI, surface, compile, flags, agreement, PIE, constraints, lattice-report, lattice_probe, cell, plugin_abi, tls_model, contract]
```
