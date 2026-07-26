### Decision
GO — Attempt 1. Distributed fix across phase/relay/acct roots, opaque CLI names, surfcheck false-green trap, and mixed simulated cgroupfs seed.

### Metadata
- Task name: cgroup-v2-hierarchy-cutover
- Title: Cgroup v2 Hierarchy Cutover
- Category: system-administration
- Languages: ["Go", "bash"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: ["cgroup", "ops", "go", "containers", "host", "migration"]
- Milestones: 0

### Discovery budget

- Discovery: `surfcheck` reports OK when unified root lists io and memory in cgroup.controllers but `cgroup.subtree_control` on app.slice lacks those brakes.
  Planned location: `environment/cmd/surfcheck/main.go` and `environment/internal/tree/read.go`
  Why instruction must not reveal it: Naming the subtree_control omission tells the agent to ignore surfcheck entirely.

- Discovery: `nodescope` JSON shows app-api.scope still has legacy per-controller nodes while app-batch and app-worker sit under unified paths without io.max lines until `step_phase_a` runs on app.slice before relay.
  Planned location: `environment/cmd/nodescope/main.go`, `environment/pkg/phase/relay.go`, seeded fixtures
  Why instruction must not reveal it: Stating enable-before-relay order collapses diagnosis to a recipe.

- Discovery: `loadpulse` only increments brake tallies when io.max and memory.max are present; `wire_node_b` must detach legacy shadows before limits propagate.
  Planned location: `environment/pkg/relay/move.go`, `environment/cmd/loadpulse/main.go`, `environment/internal/acct/rollup.go`
  Why instruction must not reveal it: Revealing detach-then-stress ordering removes relay-phase reasoning.

### Anti-trivialization verdict

| # | Check | Verdict | Reasoning |
|---|-------|---------|-----------|
| 1 | Disclosure-collapse | PASS | Symptoms-only brief omits enable order and relay sequence. |
| 2 | Hidden-instance | PASS | Fixed lab topology. |
| 3 | Single-artifact repair | PASS | Enable + detach + relay + stress + ledger required. |
| 4 | Generalization | PASS | Computed counter thresholds in tests. |
| 5 | Prompt-honesty | PASS | Does not name faulty module. |
| 6 | Cheating-vs-difficulty | PASS | Verification not the difficulty source. |
| 7 | Mechanical-fix filter | PASS | Not deps/timeout task. |
| 8 | Localized-fix | PASS | Three module roots. |
| 9 | Oracle-locality | PASS | Multi-step CLI oracle. |
| 10 | Small declarative-cluster | PASS | Not one config knob. |
| 11 | Grep-collapse | PASS | Instruction nouns banned from code symbols. |
| 12 | Pre-factored-helper | PASS | Opaque step_phase_a, wire_node_b, emit_ledger_c. |
| 13 | Recipe-discount | PASS | False-green surfcheck defeats textbook order. |
| 14 | Security-aura discount | PASS | Ops framing only. |
| 15 | Orthogonal-checklist | PASS | Order-dependent coupled phases. |
| 16 | Harness-discount | PASS | Fixtures add realism. |
| 17 | One-pass solvability | PASS | 25+ files block one-pass. |
| 18 | Hard-only gate | PASS | Hard under Edition 2. |
| 19 | Discovery budget test | PASS | Three discoveries above. |
| 20 | Instruction specificity test | PASS | symptoms-only. |
| 21 | Topology distribution test | PASS | Three topologies below. |

### Topology enumeration (3 candidate fix topologies)

**Topology A — Parent subtree gate before child relay:** `environment/pkg/phase/relay.go`, `environment/internal/tree/write.go`, `environment/cmd/phasegate/main.go`. Enabling on leaf only leaves io.max absent.

**Topology B — Legacy detach before unified limit wiring:** `environment/pkg/relay/move.go`, `environment/internal/tree/legacy.go`, `environment/cmd/loadpulse/main.go`. Relay without detach leaves v1 shadows.

**Topology C — Stress-then-ledger aggregation:** `environment/cmd/loadpulse/main.go`, `environment/internal/acct/rollup.go`, `environment/cmd/acctpull/main.go`. Ledger without stress shows zero counters.

### Rubric axes

- **Verifiable:** PASS — cgroup state, counters, JSON ledger.
- **Well-specified:** PASS — Output path and fields in instruction.
- **Solvable:** PASS — Expert sysadmin in hours.
- **Difficult:** PASS — Mixed-tree cutover exceeds undergrad scope.
- **Interesting:** PASS — Real cgroup v2 migration pattern.
- **Outcome-verified:** PASS — Grades ledger and tree shape.

### Hardness axes

- **Discover:** PASS — surfcheck heuristic and nodescope attachments not in instruction.
- **Synthesize:** PASS — CLIs, fixtures, and simulated cgroupfs form one system.
- **Diagnose:** PASS — Green checks and zero tallies only.
- **Navigate coupling:** PASS — Wrong order leaves counters at zero.
- **Reason beyond training:** PASS — Partial relay fixture requires ops sequencing.

### Instruction completeness test

Can the agent solve this by reading ONLY instruction.md? **No.** surfcheck heuristic, per-name legacy attachments, and parent-before-child enable order are only visible via CLI sources and nodescope output.

## Reviewer Appendix

### Implementation plan

Build a Go CLI lab under `/opt/lab/bin` simulating cgroupfs under `/sys/lab/cgroup/`. Seed a broken mixed tree where two names sit under unified without delegated brakes and one name remains on legacy v1 shadows. `surfcheck` checks only root controller list. Agent inspects with `nodescope`, runs `phasegate` enable on `app.slice`, relays each name with detach via `wire_node_b`, stresses with `loadpulse`, writes `/output/cutover-report.json` via `acctpull`/`emit_ledger_c`.

### Proposed file inventory

```
tasks/cgroup-v2-hierarchy-cutover/
  task.toml, instruction.md
  tests/test.sh, test_outputs.py
  solution/solve.sh
  environment/
    Dockerfile, .dockerignore, go.mod, go.sum, config/lab.toml
    cmd/{surfcheck,nodescope,phasegate,loadpulse,acctpull}/main.go
    internal/tree/{read,write,legacy,doc}.go
    internal/acct/{counter,rollup,doc}.go
    pkg/phase/{relay,legacy_relay}.go
    pkg/relay/{move,probe_node}.go
    scripts/{unit-top,cutover-stub,phasegate-wrapper}.sh
    data/build_fixtures.sh
    data/fixtures/cgroup-seed/manifest.txt
```

### Oracle notes

`solve.sh`: phasegate enable io+memory on app.slice; for each name nodescope reports as legacy-attached, phasegate relay with detach; loadpulse all three names; acctpull to /output/cutover-report.json. Must not overwrite cgroup-seed anchor.

### Collapse audit

Stage: implementation-plan

**Smallest plausible successful patch:** Enable parent gates, detach+relay each name, stress, emit ledger — five coupled ops.

**Likely editable frontier:** Agent uses CLIs; oracle touches step_phase_a, wire_node_b, emit_ledger_c via phasegate/acctpull.

**Oracle estimated complexity:** ~50–80 lines bash + CLI flags.

**Collapse verdict:** PASS

### Naming-pass record

**Instruction nouns extracted:**
container, host, migration, systemd, health, throttling, memory, scope, hierarchy, controller, cutover, accounting, fixture, workload, unified, delegation, report, stress, event, migrated, legacy, limit, tree, surface, job, pressure, notification, seed, resource, check, partial, zero, stub, attach, root, layout, produce, cgroup, v2, v1, io, throttle, high-water, systemd-cgtop

**Renames during drafting:**
- `step_cutover_a` → `step_phase_a`: overlapped noun cutover
- `wire_scope_b` → `wire_node_b`: overlapped noun scope
- `emit_report_c` → `emit_ledger_c`: overlapped noun report

**Test names audited:**
test_x3_shape_bundle, test_f7_brake_hits, test_j2_peak_log, test_n5_unit_ledger, test_p1_shadow_gone, test_r4_anchor_intact

**Concentration math:**
- Total tests: 6
- A (pkg/phase/relay.go): 2/6 = 0.333
- B (pkg/relay/move.go): 2/6 = 0.333
- C (internal/acct/rollup.go): 2/6 = 0.333
- Cap: 0.5. Max ratio: 0.333. Status: PASS

### Per-test feasibility pre-check

- test_x3_shape_bundle — ledger tree labels; 2+ approaches; chain-dependent on relay
- test_f7_brake_hits — io counter > 0; chain-dependent on limits
- test_j2_peak_log — memory counter > 0; chain-dependent
- test_n5_unit_ledger — schema shape; multiple approaches; not chain-dependent
- test_p1_shadow_gone — no v1 dirs; chain-dependent on detach
- test_r4_anchor_intact — checksum; not chain-dependent
