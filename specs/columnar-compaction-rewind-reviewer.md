### Decision
GO — Attempt 2. Added variant-ladder anchor decoy, tri-file recovery config split, and dual read-path trap beyond standard LSM rewind recipes.

### Metadata
- Task name: columnar-compaction-rewind
- Title: Columnar Compaction Rewind
- Category: data-processing
- Languages: [Rust]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [lsm, columnar, operational-recovery, manifest, wal, secondary-index]
- Milestones: 0

### Discovery budget
- Discovery: Point-resolution and aggregate rollup use different manifest tiers after partial merge; rollups read merged column stats from head tier while point path walks sidecar bound to pre-merge segment IDs.
  Planned location: `environment/store/src/rollup.rs` vs `environment/store/src/column_reader.rs` + `environment/store/index/src/sidecar.rs`
  Why instruction must not reveal it: Naming the dual read path tells the agent to grep `rollup` vs `column_reader` and skip diagnosing stale sidecar binding.

- Discovery: Safe rollback anchor is generation N-2 (tier_c), not head generation N, because tier_b is a partial merge journal entry that must not become authoritative.
  Planned location: `environment/data/manifests/tier_*.jsonl` compaction journal entries; consumed via `anchors.toml` `TIER_C`
  Why instruction must not reveal it: Stating "roll back two generations" collapses manifest archaeology to counting lines.

- Discovery: Sidecar rebuild (`run_p4`) must run only after WAL barrier `apply_k2` at `seq_cutoff` from compaction journal; otherwise tombstone windows from truncated WAL segments remain invisible to index but visible in column stripes.
  Planned location: `environment/store/ops/src/barrier.rs`, `environment/config/recovery/barrier.toml`, compaction log in `tier_b.jsonl`
  Why instruction must not reveal it: Disclosing barrier-before-rebuild ordering is the recipe; agent must infer from tombstone test failures.

- Discovery: `ctl compact` decoy subcommand advances head and poisons recovery; only `exec_m9` roll path is safe for the affected keyspace.
  Planned location: `environment/store/ctl/src/subcmd_compact.rs` vs `subcmd_roll.rs`
  Why instruction must not reveal it: Naming the correct subcommand removes CLI discovery.

### Anti-trivialization verdict

| # | Check | Verdict | Reasoning |
|---|-------|---------|-----------|
| 1 | Disclosure-collapse | PASS | Instruction states symptoms and constraints only; safe anchor, barrier seq, and phase order are not disclosed. |
| 2 | Hidden-instance | PASS | Failure is cross-tier coupling, not "find the one corrupt file among 400"; multiple manifest tiers are structurally valid but only one anchor+barrier pair restores invariants. |
| 3 | Single-artifact repair | PASS | Anchor TOML alone, barrier alone, or index alone each fail overlapping test subsets. |
| 4 | Generalization | PASS | Variant ladder with decoy anchor for secondary namespace blocks wrong-generation shortcut. |
| 5 | Prompt-honesty | PASS | Honest symptoms-only prompt does not reveal broken tier or generation number. |
| 6 | Cheating-vs-difficulty | PASS | Anti-cheat is golden vectors and digests; difficulty is operational discovery. |
| 7 | Mechanical-fix filter | PASS | Core challenge is not verifier deps or timeouts. |
| 8 | Localized-fix | PASS | No single module or config file suffices. |
| 9 | Oracle-locality | PASS | Oracle performs ordered multi-step workflow, not one-file wholesale replace. |
| 10 | Small declarative-cluster | PASS | Recovery split across three TOML files with ctl cross-validation; not a single knob transcription. |
| 11 | Grep-collapse | PASS | Instruction nouns banned from fix-path symbols; decoys rhyme structurally. |
| 12 | Pre-factored-helper | PASS | Helpers use opaque names (`exec_m9`, `run_p4`), not prompt-mirroring names. |
| 13 | Recipe-discount | PASS | Partial-merge tier semantics and dual read-path bait exceed textbook LSM rewind recipes. |
| 14 | Security-aura discount | PASS | No security nouns creating false hardness. |
| 15 | Orthogonal-checklist | PASS | Anchor, barrier, rebuild order, and ctl choice are coupled with tradeoffs. |
| 16 | Harness-discount | PASS | 25+ Rust modules provide realism, not difficulty by themselves. |
| 17 | One-pass solvability | PASS | Rollup-pass/point-fail bait prevents one-pass config guess. |
| 18 | Hard-only gate | PASS | Requires LSM visibility reasoning, multi-phase destructive workflow, dual read-path diagnosis. |
| 19 | Discovery budget test | PASS | Four concrete discoveries enumerated above. |
| 20 | Instruction specificity test | PASS | Symptoms-only: wrong rows at timestamps, correct rollups, one keyspace affected. |
| 21 | Topology distribution test | PASS | Three topologies enumerated below, each ≥3 locations. |

