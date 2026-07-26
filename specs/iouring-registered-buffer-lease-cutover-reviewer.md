### Decision
GO — Attempt 1. Ops-only ingest cutover (no repair/debug framing): C io_uring fixed-buffer registry × Go lease broker × sealed-journal preflight authority; opaque symbols; false-green healthctl; decoy live profiles.

### Metadata
- Task name: iouring-registered-buffer-lease-cutover
- Title: io_uring Buffer Lease Cutover
- Category: system-administration
- Languages: ["C", "Go"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: ["io-uring", "mount", "namespaces", "leases", "ops", "c"]
- Milestones: 0

### Discovery budget
- Discovery: Durable lease epoch and journal seal tip come from the fleet profile via the Go mesh writer; harbor/live map is a decoy that healthctl ignores.
  Planned location: environment/mesh/sieve_b.go, environment/config/fleet.toml, environment/cmd/preflight/main.go
  Why instruction must not reveal it: Naming fleet vs harbor or seal math collapses to profile transcription.

- Discovery: Fixed-buffer registration must write broker-tree slots with generation equal to durable epoch, and PrivateMounts=yes clears/blocks fresh registration.
  Planned location: environment/ring/fold_a.c, environment/units/
  Why instruction must not reveal it: Naming fold_a or the PrivateMounts gate turns the task into a checklist patch.

- Discovery: Preflight rewrites naive unit/lease edits unless the seal matches durable epoch; emit must fold PrivateMounts and seat tenants into the broker mount tree.
  Planned location: environment/cmd/preflight/main.go, environment/roll/emit_c.c
  Why instruction must not reveal it: Revealing rewrite authority removes the journal/preflight coupling that blocks shallow unit edits.

### Anti-trivialization verdict
| Check | Verdict | Reasoning |
| --- | --- | --- |
| 1 Disclosure-collapse | PASS | Symptoms-only; omits order, seal, fleet authority |
| 2 Hidden-instance | PASS | Fixed three-tenant lab, not hunt-one-file |
| 3 Single-artifact repair | PASS | Buffer reg + durable lease/seal + PrivateMounts/seat/emit |
| 4 Generalization | PASS | Per-tenant outcomes + preflight re-entry |
| 5 Prompt-honesty | PASS | Does not name fold_a/SieveB/emit_c |
| 6 Cheating-vs-difficulty | PASS | Hardness is authority coupling |
| 7 Mechanical-fix filter | PASS | Not deps/timeout |
| 8 Localized-fix | PASS | Three roots: ring/mesh/roll |
| 9 Oracle-locality | PASS | Rebuild three bodies + multi-CLI ops |
| 10 Small declarative-cluster | PASS | Preflight undoes unit-only edits |
| 11 Grep-collapse | PASS | Opaque fold_a/SieveB/emit_c |
| 12 Pre-factored-helper | PASS | Helpers do not mirror prompt verbs as fix symbols |
| 13 Recipe-discount | PASS | Not a textbook io_uring tutorial |
| 14 Security-aura discount | PASS | Category is system-administration |
| 15 Orthogonal-checklist | PASS | Seal×epoch×buffers×PrivateMounts coupled |
| 16 Harness-discount | PASS | Single container; harness not hardness |
| 17 One-pass solvability | PASS | Decoy profiles + preflight rewrite defeat one-pass |
| 18 Hard-only gate | PASS | Designed hard-only |
| 19 Discovery budget | PASS | Three discoveries above |
| 20 Instruction specificity | PASS | symptoms-only |
| 21 Topology distribution | PASS | Three topologies below |

### Topology enumeration (3 candidate fix topologies)
1. **Register-first lattice:** fold_a (registry gen) + SieveB (durable+seal) + emit_c (PrivateMounts+seat+JSON). No single location seats fresh buffers under a seal-stable epoch.
2. **Lease-authority-first:** SieveB seal tip + preflight behavior + fold_a gen agreement + emit seating. Skipping seal leaves preflight destroying unit folds.
3. **Seat-and-fold-last:** emit_c seating/PrivateMounts + fold_a broker slots + SieveB epoch. Seating alone leaves stale gen and failing preflight_stable.

### Rubric axes
- Verifiable: PASS — deterministic JSON + on-disk ledgers + preflight re-run.
- Well-specified: PASS — symptoms + output schema fields named.
- Solvable: PASS — expert ops engineer can cut over in a few hours.
- Difficult: PASS — multi-authority OS state with decoys and rewrite trap.
- Interesting: PASS — real ingest broker lease/buffer cutover work.
- Outcome-verified: PASS — grades ledgers and JSON, not process.

### Hardness axes
- Discover: PASS — must learn fleet vs harbor, seal tip, register/seat coupling from tools/code.
- Synthesize: PASS — C ring + Go mesh + unit fragments + journal preflight.
- Diagnose: PASS — instruction reports OK health and stale jobs, not causes.
- Navigate coupling: PASS — local PrivateMounts or live-map edits fail distant preflight/buffer tests.
- Reason beyond training: PASS — simulated io_uring fixed buffers × mount-ns lease epochs × sealed journal is not a stock recipe.

### Instruction completeness test
Can the agent solve this by reading ONLY instruction.md? No — must discover which profile backs the durable map, how seal interacts with preflight, and that healthctl is shallow.

## Reviewer Appendix

### Implementation plan
Ship a broken ingest lab: healthctl greens; buffers on host with stale gen; live lease map from harbor; PrivateMounts=yes; journal seal mismatched. Agent must implement fold_a/SieveB/emit_c correctly, rebuild, and run leasectl→bufreg→nsbind→ledgerout so durable epoch, broker seating, and seal-stable preflight agree. Distinct from fanotify mark cutover (buffers+leases+journal, not fanotify marks).

### Proposed file inventory
Matches Initial Draft Commitments in the authoring spec (25+ environment files excluding Dockerfile).

### Oracle notes
solve.sh rewrites fold_a.c, sieve_b.go, emit_c.c with correct bodies; make + go build; run leasectl (durable path), bufreg, nsbind, ledgerout --fold/--emit; run preflight once to confirm stability; do not touch ingest-seed.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
Implement three opaque bodies and run the ops CLI chain so durable epoch, broker registry gen, PrivateMounts fold, seating, and seal agree under preflight.

Likely editable frontier:
- environment/ring/fold_a.c
- environment/mesh/sieve_b.go
- environment/roll/emit_c.c
- unit fragments / config profiles (naive edits alone fail)

Requirement-to-file map:
- buf_fresh / slots -> fold_a
- lease_epoch / preflight_stable -> SieveB + preflight
- mount_ns / PrivateMounts -> emit_c

Oracle estimated complexity: 80–120 non-boilerplate LOC

Red flags:
- none if field-notes stay formula-free and decoys lack “ignore me” banners

Residual hardness:
Even with visible CLIs, agents must learn seal/preflight coupling and that harbor live maps are insufficient.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
surface, health, ingest, broker, lab, lease, rollover, jobs, registered, buffers, PrivateMounts, tenant, trees, preflight, sealed, journal, config, profiles, authoritative, durable, map, cutover, fixed-buffer, registrations, mount, namespace, epoch, seating, registry, fixtures, ingest-seed, output, version, tenants, array, row, buf_slot, mount_ns, lease_epoch, buf_fresh, preflight_stable, booleans, integer, string, on-disk, slot, id, host

**Renames during drafting:**
- [`broker/` → `mesh/`: instruction noun `broker` must not appear as fix-path directory]
- [`leasectl` kept as CLI: not on symbol_table fix path; ops discoverability]

**Test names audited:**
- test_n4_quartz
- test_p7_jasper
- test_r2_citrine
- test_k8_fluorite
- test_w3_beryl
- test_y6_spinel

**Concentration math:**
- Total tests across `flipping_point_contract`: 6
- Per location:
  - L1 (`environment/ring/fold_a.c`): 2/6 = 0.333
  - L2 (`environment/mesh/sieve_b.go`): 2/6 = 0.333
  - L3 (`environment/roll/emit_c.c`): 2/6 = 0.333
- Cap: 0.5. Max ratio observed: 0.333. Status: PASS

### Per-test feasibility pre-check
- Test: test_n4_quartz — Checks broker mount seating for all tenants — Valid approaches: 2+ — Chain-dependent: no (needs emit seating) — Feasibility: LOW
- Test: test_p7_jasper — Checks buf_fresh + gen==durable epoch — Valid approaches: 2+ — Chain-dependent: partial on lease map — Feasibility: LOW
- Test: test_r2_citrine — Checks lease_epoch vs durable/fleet — Valid approaches: 2+ — Chain-dependent: no — Feasibility: LOW
- Test: test_k8_fluorite — Checks PrivateMounts=no — Valid approaches: 2+ — Chain-dependent: no — Feasibility: LOW
- Test: test_w3_beryl — Re-runs preflight; asserts stability — Valid approaches: 2+ — Chain-dependent: yes on seal — Feasibility: LOW
- Test: test_y6_spinel — Schema + seed + buf_slot match — Valid approaches: 2+ — Chain-dependent: no — Feasibility: LOW
