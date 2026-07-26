### Decision
GO — Attempt 1. Build-and-dependency-management matrix contract: Cargo workspace splits a shared artifact into a proc-macro crate plus a cdylib; three coupled loci (feature forward into the macro, version-tag namespace isolation, pkg-config dual emit / release path); opaque symbols; probe-produced `/output/abi-matrix.json`; distinct from accepted `cdylib-feature-abi-lattice` (macro+cdylib, not two cdylibs).

### Metadata
- version: 2
- Task name: cargo-proc-macro-feature-isolation
- Title: Proc Macro Feature Isolation
- Category: build-and-dependency-management
- Languages: [Rust, C]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: [tool_specific]
- Tags: [cargo, proc-macro, cdylib, features, abi-matrix]
- Milestones: 0

## Authoring Brief

### Public contract

A Cargo workspace under `/app` builds a proc-macro crate and a cdylib consumed by C host binaries across the feature-set and profile matrix declared in `/app/ops/matrix.toml`. After a split from a single shared artifact, some matrix cells fail to compile, some load with missing symbols, and one dual-load cell sees version-tag collisions between macro-generated symbols and the cdylib. The pkg-config layer still describes a pre-split single artifact. Feature sets that should enable transitive dependency code have no effect on the macro path. Release-profile cells that go through pkg-config can resolve a stale library path.

Bring the Cargo feature graph, exported symbol surfaces, version-tag namespaces, and pkg-config emission into mutual agreement so every cell listed in `/app/ops/matrix.toml` passes. Produce `/output/abi-matrix.json` **only** through `/app/bin/abi_probe` (not by hand). Each cell must report `status` equal to `ok`. The dual-load cell must show disjoint version-tag families between the proc-macro-generated surface and the cdylib. Do not rewrite expected cell ids in `/app/ops/matrix.toml`; fix the build graph.

Report shape (details in `/app/ops/runbooks/ctl_usage.md` and probe docs):

- `schema_tag` (string)
- `cells` (array) — one object per matrix cell with at least `id`, `status`, `features`, `profile`, `artifact_kind`, `version_tags` (array of strings)
- Dual-load cell additionally reports `tag_families` (object mapping artifact id → tag list) that must be disjoint

### Failure topology

Cluster A: feature-gated transitive symbols never appear in hosts that enable those features — the proc-macro crate does not forward/unify workspace features into its expand path, so generated glue omits gated exports while the cdylib side may still look fine. Cluster B: dual-load (or same-process hosts) see colliding version-tag symbol names — macro-emitted tags and cdylib `#[no_mangle]` tags share one namespace / prefix. Cluster C: release cells via pkg-config link the wrong `.so` or a pre-split name — `.pc` templates / build.rs emit still describe a single legacy library, and release install paths rematerialize that legacy name.

These interact: fixing only features can green compile cells while dual-load still collides; fixing only tag prefixes leaves release pkg-config stale; fixing only `.pc` leaves feature cells missing symbols. The agent must coordinate all three.

### Environment shape

- **`environment/` workspace root** — Cargo workspace members (opaque crate dirs).
- **Proc-macro member** — expands host-facing glue / version tags (fix locus A touches feature forward).
- **cdylib member** — exported C ABI + version tags (fix locus B touches tag namespace).
- **Supporting crates** — transitive feature-gated code the macro/cdylib should pull.
- **`environment/pkg/`** — `.pc.in` templates and emission (fix locus C).
- **`environment/hosts/`** — C hosts for matrix cells including one dual-load host.
- **`environment/ops/matrix.toml`** — declared cells (ids frozen).
- **`environment/config/profiles/`** — profile snippets (debug/release / ship-like).
- **`environment/tools/abi_probe`** — sealed/observation binary that builds hosts and writes the report (sources stripped or not shipped if binary-only; if built in-image, strip answer predicates from solver-visible source).
- **`environment/link/`** — abi notes / legacy decoy notes.
- **`environment/data/fixtures/`** — seed inputs for probe.
- **`environment/ops/runbooks/`** — ctl/probe usage (outcomes, not fix recipes).

