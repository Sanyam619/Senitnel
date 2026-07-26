### Decision
GO — Attempt 2. Hard system-administration Ceph OSD CRUSH reweight seating with coupled preference-gated rematerialize × packed-map tip resolution × sealed out-journal continuity × hold-window pool placement × canonical idempotent ledger emit.

### Metadata
- Task name: ceph-osd-crush-reweight-seating
- Title: Ceph CRUSH Reweight Seating
- Category: system-administration
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["ceph", "crush-map", "osd-reweight", "placement-group", "out-journal", "generation-gate"]
- Milestones: 0

### Discovery budget
- Discovery: Durable tip per device is the highest-generation row inside the packed binary CRUSH map (text mirror under `/app/data/crush/`); the surface map under `/var/lib/ceph/ops/` and the live sheets under `/etc/ceph/` carry stale, mutually conflicting values.
  Planned location: packed map + faithful text mirror + `ops/gorse_t.sh` behavior; stale `surface.map` and drifted `reweight.d` seeds
  Why instruction must not reveal it: naming which source is stale collapses reweight diagnosis to transcription of the durable rows.
- Discovery: Live reweight sheets rematerialize from the surface map on every seating pass unless the preference selects the durable map AND a receipt matching `gen.target` with `mode=seal` exists; naive `/etc` edits are undone by verifier re-entry.
  Planned location: `ops/kelp_v.sh` + `/var/lib/ceph/ops/prefer.toml` + receipt outcome prose in `/app/docs/`
  Why instruction must not reveal it: pasting the gate recipe beside helper names turns the authority locus into a one-pass checklist.
- Discovery: Sealed out-journal continuity is last-action-by-epoch (out followed by later in is in); hold windows are strict (`until_epoch > clock`) so an expired hold row must not exclude its host.
  Planned location: sealed `out.jsonl`/`holds.jsonl` (digest-pinned mirrors under `/app/data/ceph/`) + `lane/moss_q.sh` and `mast/fern_h.sh`
  Why instruction must not reveal it: stating ordering and strict inequality reduces journal and hold cells to spec implementation.
- Discovery: Pool degraded is computed from distinct unheld hosts carrying an in+up device versus pool size; live `pools.d` state flags are stale bait; one pool stays truthfully degraded even after fully correct seating.
  Planned location: `mast/fern_h.sh` + durable pool fixtures + stale flags seeded into `/etc/ceph/pools.d/`
  Why instruction must not reveal it: revealing computed-vs-reported polarity and the held-host arithmetic lets agents hardcode pool rows.

### Anti-trivialization verdict
All 21 checks PASS except oracle_locality WARN (oracle rewrites five helper bodies wholesale — the accepted house pattern for seating desks; mitigated by substantive multi-authority bodies and a flipping-point contract with max per-location concentration 0.417). Key checks: disclosure-collapse PASS (rules are outcomes, work remains), grep-collapse PASS (opaque fix-path symbols), one-pass solvability PASS (three conflicting value sources force behavioral reasoning), hard-only gate PASS (rematerialize coupling + placement math).

### Topology enumeration (3 candidate fix topologies)
1. Rewrite the shipped pipeline in place — `ops/kelp_v.sh`, `ops/gorse_t.sh`, `lane/moss_q.sh`, `mast/fern_h.sh`, `deck/tarn_e.sh`. No single body suffices: each owns a distinct authority and reverting any one flips its declared test subset.
2. Replace the pipeline with one consolidated emitter — entrypoint `ops/run_crush_seat.sh`, new emitter, `prefer.toml`, receipt plane. The emitter must still implement all five authorities and the clobbering preflight must be gated, so ≥3 locations change together.
3. Data-plane-first — hand-align `reweight.d`, flip `prefer.toml`, hand-write the receipt, then fix compute/emit. Fails unless `kelp_v` stops deleting the receipt and `moss_q`/`fern_h`/`tarn_e` compute truthful in/up/degraded, so ≥3 locations again.

### Rubric axes
- Verifiable: deterministic pytest recomputation from digest-pinned fixtures + double re-entry — Pass
- Well-specified: two-paragraph contract + docs rulebook; equivalent verifiers derivable — Pass
- Solvable: storage operator solves in hours; few hundred lines of shell/inline python — Pass
- Difficult: multi-authority reconciliation with misleading sources and strict windows — Pass
- Interesting: placement-drift reconciliation is real paid Ceph ops work — Pass
- Outcome-verified: only end-state ledger and live/durable agreement graded — Pass

### Hardness axes
- Discover: stale-vs-durable source identification, gate semantics, ordering rules all live in fixtures/runtime only.
- Synthesize: five interacting subsystems spanning `/app`, `/etc`, `/var` must agree before seat_ok.
- Diagnose: symptoms-only instruction; agent must explain reverting sheets, stuck-out devices, stuck-degraded pools.
- Navigate coupling: preflight undoes naive edits; pool cells consume the seated set produced by other fixes.
- Reason beyond training: desk-specific invariants (hold windows vs replica spread, last-in-epoch continuity) are not tutorial Ceph.

### Instruction completeness test
No — the instruction gives the contract and symptoms but never says which sources are stale, how tips resolve, how the rematerialize gate works, how journal/hold ordering computes, or why a pool can stay degraded after seating a device. Solving requires engaging the environment.

## Reviewer Appendix

