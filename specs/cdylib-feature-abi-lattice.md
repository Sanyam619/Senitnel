### Decision
GO — Attempt 1. Distributed fix across version-map emission, export gating, and metadata roots; opaque symbols; link-green/load-red trap; dual crate-type + C host matrix.

### Metadata
- version: 2
- Task name: cdylib-feature-abi-lattice
- Title: Cdylib Feature ABI Lattice
- Category: build-and-dependency-management
- Languages: ["Rust", "C"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: ["tool_specific"]
- Tags: ["rust", "cdylib", "ffi", "cargo", "features", "linker"]
- Milestones: 0

## Authoring Brief

### Public contract

A Rust workspace under `/app/` ships a plugin shared library consumed by several C host binaries. After a dual crate-type cutover, some host matrix cells finish the link step yet refuse to load the shared object, while others stop at unresolved or versioned symbols. Feature sets that look coherent still emit incompatible ABIs across release profiles.

**Symptoms the agent sees (instruction.md level):**
- Some host cells link but fail dynamic load.
- Other cells fail at link with unresolved/versioned symbols.
- Clean-looking feature combinations still disagree across release profiles.

**Required outcomes:**
- Every cell in `/app/ops/matrix.toml` both links and loads under its declared feature set and profile.
- `/output/abi-matrix.json` is produced via `/app/bin/abi_probe` (not hand-written).
- Each cell reports `status` `ok`, with `soname` and `symbol_versions` matching expectations under `/app/link/`.

**Constraints:**
- `[environment] allow_internet = false`; verifier deps in Dockerfile.
- No multi-container layout.
- Agent reconciles Cargo workspace, export surface, version map, and host build graph — not a golden JSON rewrite.
- Languages: Rust + C hosts.

### Failure topology

Three cutover remnants interact. First, `knit_map_a` in the cdylib `build.rs` still places facet_a exports under legacy `NEXUS_1` version tags, so hosts that resolve at link time reject the `.so` at dlopen. Second, `gate_sym_b` inverts facet_b export polarity (present on default builds, omitted when facet_b is enabled), so alt hosts miss required `no_mangle` symbols. Third, `write_meta_c` still publishes a legacy soname and Libs line that disagree with the cdylib release link, so release-profile load and `.pc` agreement fail even when export symbols look right.

The task is hard because link success is a false acceptance signal, version scripts and export cfg interact nonlinearly with features, and metadata must agree with the actual cdylib ABI under release.

### Environment shape

- `environment/Dockerfile` + `.dockerignore` — Rust + gcc toolchain, offline cargo cache, pytest.
- `environment/` workspace with crates: `k2` (rlib core), `n6` (optional facet bridge), `q3` (cdylib), `k9` (metadata helper).
- `environment/hosts/` — C host binaries and makefile fragment.
- `environment/ops/` — matrix and runbook (discovery, not instruction-by-reference for the ops contract).
- `environment/link/` — soname/symbol_versions expectations (correct + decoy).
- `environment/pkg/` — pkg-config template.
- `environment/bin/abi_probe` — builds matrix and writes `/output/abi-matrix.json`.
- `environment/.cargo/config.toml` — rustflags decoy surface.

### Required artifacts

- `tasks/cdylib-feature-abi-lattice/task.toml` with `allow_internet = false`.
- `tasks/cdylib-feature-abi-lattice/instruction.md` — symptoms-only cutover prose (not repair/debug framing).
- `tasks/cdylib-feature-abi-lattice/tests/test.sh`, `tests/test_outputs.py` — six hard tests; session-cached builds.
- `tasks/cdylib-feature-abi-lattice/solution/solve.sh` — oracle patches ≥3 loci (≥30 LOC substantive).
- `tasks/cdylib-feature-abi-lattice/environment/**` — 25+ non-Docker files per Initial Draft Commitments.

### Test plan

- `test_r3_tier_alpha_ok` — Primary matrix cell links and loads (`status` `ok`).
- `test_v7_tier_beta_ok` — Alt matrix cell links and loads.
- `test_j2_tagbag_alpha` — Primary `.so` exposes required `NEXUS_2` versioned exports for facet_a.
- `test_h5_tagbag_beta` — Alt `.so` exposes facet_b versioned exports and omits facet_a-only tags.
- `test_p6_opt_dlopen` — Release-profile cell loads successfully (LTO/strip coherent with map).
- `test_c8_meta_match` — `.pc` / probe `soname` and `symbol_versions` agree with `/app/link/` expectations.

Chain-dependent: tagset/load tests need successful builds; session fixture builds once per cell. Multiple valid approaches exist (any coherent feature/map/export/meta reconciliation that satisfies outcomes).

### Drafting guardrails

Do not embed instruction nouns in fix-path function names, parameters, or test names. Instruction uses standard Cargo/FFI language freely. Do not frame as bug-hunt or repair checklist — cutover/build-graph reconciliation only. Do not hide the operational contract in environment README files. No HINT/STEP walkthroughs in environment/.

### Triviality Ledger

- Making only the primary cell link succeeds fails `test_v7_tier_beta_ok` / `test_h5_tagbag_beta` because facet_b export polarity remains inverted.
- Retargeting version tags alone without export gates still fails alt unresolved symbols.
- Fixing exports alone leaves primary cells failing versioned dlopen (`test_r3_tier_alpha_ok` / `test_j2_tagbag_alpha`).
- Fixing map+exports without metadata leaves `test_p6_opt_dlopen` / `test_c8_meta_match` red.
- Hand-writing `/output/abi-matrix.json` without a real `.so` fails tagset and rebuild-from-sources checks.
- Enabling all features globally greens naive compiles but fails alt tagset expectations.

### Per-gate Pitfall Inventory

- RC1: Oracle must reconcile map/export/meta — not delete one version line or copy a golden JSON.
- RC3: Tests assert link+load status, versioned symbol sets, and metadata agreement — not file existence alone.
- RC5: Expected soname/tag values live in test code and `/app/link/` contract named by instruction; no golden JSON under environment/output.
- RC6: Instruction stays symptoms-only cutover language — do not name `knit_map_a`, `gate_sym_b`, or `write_meta_c`.
- RC7: `solve.sh` edits ≥3 loci with substantive logic ≥30 LOC.
- CR1/CR2: Use construction manifest symbols verbatim; flipping-point 2+2+2.
- CR7/GX9: Field names `status`/`soname`/`symbol_versions` appear in instruction; do not recite per-test answer triples beyond contract.
- Static checks: `allow_internet = false`, `.dockerignore`, absolute paths, timeout coherence with cached cargo/cc builds.

### Initial Draft Commitments

- `tasks/cdylib-feature-abi-lattice/task.toml`
- `tasks/cdylib-feature-abi-lattice/instruction.md`
- `tasks/cdylib-feature-abi-lattice/output_contract.toml`
- `tasks/cdylib-feature-abi-lattice/tests/test.sh`
- `tasks/cdylib-feature-abi-lattice/tests/test_outputs.py`
- `tasks/cdylib-feature-abi-lattice/solution/solve.sh`
- `tasks/cdylib-feature-abi-lattice/environment/Dockerfile`
- `tasks/cdylib-feature-abi-lattice/environment/.dockerignore`
- `tasks/cdylib-feature-abi-lattice/environment/Cargo.toml`
- `tasks/cdylib-feature-abi-lattice/environment/.cargo/config.toml`
- `tasks/cdylib-feature-abi-lattice/environment/tools/abi_probe`
- `tasks/cdylib-feature-abi-lattice/environment/ops/matrix.toml`
- `tasks/cdylib-feature-abi-lattice/environment/ops/runbooks/ctl_usage.md`
- `tasks/cdylib-feature-abi-lattice/environment/link/abi_notes.toml`
- `tasks/cdylib-feature-abi-lattice/environment/link/legacy_notes.toml`
- `tasks/cdylib-feature-abi-lattice/environment/pkg/templates/plugin.pc.in`
- `tasks/cdylib-feature-abi-lattice/environment/config/profiles/alpha.toml`
- `tasks/cdylib-feature-abi-lattice/environment/config/profiles/beta.toml`
- `tasks/cdylib-feature-abi-lattice/environment/data/fixtures/seed.json`
- `tasks/cdylib-feature-abi-lattice/environment/k2/Cargo.toml`
- `tasks/cdylib-feature-abi-lattice/environment/k2/src/lib.rs`
- `tasks/cdylib-feature-abi-lattice/environment/k2/src/codec.rs`
- `tasks/cdylib-feature-abi-lattice/environment/n6/Cargo.toml`
- `tasks/cdylib-feature-abi-lattice/environment/n6/src/lib.rs`
- `tasks/cdylib-feature-abi-lattice/environment/q3/Cargo.toml`
- `tasks/cdylib-feature-abi-lattice/environment/q3/build.rs`
- `tasks/cdylib-feature-abi-lattice/environment/q3/src/lib.rs`
- `tasks/cdylib-feature-abi-lattice/environment/q3/src/slot.rs`
- `tasks/cdylib-feature-abi-lattice/environment/q3/src/map_legacy.rs`
- `tasks/cdylib-feature-abi-lattice/environment/k9/Cargo.toml`
- `tasks/cdylib-feature-abi-lattice/environment/k9/src/lib.rs`
- `tasks/cdylib-feature-abi-lattice/environment/k9/src/meta.rs`
- `tasks/cdylib-feature-abi-lattice/environment/k9/src/preview.rs`
- `tasks/cdylib-feature-abi-lattice/environment/hosts/alpha/main.c`
- `tasks/cdylib-feature-abi-lattice/environment/hosts/beta/main.c`
- `tasks/cdylib-feature-abi-lattice/environment/hosts/gamma/main.c`
- `tasks/cdylib-feature-abi-lattice/environment/hosts/mk/lattice.mk`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: q3/Cargo.toml
  symbol: feat_fwd_q3
  kind: config
  purpose: Feature forwarding declarations for q3 optional deps.

- path: q3/build.rs
  symbol: knit_map_a
  kind: function
  signature: fn knit_map_a(a: &str, b: &str, c: &str) -> String
  purpose: Emits linker version-script text from feature environment probes during the cdylib build.

- path: q3/src/slot.rs
  symbol: gate_sym_b
  kind: function
  signature: fn gate_sym_b(a: bool, b: bool) -> u32
  purpose: Selects which no_mangle export arms are compiled for the dual crate-type surface.

- path: q5/build.rs
  symbol: knit_cascade_map
  kind: function
  signature: fn knit_cascade_map(c: &str) -> String
  purpose: Emits version-tag map for the cascade cdylib from feature probes.

- path: q5/src/exports.rs
  symbol: cx_ns_partition
  kind: export-set
  purpose: The cx_ symbol namespace exports for cascade; must not include nx_ symbols.

- path: q5/src/exports.rs
  symbol: cx_trunk_open
  kind: ffi-export
  purpose: Cascade trunk entry point.

- path: q5/src/exports.rs
  symbol: cx_trunk_close
  kind: ffi-export
  purpose: Cascade trunk teardown.

- path: q5/src/exports.rs
  symbol: nx_trunk_open
  kind: stray-export
  purpose: Duplicate nuclide trunk symbol mistakenly left in cascade after split.

- path: q5/src/exports.rs
  symbol: cx_facet_c_open
  kind: ffi-export
  purpose: Cascade facet_c entry point.

- path: q5/src/exports.rs
  symbol: cx_facet_c_close
  kind: ffi-export
  purpose: Cascade facet_c teardown.

- path: q5/Cargo.toml
  symbol: feat_fwd_q5
  kind: config
  purpose: Feature forwarding declarations for q5 optional deps.

- path: k9/src/meta.rs
  symbol: write_meta_c
  kind: function
  signature: fn write_meta_c(a: &str, b: &str, c: &str) -> std::io::Result<()>
  purpose: Emits pkg-config and soname files consumed by host builds and abi_probe.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: q3/Cargo.toml
    controls_tests: [test_v7_tier_beta_ok, test_h5_tagbag_beta]
  - id: B
    path: q3/build.rs
    controls_tests: [test_r3_tier_alpha_ok, test_j2_tagbag_alpha]
  - id: C
    path: q3/src/slot.rs
    controls_tests: [test_h5_tagbag_beta]
  - id: D
    path: q5/build.rs
    controls_tests: [test_w4_cascade_delta_ok, test_m9_cascade_tags, test_f8_dual_partition]
  - id: E
    path: q5/src/exports.rs
    controls_tests: [test_w4_cascade_delta_ok, test_k3_dual_epsilon_ok]
  - id: F
    path: q5/Cargo.toml
    controls_tests: [test_w4_cascade_delta_ok]
  - id: G
    path: k9/src/meta.rs
    controls_tests: [test_p6_opt_dlopen, test_c8_meta_match]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: q3/src/map_legacy.rs
  kind: helper
  rhymes_with: knit_map_a
  non_fix_purpose: Pretty-prints historical map fragments for ops docs; not invoked by release cdylib builds.

- path: k9/src/preview.rs
  kind: helper
  rhymes_with: write_meta_c
  non_fix_purpose: Dry-run metadata printer used by local docs generation; not consumed by abi_probe.

- path: link/legacy_notes.toml
  kind: config
  non_fix_purpose: Pre-cutover expectations retained for operators. Not authoritative.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [plugin, workspace, shared-object, ABI, host, binaries, dual, crate-type, cutover, matrix, cells, link, load, unresolved, versioned, symbols, feature, sets, ABIs, release, profiles, Cargo, exported, symbol, set, build, graph, agreement, cell, ops, profile, abi-matrix, abi_probe, status, soname, symbol_versions, expectations, cascade, nuclide, version, tag, namespace]
```