### Required artifacts

- `tasks/cargo-proc-macro-feature-isolation/instruction.md` — build-graph framing (features, symbols, pkg-config, matrix); no `make`/`cargo build` as the task; no answer-key feature table.
- `tasks/cargo-proc-macro-feature-isolation/task.toml` — category `build-and-dependency-management`, languages Rust+C, `allow_internet = false`, `tool_specific` ok.
- `tasks/cargo-proc-macro-feature-isolation/output_contract.toml`
- `tasks/cargo-proc-macro-feature-isolation/environment/Dockerfile` + `.dockerignore`
- `tasks/cargo-proc-macro-feature-isolation/tests/test.sh` + `test_outputs.py` (≥8 tests)
- `tasks/cargo-proc-macro-feature-isolation/solution/solve.sh`
- Full environment tree per Initial Draft Commitments (25+ substantive files)

### Test plan

1. **test_report_surface** — `/output/abi-matrix.json` exists; schema keys; produced only after probe (mtime/rebuild path as needed).
2. **test_all_cells_ok** — every matrix.toml cell id present with `status=ok`.
3. **test_feature_cell_symbols** — a feature-on cell exports the gated symbol set the probe records (not empty).
4. **test_feature_off_absent** — feature-off cell does not export the gated symbol.
5. **test_dual_load_disjoint** — dual-load cell `tag_families` sets are disjoint.
6. **test_pc_names** — installed/generated `.pc` files name both artifacts (no single legacy `Libs:` only).
7. **test_release_pc_path** — release-profile cell resolves lib path under the release install prefix (not debug/legacy).
8. **test_probe_reentry** — re-running abi_probe keeps the same ok matrix (idempotent).
9. **test_matrix_ids_frozen** — matrix.toml cell id set unchanged from image seed (hash or content check in tests).
10. **test_no_handwritten_bypass** — verifier invokes probe (or rebuilds probe inputs) so a static forged JSON without building hosts fails.

Multiple valid Cargo layouts pass if matrix outcomes hold.

### Drafting guardrails

Instruction leads with build-graph reconciliation (features, exports, version tags, pkg-config), not “fix the Rust bug.” Do not list expected symbol names as an answer key in instruction; point at matrix + probe outcomes. Opaque crate/dir names (`m4`, `d7`, `p2`, …) — not `proc_macro_fix`. No readable probe source that prints EXPECTED stamps as a recipe if that collapses the task; prefer compiled probe + matrix-driven checks. Forbidden: rewriting matrix expected ids as the solve.

### Triviality Ledger

- Editing only cdylib `Cargo.toml` features greens some host cells but leaves macro-expanded glue without gated symbols (feature-forward locus).
- Renaming only cdylib tag strings leaves macro-emitted tags colliding on dual-load.
- Hand-updating `.pc` files without build.rs/emission authority gets overwritten on probe rebuild / install.
- Hand-writing `/output/abi-matrix.json` fails verifier re-entry that runs abi_probe.
- Grepping “version” / flipping one `crate-type` is insufficient — three loci must agree.

### Per-gate Pitfall Inventory

- **RC1**: Oracle edits ≥3 substantive sites (macro features, tag namespace, pc emit), not deletions.
- **RC2**: No broken_/buggy_/golden_ names on solver-visible paths.
- **RC3**: Tests assert symbol presence, disjoint tags, and pc paths — not schema-only.
- **RC4/RC5**: EXPECTED cell outcomes live in tests / sealed probe behavior, not agent-writable goldens under environment/.
- **RC6**: Instruction symptoms/outcomes only; no “set feature X in crate Y” recipe.
- **RC7**: Oracle LOC ≥30 across three sites.
- **GX9/GX10**: Do not paste full symbol lists or polarity pairs that recite the answer key.
- **static**: allow_internet=false; 20+ env files; .dockerignore; never COPY hidden `.cargo/` — seed non-hidden and RUN materialize if needed.
- **category**: Frame as build matrix / feature propagation / packing / linking — not “repair the plugin host.”

