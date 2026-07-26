### Decision
GO — Attempt 1. Build matrix contract for proc-macro + cdylib isolation; three coupled loci; opaque symbols; probe-produced report; distinct from `cdylib-feature-abi-lattice`.

### Metadata
- Task name: cargo-proc-macro-feature-isolation
- Title: Proc Macro Feature Isolation
- Category: build-and-dependency-management
- Languages: [Rust, C]
- Difficulty: hard
- Codebase size: small
- Subcategories: [tool_specific]
- Tags: [cargo, proc-macro, cdylib, features, abi-matrix]
- Milestones: 0

### Discovery budget
- Discovery: Proc-macro expand path does not forward/unify workspace feature flags into generated glue, so gated transitive symbols never appear for feature-on cells.
  Planned location: `environment/m4/src/expand.rs` (`knit_a`) + `environment/m4/Cargo.toml` feature declarations
  Why instruction must not reveal it: Naming “forward features into the macro” collapses to a one-file Cargo.toml checklist.

- Discovery: Macro-emitted version-tag prefixes and cdylib `stamp_b` prefixes share one namespace, so dual-load reports colliding tag families.
  Planned location: `environment/d7/src/tags.rs` vs expand-emitted tag literals in `m4`
  Why instruction must not reveal it: Publishing the two prefixes is an answer key.

- Discovery: `emit_c` / `.pc` templates still emit a legacy mono `Libs:` (or release profile rematerializes legacy path), so release cells resolve the wrong artifact.
  Planned location: `environment/d7/build.rs` (`emit_c`) + `environment/pkg/templates/`
  Why instruction must not reveal it: “Fix the pc template” without coupling to features/tags leaves a false local green.

### Anti-trivialization verdict
1 Disclosure-collapse: PASS — honest matrix outcomes still require three authorities.
2 Hidden-instance: PASS — systemic across matrix cells.
3 Single-artifact repair: PASS — three loci.
4 Generalization: PASS — multi-cell matrix including dual-load and release.
5 Prompt-honesty: PASS — symptoms/outcomes; no feature recipe.
6 Cheating-vs-difficulty: PASS — build-graph coupling.
7 Mechanical-fix filter: PASS — N/A at idea stage.
8 Localized-fix: PASS — m4 + d7 tags + build.rs.
9 Oracle-locality: PASS — ≥3 files.
10 Small declarative-cluster: PASS — not one manifest flip.
11 Grep-collapse: PASS — opaque knit_a/stamp_b/emit_c.
12 Pre-factored-helper: PASS — decoy preview/legacy map rhyme but are non-fix.
13 Recipe-discount: PASS — not textbook “add crate-type = cdylib”.
14 Security-aura: PASS — N/A.
15 Orthogonal-checklist: PASS — loci interact.
16 Harness-discount: PASS — matrix hosts are the graded surface.
17 One-pass solvability: PASS — needs probe runs across cells.
18 Hard-only gate: PASS.
19 Discovery budget: PASS — three items.
20 Instruction specificity: PASS — symptoms/outcomes planned.
21 Topology distribution: PASS — three topologies below.

### Topology enumeration (3 candidate fix topologies)
1. **Forward-first**: knit_a feature unify + stamp_b namespace + emit_c dual pc — chosen realization.
2. **Host-first**: change every C host to avoid dual symbols + leave graph wrong — fails probe dual-load and feature cells; still need graph fixes.
3. **Pc-only + rename**: fix templates and rename exports without macro feature forward — feature-on cells still miss transitive symbols; dual-load may still collide via expand path.

### Rubric axes
1 Verifiable: Pass — probe JSON + symbol/pc asserts.
2 Well-specified: Pass — matrix + report fields + dual-load disjointness.
3 Solvable: Pass — Cargo/FFI engineer in a few hours.
4 Difficult: Pass — feature×macro×cdylib×pc coupling.
5 Interesting: Pass — real workspace split pain.
6 Outcome-verified: Pass — matrix ok via probe, not process.

### Hardness axes
- Discover: Must find macro feature isolation, shared tag namespace, legacy pc emit from code/probe failures.
- Synthesize: Macro, cdylib tags, and pc emission must agree.
- Diagnose: Instruction states matrix symptoms, not causes.
- Navigate coupling: One-locus fixes leave other cell classes red.
- Reason beyond training: Not a stock “cdylib tutorial”; proc-macro feature unify × dual-load tags is less common as a graded unit.

### Instruction completeness test
No — instruction does not name which crate forwards features, which prefix to use, or which pc templates are authoritative. Agent must engage the workspace and probe.

## Reviewer Appendix

### Implementation plan
Ship a Cargo workspace with opaque members: `m4` (proc-macro), `d7` (cdylib + build.rs pc emit), `p2` (feature-gated transitive), `k9` (decoy preview). C hosts under `hosts/` cover feature-on, feature-off, release-pc, and dual-load cells per `ops/matrix.toml`. Seed broken defaults: `knit_a` ignores features; `stamp_b` shares prefix with macro tags; `emit_c` writes legacy mono pc. Oracle fixes those three. `abi_probe` builds matrix and writes `/output/abi-matrix.json`. Verifier re-runs probe and asserts cell ok, symbol gates, disjoint families, and pc paths.

### Proposed file inventory
Matches authoring Initial Draft Commitments (≥30 environment files excl. Dockerfile). Distinct crate roles from `cdylib-feature-abi-lattice` (proc-macro member required).