### Topology enumeration (3 candidate fix topologies)

**Topology 1 — Manifest-first rollback:** Roll manifest to `TIER_C`, truncate WAL at `SEQ_CUTOFF`, rebuild sidecar for `events`.
- Locations: `anchors.toml`, `subcmd_roll.rs`/`exec_m9`, `barrier.toml`/`apply_k2`, `rebuild_full.rs`/`run_p4`
- No single location suffices: wrong anchor fails point tests; missing barrier leaves tombstones wrong; skipping rebuild leaves sidecar digest mismatch.

**Topology 2 — WAL-barrier-led recovery:** Establish WAL cutoff first from compaction journal, then align manifest anchor, then index rebuild.
- Locations: `barrier.toml`, `wal/replayer.rs` journal parsing, `anchors.toml`, `run_p4`
- No single location suffices: barrier without manifest rollback leaves segment chain inconsistent; manifest without barrier leaves tombstone window stale.

**Topology 3 — Index-led reconciliation (invalid but plausible):** Rebuild sidecar from visible column stripes, then adjust manifest pointers.
- Locations: `rebuild_fast.rs` (decoy), `rebuild_full.rs`, `manifest/journal.rs`, `phase_table.toml`
- No single location suffices: fast rebuild passes partial checks; full rebuild without manifest/WAL coordination still fails point vectors; decoy path poisons state.

### Rubric axes
- **Verifiable:** PASS — Golden JSON vectors, digest checks, and report schema are deterministic.
- **Well-specified:** PASS — Two-paragraph symptom contract plus output JSON fields; two readers produce equivalent verifiers.
- **Solvable:** PASS — Expert with LSM ops background solves in hours via ctl workflow; oracle < 200 lines.
- **Difficult:** PASS — Dual read-path trap and destructive phase ordering exceed undergrad scale; Opus-strong category justified by coherence/verification failure modes.
- **Interesting:** PASS — Post-compaction visibility reconciliation is paid production SRE work.
- **Outcome-verified:** PASS — Tests grade query results and report artifact, not specific commands used.

### Hardness axes
- **Discover:** Agent must find safe anchor generation, WAL barrier seq, and correct ctl subcommand from journals and module behavior — not stated in instruction.
- **Synthesize:** Manifest tiers, WAL segments, sidecar index, and dual read paths interact; mental model spans `manifest/`, `wal/`, `index/`, `rollup.rs`, `column_reader.rs`.
- **Diagnose:** Symptom is wrong historical rows with correct aggregates — agent must determine visibility reconciliation failure, not a generic bug.
- **Navigate coupling:** Rebuild-before-rollback and forward-compact decoy break distant invariants; local green checks mislead.
- **Reason beyond training:** Partial-merge tier journal semantics and tombstone propagation across columnar stripes require domain reasoning beyond generic LSM tutorials.

### Instruction completeness test
Cannot solve from instruction.md alone. Instruction does not name stale tier, anchor generation, barrier sequence, ctl subcommands, or rebuild order. Agent must read compaction journals, compare read paths in Rust modules, and experiment with ctl queries.

## Reviewer Appendix

### Implementation plan
Ship a prebuilt Rust columnar store with ctl CLI and seeded fixtures representing a post-merge broken state: manifest head advanced, `events` sidecar stale, `metrics` healthy. Initial recovery TOML contains placeholder/wrong anchor and barrier values. Agent edits recovery config and runs ordered ctl invocations (`roll` → barrier apply → full index rebuild) to restore golden visibility vectors. Tests compare point/range results, tombstone absence, rollup stability, sidecar digests, and report JSON. Hardness comes from rollup-pass bait, decoy compact command, and opaque symbol naming.

**Docker build (Step 2b):** Multi-stage Dockerfile per `docker environment.mdc` and Dockerfile & Image Best Practices. Builder uses canonical `rust:1.85-slim@sha256:9f841bbe9…`. Runtime uses canonical `debian:bookworm-slim@sha256:4724b8cc…`. **First runtime layers (before COPY):** pinned `tmux=3.3a-3` + `asciinema=2.2.0-1`, `ENV TERM=xterm-256color`, `RUN tmux -V && asciinema --version`, then pinned pytest — same pattern as `cgroup-v2-hierarchy-cutover` / `amr-ghost-cell-rebind-restart` submission zips. Copy release `ctl` to `/app/bin/ctl`, fixtures to `/app/data/`, configs to `/app/config/`, store sources for agent reading. `WORKDIR /app` in Dockerfile only. `task.toml` has no `workdir` field (standard non-milestone task). Expected assertion values embedded in `tests/test_outputs.py` — no golden JSON under `environment/`.