### Implementation plan
The environment ships a simulated Ceph placement desk: live `/etc/ceph` (drifted reweight sheets, pool declarations with stale state flags), durable `/var/lib/ceph/ops` (packed binary CRUSH map built from the frozen text mirror, stale surface map, preference file selecting the surface map, sealed out-journal and hold ledger, generation floor/target, state plane), and frozen digest-pinned fixtures under `/app/data`. Five bash helpers under `/app/{ops,lane,mast,deck}` form the seating pipeline invoked by `/app/ops/run_crush_seat.sh`; all five ship with wrong authority choices (always-rematerialize + receipt deletion, oldest-row tip pick from the mirror without floor/receipt, any-out-is-out journal reading, reported-flag pool marks ignoring holds, assert-everything-fine emit). The agent must reconcile the desk so the ledger reports the truthful in/up/generation/degraded matrix, stays byte-identical across passes, and survives verifier re-entry.

### Proposed file inventory
See authoring spec Initial Draft Commitments (52 paths; ~47 files under environment/ excluding Dockerfile).

### Oracle notes
`solve.sh` rewrites the five helper bodies via heredocs: kelp_v honors the preference+receipt gate (rematerializing from the surface map remains the ungated path), gorse_t decodes the packed map with inline python, resolves newest-generation rows, verifies the sealed target row, aligns `reweight.d`, writes state and the receipt, moss_q computes last-action flags, fern_h computes active-hold-aware host spread per pool, tarn_e emits the canonical ledger with the agreement conjunction. It then flips `prefer.toml` to durable and runs the entrypoint twice.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
Rewrite five helper bodies across four directories, flip the map preference, and let the pipeline write a matching receipt. Anything smaller is clobbered by the preflight or fails recomputed matrix cells.

Likely editable frontier:
- environment/ops/kelp_v.sh, environment/ops/gorse_t.sh, environment/lane/moss_q.sh, environment/mast/fern_h.sh, environment/deck/tarn_e.sh, /var/lib/ceph/ops/prefer.toml (runtime)

Requirement-to-file map:
- reweight persistence across passes -> kelp_v + prefer + receipt
- truthful weight/generation/up -> gorse_t (+ kelp_v gate)
- truthful in -> moss_q (+ gorse_t up inputs)
- truthful degraded -> fern_h (+ seated set from B/C)
- ledger bytes + seat_ok -> tarn_e

Oracle estimated complexity: ~230 non-boilerplate LOC

Red flags:
- none (oracle_locality WARN documented: five wholesale helper rewrites, mitigated by distribution and coupling)

Residual hardness:
After the file tree is visible, the agent still must determine which of three conflicting weight sources is durable, discover the rematerialize gate from re-entry behavior, derive journal/hold ordering semantics from sealed fixtures, and build placement math that leaves one pool truthfully degraded.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
ceph, crush, osd, osds, reweight, seat, seating, pool, pools, degraded, generation, journal, host, hosts, hold, held, weight, placement, tip, map, mirror, floor, epoch, ledger, authority, fixtures, schema, desk, materials, device, health

**Renames during drafting:**
- `prefer_gate` → `kelp_v`: avoid preference/gate adjacency on fix path
- `apply_tips` → `gorse_t`: avoid tip/map/generation tokens
- `journal_flags` → `moss_q`: avoid journal/epoch tokens
- `pool_spread` → `fern_h`: avoid pool/host/hold tokens
- `emit_seat` → `tarn_e`: avoid seat/ledger tokens

**Test names audited:**
- test_k2_agate
- test_d5_basalt
- test_y8_gneiss
- test_r3_pumice
- test_m6_schist
- test_w4_marble
- test_h9_shale
- test_c1_borax
- test_p5_ochre
- test_t8_umber
- test_j4_lignite
- test_e2_galena

**Concentration math:**
- Total tests across `flipping_point_contract`: 12
- Per location:
  - A (`ops/kelp_v.sh`): 3/12 = 0.25
  - B (`ops/gorse_t.sh`): 4/12 = 0.333333
  - C (`lane/moss_q.sh`): 2/12 = 0.166667
  - D (`mast/fern_h.sh`): 3/12 = 0.25
  - E (`deck/tarn_e.sh`): 5/12 = 0.416667
- Cap: 0.5. Max ratio observed: 0.416667. Status: PASS

### Per-test feasibility pre-check
- Test: test_k2_agate — Checks: schema/types/seat_ok after re-entry — Valid approaches: 2+ — Chain-dependent: no (re-enters entrypoint) — Feasibility risk: LOW
- Test: test_d5_basalt — Checks: byte-identical double run — Valid approaches: 2+ (any deterministic emit) — Chain-dependent: no — Feasibility risk: LOW
- Test: test_y8_gneiss — Checks: fixture pins + sealed live copies + seat_ok — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_r3_pumice — Checks: weight/up matrix vs durable tips incl. floor — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_m6_schist — Checks: journal last-action continuity — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_w4_marble — Checks: degraded recomputed from seated set — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_h9_shale — Checks: active vs expired hold effects — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_c1_borax — Checks: receipt/gen.live agreement + sheet persistence — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_p5_ochre — Checks: generation fields + floor polarity — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_t8_umber — Checks: surface health bait still HEALTH_OK — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_j4_lignite — Checks: full osds array vs EXPECTED — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
- Test: test_e2_galena — Checks: full pools array + seat_ok coupling — Valid approaches: 2+ — Chain-dependent: no — Feasibility risk: LOW
