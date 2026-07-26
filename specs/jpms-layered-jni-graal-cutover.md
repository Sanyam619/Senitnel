### Decision
GO — Attempt 1. Distributed fix across jlink/ModuleLayer root selection, shade relocation for JNI-visible types, and Graal reachability emission; opaque symbols; cutover framing (no repair/debug); hard multi-mode outcome tests only; distinct from APT/BOM cutover.

### Metadata
- version: 2
- Task name: jpms-layered-jni-graal-cutover
- Title: JPMS JNI Graal Cutover
- Category: build-and-dependency-management
- Languages: ["Java", "C"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: ["tool_specific"]
- Tags: ["java", "jni", "jpms", "jlink", "graal", "native-image"]
- Milestones: 0

## Authoring Brief

### Public contract

A Java control plane under `/app/` is mid-cutover onto layered module runtime images and native packaging with a JNI shared library. Modular JVM launches and packaging dry-runs can look coherent while `/app/tools/packctl` still writes `/output/pack-report.json` where jlink and native launch modes disagree with the ship roster under `/app/ops/matrix.toml` and the cutover notes under `/app/link/pack-notes.toml`.

**Symptoms the agent sees (instruction.md level):**
- Modular JVM packaging dry-runs can look locally coherent.
- `/output/pack-report.json` still disagrees across jlink and native launch modes versus the ship roster / cutover notes.
- Fields `status`, `spi_bound`, `jni_bridge`, and `reflect_kept` do not all match the cutover notes for every matrix mode.

**Required outcomes:**
- Every launch mode named in `/app/ops/matrix.toml` reports `status` `ok`.
- `spi_bound`, `jni_bridge`, and `reflect_kept` match `/app/link/pack-notes.toml` for each mode.
- Report comes from a real `/app/tools/packctl` packaging probe, not a hand-written stand-in.

**Constraints:**
- `[environment] allow_internet = false`; verifier deps in Dockerfile.
- No multi-container layout; no repair/debug framing in instruction.
- Languages: Java + C (JNI `.so`).
- Agent reconciles module-graph packaging, shade relocation, and native reachability — not a golden JSON rewrite.

### Failure topology

Three cutover remnants interact. First, `knit_a` still selects a jlink/ModuleLayer root set that keeps the app and api units but omits the SPI provider (and skips service binding), so jlink boots while `spi_bound` stays false. Second, `fold_b` relocates JNI-visible bridge types into an internal package while the C shared library still `FindClass`-es the pre-relocation binary name, so JVM `jni_bridge` fails after shade. Third, `sieve_c` emits native reachability metadata that keeps only the boot entry and omits SPI plus NativeHook reflective/JNI entries, so native `reflect_kept` and native `status` disagree with the cutover notes.

The task is hard because module-graph packaging, shade relocation, and Graal-style reachability must agree with the JNI shared library across three launch modes; dry-run-green signals do not satisfy the ship report.

### Environment shape

- `environment/Dockerfile` + `.dockerignore` — JDK 21, gcc, pytest; offline image build.
- `environment/unit/{a1,b2,c3,d4}/` — api, spi, bridge, app JPMS units.
- `environment/drv/{k9,p7,m2}/` — layer recipe (`knit_a`), shade (`fold_b`), reachability (`sieve_c`) plus decoy helpers.
- `environment/native/` — JNI C sources and Makefile.
- `environment/tools/packctl` — builds, shades, jlinks, native-probes, writes `/output/pack-report.json`.
- `environment/ops/` — ship matrix and runbook (discovery).
- `environment/link/` — cutover notes + decoy legacy notes.
- `environment/config/` — profile TOML decoys.
- `environment/data/fixtures/` — seed fixtures.

### Required artifacts

- `tasks/jpms-layered-jni-graal-cutover/task.toml` with `allow_internet = false`.
- `instruction.md` — symptoms-only cutover prose (not repair/debug framing).
- `tests/test.sh`, `tests/test_outputs.py` — six hard tests; session-cached packctl.
- `solution/solve.sh` — oracle patches ≥3 loci (≥30 LOC substantive).
- `environment/**` — 25+ non-Docker files per Initial Draft Commitments.

### Test plan

- `test_k4_v_lane` — JVM mode `status` is `ok`.
- `test_m8_w_lane` — jlink mode `status` is `ok`.
- `test_q2_x_lane` — native mode `status` is `ok`.
- `test_t6_y_bind` — jlink `spi_bound` is `true` (matches notes).
- `test_w1_z_hook` — JVM `jni_bridge` is `true` (matches notes).
- `test_n9_u_keep` — native `reflect_kept` contains the types named in cutover notes.

Chain-dependent: field tests need a successful packctl run (session fixture). Multiple valid approaches exist (any coherent module-graph/shade/reachability reconciliation satisfying outcomes).

### Drafting guardrails

Do not embed instruction nouns in fix-path function names, parameters, or test names. Instruction uses standard JPMS/jlink/JNI/Graal language freely. Do not frame as bug-hunt or repair checklist — cutover/build-graph reconciliation only. Do not hide the operational contract in environment README files. No HINT/STEP walkthroughs in environment/. Do not create `environment/bin/` (package hygiene); install packctl to `/app/bin` from `tools/` in the Dockerfile.

### Triviality Ledger

- Expanding only jlink roots greens `test_m8_w_lane` / `test_t6_y_bind` but leaves JVM JNI and native reflect tests red.
- Fixing only shade relocation greens `test_k4_v_lane` / `test_w1_z_hook` but leaves jlink SPI unbound and native metadata sparse.
- Fixing only reachability greens `test_q2_x_lane` / `test_n9_u_keep` while jlink and JVM JNI modes stay red.
- Hand-writing `/output/pack-report.json` without a real packaging probe fails rebuild-from-sources / integrity checks.
- Treating a green modular compile dry-run as done still fails cross-mode ship fields.

### Per-gate Pitfall Inventory

- RC1: Oracle must reconcile layer roots, shade policy, and reachability — not delete one sentinel or copy a golden report.
- RC3: Tests assert computed mode status and domain fields — not file existence alone.
- RC5: Expected type names live in test code (and discoverable notes); no golden pack-report under environment/.
- RC6: Instruction stays symptoms-only cutover language — do not name `knit_a`, `fold_b`, or `sieve_c`.
- RC7: `solve.sh` edits ≥3 loci with substantive logic ≥30 LOC.
- CR1/CR2: Use construction manifest symbols verbatim; flipping-point 2+2+2.
- CR7/GX9: Field names appear in instruction; do not recite per-test answer triples beyond contract.
- Static checks: `allow_internet = false`, `.dockerignore`, absolute paths, timeout coherence with javac/jlink/gcc builds; no `environment/bin/` source tree.

### Initial Draft Commitments

- `tasks/jpms-layered-jni-graal-cutover/task.toml`
- `tasks/jpms-layered-jni-graal-cutover/instruction.md`
- `tasks/jpms-layered-jni-graal-cutover/output_contract.toml`
- `tasks/jpms-layered-jni-graal-cutover/tests/test.sh`
- `tasks/jpms-layered-jni-graal-cutover/tests/test_outputs.py`
- `tasks/jpms-layered-jni-graal-cutover/solution/solve.sh`
- `tasks/jpms-layered-jni-graal-cutover/environment/Dockerfile`
- `tasks/jpms-layered-jni-graal-cutover/environment/.dockerignore`
- `tasks/jpms-layered-jni-graal-cutover/environment/tools/packctl`
- `tasks/jpms-layered-jni-graal-cutover/environment/ops/matrix.toml`
- `tasks/jpms-layered-jni-graal-cutover/environment/ops/runbooks/ctl_usage.md`
- `tasks/jpms-layered-jni-graal-cutover/environment/link/pack-notes.toml`
- `tasks/jpms-layered-jni-graal-cutover/environment/link/legacy-notes.toml`
- `tasks/jpms-layered-jni-graal-cutover/environment/config/profiles/ship.toml`
- `tasks/jpms-layered-jni-graal-cutover/environment/config/profiles/field.toml`
- `tasks/jpms-layered-jni-graal-cutover/environment/data/fixtures/seed.json`
- `tasks/jpms-layered-jni-graal-cutover/environment/native/hook.c`
- `tasks/jpms-layered-jni-graal-cutover/environment/native/Makefile`
- `tasks/jpms-layered-jni-graal-cutover/environment/unit/a1/module-info.java`
- `tasks/jpms-layered-jni-graal-cutover/environment/unit/a1/io/helix/api/Slot.java`
- `tasks/jpms-layered-jni-graal-cutover/environment/unit/b2/module-info.java`
- `tasks/jpms-layered-jni-graal-cutover/environment/unit/b2/io/helix/spi/SlotProvider.java`
- `tasks/jpms-layered-jni-graal-cutover/environment/unit/b2/META-INF/services/io.helix.api.Slot`
- `tasks/jpms-layered-jni-graal-cutover/environment/unit/c3/module-info.java`
- `tasks/jpms-layered-jni-graal-cutover/environment/unit/c3/io/helix/bridge/NativeHook.java`
- `tasks/jpms-layered-jni-graal-cutover/environment/unit/d4/module-info.java`
- `tasks/jpms-layered-jni-graal-cutover/environment/unit/d4/io/helix/app/Main.java`
- `tasks/jpms-layered-jni-graal-cutover/environment/k9/module-info.java`
- `tasks/jpms-layered-jni-graal-cutover/environment/k9/src/main/java/io/helix/kz/knit_a.java`
- `tasks/jpms-layered-jni-graal-cutover/environment/k9/src/main/java/io/helix/kz/knit_legacy.java`
- `tasks/jpms-layered-jni-graal-cutover/environment/k9/src/main/java/io/helix/kz/DriverK.java`
- `tasks/jpms-layered-jni-graal-cutover/environment/p7/module-info.java`
- `tasks/jpms-layered-jni-graal-cutover/environment/p7/src/main/java/io/helix/qx/fold_b.java`
- `tasks/jpms-layered-jni-graal-cutover/environment/p7/src/main/java/io/helix/qx/fold_preview.java`
- `tasks/jpms-layered-jni-graal-cutover/environment/p7/src/main/java/io/helix/qx/DriverP.java`
- `tasks/jpms-layered-jni-graal-cutover/environment/m2/module-info.java`
- `tasks/jpms-layered-jni-graal-cutover/environment/m2/src/main/java/io/helix/ry/sieve_c.java`
- `tasks/jpms-layered-jni-graal-cutover/environment/m2/src/main/java/io/helix/ry/sieve_preview.java`
- `tasks/jpms-layered-jni-graal-cutover/environment/m2/src/main/java/io/helix/ry/DriverM.java`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: k9/src/main/java/io/helix/kz/knit_a.java
  symbol: knit_a
  kind: class
  signature: static List<String> apply(List<String> a, boolean b)
  purpose: Selects module names included in the layered/jlink root set and whether services are bound.
- path: p7/src/main/java/io/helix/qx/fold_b.java
  symbol: fold_b
  kind: class
  signature: static String apply(String a, String b)
  purpose: Maps a class binary name through the shade relocation table for packaging.
- path: m2/src/main/java/io/helix/ry/sieve_c.java
  symbol: sieve_c
  kind: class
  signature: static List<Map<String, Object>> apply(List<String> a, List<String> b)
  purpose: Emits native reachability entries for reflective and JNI-visible types.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: k9/src/main/java/io/helix/kz/knit_a.java
    controls_tests: [test_m8_w_lane, test_t6_y_bind]
  - id: B
    path: p7/src/main/java/io/helix/qx/fold_b.java
    controls_tests: [test_k4_v_lane, test_w1_z_hook]
  - id: C
    path: m2/src/main/java/io/helix/ry/sieve_c.java
    controls_tests: [test_q2_x_lane, test_n9_u_keep]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: k9/src/main/java/io/helix/kz/knit_legacy.java
  kind: helper
  rhymes_with: knit_a
  non_fix_purpose: Formats legacy classpath launch args for dry-runs; not used for modular/jlink root selection.
- path: p7/src/main/java/io/helix/qx/fold_preview.java
  kind: helper
  rhymes_with: fold_b
  non_fix_purpose: Pretty-prints proposed relocation tables for ops dry-runs without mutating packaged names.
- path: m2/src/main/java/io/helix/ry/sieve_preview.java
  kind: helper
  rhymes_with: sieve_c
  non_fix_purpose: Summarizes reachability counts for matrix dry-runs without writing native metadata.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [Java, control, plane, cutover, layered, module, runtime, images, native, packaging, JNI, shared, library, Modular, JVM, launches, dry-runs, packctl, pack-report, jlink, launch, modes, ship, roster, matrix, notes, module-graph, shade, relocation, bridge, classes, reachability, metadata, agreement, status, spi_bound, jni_bridge, reflect_kept, report, probe, stand-in, ops, link, pack-notes, tools, output, Graal]
```
