### Decision
GO — Attempt 2. Ops-only fanotify mark cutover (no repair/debug framing), distributed across ring/gate/roll, opaque C symbols, false-green topsurf, simulated mount-ns mark ledgers under concurrent writer race.

### Metadata
- version: 2
- Task name: fanotify-mount-ns-mark-cutover
- Title: Fanotify Mount-NS Mark Cutover
- Category: system-administration
- Languages: ["C"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: ["fanotify", "mount", "namespaces", "ops", "c", "systemd"]
- Milestones: 0

## Authoring Brief

### Public contract

A single-container file-event broker lab simulates nested mount trees and fanotify mark ledgers under `/data/lab/`. Three watch paths — `path-alpha`, `path-beta`, `path-gamma` — belong to the broker. Operators see active unit status and a local scanner still seeing write events while marks land in the wrong mount namespace after pivot/bind; reopen after restart misses inherited mounts; concurrent writers race mark add/remove.

**Symptoms the agent sees (instruction.md level):**
- Unit status reads active; local scanner still sees write events.
- Broker marks land in the wrong mount namespace after the pivot/bind handoff.
- Reopen after restart misses inherited mounts.
- Concurrent writers race mark add/remove.
- `topsurf` prints OK; cutover stub will not emit a ledger yet.

**Required outcomes:**
- `/output/mark-cutover.json` exists with integer `version` `1` and array `watches`. Each row has string `path`, string `mark_ns` (`broker` or `host`), string `mark_kind` (`filesystem` or `inode`), boolean `inherited_ok`, boolean `race_stable`.
- All three broker-owned paths appear with `mark_ns` `broker`, `mark_kind` `filesystem`, `inherited_ok` true, `race_stable` true.
- Host-tree mark rows for those paths are gone after seating; inherit table records remount-ok for each path.
- Unit `PrivateMounts` must not block mark inheritance across the nested tree (`PrivateMounts=no` on the live fragment).
- Seeded tree under `/data/fixtures/watch-seed/` unchanged.

**Constraints:**
- `[environment] allow_internet = false`; verifier deps in Dockerfile.
- No multi-container layout.
- Agent performs ops cutover using bundled C CLIs — not repair/debug framing.
- Language surface is C helpers + unit fragments + bash wrappers.

### Failure topology

Three interacting clusters. First, false-green surface: `topsurf` checks unit active plus any mark file presence and ignores mount-ns identity and mark kind. Second, attach seating: inode marks remain under host after bind; filesystem marks are required in the broker tree. Third, reopen vs race: inherited mounts stay unmarked across restart unless remount cycle runs after `PrivateMounts` fold; concurrent writers recreate jitter unless seating+reopen complete first.

Hard because no single CLI documents full order. `nsprobe` exposes truth; `ringapply`, `gatecycle`, and `ledgerout` mutate distinct subsystems; wrong order keeps `topsurf` green.

### Environment shape

- `environment/Dockerfile` + `.dockerignore` — GCC build, python3/pytest, seeded lab under `/data/lab/`.
- `environment/cmd/` — opaque CLIs: `topsurf`, `nsprobe`, `ringapply`, `gatecycle`, `racepulse`, `ledgerout`.
- `environment/ring/` — `apply_ring_a` fix-path + `legacy_ring` decoy.
- `environment/gate/` — `cycle_gate_b` fix-path + `probe_gate` decoy.
- `environment/roll/` — `emit_roll_c` fix-path.
- `environment/lib/` — shared state_io / path helpers.
- `environment/units/` — broker unit fragments.
- `environment/config/` — paths and field notes only.
- `environment/scripts/` — status wrappers and cutover stub.
- `environment/data/` — fixture builder + watch-seed anchor.

### Required artifacts

- `tasks/fanotify-mount-ns-mark-cutover/task.toml` with `allow_internet = false`, `category = "system-administration"`.
- `instruction.md` — symptoms-only; names output path and JSON fields.
- `tests/test.sh`, `tests/test_outputs.py` — six opaque hard tests.
- `solution/solve.sh` — oracle CLI chain (≥30 LOC), implements opaque C bodies then ops sequence.
- `environment/**` — 25+ non-Docker files per Initial Draft Commitments.

### Test plan

- `test_v4_quartz` — mark_ns is `broker` for all three paths; broker mark files exist; host mark files absent.
- `test_w9_jasper` — mark_kind is `filesystem` for every path (not inode).
- `test_x2_citrine` — inherited_ok true for every path after reopen simulation.
- `test_k6_fluorite` — inherit table records remount-ok for each path on disk.
- `test_y5_beryl` — race_stable true; post-cutover racepulse leaves race clean and no jitter rows.
- `test_z1_spinel` — PrivateMounts=no on live unit; ledger schema version 1 + watches fields; watch-seed checksums intact.

Multiple valid CLI sequences allowed if outcomes match. Chain-dependent: race/ledger tests need prior seating+reopen.

### Drafting guardrails

Do not embed instruction nouns in fix-path symbols, parameters, or test names. Instruction may use standard ops language. No repair/debug TODOs. topsurf must genuinely implement shallow host checks. No HINT walkthroughs under environment/.

### Triviality Ledger

- Calling legacy_ring (inode/host) passes topsurf but fails mark_ns and mark_kind tests.
- Seating without cycle_gate_b leaves inherited_ok false → test_x2_citrine / test_k6_fluorite fail.
- Reopen without apply_ring_a has nothing to remount in broker tree.
- ledgerout without unit fold fails PrivateMounts test (test_z1_spinel).
- Touching watch-seed fails checksum expectations inside schema test.

### Per-gate Pitfall Inventory

- RC1: Oracle adds CLI logic only — never delete-bug or wholesale restore golden.
- RC3: Tests assert mark_ns, mark_kind, inherited_ok, race_stable — not mere file existence.
- RC5: Expected path names and kind tokens live in test code / instruction field names, not golden under environment/.
- RC6: Instruction symptoms-only — no apply_ring_a / seating order.
- RC7: solve.sh CLI chain ≥30 substantive LOC.
- CR1/CR2: Construction manifest symbols verbatim; 2+2+2 flip split.
- CR7/GX9: JSON field names in instruction; order only in runtime.
- Static: allow_internet=false, .dockerignore, absolute paths, category system-administration.

### Initial Draft Commitments

- `tasks/fanotify-mount-ns-mark-cutover/task.toml`
- `tasks/fanotify-mount-ns-mark-cutover/instruction.md`
- `tasks/fanotify-mount-ns-mark-cutover/output_contract.toml`
- `tasks/fanotify-mount-ns-mark-cutover/tests/test.sh`
- `tasks/fanotify-mount-ns-mark-cutover/tests/test_outputs.py`
- `tasks/fanotify-mount-ns-mark-cutover/solution/solve.sh`
- `tasks/fanotify-mount-ns-mark-cutover/environment/Dockerfile`
- `tasks/fanotify-mount-ns-mark-cutover/environment/.dockerignore`
- `tasks/fanotify-mount-ns-mark-cutover/environment/Makefile`
- `tasks/fanotify-mount-ns-mark-cutover/environment/include/lab.h`
- `tasks/fanotify-mount-ns-mark-cutover/environment/include/state.h`
- `tasks/fanotify-mount-ns-mark-cutover/environment/lib/state_io.c`
- `tasks/fanotify-mount-ns-mark-cutover/environment/lib/state_io.h`
- `tasks/fanotify-mount-ns-mark-cutover/environment/lib/path_util.c`
- `tasks/fanotify-mount-ns-mark-cutover/environment/lib/path_util.h`
- `tasks/fanotify-mount-ns-mark-cutover/environment/ring/apply_ring_a.c`
- `tasks/fanotify-mount-ns-mark-cutover/environment/ring/apply_ring_a.h`
- `tasks/fanotify-mount-ns-mark-cutover/environment/ring/legacy_ring.c`
- `tasks/fanotify-mount-ns-mark-cutover/environment/ring/legacy_ring.h`
- `tasks/fanotify-mount-ns-mark-cutover/environment/gate/cycle_gate_b.c`
- `tasks/fanotify-mount-ns-mark-cutover/environment/gate/cycle_gate_b.h`
- `tasks/fanotify-mount-ns-mark-cutover/environment/gate/probe_gate.c`
- `tasks/fanotify-mount-ns-mark-cutover/environment/gate/probe_gate.h`
- `tasks/fanotify-mount-ns-mark-cutover/environment/roll/emit_roll_c.c`
- `tasks/fanotify-mount-ns-mark-cutover/environment/roll/emit_roll_c.h`
- `tasks/fanotify-mount-ns-mark-cutover/environment/cmd/topsurf/main.c`
- `tasks/fanotify-mount-ns-mark-cutover/environment/cmd/nsprobe/main.c`
- `tasks/fanotify-mount-ns-mark-cutover/environment/cmd/ringapply/main.c`
- `tasks/fanotify-mount-ns-mark-cutover/environment/cmd/gatecycle/main.c`
- `tasks/fanotify-mount-ns-mark-cutover/environment/cmd/racepulse/main.c`
- `tasks/fanotify-mount-ns-mark-cutover/environment/cmd/ledgerout/main.c`
- `tasks/fanotify-mount-ns-mark-cutover/environment/units/broker.service`
- `tasks/fanotify-mount-ns-mark-cutover/environment/units/broker-watches.conf`
- `tasks/fanotify-mount-ns-mark-cutover/environment/config/lab.toml`
- `tasks/fanotify-mount-ns-mark-cutover/environment/config/field-notes.md`
- `tasks/fanotify-mount-ns-mark-cutover/environment/scripts/status-top.sh`
- `tasks/fanotify-mount-ns-mark-cutover/environment/scripts/cutover-stub.sh`
- `tasks/fanotify-mount-ns-mark-cutover/environment/scripts/race-harness.sh`
- `tasks/fanotify-mount-ns-mark-cutover/environment/data/build_fixtures.sh`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: environment/ring/apply_ring_a.c
  symbol: apply_ring_a
  kind: function
  signature: int apply_ring_a(const char *a, const char *b)
  purpose: Seats watch paths into broker tree and writes filesystem mark ledger rows under broker identity.

- path: environment/gate/cycle_gate_b.c
  symbol: cycle_gate_b
  kind: function
  signature: int cycle_gate_b(const char *a, const char *b, const char *c)
  purpose: Reopens inherited mount rows and records remount-ok flags in the inherit table.

- path: environment/roll/emit_roll_c.c
  symbol: emit_roll_c
  kind: function
  signature: int emit_roll_c(const char *a, const char *b)
  purpose: Folds unit PrivateMounts and writes mark-cutover.json from live lab state.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: environment/ring/apply_ring_a.c
    controls_tests: [test_v4_quartz, test_w9_jasper]
  - id: B
    path: environment/gate/cycle_gate_b.c
    controls_tests: [test_x2_citrine, test_k6_fluorite]
  - id: C
    path: environment/roll/emit_roll_c.c
    controls_tests: [test_y5_beryl, test_z1_spinel]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: environment/ring/legacy_ring.c
  kind: helper
  rhymes_with: apply_ring_a
  non_fix_purpose: Writes inode marks under host tree for diagnostic scripts; never seats broker identity.

- path: environment/gate/probe_gate.c
  kind: helper
  rhymes_with: cycle_gate_b
  non_fix_purpose: Lists inherit table for nsprobe diagnostics; never remounts or sets remount-ok flags.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [cutover, file-event, broker, lab, unit, status, local, scanner, write, events, marks, mount, namespace, pivot, bind, handoff, reopen, restart, inherited, mounts, concurrent, writers, race, mark, add, remove, tree, helpers, notes, config, sources, fragments, fixtures, watch-seed, output, version, watches, array, row, path, mark_ns, mark_kind, inherited_ok, race_stable, filesystem, PrivateMounts, inheritance, nested]
```