### Proposed file inventory
See Initial Draft Commitments in authoring spec (38 task files; 30+ under `environment/` excluding Docker).

### Oracle notes
`solve.sh`: (1) set `tier_c` in `anchors.toml` from journal archaeology (value 17 in fixtures); (2) set `seq_cutoff` in `barrier.toml` (value 8842); (3) `ctl roll --anchor 17 --ns events`; (4) `ctl barrier --seq 8842`; (5) `ctl rebuild --ns events --mode full`; (6) write `/output/rewind-report.json` with generation 17, segment counts, sidecar digests from ctl output. Do not run `ctl compact`.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
Editing `anchors.toml` to the correct generation plus running roll and rebuild without WAL barrier might pass point vectors for some keys but fail tombstone window test; minimal patch that passes all tests requires anchor + barrier + ordered rebuild — roughly 3 config fields and 3 ctl calls, but discovering values requires multi-file journal analysis.

Likely editable frontier:
- `environment/config/recovery/*.toml`
- `solution/solve.sh` (ctl invocation sequence)

Requirement-to-file map:
- Correct point visibility → anchor + roll + rebuild
- Tombstone window → barrier seq + apply_k2
- Unaffected keyspace → scoped `--ns events` only
- Report artifact → solve.sh JSON writer

Oracle estimated complexity: ~80 lines solve.sh + correct TOML values

Red flags:
- data-processing is Opus-strong; mitigated by multi-source-of-truth and destructive-phase exploits
- LSM domain is in-distribution; mitigated by dual read-path coupling

Residual hardness:
After file tree is visible, agent still must diagnose why rollups pass while points fail, archaeology the safe anchor from tier journals (not head), avoid decoy compact, and sequence barrier before rebuild — none of which instruction.md states.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
production, columnar, storage, time-travel, queries, embedded, engine, background, merge, point, lookups, range, scans, events, keyspace, rows, timestamps, rollup, counts, keyspaces, visibility, operator, tooling, recovery, configuration, manifest, generation, segment, statistics, rewind

**Renames during drafting:**
- `subcmd_rewind` → `subcmd_roll` / `exec_m9`: instruction uses "rewind" noun banned on fix path
- `rebuild_sidecar` → `run_p4`: avoid domain noun on fix-path function
- `manifest_anchor` → `TIER_C`: avoid manifest/generation nouns in constant name

**Test names audited:**
- test_golden_vector_alpha
- test_golden_vector_beta
- test_absent_marker_at_window
- test_aggregate_totals_stable
- test_output_json_schema_valid
- test_chain_order_invariant
- test_digest_checksum_match
- test_secondary_namespace_stable

**Concentration math:**
- Total tests across `flipping_point_contract`: 8
- Per location:
  - A (`environment/config/recovery/anchors.toml`): 3/8 = 0.375
  - B (`environment/config/recovery/barrier.toml`): 2/8 = 0.25
  - C (`solution/solve.sh`): 3/8 = 0.375
- Cap: 0.5. Max ratio observed: 0.375. Status: PASS

### Per-test feasibility pre-check
- Test: test_golden_vector_alpha — Checks primary fixture visibility vs golden JSON. Valid approaches: 1 (correct anchor+workflow). Chain-dependent: yes — after full recovery. Feasibility risk: LOW
- Test: test_golden_vector_beta — Checks secondary fixture ordering. Valid approaches: 1. Chain-dependent: yes. Feasibility risk: LOW
- Test: test_absent_marker_at_window — Deleted key absent at window. Valid approaches: 1 (needs barrier). Chain-dependent: yes. Feasibility risk: LOW
- Test: test_aggregate_totals_stable — Aggregates still match (bait guard). Valid approaches: 2+ (passes even before fix). Chain-dependent: no. Feasibility risk: LOW
- Test: test_output_json_schema_valid — Output JSON schema. Valid approaches: 1. Chain-dependent: yes. Feasibility risk: LOW
- Test: test_chain_order_invariant — Generation monotonicity. Valid approaches: 1. Chain-dependent: yes. Feasibility risk: LOW
- Test: test_digest_checksum_match — Index checksum. Valid approaches: 1. Chain-dependent: yes — after rebuild. Feasibility risk: LOW
- Test: test_secondary_namespace_stable — unaffected namespace unchanged. Valid approaches: 1 (scoped recovery). Chain-dependent: yes. Feasibility risk: LOW
