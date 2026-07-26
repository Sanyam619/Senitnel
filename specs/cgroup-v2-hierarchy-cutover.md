### Decision
GO — Attempt 1. Distributed fix across phase/relay/acct roots, opaque CLI names, surfcheck false-green trap, and mixed simulated cgroupfs seed.

### Metadata
- version: 2
- Task name: cgroup-v2-hierarchy-cutover
- Title: Cgroup v2 Hierarchy Cutover
- Category: system-administration
- Languages: ["Go", "bash"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: ["cgroup", "ops", "go", "containers", "host", "migration"]
- Milestones: 0

## Authoring Brief

### Public contract

A single-container host lab simulates mixed legacy and unified resource trees under `/sys/lab/cgroup/`. Three unit names — `app-batch.scope`, `app-worker.scope`, `app-api.scope` — run fixture jobs. Operators see green surface checks while brake and peak tallies stay at zero on partially moved names.

**Symptoms the agent sees (instruction.md level):**
- `/opt/lab/bin/surfcheck` prints OK and `/opt/lab/scripts/unit-top.sh` lists active names.
- `/opt/lab/scripts/cutover-stub.sh` exits non-zero.
- Write-heavy fixture jobs on partially moved names never accumulate IO brake hits; peak notifications stay at zero.
- `/opt/lab/bin/nodescope` shows some names still attached to legacy per-controller trees while others sit under the unified root without active brake lines.

**Required outcomes:**
- `/output/cutover-report.json` exists with integer `version` `1` and array `scopes`. Each scope entry has string `name`, string `tree` (`unified` or `legacy`), string `controllers` (space-separated enabled names), integer `io_throttle_events`, integer `memory_high_events`.
- All three named scopes appear in `scopes` with `tree` `unified`, `controllers` containing `io` and `memory`, `io_throttle_events` > 0, `memory_high_events` > 0 after fixture stress.
- No legacy shadow directories remain for migrated names under `/sys/lab/cgroup/v1/`.
- Seeded anchor tree under `/data/fixtures/cgroup-seed/` unchanged (checksum guard in tests).

**Constraints:**
- `[environment] allow_internet = false`; verifier deps in Dockerfile.
- No multi-container layout.
- Agent performs ops using bundled CLIs — not Go source patching.
- Go-only environment sources.

### Failure topology

Three symptom clusters interact. First, a false-green surface path: `surfcheck` verifies the unified root lists io and memory in its controllers file but does not inspect `cgroup.subtree_control` on `app.slice`, so operators believe brakes are delegated while children lack `io.max` lines. Second, partial relay: `app-batch.scope` and `app-worker.scope` were copied under the unified tree before parent delegation and before legacy detach, so limit files are empty and counters never increment under `loadpulse`. Third, `app-api.scope` remains on legacy v1 per-controller trees; relay without `wire_node_b` detach leaves shadows that block unified accounting.

The task is hard because no single CLI documents the full order. `nodescope` exposes attachment facts, `phasegate` mutates subtree gates and relays names, `loadpulse` drives tallies only when limits exist, and `acctpull` aggregates results. Wrong ordering does not always fail immediately — surfcheck can stay green while ledger counters remain zero.

### Environment shape

- `environment/Dockerfile` + `.dockerignore` — Go 1.24 build, python3/pytest, seeded cgroupfs under `/sys/lab/cgroup/`.
- `environment/cmd/` — five opaque CLIs: `surfcheck`, `nodescope`, `phasegate`, `loadpulse`, `acctpull`.
- `environment/internal/tree/` — read/write simulated cgroupfs files.
- `environment/internal/acct/` — counter files and `emit_ledger_c` rollup.
- `environment/pkg/phase/` — `step_phase_a` fix-path + `legacy_relay` decoy.
- `environment/pkg/relay/` — `wire_node_b` fix-path + `probe_node` decoy.
- `environment/scripts/` — `unit-top.sh`, `cutover-stub.sh`, thin wrappers.
- `environment/data/fixtures/cgroup-seed/` — pristine anchor snapshot of pre-cutover tree.
- `environment/config/lab.toml` — paths only.

### Required artifacts

- `tasks/cgroup-v2-hierarchy-cutover/task.toml` with `allow_internet = false`.
- `tasks/cgroup-v2-hierarchy-cutover/instruction.md` — symptoms-only prose; includes output path and ledger JSON field names tests check.
- `tasks/cgroup-v2-hierarchy-cutover/tests/test.sh`, `tests/test_outputs.py` — six tests per plan.
- `tasks/cgroup-v2-hierarchy-cutover/solution/solve.sh` — oracle CLI chain (≥30 LOC substantive).
- `tasks/cgroup-v2-hierarchy-cutover/environment/**` — 25+ non-Docker files per Initial Draft Commitments.

### Test plan

- `test_x3_shape_bundle` — Parses ledger and nodescope; asserts all three names report `tree` `unified` with io+memory in `controllers`.
- `test_f7_brake_hits` — Asserts each scope has `io_throttle_events` > 0 in `/output/cutover-report.json`.
- `test_j2_peak_log` — Asserts each scope has `memory_high_events` > 0 in ledger.
- `test_n5_unit_ledger` — Validates ledger schema: version, scopes array shape, required string/int fields.
- `test_p1_shadow_gone` — Asserts no legacy shadow dirs for migrated names under v1 roots.
- `test_r4_anchor_intact` — Compares checksum of `/data/fixtures/cgroup-seed/**` against embedded hash list.

Chain-dependent: brake and peak tests depend on correct phasegate ordering and loadpulse stress.

### Drafting guardrails

Do not embed instruction nouns in fix-path function names, parameters, directories, or test function names. Instruction.md may use standard cgroup ops language freely. Do not hide the operational contract in environment README files. `surfcheck` must genuinely implement superficial controller-list logic visible in source. Seeded fixture must encode partial-relay state without HINT comments naming enable order.

### Triviality Ledger

- Naive `loadpulse` first passes surfcheck green but fails `test_f7_brake_hits` because `io.max` lines are absent on unified children.
- Leaf-only enable via `legacy_relay` decoy fails `test_j2_peak_log` because parent `cgroup.subtree_control` never gains io+memory.
- Relay before `step_phase_a` leaves empty limit files and fails `test_x3_shape_bundle` controller assertions.
- Skipping detach leaves v1 shadows and fails `test_p1_shadow_gone`.
- Copying anchor seed over live tree fails `test_r4_anchor_intact` and brake tests.

### Per-gate Pitfall Inventory

- RC1: Oracle must execute real CLI sequence — not restore golden tree wholesale.
- RC3: Tests assert computed counter integers and tree labels, not mere file existence.
- RC5: Expected counter thresholds live in test code, not under `environment/data/golden/`.
- RC6: Instruction stays symptoms-only — do not name `step_phase_a`, `wire_node_b`, or step order.
- RC7: `solve.sh` chains nodescope + phasegate + loadpulse + acctpull with error handling ≥30 LOC.
- CR1/CR2: Use construction manifest symbols verbatim; flipping-point revert splits tests 2+2+2.
- CR7/GX9: Ledger JSON field names appear in instruction.md; enable order appears only in nodescope/runtime behavior.
- Static checks: `allow_internet = false`, `.dockerignore` present, absolute paths in instruction.

### Initial Draft Commitments

- `tasks/cgroup-v2-hierarchy-cutover/task.toml`
- `tasks/cgroup-v2-hierarchy-cutover/instruction.md`
- `tasks/cgroup-v2-hierarchy-cutover/tests/test.sh`
- `tasks/cgroup-v2-hierarchy-cutover/tests/test_outputs.py`
- `tasks/cgroup-v2-hierarchy-cutover/solution/solve.sh`
- `tasks/cgroup-v2-hierarchy-cutover/environment/Dockerfile`
- `tasks/cgroup-v2-hierarchy-cutover/environment/.dockerignore`
- `tasks/cgroup-v2-hierarchy-cutover/environment/go.mod`
- `tasks/cgroup-v2-hierarchy-cutover/environment/go.sum`
- `tasks/cgroup-v2-hierarchy-cutover/environment/config/lab.toml`
- `tasks/cgroup-v2-hierarchy-cutover/environment/cmd/surfcheck/main.go`
- `tasks/cgroup-v2-hierarchy-cutover/environment/cmd/nodescope/main.go`
- `tasks/cgroup-v2-hierarchy-cutover/environment/cmd/phasegate/main.go`
- `tasks/cgroup-v2-hierarchy-cutover/environment/cmd/loadpulse/main.go`
- `tasks/cgroup-v2-hierarchy-cutover/environment/cmd/acctpull/main.go`
- `tasks/cgroup-v2-hierarchy-cutover/environment/internal/tree/read.go`
- `tasks/cgroup-v2-hierarchy-cutover/environment/internal/tree/write.go`
- `tasks/cgroup-v2-hierarchy-cutover/environment/internal/tree/legacy.go`
- `tasks/cgroup-v2-hierarchy-cutover/environment/internal/tree/doc.go`
- `tasks/cgroup-v2-hierarchy-cutover/environment/internal/acct/counter.go`
- `tasks/cgroup-v2-hierarchy-cutover/environment/internal/acct/rollup.go`
- `tasks/cgroup-v2-hierarchy-cutover/environment/internal/acct/doc.go`
- `tasks/cgroup-v2-hierarchy-cutover/environment/pkg/phase/relay.go`
- `tasks/cgroup-v2-hierarchy-cutover/environment/pkg/phase/legacy_relay.go`
- `tasks/cgroup-v2-hierarchy-cutover/environment/pkg/relay/move.go`
- `tasks/cgroup-v2-hierarchy-cutover/environment/pkg/relay/probe_node.go`
- `tasks/cgroup-v2-hierarchy-cutover/environment/scripts/unit-top.sh`
- `tasks/cgroup-v2-hierarchy-cutover/environment/scripts/cutover-stub.sh`
- `tasks/cgroup-v2-hierarchy-cutover/environment/scripts/phasegate-wrapper.sh`
- `tasks/cgroup-v2-hierarchy-cutover/environment/data/build_fixtures.sh`
- `tasks/cgroup-v2-hierarchy-cutover/environment/data/fixtures/cgroup-seed/manifest.txt`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: environment/pkg/phase/relay.go
  symbol: step_phase_a
  kind: function
  signature: func step_phase_a(root string, gates []string) error
  purpose: Writes delegated brake tokens into a parent subtree gate file.

- path: environment/pkg/relay/move.go
  symbol: wire_node_b
  kind: function
  signature: func wire_node_b(legacy string, target string, brakes map[string]string) error
  purpose: Detaches legacy shadows and wires limit lines on the unified node.

- path: environment/internal/acct/rollup.go
  symbol: emit_ledger_c
  kind: function
  signature: func emit_ledger_c(out string, names []string) error
  purpose: Aggregates per-name brake and peak tallies into the output JSON object.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: environment/pkg/phase/relay.go
    controls_tests: [test_x3_shape_bundle, test_f7_brake_hits]
  - id: B
    path: environment/pkg/relay/move.go
    controls_tests: [test_j2_peak_log, test_p1_shadow_gone]
  - id: C
    path: environment/internal/acct/rollup.go
    controls_tests: [test_n5_unit_ledger, test_r4_anchor_intact]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: environment/pkg/phase/legacy_relay.go
  kind: helper
  rhymes_with: step_phase_a
  non_fix_purpose: Deprecated leaf-only gate writer used by diagnostic scripts, not the cutover path.

- path: environment/pkg/relay/probe_node.go
  kind: helper
  rhymes_with: wire_node_b
  non_fix_purpose: Read-only legacy attachment dumper for nodescope; does not detach or wire limits.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [container, host, migration, systemd, health, throttling, memory, scope, hierarchy, controller, cutover, accounting, fixture, workload, unified, delegation, report, stress, event, migrated, legacy, limit, tree, surface, job, pressure, notification, seed, resource, check, partial, zero, stub, attach, root, layout, produce, cgroup, v2, v1, io, throttle, high-water, systemd-cgtop]
```
