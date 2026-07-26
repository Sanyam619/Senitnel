### Decision
GO — Attempt 1. Distributed fix across APT emit slot, modular layer probe, and BOM/wire+processor classpath wiring; opaque symbols; cutover framing (no repair/debug); hard outcome tests only.

### Metadata
- version: 2
- Task name: pms-annotation-processor-bom-cutover
- Title: PMS APT BOM Cutover
- Category: build-and-dependency-management
- Languages: ["Java"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: ["tool_specific"]
- Tags: ["java", "maven", "jpms", "annotation-processing", "bom", "module-path"]
- Milestones: 0

## Authoring Brief

### Public contract

A Java Maven multi-module reactor under `/app/` is mid-cutover onto a new platform BOM and JPMS layout. Default reactor builds can look locally coherent while packaged archives omit APT-emitted classes, and `/app/bin/layerctl` fails to publish a modular runtime report that matches the ship matrix.

**Symptoms the agent sees (instruction.md level):**
- Reactor units may compile while packaged model archives omit APT-emitted classes named in `/app/link/module-notes.toml`.
- `/app/bin/layerctl` writes `/output/layer-report.json` with non-ok status and/or wrong wire module / APT-on-runtime fields.
- Ops matrix under `/app/ops/matrix.toml` describes the intended ship module roster without naming broken emit/probe/BOM sites.

**Required outcomes:**
- Full reactor `mvn -DskipTests package` succeeds.
- Model archive contains APT-emitted classes under the package named in module-notes.
- `/output/layer-report.json` from `/app/bin/layerctl` has `status` `ok`, `lane` `modular`, `wire_module` matching notes, `apt_on_runtime` `false`, and `emitted` listing the required class simple names.

**Constraints:**
- `[environment] allow_internet = false`; verifier deps in Dockerfile.
- No multi-container layout; no repair/debug framing in instruction.
- Agent edits reactor POMs / Java sources — not hand-written golden JSON.
- Java + Maven only (plus ops/link notes and layerctl).

### Failure topology

Three coupled cutover remnants interact. First, `knit_a` in the annotation processor still emits schema classes into a legacy shadow package, so the model jar and modular reflection miss the names the ship notes require. Second, `knit_b` in the boot probe still stamps a classpath cutover sentinel (`degraded` / `classpath`) even when a modular layer can form. Third, the root BOM/parent still pulls the legacy wire artifact and keeps the processor jar on the boot runtime module path, so `wire_module` and `apt_on_runtime` disagree with `/app/link/module-notes.toml`.

The task is hard because APT package emission, modular layer reporting, and BOM-mediated wire/processor path selection must agree; classpath-oriented “looks fine” signals do not satisfy the ship report.

### Environment shape

- `environment/Dockerfile` + `.dockerignore` — JDK 21, Maven, offline `.m2` plugin/deps cache, pytest.
- `environment/` Maven reactor: BOM (`z4`), annotations (`m8`), processor (`p3`), wire legacy (`w0`), wire current (`w1`), model (`q7`), service (`s2`), boot (`t9`).
- `environment/bin/layerctl` — modular probe writing `/output/layer-report.json`.
- `environment/ops/` — ship matrix notes (discovery).
- `environment/link/` — module roster / emitted class notes.
- `environment/config/` — profile TOML decoys.
- `environment/data/fixtures/` — checksum-guarded fixtures.

### Required artifacts

- `tasks/pms-annotation-processor-bom-cutover/task.toml` with `allow_internet = false`.
- `tasks/pms-annotation-processor-bom-cutover/instruction.md` — symptoms-only cutover prose (not repair/debug framing).
- `tests/test.sh`, `tests/test_outputs.py` — six hard tests; session-cached reactor package + layerctl.
- `solution/solve.sh` — oracle patches ≥3 loci (≥30 LOC substantive).
- `environment/**` — 25+ non-Docker files per Initial Draft Commitments.

### Test plan

- `test_k4_v_ok` — layer report `lane` is `modular` (not classpath sentinel).
- `test_m8_w_ok` — model jar contains `io/kestrel/model/EventSchema.class` (and sibling schema).
- `test_q2_x_ok` — layer report `status` is `ok`.
- `test_t6_y_ok` — layer report `wire_module` equals `wire.core`.
- `test_w1_z_ok` — layer report `apt_on_runtime` is `false`.
- `test_n9_u_ok` — layer report `emitted` contains required simple names from module-notes.

Chain-dependent: report tests need a successful package + layerctl run (session fixture). Multiple valid approaches exist (any coherent APT/BOM/module-path reconciliation satisfying outcomes).

### Drafting guardrails

Do not embed instruction nouns in fix-path function names, parameters, or test names. Instruction uses standard Maven/JPMS/APT language freely. Do not frame as bug-hunt or repair checklist. Do not hide the operational contract in environment README files — ops notes may describe matrix intent the solver discovers. No HINT/STEP walkthroughs in environment/.

### Triviality Ledger

- Pointing only the BOM at `w1` still leaves shadow APT emission and fails jar/emitted tests.
- Fixing only `knit_a` leaves degraded/classpath sentinel and wrong wire/APT runtime flags.
- Fixing only `knit_b` leaves wrong wire artifact and processor on the runtime module path.
- Hand-writing `/output/layer-report.json` without a real modular layer fails harness integrity / rebuild-from-sources checks.
- Treating a green `mvn test` classpath run as done still fails modular lane and APT-absence checks.

### Per-gate Pitfall Inventory

- RC1: Oracle must reconcile APT emit, layer probe, and BOM wiring — not delete a sentinel line alone or copy a golden report.
- RC3: Tests assert jar class presence, computed report fields, and modular lane — not file existence alone.
- RC5: Expected class names / wire module live in test code and link notes; no golden layer-report under environment/.
- RC6: Instruction stays symptoms-only cutover language — do not name `knit_a`, `knit_b`, or exact POM property keys.
- RC7: `solve.sh` edits ≥3 loci with substantive logic ≥30 LOC.
- CR1/CR2: Use construction manifest symbols verbatim; flipping-point 2+2+2.
- CR7/GX9: Report field names appear in instruction; do not recite per-test answer triples beyond contract.
- Static checks: `allow_internet = false`, `.dockerignore`, absolute paths, timeout coherence with Maven builds.

### Initial Draft Commitments

- `tasks/pms-annotation-processor-bom-cutover/task.toml`
- `tasks/pms-annotation-processor-bom-cutover/instruction.md`
- `tasks/pms-annotation-processor-bom-cutover/output_contract.toml`
- `tasks/pms-annotation-processor-bom-cutover/tests/test.sh`
- `tasks/pms-annotation-processor-bom-cutover/tests/test_outputs.py`
- `tasks/pms-annotation-processor-bom-cutover/solution/solve.sh`
- `tasks/pms-annotation-processor-bom-cutover/environment/Dockerfile`
- `tasks/pms-annotation-processor-bom-cutover/environment/.dockerignore`
- `tasks/pms-annotation-processor-bom-cutover/environment/pom.xml`
- `tasks/pms-annotation-processor-bom-cutover/environment/settings.xml`
- `tasks/pms-annotation-processor-bom-cutover/environment/bin/layerctl`
- `tasks/pms-annotation-processor-bom-cutover/environment/ops/matrix.toml`
- `tasks/pms-annotation-processor-bom-cutover/environment/ops/runbooks/ctl_usage.md`
- `tasks/pms-annotation-processor-bom-cutover/environment/link/module-notes.toml`
- `tasks/pms-annotation-processor-bom-cutover/environment/link/legacy-notes.toml`
- `tasks/pms-annotation-processor-bom-cutover/environment/config/profiles/ship.toml`
- `tasks/pms-annotation-processor-bom-cutover/environment/config/profiles/field.toml`
- `tasks/pms-annotation-processor-bom-cutover/environment/data/fixtures/seed.json`
- `tasks/pms-annotation-processor-bom-cutover/environment/z4/pom.xml`
- `tasks/pms-annotation-processor-bom-cutover/environment/m8/pom.xml`
- `tasks/pms-annotation-processor-bom-cutover/environment/m8/src/main/java/io/kestrel/marks/MarkSlot.java`
- `tasks/pms-annotation-processor-bom-cutover/environment/m8/src/main/java/module-info.java`
- `tasks/pms-annotation-processor-bom-cutover/environment/p3/pom.xml`
- `tasks/pms-annotation-processor-bom-cutover/environment/p3/src/main/java/io/kestrel/apt/knit_a.java`
- `tasks/pms-annotation-processor-bom-cutover/environment/p3/src/main/java/io/kestrel/apt/ScanLegacy.java`
- `tasks/pms-annotation-processor-bom-cutover/environment/p3/src/main/resources/META-INF/services/javax.annotation.processing.Processor`
- `tasks/pms-annotation-processor-bom-cutover/environment/w0/pom.xml`
- `tasks/pms-annotation-processor-bom-cutover/environment/w0/src/main/java/io/kestrel/wire/legacy/WireLegacy.java`
- `tasks/pms-annotation-processor-bom-cutover/environment/w0/src/main/java/module-info.java`
- `tasks/pms-annotation-processor-bom-cutover/environment/w1/pom.xml`
- `tasks/pms-annotation-processor-bom-cutover/environment/w1/src/main/java/io/kestrel/wire/core/WireCore.java`
- `tasks/pms-annotation-processor-bom-cutover/environment/w1/src/main/java/module-info.java`
- `tasks/pms-annotation-processor-bom-cutover/environment/q7/pom.xml`
- `tasks/pms-annotation-processor-bom-cutover/environment/q7/src/main/java/io/kestrel/model/Event.java`
- `tasks/pms-annotation-processor-bom-cutover/environment/q7/src/main/java/io/kestrel/model/Ticket.java`
- `tasks/pms-annotation-processor-bom-cutover/environment/q7/src/main/java/module-info.java`
- `tasks/pms-annotation-processor-bom-cutover/environment/s2/pom.xml`
- `tasks/pms-annotation-processor-bom-cutover/environment/s2/src/main/java/io/kestrel/svc/RosterGate.java`
- `tasks/pms-annotation-processor-bom-cutover/environment/s2/src/main/java/module-info.java`
- `tasks/pms-annotation-processor-bom-cutover/environment/t9/pom.xml`
- `tasks/pms-annotation-processor-bom-cutover/environment/t9/src/main/java/io/kestrel/boot/knit_b.java`
- `tasks/pms-annotation-processor-bom-cutover/environment/t9/src/main/java/io/kestrel/boot/ProbeLegacy.java`
- `tasks/pms-annotation-processor-bom-cutover/environment/t9/src/main/java/io/kestrel/boot/Main.java`
- `tasks/pms-annotation-processor-bom-cutover/environment/t9/src/main/java/module-info.java`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: p3/src/main/java/io/kestrel/apt/knit_a.java
  symbol: knit_a
  kind: class
  signature: class knit_a extends AbstractProcessor
  purpose: Emits schema companion source files for MarkSlot-annotated types during APT.

- path: t9/src/main/java/io/kestrel/boot/knit_b.java
  symbol: knit_b
  kind: class
  signature: class knit_b
  purpose: Builds a ModuleLayer from the packaged module path and writes the layer report JSON.

- path: pom.xml
  symbol: SLOT_C_KEY
  kind: constant
  signature: property SLOT_C_KEY (Maven project property)
  purpose: Selects which wire artifact id boot and service modules depend on, and whether p3 is a runtime dependency of t9.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: p3/src/main/java/io/kestrel/apt/knit_a.java
    controls_tests: [test_m8_w_ok, test_n9_u_ok]
  - id: B
    path: t9/src/main/java/io/kestrel/boot/knit_b.java
    controls_tests: [test_q2_x_ok, test_k4_v_ok]
  - id: C
    path: pom.xml
    controls_tests: [test_t6_y_ok, test_w1_z_ok]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: p3/src/main/java/io/kestrel/apt/ScanLegacy.java
  kind: helper
  rhymes_with: knit_a
  non_fix_purpose: Read-only annotation inventory printer for ops docs; not registered as a Processor.

- path: t9/src/main/java/io/kestrel/boot/ProbeLegacy.java
  kind: helper
  rhymes_with: knit_b
  non_fix_purpose: Classpath-mode diagnostic that prints jar URLs for local ops; not invoked by layerctl.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [Java, reactor, cutover, platform, catalog, JPMS, layout, package, model, archive, companions, link, layerctl, layer-report, ship, roster, ops, BOM, alignment, companion-generation, isolation, module-path, packaging, module-notes, document, modular, launch, output]
```
