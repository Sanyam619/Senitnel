### Decision
GO — Attempt 1. Original RT trace reconstruction task; distributed C fix path with opaque weave/latch/band/map symbols.

### Metadata
- version: 2
- Task name: rt-priority-inversion-reconstruction
- Title: RT Inversion Rebuild
- Category: scientific-computing
- Languages: ["C"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["tool_specific"]
- Tags: ["c", "real-time", "scheduling", "trace", "simulation", "scientific-computing"]
- Milestones: 0

## Authoring Brief

### Public contract
Agent rebuilds `/opt/kernlab/bin/kernprobe` and runs `/opt/kernlab/bin/kernprobe --manifest /opt/kernlab/config/manifest.json --out /output/analysis.json`. Each manifest scenario id must appear under `scenarios` with `missed_deadline_task`, ordered `chain` of three actor ids, and integer `ceilings` map keyed by gate ids. The bundled replay tool `/opt/kernlab/bin/klreplay` must report zero misses when driven with the emitted ceilings. Event layout and set catalog live under `/opt/kernlab/docs/`.

### Failure topology
Recorded runs show periodic actors missing release windows while a mid-band runnable keeps the CPU. The stock probe names only the immediate gate holder, drops waiters after context changes, and assigns ceilings from the holder band instead of the waiter band. Replay proof fails on every manifest row.

### Environment shape
C tree under `/opt/kernlab` with deterministic replay core, probe CLI, opaque modules under `kern/a7`, `relay/m3`, `span/q9`, `lift/w2`, trace corpus, per-case set configs, manifest.

### Required artifacts
instruction.md, task.toml, output_contract.toml, Dockerfile, .dockerignore, Makefile, 24+ environment files, solve.sh, test.sh, test_outputs.py.

### Test plan
- test_h4_schema_bundle — analysis.json version and per-scenario keys
- test_u2_nova_chain — case_nova chain triple
- test_k7_orbit_chain — case_orbit chain triple
- test_m3_pulse_chain — case_pulse chain triple
- test_p9_delta_chain — case_delta chain triple
- test_q1_nova_replay — klreplay zero misses for nova ceilings
- test_r5_orbit_replay — klreplay zero misses for orbit ceilings
- test_s8_pulse_replay — klreplay zero misses for pulse ceilings
- test_t2_delta_replay — klreplay zero misses for delta ceilings

### Drafting guardrails
Symptoms-only instruction; opaque fix-path symbols; expected chains live in tests only.

### Triviality Ledger
- Direct-holder scan passes one field but fails chain tests because band module ignores preemptor.
- Timestamp-only weave passes sorting but mis-attributes waiters after wakeups.
- Holder-band ceilings pass replay on trivial rows but fail delta and orbit deadline windows.

### Per-gate Pitfall Inventory
- RC3: tests compare chain triples and replay miss counts, not file existence.
- RC6: instruction describes symptoms and output schema, not weave/latch/band/map internals.
- RC7: oracle rewrites four modules with substantive timeline/ownership/chain/ceiling logic.
- CR7: fix-path symbols op_weave, op_latch, op_span, op_lift avoid instruction nouns.

### Initial Draft Commitments
- instruction.md
- task.toml
- output_contract.toml
- environment/Dockerfile
- environment/.dockerignore
- environment/Makefile
- environment/include/klb_fmt.h
- environment/include/klb_sim.h
- environment/include/klb_types.h
- environment/src/sim/core.c
- environment/src/sim/queue.c
- environment/src/sim/lock.c
- environment/src/sim/deadline.c
- environment/src/sim/replay.c
- environment/src/sim/util.c
- environment/src/probe/main.c
- environment/src/probe/stage_a.c
- environment/src/probe/stage_b.c
- environment/kern/a7/weave.c
- environment/kern/a7/hash.c
- environment/relay/m3/latch.c
- environment/relay/m3/shadow.c
- environment/span/q9/span.c
- environment/span/q9/ring.c
- environment/lift/w2/lift.c
- environment/config/manifest.json
- environment/config/case_nova.toml
- environment/config/case_orbit.toml
- environment/config/case_pulse.toml
- environment/config/case_delta.toml
- environment/traces/case_nova.evt
- environment/traces/case_orbit.evt
- environment/traces/case_pulse.evt
- environment/traces/case_delta.evt
- environment/docs/event_layout.txt
- environment/docs/set_catalog.txt
- environment/scripts/smoke.sh
- solution/solve.sh
- tests/test.sh
- tests/test_outputs.py
- tests/chain_ref.py

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table
- path: kern/a7/weave.c
  symbol: op_weave
  kind: function
  signature: int op_weave(const char *path, KlbWeave *out)
  purpose: parse trace file into ordered actor timeline with wait edges
- path: relay/m3/latch.c
  symbol: op_latch
  kind: function
  signature: int op_latch(const KlbWeave *w, KlbLatch *out)
  purpose: derive gate holder and waiter sets at each step
- path: span/q9/span.c
  symbol: op_span
  kind: function
  signature: int op_span(const KlbLatch *l, const char *tgt, char chain[3][32])
  purpose: locate three-actor blocking span including mid-band preemptor
- path: lift/w2/lift.c
  symbol: op_lift
  kind: function
  signature: int op_lift(const char *cfg, const char *tgt, int *ceilings, int cap)
  purpose: compute static band map from set catalog and waiter band

#### flipping_point_contract
locations:
  - id: A
    path: kern/a7/weave.c
    controls_tests: [test_m3_pulse_chain, test_u2_nova_chain]
  - id: B
    path: relay/m3/latch.c
    controls_tests: [test_k7_orbit_chain, test_p9_delta_chain]
  - id: C
    path: span/q9/span.c
    controls_tests: [test_u2_nova_chain, test_k7_orbit_chain, test_m3_pulse_chain, test_p9_delta_chain]
  - id: D
    path: lift/w2/lift.c
    controls_tests: [test_q1_nova_replay, test_r5_orbit_replay, test_s8_pulse_replay, test_t2_delta_replay]
no_single_location_flips_majority: true
concentration_cap: 0.5

#### decoy_manifest
- path: kern/a7/hash.c
  kind: helper
  rhymes_with: op_weave
  non_fix_purpose: fingerprint rows for manifest validation
- path: relay/m3/shadow.c
  kind: helper
  rhymes_with: op_latch
  non_fix_purpose: shadow table for debug dumps
- path: span/q9/ring.c
  kind: helper
  rhymes_with: op_span
  non_fix_purpose: ring buffer for probe stderr

#### code_forbidden_tokens
code_forbidden_tokens: [periodic, deadline, trace, event, lock, acquire, release, wakeup, timer, scheduler, simulator, replay, priority, inversion, chain, holder, waiter, preemptor, runqueue, timeline, ownership, ceiling, assignment, analysis, scenario, task, reconstruction, missed, preempt, periodic]
