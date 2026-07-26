### Decision
GO — Attempt 1. Same decision line as the authoring spec.

### Metadata
- Task name: dm-thin-snapshot-fanout-reconcile
- Title: Thin Snapshot Fanout
- Category: system-administration
- Languages: ["go", "c"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["device-mapper", "thin-pool", "snapshot", "activation", "leases", "state-reconciliation"]
- Milestones: 0

### Discovery budget
- Discovery: Sealed journal lines are applied only when generation ≤ pool.seal; disagreeing meta/activation.toml tip pointers are wiped on every materialize preflight.
  Planned location: environment/internal/fold/fold.go (`phase_k`) + environment/config/pool.seal + environment/data/pool/journal/act.wal
  Why instruction must not reveal it: Naming seal-capped journal precedence collapses the task to a ledger transcription checklist.

- Discovery: Tip vs origin byte selection uses epoch compare (tip epoch ≥ floor → cow snap payload; else live origin); stamp-matching decoys never win when a sealed tip exists.
  Planned location: environment/c/ioctl_a.c (`op_q`) + snap meta epoch fields
  Why instruction must not reveal it: Publishing the epoch floor formula turns gamma/beta into one-pass preference flips.

- Discovery: Concurrent materialize requires exclusive per-tip leases; torn `.part` lease files indicate failed serialization.
  Planned location: environment/internal/hold/hold.go (`phase_m`)
  Why instruction must not reveal it: Stating flock/lease mechanics removes the race-diagnosis work.

### Anti-trivialization verdict
All 21 checks PASS for this design: symptoms-only prompt, multi-scenario roster, distributed Go+C loci, opaque symbols, sealed authority that undoes ledger-only edits, false-green surface tool, no answer-key docs.

### Topology enumeration (3 candidate fix topologies)
1. **Journal-first authority**: fold.go phase_k + ioctl_a.c op_q + hold.go phase_m — seal replay selects tips; C preference fills bytes; leases serialize. No single location covers tip authority, decoy rejection, and race.
2. **Haul-centric rewrite**: pull.go wiring + fold preflight + C preference — still needs fold and C; haul alone cannot undo meta or reject decoys.
3. **State-only ops**: rewrite act.wal / activation.toml / origins by hand without code fixes — sealed preflight and wrong op_q still emit decoy/wrong-epoch bytes; concurrent path still tears.

### Rubric axes
- Verifiable: PASS — deterministic payload digests and JSON fields.
- Well-specified: PASS — output paths and report field names stated.
- Solvable: PASS — expert can recover seal/epoch/lease coupling in a few hours.
- Difficult: PASS — multi-authority thin-pool fanout under race, not knob fill.
- Interesting: PASS — real appliance thin-snap fanout ops work.
- Outcome-verified: PASS — grades payloads/report/leases, not process.

### Hardness axes
- Discover: PASS — seal cap, epoch preference, lease rules absent from instruction.
- Synthesize: PASS — journal × C ioctl × leases × decoy shelves.
- Diagnose: PASS — symptoms only (wrong payloads, OK surface).
- Navigate coupling: PASS — ledger edits wiped; local stamp match fails gamma; missing leases fails concurrency.
- Reason beyond training: PASS — simulated dm-thin fanout authority lattice, not textbook LVM recipe.

### Instruction completeness test
No — instruction alone does not give seal-capped replay, epoch floor preference, or lease serialization; solver must engage code and runtime materialize behavior.

## Reviewer Appendix

### Implementation plan
Ship a Go matfan orchestrator that calls fold preflight, C op_q for byte selection, hold for leases, then writes drills + report. Seed crashed meta (wrong tip for alpha), decoy stamp-match for gamma, inverted op_q, fold that ignores seal / skips wipe, and hold that skips exclusive lock. Oracle rewrites phase_k, phase_m, and op_q bodies then rebuilds and runs matfan.

### Proposed file inventory
Matches Initial Draft Commitments in the authoring spec (≥20 environment files excluding Dockerfile).

### Oracle notes
solve.sh patches fold.go, hold.go, and ioctl_a.c with correct seal-capped replay + meta wipe, exclusive flock leases, and epoch-correct buffer preference; `make install`; run matfan materialize once (tests also re-invoke).

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
Rewrite three substantive functions across Go fold, Go hold, and C ioctl — not a config transcription.

Likely editable frontier:
- internal/fold/fold.go
- internal/hold/hold.go
- c/ioctl_a.c
- possibly pull.go wiring if agent rediscovers call order

Requirement-to-file map:
- tip authority after partial roll -> fold.go
- live/cow + decoy rejection -> ioctl_a.c
- concurrent clean leases -> hold.go

Oracle estimated complexity: ~120–180 non-boilerplate LOC

Red flags:
- none if docs stay layout-only and instruction stays symptoms-only

Residual hardness:
Even with the tree visible, agents must recover seal-capped journal precedence, epoch-coupled preference, and lease serialization while ignoring false-green dmhealth and stamp-matched decoys.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
lab, thin, pool, fans, snapshots, per-drill, volumes, crash, mid-roll, drills, payloads, fanout-report, surface, checks, roster, materialize, report, array, name, tip_id, origin_kind, order_index, live, cow, shelves, origins, lease, leases, tooling, sources, correct, coherent, matching, torn

**Renames during drafting:**
- `replay_journal` → `phase_k`: avoid journal/activation nouns
- `take_lease` → `phase_m`: avoid lease noun
- `pick_origin` → `op_q`: avoid origin/tip nouns

**Test names audited:**
- test_k3_zircon
- test_m8_obsidian
- test_p2_garnet
- test_q7_topaz
- test_r1_onyx
- test_t6_amber
- test_v4_jade
- test_w9_quartz
- test_x2_flint

**Concentration math:**
- Total tests across flipping_point_contract: 9
- Per location:
  - L1 (internal/fold/fold.go): 3/9 = 0.333
  - L2 (c/ioctl_a.c): 3/9 = 0.333
  - L3 (internal/hold/hold.go): 3/9 = 0.333
- Cap: 0.5. Max ratio observed: 0.333. Status: PASS

### Per-test feasibility pre-check
- Test: test_k3_zircon — Checks: alpha payload digest — Approaches: 2+ — Chain-dependent: no — Risk: LOW
- Test: test_m8_obsidian — Checks: beta live-origin bytes — Approaches: 2+ — Chain-dependent: no — Risk: LOW
- Test: test_p2_garnet — Checks: gamma not decoy — Approaches: 2+ — Chain-dependent: no — Risk: LOW
- Test: test_q7_topaz — Checks: report fields — Approaches: 2+ — Chain-dependent: no — Risk: MEDIUM
- Test: test_r1_onyx — Checks: origins immutable — Approaches: 2+ — Chain-dependent: no — Risk: LOW
- Test: test_t6_amber — Checks: idempotent rematerialize — Approaches: 2+ — Chain-dependent: no — Risk: LOW
- Test: test_v4_jade — Checks: concurrent leases — Approaches: 2+ — Chain-dependent: no — Risk: MEDIUM
- Test: test_w9_quartz — Checks: ledger wipe under seal — Approaches: 2+ — Chain-dependent: no — Risk: MEDIUM
- Test: test_x2_flint — Checks: payloads despite surface OK — Approaches: 2+ — Chain-dependent: no — Risk: LOW
