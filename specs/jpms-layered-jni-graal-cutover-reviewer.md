### Decision
GO — Attempt 1. Distributed fix across jlink/ModuleLayer root selection, shade relocation for JNI-visible types, and Graal reachability emission; opaque symbols; cutover framing (no repair/debug); hard multi-mode outcome tests only; distinct from APT/BOM cutover.

### Metadata
- Task name: jpms-layered-jni-graal-cutover
- Title: JPMS JNI Graal Cutover
- Category: build-and-dependency-management
- Languages: ["Java", "C"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: ["tool_specific"]
- Tags: ["java", "jni", "jpms", "jlink", "graal", "native-image"]
- Milestones: 0

### Discovery budget
- Discovery: knit_a omits SPI from jlink/ModuleLayer roots and skips service binding
  Planned location: k9/src/main/java/io/helix/kz/knit_a.java
  Why instruction must not reveal it: Naming the omitted root collapses to a one-line add-modules edit.
- Discovery: fold_b relocates JNI-visible bridge types while C FindClass keeps the pre-relocation name
  Planned location: p7/src/main/java/io/helix/qx/fold_b.java
  Why instruction must not reveal it: Naming the relocation prefix becomes a string-replace recipe.
- Discovery: sieve_c emits sparse reachability metadata omitting SPI and NativeHook entries
  Planned location: m2/src/main/java/io/helix/ry/sieve_c.java
  Why instruction must not reveal it: Listing missing entries removes Graal-metadata discovery.

### Anti-trivialization verdict
All 21 checks PASS — see attempt evidence JSON. Not hidden-instance, not single-artifact, not APT/BOM checklist, not repair/debug framing.

### Topology enumeration (3 candidate fix topologies)
- T1 Layer-first: knit_a → fold_b → sieve_c (≥3 loci; jlink-only insufficient)
- T2 Relocation-first: fold_b → sieve_c → knit_a (≥3 loci; shade-only insufficient)
- T3 Reachability-first: sieve_c → fold_b → knit_a (≥3 loci; metadata-only insufficient)

### Rubric axes
- Verifiable: PASS — deterministic packctl JSON
- Well-specified: PASS — status/spi_bound/jni_bridge/reflect_kept contract
- Solvable: PASS — expert packaging engineer hours
- Difficult: PASS — three packaging authorities + JNI
- Interesting: PASS — real cutover work
- Outcome-verified: PASS — grades report fields

### Hardness axes
- Discover: PASS — three hidden packaging drifts
- Synthesize: PASS — JVM/jlink/native lattice
- Diagnose: PASS — symptoms-only mode disagreement
- Navigate coupling: PASS — each partial fix leaves other modes red
- Reason beyond training: PASS — not APT/BOM or single module-info recipe

### Instruction completeness test
Cannot solve from instruction.md alone: must recover omitted SPI roots, shade/JNI name skew, and sparse reachability from the codebase and probe behavior.

## Reviewer Appendix

### Implementation plan
Ship a JDK 21 + gcc environment with four JPMS units (api/spi/bridge/app), three pack drivers (layer/shade/reachability), a JNI `.so`, and `packctl` that builds, shades, jlinks, and native-probes into `/output/pack-report.json`. Broken cutover leaves dry-runs green while modes disagree. Oracle patches `knit_a`, `fold_b`, and `sieve_c` to restore agreement. Native-image semantics are implemented by a project reachability driver (offline-safe) that prunes to metadata-kept types — authentic Graal reachability contract without shipping full GraalVM.

### Proposed file inventory
Matches Initial Draft Commitments in the authoring spec (≥25 non-Docker environment files): units a1/b2/c3/d4, pack k9/p7/m2 with drivers+decoys, native hook+Makefile, tools/packctl, ops/link/config/data, Dockerfile, .dockerignore.

### Oracle notes
`solve.sh` rewrites `knit_a.apply` to include `helix.spi` and bind services; rewrites `fold_b.apply` to leave `io.helix.bridge.` names unrelocated (identity for JNI-visible prefix); rewrites `sieve_c.apply` to emit reflect/jni entries for SPI provider and NativeHook. Then rebuilds via packctl semantics are exercised by tests.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
Must change three functions across three pack roots; one-file patch cannot pass all six tests.

Likely editable frontier:
- k9/.../knit_a.java
- p7/.../fold_b.java
- m2/.../sieve_c.java

Requirement-to-file map:
- jlink status/spi_bound -> knit_a
- JVM status/jni_bridge -> fold_b
- native status/reflect_kept -> sieve_c

Oracle estimated complexity: 60–100 lines non-boilerplate

Red flags:
- none if instruction stays symptoms-only and packctl is not a golden writer

Residual hardness:
Mode disagreement plus shade/JNI name skew plus reachability pruning remain after the tree is visible.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
Java, control, plane, cutover, layered, module, runtime, images, native, packaging, JNI, shared, library, Modular, JVM, launches, dry-runs, packctl, pack-report, jlink, launch, modes, ship, roster, matrix, notes, module-graph, shade, relocation, bridge, classes, reachability, metadata, agreement, status, spi_bound, jni_bridge, reflect_kept, report, probe, stand-in, ops, link, pack-notes, tools, output, Graal

**Renames during drafting:**
- `resolve_layer_roots` → `knit_a`: echoed layered/module
- `apply_shade_relocation` → `fold_b`: echoed shade/relocation
- `emit_reachability` → `sieve_c`: echoed reachability
- `test_jlink_spi_ok` → `test_m8_w_ok`: jlink/spi collision
- `modules/` → `unit/`: path token module

**Test names audited:**
- test_k4_v_ok
- test_m8_w_ok
- test_q2_x_ok
- test_t6_y_ok
- test_w1_z_ok
- test_n9_u_ok

**Concentration math:**
- Total tests across flipping_point_contract: 6
- Per location:
  - L1 (knit_a): 2/6 = 0.333
  - L2 (fold_b): 2/6 = 0.333
  - L3 (sieve_c): 2/6 = 0.333
- Cap: 0.5. Max ratio observed: 0.333. Status: PASS

### Per-test feasibility pre-check
- Test: test_k4_v_ok — Checks JVM status ok — Valid approaches: 2+ — Chain-dependent: session packctl — Feasibility: LOW
- Test: test_m8_w_ok — Checks jlink status ok — Valid approaches: 2+ — Chain-dependent: session packctl — Feasibility: LOW
- Test: test_q2_x_ok — Checks native status ok — Valid approaches: 2+ — Chain-dependent: session packctl — Feasibility: LOW
- Test: test_t6_y_ok — Checks jlink spi_bound true — Valid approaches: 2+ — Chain-dependent: session packctl — Feasibility: LOW
- Test: test_w1_z_ok — Checks JVM jni_bridge true — Valid approaches: 2+ — Chain-dependent: session packctl — Feasibility: LOW
- Test: test_n9_u_ok — Checks native reflect_kept membership — Valid approaches: 2+ — Chain-dependent: session packctl — Feasibility: LOW
