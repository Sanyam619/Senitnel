### Decision
GO — Attempt 1. Ops-only cutover (no source repair/debug), distributed across lane/seat/roll, opaque C symbols, false-green topsurf, simulated mount+cap ledgers under concurrent race.

### Metadata
- Task name: ambient-cap-device-broker-cutover
- Title: Ambient-Cap Device Broker Cutover
- Category: system-administration
- Languages: ["C", "bash"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: ["capabilities", "mount", "ops", "c", "devices", "namespaces"]
- Milestones: 0

### Discovery budget
- Discovery: Ambient bits vanish across enter unless apply_lane_a runs after PrivateDevices is folded off.
  Planned location: environment/lane/apply_lane_a.c, environment/units/broker.service
  Why instruction must not reveal it: Would collapse diagnose into checklist.

- Discovery: Host-dev nodes must be seated into broker-dev before racepulse or stale markers return.
  Planned location: environment/seat/seat_node_b.c, environment/data/build_fixtures.sh
  Why instruction must not reveal it: Would make seating-before-race a recited recipe.

- Discovery: topsurf is false-green; only nsprobe reports mount_ns and ambient_set truth.
  Planned location: environment/cmd/topsurf/main.c, environment/cmd/nsprobe/main.c
  Why instruction must not reveal it: Removes discovery tax on surface health.

### Anti-trivialization verdict
All 21 checks PASS in attempt-1 evidence JSON — primary residual risk is decoy legacy_lane looking like a one-shot privilege path; countered by ambient-equality tests after nested enter.

### Topology enumeration (3 candidate fix topologies)
- T1 ops CLI order on correct libraries: apply_lane_a + seat_node_b + emit_rollup_c — chosen for Step 2b.
- T2 unit-first fold then privilege path: broker.service + apply_lane_a + seat_node_b.
- T3 race-hardened seating then ledger: seat_node_b + racepulse + emit_rollup_c.

### Rubric axes
- Verifiable: PASS — JSON + filesystem.
- Well-specified: PASS — field names in instruction.
- Solvable: PASS — CLI ops cutover.
- Difficult: PASS — coupled ambient×mount×unit×race.
- Interesting: PASS — real broker cutovers.
- Outcome-verified: PASS — grades results.

### Hardness axes
- Discover: nsprobe vs topsurf divergence.
- Synthesize: four subsystems.
- Diagnose: symptoms-only.
- Navigate coupling: order-sensitive.
- Reason beyond training: ambient inheritance under nested layout.

### Instruction completeness test
Cannot solve from instruction.md alone — must engage CLIs, unit fragments, and seeded state.

## Reviewer Appendix

### Implementation plan
Build a simulated device-broker lab in C. Seed incomplete ambient ledgers, host-side char nodes, PrivateDevices=yes conflicting with DeviceAllow, and race markers. Ship six CLIs; oracle only chains them (no source repair). Tests assert ambient equality, broker mount_ns, post-race stale clearance, bounding match, unit contradiction cleared, and ledger schema.

### Proposed file inventory
Matches authoring Initial Draft Commitments (25+ environment files excluding Dockerfile/.dockerignore).

### Oracle notes
solve.sh: fold via ledgerout precondition or nodeseat/laneapply order — specifically: nsprobe inspect → laneapply (apply_lane_a) after ensuring unit private flag cleared via ledgerout fold path OR fold first through ledgerout --fold then laneapply then nodeseat then racepulse then ledgerout --emit. Implement fold+emit in emit_rollup_c. Sequence: ledgerout --fold, laneapply, nodeseat, racepulse, ledgerout --emit. ≥30 LOC with checks.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
CLI chain invoking three libraries; no sed-delete of bugs.

Likely editable frontier:
- units/broker.service (agent may edit)
- invoking CLIs (primary)
- possibly rewriting state files under /data/lab

Requirement-to-file map:
- ambient survival -> apply_lane_a via laneapply
- mount seating -> seat_node_b via nodeseat
- unit fold + report -> emit_rollup_c via ledgerout

Oracle estimated complexity: 60–90 LOC bash

Red flags:
- none if CLI names stay opaque and topsurf stays shallow

Residual hardness:
Order and contradictory unit knobs remain after tree is visible.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
cutover, device, broker, lab, unit, status, host, char, nodes, process, mount, namespace, ambient, capabilities, nested, handoff, concurrent, open, replay, stale, view, tree, helpers, notes, config, fragments, fixtures, seed, output, version, devices, array, row, name, mount_ns, ambient_set, bounding_set, stale_cleared, bits, race, PrivateDevices, DeviceAllow, list

**Renames during drafting:**
- `fix_ambient` → `apply_lane_a`
- `move_devices` → `seat_node_b`
- `write_report` → `emit_rollup_c`

**Test names audited:**
- test_k3_zircon
- test_m8_obsidian
- test_p2_garnet
- test_q7_topaz
- test_r1_onyx
- test_t6_amber

**Concentration math:**
- Total tests: 6
- L1 (apply_lane_a.c): 2/6 = 0.333
- L2 (seat_node_b.c): 2/6 = 0.333
- L3 (emit_rollup_c.c): 2/6 = 0.333
- Cap: 0.5. Max ratio: 0.333. Status: PASS

### Per-test feasibility pre-check
- Test: test_k3_zircon — ambient equality — 2+ approaches (CLI or equivalent state writes) — chain: after handoff — LOW
- Test: test_m8_obsidian — mount_ns broker — 2+ — after seating — LOW
- Test: test_p2_garnet — stale cleared post race — 2+ — after seating — MEDIUM (agent must run race)
- Test: test_q7_topaz — bounding tokens — 2+ — after handoff — LOW
- Test: test_r1_onyx — PrivateDevices vs DeviceAllow — 2+ — after fold — LOW
- Test: test_t6_amber — schema — 2+ — after emit — LOW
