### Decision
GO — Attempt 1. Ops-only cutover (no source repair/debug), distributed across lane/seat/roll, opaque C symbols, false-green topsurf, simulated mount+cap ledgers under concurrent race.

### Metadata
- version: 2
- Task name: ambient-cap-device-broker-cutover
- Title: Ambient-Cap Device Broker Cutover
- Category: system-administration
- Languages: ["C", "bash"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: ["capabilities", "mount", "ops", "c", "devices", "namespaces"]
- Milestones: 0

## Authoring Brief

### Public contract

A single-container device-broker lab simulates nested mount/user layout and capability ledgers under `/data/lab/`. Three char devices — `dev-alpha`, `dev-beta`, `dev-gamma` — belong to the broker. Operators see active unit status and host `/dev` listings while ambient bits vanish across enter and nodes remain on the wrong mount tree; concurrent open/replay leaves stale host markers.

**Symptoms the agent sees (instruction.md level):**
- Unit status reads active; host `/dev` lists the char nodes.
- Broker view still lands in the wrong mount namespace; ambient capabilities vanish across the nested handoff.
- Concurrent open/replay leaves stale nodes on the host view.
- `topsurf` prints OK; cutover stub will not emit a ledger yet.

**Required outcomes:**
- `/output/broker-cutover.json` exists with integer `version` `1` and array `devices`. Each row has string `name`, string `mount_ns` (`broker` or `host`), string `ambient_set`, string `bounding_set`, boolean `stale_cleared`.
- All three broker-owned names appear with `mount_ns` `broker`, `ambient_set` equal to the required bounding bits after handoff, `stale_cleared` true.
- Host-tree stale markers for those names are gone after a post-cutover race.
- Unit `PrivateDevices` must not contradict the `DeviceAllow` list used by the broker.
- Seeded tree under `/data/fixtures/broker-seed/` unchanged.

**Constraints:**
- `[environment] allow_internet = false`; verifier deps in Dockerfile.
- No multi-container layout.
- Agent performs ops cutover using bundled C CLIs — not source repair/debug patching.
- Language surface is C helpers + unit fragments + bash wrappers.

### Failure topology

Three interacting clusters. First, false-green surface: `topsurf` checks unit active plus host `/dev` presence and ignores nested mount identity and ambient ledger emptiness. Second, ambient handoff: bounding lines exist but ambient/effective clear across enter while `PrivateDevices=yes` contradicts `DeviceAllow`. Third, seating vs race: nodes remain under host-dev; open/replay recreates stale markers unless seating completes first.

Hard because no single CLI documents full order. `nsprobe` exposes truth; `laneapply`, `nodeseat`, and `ledgerout` mutate distinct subsystems; wrong order keeps `topsurf` green.

### Environment shape

- `environment/Dockerfile` + `.dockerignore` — GCC 13 build, python3/pytest, seeded lab under `/data/lab/`.
- `environment/cmd/` — opaque CLIs: `topsurf`, `nsprobe`, `laneapply`, `nodeseat`, `racepulse`, `ledgerout`.
- `environment/lane/` — `apply_lane_a` fix-path + `legacy_lane` decoy.
- `environment/seat/` — `seat_node_b` fix-path + `probe_node` decoy.
- `environment/roll/` — `emit_rollup_c` fix-path.
- `environment/lib/` — shared state_io / path helpers.
- `environment/units/` — broker unit fragments.
- `environment/config/` — paths and field notes only.
- `environment/scripts/` — status wrappers and cutover stub.
- `environment/data/` — fixture builder + broker-seed anchor.

### Required artifacts

- `tasks/ambient-cap-device-broker-cutover/task.toml` with `allow_internet = false`, `category = "system-administration"`.
- `instruction.md` — symptoms-only; names output path and JSON fields.
- `tests/test.sh`, `tests/test_outputs.py` — six opaque hard tests.
- `solution/solve.sh` — oracle CLI chain only (≥30 LOC), no source repair.
- `environment/**` — 25+ non-Docker files per Initial Draft Commitments.

### Test plan

- `test_k3_zircon` — ambient_set equals required bounding bits for every device after handoff.
- `test_m8_obsidian` — mount_ns is `broker` for all three; nodes live under broker mount tree.
- `test_p2_garnet` — post-race stale_cleared true; host stale markers absent.
- `test_q7_topaz` — bounding_set contains required capability tokens matching ambient after handoff.
- `test_r1_onyx` — PrivateDevices does not contradict DeviceAllow on the live unit fragment.
- `test_t6_amber` — ledger schema: version 1, devices array with required fields.

Multiple valid CLI sequences allowed if outcomes match. Chain-dependent: race/ledger tests need prior seating+handoff.

### Drafting guardrails

Do not embed instruction nouns in fix-path symbols, parameters, or test names. Instruction may use standard ops language. No source-repair TODOs. topsurf must genuinely implement shallow host checks. No HINT walkthroughs under environment/.

### Triviality Ledger

- Calling legacy_lane (privileged full-set) passes topsurf but fails ambient equality after nested enter.
- Seating without apply_lane_a leaves ambient_set empty → test_k3_zircon / test_q7_topaz fail.
- Handoff without seating fails mount_ns and race stale tests.
- ledgerout without unit fold fails PrivateDevices contradiction test.
- Touching broker-seed fails any checksum-adjacent expectations used by verifier fixture guard inside schema tests via live paths only (seed guard embedded in test_t6 companion path checks living under fixtures).

### Per-gate Pitfall Inventory

- RC1: Oracle adds CLI logic only — never delete-bug or wholesale restore golden.
- RC3: Tests assert ambient equality, mount_ns labels, stale clearance — not mere file existence.
- RC5: Expected capability tokens live in test code / instruction field names, not golden under environment/.
- RC6: Instruction symptoms-only — no apply_lane_a / seating order.
- RC7: solve.sh CLI chain ≥30 substantive LOC.
- CR1/CR2: Construction manifest symbols verbatim; 2+2+2 flip split.
- CR7/GX9: JSON field names in instruction; order only in runtime.
- Static: allow_internet=false, .dockerignore, absolute paths, category system-administration.

### Initial Draft Commitments

- `tasks/ambient-cap-device-broker-cutover/task.toml`
- `tasks/ambient-cap-device-broker-cutover/instruction.md`
- `tasks/ambient-cap-device-broker-cutover/tests/test.sh`
- `tasks/ambient-cap-device-broker-cutover/tests/test_outputs.py`
- `tasks/ambient-cap-device-broker-cutover/solution/solve.sh`
- `tasks/ambient-cap-device-broker-cutover/environment/Dockerfile`
- `tasks/ambient-cap-device-broker-cutover/environment/.dockerignore`
- `tasks/ambient-cap-device-broker-cutover/environment/Makefile`
- `tasks/ambient-cap-device-broker-cutover/environment/include/lab.h`
- `tasks/ambient-cap-device-broker-cutover/environment/include/state.h`
- `tasks/ambient-cap-device-broker-cutover/environment/lib/state_io.c`
- `tasks/ambient-cap-device-broker-cutover/environment/lib/state_io.h`
- `tasks/ambient-cap-device-broker-cutover/environment/lib/path_util.c`
- `tasks/ambient-cap-device-broker-cutover/environment/lib/path_util.h`
- `tasks/ambient-cap-device-broker-cutover/environment/lane/apply_lane_a.c`
- `tasks/ambient-cap-device-broker-cutover/environment/lane/apply_lane_a.h`
- `tasks/ambient-cap-device-broker-cutover/environment/lane/legacy_lane.c`
- `tasks/ambient-cap-device-broker-cutover/environment/lane/legacy_lane.h`
- `tasks/ambient-cap-device-broker-cutover/environment/seat/seat_node_b.c`
- `tasks/ambient-cap-device-broker-cutover/environment/seat/seat_node_b.h`
- `tasks/ambient-cap-device-broker-cutover/environment/seat/probe_node.c`
- `tasks/ambient-cap-device-broker-cutover/environment/seat/probe_node.h`
- `tasks/ambient-cap-device-broker-cutover/environment/roll/emit_rollup_c.c`
- `tasks/ambient-cap-device-broker-cutover/environment/roll/emit_rollup_c.h`
- `tasks/ambient-cap-device-broker-cutover/environment/cmd/topsurf/main.c`
- `tasks/ambient-cap-device-broker-cutover/environment/cmd/nsprobe/main.c`
- `tasks/ambient-cap-device-broker-cutover/environment/cmd/laneapply/main.c`
- `tasks/ambient-cap-device-broker-cutover/environment/cmd/nodeseat/main.c`
- `tasks/ambient-cap-device-broker-cutover/environment/cmd/racepulse/main.c`
- `tasks/ambient-cap-device-broker-cutover/environment/cmd/ledgerout/main.c`
- `tasks/ambient-cap-device-broker-cutover/environment/units/broker.service`
- `tasks/ambient-cap-device-broker-cutover/environment/units/broker-devices.conf`
- `tasks/ambient-cap-device-broker-cutover/environment/config/lab.toml`
- `tasks/ambient-cap-device-broker-cutover/environment/config/field-notes.md`
- `tasks/ambient-cap-device-broker-cutover/environment/scripts/status-top.sh`
- `tasks/ambient-cap-device-broker-cutover/environment/scripts/cutover-stub.sh`
- `tasks/ambient-cap-device-broker-cutover/environment/scripts/race-harness.sh`
- `tasks/ambient-cap-device-broker-cutover/environment/data/build_fixtures.sh`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: environment/lane/apply_lane_a.c
  symbol: apply_lane_a
  kind: function
  signature: int apply_lane_a(const char *a, const char *b)
  purpose: Writes ambient and effective cap lines for the nested enter from bounding.

- path: environment/seat/seat_node_b.c
  symbol: seat_node_b
  kind: function
  signature: int seat_node_b(const char *a, const char *b, const char *c)
  purpose: Moves char nodes into broker mount tree and clears host stale markers.

- path: environment/roll/emit_rollup_c.c
  symbol: emit_rollup_c
  kind: function
  signature: int emit_rollup_c(const char *a, const char *b)
  purpose: Folds unit PrivateDevices/DeviceAllow and writes broker-cutover.json.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: environment/lane/apply_lane_a.c
    controls_tests: [test_k3_zircon, test_q7_topaz]
  - id: B
    path: environment/seat/seat_node_b.c
    controls_tests: [test_m8_obsidian, test_p2_garnet]
  - id: C
    path: environment/roll/emit_rollup_c.c
    controls_tests: [test_r1_onyx, test_t6_amber]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: environment/lane/legacy_lane.c
  kind: helper
  rhymes_with: apply_lane_a
  non_fix_purpose: Privileged full-set writer used by diagnostic scripts; does not preserve ambient across enter.

- path: environment/seat/probe_node.c
  kind: helper
  rhymes_with: seat_node_b
  non_fix_purpose: Host-tree listing helper for nsprobe diagnostics; never moves nodes.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [cutover, device, broker, lab, unit, status, host, char, nodes, process, mount, namespace, ambient, capabilities, nested, handoff, concurrent, open, replay, stale, view, tree, helpers, notes, config, fragments, fixtures, seed, output, version, devices, array, row, name, mount_ns, ambient_set, bounding_set, stale_cleared, bits, race, PrivateDevices, DeviceAllow, list]
```
