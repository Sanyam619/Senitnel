### Decision
GO — Attempt 2. Ops-only fanotify mark cutover (no repair/debug framing), distributed across ring/gate/roll, opaque C symbols, false-green topsurf, simulated mount-ns mark ledgers under concurrent writer race.

### Metadata
- Task name: fanotify-mount-ns-mark-cutover
- Title: Fanotify Mount-NS Mark Cutover
- Category: system-administration
- Languages: ["C"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: ["fanotify", "mount", "namespaces", "ops", "c", "systemd"]
- Milestones: 0

### Discovery budget
- Discovery: Marks must live under the broker mount-ns tree after bind seating; host-ns mark count keeps topsurf green while broker view stays empty.
  Planned location: environment/cmd/nsprobe/main.c and /data/lab/marks/{host,broker}/ plus identity/mnt_ns
  Why instruction must not reveal it: Naming host-vs-broker mark directories collapses the seating discovery.
- Discovery: After pivot/bind, watched paths need filesystem marks; inode marks miss inherited bind children and fail mark_kind checks.
  Planned location: environment/ring/apply_ring_a.c ledger writes and nsprobe kind field
  Why instruction must not reveal it: Naming FAN_MARK_FILESYSTEM vs inode as the fix collapses kind diagnosis.
- Discovery: PrivateMounts=yes blocks reopen inheritance; fold to no before remount cycle, else inherited_ok stays false.
  Planned location: environment/units/broker.service live fragment and environment/roll/emit_roll_c.c fold mode
  Why instruction must not reveal it: Naming the unit knob and fold order turns the task into policy transcription.

### Anti-trivialization verdict
All 21 checks PASS — see attempt-2 evidence JSON. Key blockers avoided: disclosure-collapse via symptoms-only; orthogonal-checklist via coupled attach/reopen/fold; grep-collapse via opaque symbols.

### Topology enumeration (3 candidate fix topologies)
- T1: CLI-ops cutover — apply_ring_a + cycle_gate_b + emit_roll_c; no single location suffices.
- T2: Unit-first fold then attach/reopen — same three files, alternate order; fold alone leaves host marks.
- T3: Race-guarded seating with racepulse — racepulse alone cannot create broker filesystem marks.

### Rubric axes
- Verifiable: PASS — deterministic JSON + on-disk ledgers.
- Well-specified: PASS — field names and outcome constraints named.
- Solvable: PASS — expert ops hours.
- Difficult: PASS — fanotify × mount-ns expertise.
- Interesting: PASS — real broker cutover.
- Outcome-verified: PASS — results not process.

### Hardness axes
- Discover: PASS — nsprobe + unit fragment inspection required.
- Synthesize: PASS — mark ledger × trees × unit × race.
- Diagnose: PASS — symptoms only.
- Navigate coupling: PASS — wrong order keeps topsurf green.
- Reason beyond training: PASS — FAN_MARK_FILESYSTEM vs inode after bind under PrivateMounts.

### Instruction completeness test
Can the agent solve by reading ONLY instruction.md? No — must recover mark ns ownership, filesystem vs inode after bind, and PrivateMounts vs inheritance from the lab.

## Reviewer Appendix

### Implementation plan
Ship a C lab under /app with rebuildable helpers installed to /opt/fev/bin. Initial apply_ring_a / cycle_gate_b / emit_roll_c stubs keep marks on host as inode, skip remount, and emit without folding PrivateMounts. Agent implements correct bodies and runs fold→attach→reopen→race→emit. Verifier asserts live state plus JSON.

### Proposed file inventory
Matches Initial Draft Commitments in the authoring spec (25+ environment files excluding Dockerfile/dockerignore).

### Oracle notes
solve.sh rewrites apply_ring_a.c, cycle_gate_b.c, emit_roll_c.c with correct logic, make && copy binaries, then ledgerout --fold, ringapply, gatecycle, racepulse, ledgerout --emit.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
Three opaque C bodies plus a five-step CLI chain; no single-file solution.

Likely editable frontier:
- environment/ring/apply_ring_a.c
- environment/gate/cycle_gate_b.c
- environment/roll/emit_roll_c.c

Requirement-to-file map:
- mark_ns/mark_kind -> apply_ring_a
- inherited_ok/inherit table -> cycle_gate_b
- race_stable/PrivateMounts/JSON -> emit_roll_c (+ racepulse)

Oracle estimated complexity: 120+ lines non-boilerplate across bodies + solve.sh chain

Red flags:
- none

Residual hardness:
False-green topsurf and legacy_ring decoy keep surface health while ns/kind/inherit remain wrong until all three roots are correct.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
cutover, file-event, broker, lab, unit, status, local, scanner, write, events, marks, mount, namespace, pivot, bind, handoff, reopen, restart, inherited, mounts, concurrent, writers, race, mark, add, remove, tree, helpers, notes, config, sources, fragments, fixtures, watch-seed, output, version, watches, array, row, path, mark_ns, mark_kind, inherited_ok, race_stable, filesystem, PrivateMounts, inheritance, nested

**Renames during drafting:**
- [`mark_attach` → `apply_ring_a`: mark/attach collide]
- [`bind_slot_a` → `apply_ring_a`: bind substring]
- [`inherit_reopen` → `cycle_gate_b`: inherit/reopen collide]
- [`test_mark_ns_broker` → `test_v4_quartz`: instruction nouns in test name]

**Test names audited:**
- test_v4_quartz
- test_w9_jasper
- test_x2_citrine
- test_k6_fluorite
- test_y5_beryl
- test_z1_spinel

**Concentration math:**
- Total tests across `flipping_point_contract`: 6
- Per location:
  - L1 (`environment/ring/apply_ring_a.c`): 2/6 = 0.333333
  - L2 (`environment/gate/cycle_gate_b.c`): 2/6 = 0.333333
  - L3 (`environment/roll/emit_roll_c.c`): 2/6 = 0.333333
- Cap: 0.5. Max ratio observed: 0.333333. Status: PASS

### Per-test feasibility pre-check
- Test: test_v4_quartz — Checks mark_ns broker + disk seating — Valid approaches: 2+ — Chain-dependent: no — Feasibility: LOW
- Test: test_w9_jasper — Checks mark_kind filesystem — Valid approaches: 2+ — Chain-dependent: soft on seating — Feasibility: LOW
- Test: test_x2_citrine — Checks inherited_ok — Valid approaches: 2+ — Chain-dependent: yes on seating — Feasibility: MEDIUM
- Test: test_k6_fluorite — Checks inherit table remount-ok — Valid approaches: 2+ — Chain-dependent: yes on cycle — Feasibility: MEDIUM
- Test: test_y5_beryl — Checks race_stable after pulse — Valid approaches: 2+ — Chain-dependent: yes on seating+reopen+fold — Feasibility: MEDIUM
- Test: test_z1_spinel — Checks PrivateMounts + schema + seed — Valid approaches: 2+ — Chain-dependent: soft — Feasibility: LOW