### Oracle notes
`solve.sh` patches `knit_a` to honor/unify workspace features into expand output; rewrites `stamp_b` (and matching macro tag emission) to disjoint prefixes; rewrites `emit_c` to write dual `.pc` files with profile-correct lib paths (stop preferring `legacy_mono.pc.in`). Rebuilds workspace, runs abi_probe.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
Coordinate macro feature forward, tag namespaces, and pc emission — not a single Cargo.toml edit.

Likely editable frontier:
- m4/src/expand.rs
- m4/Cargo.toml (features)
- d7/src/tags.rs
- d7/build.rs
- pkg/templates/*

Requirement-to-file map:
- missing gated symbols -> knit_a / m4 features
- dual-load collisions -> stamp_b (+ macro tag emit)
- release/stale pc -> emit_c / templates

Oracle estimated complexity: 90–160 non-boilerplate lines

Red flags:
- Do not ship readable probe source with EXPECTED symbol tables
- Do not allow matrix.toml edits to “delete hard cells”
- Keep naming away from cdylib-feature-abi-lattice’s q3/q5 if Similarity is strict — this spec uses m4/d7/p2/k9

Residual hardness:
Probe-driven matrix + three interacting build-graph authorities; decoy legacy pc and preview expand mislead one-pass greps.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
workspace, proc-macro, cdylib, host, hosts, feature, features, profile, matrix, compile, load, symbols, dual-load, version-tag, collisions, pkg-config, artifact, transitive, dependency, release, agreement, status, ok, cell, cells, probe, report

**Renames during drafting:**
- `forward_features` → `knit_a`
- `version_tag_prefix` → `stamp_b`
- `write_pkgconfig` → `emit_c`
- crate dirs `proc_macro`/`cdylib` → `m4`/`d7`

**Test names audited:**
- test_report_surface
- test_all_cells_ok
- test_feature_cell_symbols
- test_feature_off_absent
- test_dual_load_disjoint
- test_pc_names
- test_release_pc_path
- test_probe_reentry
- test_matrix_ids_frozen
- test_no_handwritten_bypass

Note: several test names contain instruction nouns (`feature`, `dual_load`, `probe`, `matrix`). Before ship, rename to opaque forms if `collapse_check` grep_resistance on test names is enforced in-repo, e.g.:
- test_report_surface
- test_cells_ok
- test_gate_on_syms
- test_gate_off_absent
- test_families_disjoint
- test_pc_dual
- test_rel_pc_path
- test_probe_twice
- test_roster_ids_frozen
- test_probe_required

**Concentration math:**
- Total tests: 10
- L1 (`m4/src/expand.rs`): 3/10 = 0.30
- L2 (`d7/src/tags.rs`): 3/10 = 0.30
- L3 (`d7/build.rs`): 4/10 = 0.40
- Cap: 0.5. Max: 0.40. Status: PASS

### Per-test feasibility pre-check
- test_report_surface: LOW — schema
- test_all_cells_ok: MEDIUM — needs full graph
- test_feature_cell_symbols: MEDIUM — feature forward
- test_feature_off_absent: LOW/MEDIUM
- test_dual_load_disjoint: MEDIUM — tag namespaces
- test_pc_names: MEDIUM — emit_c
- test_release_pc_path: MEDIUM — profile path
- test_probe_reentry: LOW
- test_matrix_ids_frozen: LOW
- test_no_handwritten_bypass: MEDIUM — probe re-entry

### Draft instruction.md (Step 2b humanize; keep build-graph lead)

```
The workspace under /app/ was recently split from a single shared artifact into a proc-macro crate and a cdylib. Several C host binaries consume them through a matrix of feature-set and profile combinations declared in /app/ops/matrix.toml.

After the split, the host matrix is broken. Some cells fail to compile, others compile but refuse to load. Cells that do load report missing or unexpected symbols. One host loads both surfaces simultaneously and sees version-tag collisions between macro-generated symbols and the cdylib. The pkg-config layer still reflects the pre-split single-artifact layout. Feature sets that should enable transitive dependency code have no effect. Release-profile cells that go through pkg-config can resolve a stale library reference.

Bring the Cargo feature graph, exported symbol surfaces, version-tag namespaces, and pkg-config emission into mutual agreement so every cell listed in /app/ops/matrix.toml passes. Produce /output/abi-matrix.json through /app/bin/abi_probe (not by hand). Each cell must report status ok. The dual-load cell must show disjoint version-tag families between the two surfaces. Do not rewrite expected cell ids in /app/ops/matrix.toml; fix the build graph.
```

### Form paste (Idea Proposal)

**Idea Category:** Build / Compilation / Dependency Management

Task Idea Summary:
```
A Cargo workspace under /app builds a proc-macro crate and a cdylib consumed by C hosts across the feature/profile matrix in /app/ops/matrix.toml. After a split, some cells fail to compile, some load with missing symbols, and one dual-load cell sees version-tag collisions between macro-generated symbols and the cdylib. pkg-config still describes a pre-split single artifact. Bring feature graphs, exported symbol surfaces, version-tag namespaces, and pkg-config emission into agreement so every matrix cell passes via /app/bin/abi_probe writing /output/abi-matrix.json (not by hand). Dual-load must show disjoint version-tag families. Do not rewrite /app/ops/matrix.toml expected cell ids; fix the build graph.
```

Associated Skills:
```
Cargo features; proc-macro isolation; cdylib symbol export; pkg-config emission; linker/version tags; multi-cell build matrices; ABI probes
```

Task Tags:
```
cargo, proc-macro, cdylib, features, abi-matrix
```
