### Decision
GO — Attempt 1. System-administration chrony/timesync seating via live `/etc` + `/var` ops: preference lattice rematerialize, lexical timesync drop-in fold, hold×roster×stratum-band selection, false-green `timehealth`, durable offset budget. Configure/seat framing (not repair/debug). Languages bash only.

### Metadata
- Task name: chrony-stratum-preference-lattice
- Title: Chrony Stratum Preference Lattice
- Category: system-administration
- Languages: ["bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["chrony", "stratum", "time-seating", "preference-lattice", "dropin-policy", "hold-window"]
- Milestones: 0

### Discovery budget
- Discovery: Prefer mode `live`/`surface` rematerializes chrony sources and timesync drop-ins from `/var/lib/time/surface/` on every seat; only `durable`/`authority` preserve agent edits.
  Planned location: `ops/axle_p.sh` + `/var/lib/time/ops/prefer.toml`
  Why instruction must not reveal it: naming rematerialize turns the task into a one-knob prefer flip.

- Discovery: Timesync drop-ins fold in ascending lexical order with last-key-wins; `40-lab.conf` decoy NTP loses only when `90-local.conf` carries the durable peer.
  Planned location: `ops/knit_w.sh` + `/etc/systemd/timesyncd.conf.d/`
  Why instruction must not reveal it: publishing fold order + winner is a drop-in transcription checklist.

- Discovery: `offset_bound_ms` is the durable budget for the selected peer in `/var/lib/time/ops/offsets.toml`, not the optimistic figure `timehealth` prints.
  Planned location: `rim/mark_t.sh` + `ops/emit_q.sh`
  Why instruction must not reveal it: stating the budget table collapses offset cells to copy-paste.

- Discovery: Held roster peers must appear in `sources[]` with `hold:true` and `selected:false`; omitting them or selecting them both fail.
  Planned location: `ops/pull_m.sh` + hold file under `/var/lib/chrony/`
  Why instruction must not reveal it: listing exact hold names is an answer key once the roster is greppable.

### Anti-trivialization verdict
All 21 checks PASS for this design: symptoms-only configure framing; multi-locus prefer×fold×hold×bind×emit; false-green timehealth; rematerialize authority; verifier-owned EXPECTED; opaque symbols; hard-only coupled topology.

### Topology enumeration (3 candidate fix topologies)
1. Prefer-first: axle_p + prefer.toml + surface seeds — still needs knit_w + pull_m + bind_v for fold/hold/selection.
2. Fold-first: knit_w + timesync drop-ins — still fails rematerialize re-entry and hold×band matrix without axle_p/pull_m/bind_v.
3. Emit-first: emit_q + mark_t hand JSON — fails live chrony, drop-in fold, and wipe re-entry without bind_v/knit_w/axle_p.

### Rubric axes
- Verifiable: PASS — deterministic JSON + live file asserts.
- Well-specified: PASS — schema + seating outcomes documented; bands in docs.
- Solvable: PASS — expert sysadmin hours, bash ops only.
- Difficult: PASS — coupled lattice beyond textbook chrony.conf edit.
- Interesting: PASS — real time-desk seating work.
- Outcome-verified: PASS — grade seating report + live state, not process.

### Hardness axes
- Discover: PASS — rematerialize, fold polarity, offset budget source, hold-row shape.
- Synthesize: PASS — prefer × drop-ins × holds × roster × bands × emit.
- Diagnose: PASS — symptoms (timehealth green, drifted seating) without naming causes.
- Navigate coupling: PASS — local chrony edit undone; partial prefer fails distant cells.
- Reason beyond training: PASS — durable preference lattice + hold reporting is not a stock chrony recipe.

### Instruction completeness test
No — instruction alone lacks rematerialize trigger, fold winner rule, offset budget table, and exact hold-row shape; solver must read live trees, docs bands, and ops behavior.

## Reviewer Appendix

### Implementation plan
Ship broken bash ops that rematerialize surface chrony/timesync unless prefer is durable/authority; wrong drop-in fold; hold ignore; emit that trusts timehealth. Oracle restores prefer mode, fixes axle_p/knit_w/pull_m/bind_v/emit_q/mark_t, seats once. Verifier recomputes EXPECTED from durable roster/bands/holds/offsets and re-enters the stock entrypoint.

### Proposed file inventory
Matches authoring Initial Draft Commitments (≥35 environment files excl. Docker).

### Oracle notes
Set prefer mode to durable; rewrite axle_p to rematerialize only on live/surface; knit_w ascending lexical last-wins; pull_m load holds; bind_v write only selected peer; mark_t read offsets.toml; emit_q build schema from durable authority + selection matrix; run seating twice for determinism.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
Six coordinated bash helpers plus prefer.toml — not a single sed.

Likely editable frontier:
- ops/axle_p.sh, knit_w.sh, pull_m.sh, bind_v.sh, emit_q.sh, rim/mark_t.sh, prefer.toml, timesync drop-ins

Requirement-to-file map:
- preference/rematerialize -> axle_p + prefer.toml
- drop-in NTP -> knit_w
- hold rows -> pull_m
- selection/live chrony -> bind_v
- JSON/offset -> emit_q + mark_t

Oracle estimated complexity: 90–140 non-boilerplate LOC

Red flags:
- none if instruction stays symptoms-only and bands stay in docs without selected tallies

Residual hardness:
Coupled rematerialize × fold × hold × band selection with false-green timehealth and wipe re-entry.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
desk, time, seating, entrypoint, report, schema_tag, sources, name, stratum, selected, hold, preference, live, durable, authority, sync_ok, offset_bound_ms, chrony, timesync, materials, roster, band, published, frozen, samples, synchronized, timehealth, dropin, offset, bound, sync, source, peer, ntp

**Renames during drafting:**
(none yet — Step 2b uses opaque axle_p/knit_w/pull_m/bind_v/emit_q/mark_t)

**Test names audited:**
test_q3_schema_shape, test_n7_preference_mode, test_k4_selected_matrix, test_m2_hold_rows, test_r6_sync_ok_coupling, test_w8_offset_budget, test_j1_schema_tag, test_p5_live_chrony, test_v9_dropin_fold, test_t2_idempotent_seat, test_h5_reentry_wipe, test_u4_frozen_samples, test_y6_timehealth_insufficient, test_c8_band_reject

**Concentration math:**
A:3/14≈0.21, B:2/14≈0.14, C:2/14≈0.14, D:3/14≈0.21, E:3/14≈0.21, F:1/14≈0.07 — all ≤ 0.5
