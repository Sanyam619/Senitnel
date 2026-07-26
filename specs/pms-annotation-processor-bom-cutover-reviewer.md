### Decision
GO — Attempt 1. Distributed fix across APT emit slot, modular layer probe, and BOM/wire+processor classpath wiring; opaque symbols; cutover framing (no repair/debug); hard outcome tests only.

### Metadata
- Task name: pms-annotation-processor-bom-cutover
- Title: PMS APT BOM Cutover
- Category: build-and-dependency-management
- Languages: ["Java"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: ["tool_specific"]
- Tags: ["java", "maven", "jpms", "annotation-processing", "bom", "module-path"]
- Milestones: 0

### Discovery budget
- Discovery: knit_a still writes schema companions into io.kestrel.shadow instead of io.kestrel.model
  Planned location: p3/src/main/java/io/kestrel/apt/knit_a.java (class knit_a)
  Why instruction must not reveal it: Naming the shadow package makes the APT fix a one-string replace.

- Discovery: knit_b still stamps cutover sentinel lane=classpath and status=degraded after forming a ModuleLayer
  Planned location: t9/src/main/java/io/kestrel/boot/knit_b.java (class knit_b)
  Why instruction must not reveal it: Naming the sentinel collapses the modular-lane work to flipping two string literals.

- Discovery: root POM property SLOT_C_KEY still selects w0 and pulls p3 onto t9 runtime module path
  Planned location: environment/pom.xml properties + t9 dependency declarations
  Why instruction must not reveal it: Naming the property and artifact ids turns the BOM cutover into a checklist replace.

### Anti-trivialization verdict
| Check | Verdict | Reasoning |
|---|---|---|
| Disclosure-collapse | PASS | Symptoms-only cutover brief omits emit/probe/BOM sites |
| Hidden-instance | PASS | Fixed reactor topology, not hunt-one-file |
| Single-artifact repair | PASS | Requires APT + layer probe + POM coordination |
| Generalization | PASS | Jar content, wire module, APT absence, lane, emitted list |
| Prompt-honesty | PASS | Honest prompt does not name faulty symbols |
| Cheating-vs-difficulty | PASS | Offline m2 cache is harness, not hardness |
| Mechanical-fix filter | PASS | Not deps/timeout-only |
| Localized-fix | PASS | Fix spans three distinct roots |
| Oracle-locality | PASS | Oracle edits processor, boot probe, and parent POM |
| Small declarative-cluster | PASS | Not one config block |
| Grep-collapse | PASS | Opaque symbols; instruction nouns banned on fix path |
| Pre-factored-helper | PASS | Helpers ScanLegacy/ProbeLegacy are non-fix |
| Recipe-discount | PASS | Not textbook single POM version bump |
| Security-aura discount | PASS | N/A build category |
| Orthogonal-checklist | PASS | Outcomes couple through shared reactor |
| Harness-discount | PASS | Docker/Maven offline is realism only |
| One-pass solvability | PASS | Three interacting cutover remnants block one-pass |
| Hard-only gate | PASS | Clearly hard BOM×APT×JPMS cutover |
| Discovery budget test | PASS | Three discoveries committed |
| Instruction specificity test | PASS | symptoms-only |
| Topology distribution test | PASS | Three topologies below |

### Topology enumeration (3 candidate fix topologies)
- T1 APT-first: knit_a package map, q7 annotationProcessorPaths, module-notes class names — package alone insufficient without layer/BOM agreement.
- T2 Probe-first: knit_b sentinel, layerctl classpath, Main entry — probe alone insufficient without emitted schemas and wire artifact.
- T3 BOM-first: SLOT_C_KEY w0→w1, remove p3 runtime dep, w1 Automatic-Module-Name — BOM alone leaves shadow emit and degraded lane.

### Rubric axes
- Verifiable: PASS — Deterministic Maven package + JSON report checks.
- Well-specified: PASS — Ship report fields and notes unambiguous.
- Solvable: PASS — Expert Java/Maven engineer solvable in hours.
- Difficult: PASS — BOM×APT×JPMS coupling beyond undergrad labs.
- Interesting: PASS — Real mid-cutover reactor work.
- Outcome-verified: PASS — Grades jars and report, not process.

### Hardness axes
- Discover: PASS — Shadow emit package, degraded sentinel, SLOT_C_KEY must be recovered from sources.
- Synthesize: PASS — APT, ModuleLayer probe, and BOM dependency selection must agree.
- Diagnose: PASS — Instruction reports symptoms without naming causes.
- Navigate coupling: PASS — Fixing one locus leaves distant report/jar fields wrong.
- Reason beyond training: PASS — Not a single Maven conflict recipe; novel BOM×APT×JPMS coupling.

### Instruction completeness test
Answer: No. Instruction does not name shadow package emission, degraded/classpath sentinel, or SLOT_C_KEY/w0 wiring. Solver must engage the reactor and ops/link notes.

## Reviewer Appendix

### Implementation plan
Environment is a Maven 21 reactor with BOM, annotations, APT, two wire jars (legacy/current), model with @MarkSlot types, service, and boot ModuleLayer probe. Broken cutover leaves shadow APT output, classpath sentinel in knit_b, and parent POM selecting w0 plus p3 runtime on t9. Oracle patches knit_a package target, knit_b status/lane, and pom SLOT_C_KEY / t9 deps. Tests package reactor, inspect model jar, run layerctl, assert hard report fields.

### Proposed file inventory
Matches Authoring Brief Initial Draft Commitments (35+ non-Docker environment files).

### Oracle notes
solve.sh: (1) rewrite knit_a to emit into io.kestrel.model; (2) rewrite knit_b to set status=ok and lane=modular after successful layer form, scan emitted schema simple names, detect wire.core Automatic-Module-Name and apt jar absence; (3) set SLOT_C_KEY=w1 and drop p3 from t9 dependencies. Then mvn -DskipTests package.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
Must change APT emit package, clear probe sentinel, and rewire BOM artifact/runtime APT — single-file patch cannot satisfy all six tests.

Likely editable frontier:
- p3/.../knit_a.java
- t9/.../knit_b.java
- pom.xml / t9/pom.xml

Requirement-to-file map:
- emitted classes in model jar -> knit_a
- status/lane modular ok -> knit_b
- wire.core / apt_on_runtime false -> parent pom wiring

Oracle estimated complexity: 60-120 lines non-boilerplate

Red flags:
- none if instruction stays symptoms-only and symbols stay opaque

Residual hardness:
Three-way APT/layer/BOM coupling plus false-green classpath diagnostics remains after tree is visible.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
PMS, tree, cutover, platform, catalog, JPMS, layout, reactor, build, gaps, units, archives, APT, classes, layerctl, modular, runtime, classpath, checks, alignment, isolation, module-path, packaging, package, model, archive, output, layer-report, status, ship, matrix, ops, notes, link, module-notes, wire, module, name, absence, layer, emitted, class, names, annotation, processor, BOM, jars

**Renames during drafting:**
- [`wire.impl` → `SLOT_C_KEY`: property matched instruction noun wire]
- [`knit_a` class → `knit_a`: opaque symbol per manifest]
- [`knit_b` class → `knit_b`: opaque symbol per manifest]

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
  - L1 (knit_a.java): 2/6 = 0.333
  - L2 (knit_b.java): 2/6 = 0.333
  - L3 (pom.xml): 2/6 = 0.333
- Cap: 0.5. Max ratio observed: 0.333. Status: PASS

### Per-test feasibility pre-check
- Test: test_k4_v_ok — Checks lane==modular — Valid approaches: 2+ — Chain-dependent: yes on package+layerctl — Feasibility risk: LOW
- Test: test_m8_w_ok — Checks model jar schema classes — Valid approaches: 2+ — Chain-dependent: yes on q7 package — Feasibility risk: LOW
- Test: test_q2_x_ok — Checks status==ok — Valid approaches: 2+ — Chain-dependent: yes on layerctl — Feasibility risk: LOW
- Test: test_t6_y_ok — Checks wire_module==wire.core — Valid approaches: 2+ — Chain-dependent: yes on layerctl — Feasibility risk: LOW
- Test: test_w1_z_ok — Checks apt_on_runtime==false — Valid approaches: 2+ — Chain-dependent: yes on layerctl — Feasibility risk: LOW
- Test: test_n9_u_ok — Checks emitted name list — Valid approaches: 2+ — Chain-dependent: yes on APT+layerctl — Feasibility risk: LOW