### Initial Draft Commitments

- `environment/Cargo.toml`
- `environment/Cargo.lock`
- `environment/.dockerignore`
- `environment/Dockerfile`
- `environment/m4/Cargo.toml`
- `environment/m4/src/lib.rs`
- `environment/m4/src/expand.rs`
- `environment/d7/Cargo.toml`
- `environment/d7/build.rs`
- `environment/d7/src/lib.rs`
- `environment/d7/src/exports.rs`
- `environment/d7/src/tags.rs`
- `environment/p2/Cargo.toml`
- `environment/p2/src/lib.rs`
- `environment/p2/src/gated.rs`
- `environment/k9/Cargo.toml`
- `environment/k9/src/lib.rs`
- `environment/k9/src/preview.rs`
- `environment/pkg/templates/flux_macro.pc.in`
- `environment/pkg/templates/flux_cdylib.pc.in`
- `environment/pkg/templates/legacy_mono.pc.in`
- `environment/ops/matrix.toml`
- `environment/ops/runbooks/ctl_usage.md`
- `environment/config/profiles/debug.toml`
- `environment/config/profiles/release.toml`
- `environment/link/abi_notes.toml`
- `environment/link/legacy_notes.toml`
- `environment/hosts/mk/lattice.mk`
- `environment/hosts/alpha/main.c`
- `environment/hosts/beta/main.c`
- `environment/hosts/gamma/main.c`
- `environment/hosts/delta/main.c`
- `environment/hosts/epsilon/main.c`
- `environment/data/fixtures/seed.json`
- `environment/tools/abi_probe` (prebuilt) OR `environment/tools/probe/` sources built then stripped per Dockerfile
- `instruction.md`
- `task.toml`
- `output_contract.toml`
- `tests/test.sh`
- `tests/test_outputs.py`
- `solution/solve.sh`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: environment/m4/src/expand.rs
  symbol: knit_a
  kind: function
  signature: fn knit_a(spec: &SpecX) -> BundleY
  purpose: Builds the expanded token bundle used by downstream hosts.

- path: environment/d7/src/tags.rs
  symbol: stamp_b
  kind: function
  signature: fn stamp_b(lane: u8) -> &'static [u8]
  purpose: Returns the version-tag byte prefix for exported symbols.

- path: environment/d7/build.rs
  symbol: emit_c
  kind: function
  signature: fn emit_c(profile: &str, root: &Path) -> std::io::Result<()>
  purpose: Writes pkg-config text for the active profile into the install tree.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: environment/m4/src/expand.rs
    controls_tests: [test_feature_cell_symbols, test_feature_off_absent, test_report_surface]
  - id: B
    path: environment/d7/src/tags.rs
    controls_tests: [test_dual_load_disjoint, test_all_cells_ok, test_probe_reentry]
  - id: C
    path: environment/d7/build.rs
    controls_tests: [test_pc_names, test_release_pc_path, test_matrix_ids_frozen, test_no_handwritten_bypass]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: environment/k9/src/preview.rs
  kind: helper
  rhymes_with: knit_a
  non_fix_purpose: Optional dry-run preview of expand input shapes for runbook smoke; not on the host matrix path.

- path: environment/d7/src/map_legacy.rs
  kind: helper
  rhymes_with: stamp_b
  non_fix_purpose: Maps legacy mono tag strings for docs examples; dual-load must not use this namespace.

- path: environment/link/legacy_notes.toml
  kind: config-reader
  rhymes_with: emit_c
  non_fix_purpose: Historical single-artifact pc notes; emission must not prefer this over dual templates.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [workspace, proc, macro, cdylib, feature, features, profile, matrix, host, hosts, symbol, symbols, version, tag, tags, collision, pkg-config, pkgconfig, probe, artifact, dual, load, split, export, exports, transitive, release, debug, status, cell, cells]
```
