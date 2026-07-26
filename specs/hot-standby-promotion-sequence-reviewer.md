### Decision
GO — Attempt 3. Renamed telegraphic CLI nouns, distributed fix across walio/shm/header/mkstandalone roots, and replaced audit/snapshot test-name collisions with opaque identifiers.

### Metadata
- Task name: hot-standby-promotion-sequence
- Title: Hot-Standby Promotion Sequence
- Category: system-administration
- Languages: ["Go", "bash"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: ["sqlite", "wal", "ops", "go", "storage", "elevation"]
- Milestones: 0

### Discovery budget

- Discovery: `sizecheck` reports green when standby WAL byte length matches primary WAL, ignoring SHM checkpoint counter parity and applied-frame state.
  Planned location: `environment/cmd/sizecheck/main.go` and `environment/internal/audit/record.go`
  Why instruction must not reveal it: Naming the length-only heuristic tells the agent to ignore the probe entirely, removing the false-confidence trap.

- Discovery: `walscope` exposes a salt mismatch after frame index K indicating the safe truncate boundary; truncating at EOF leaves a torn page that fails schema_version.
  Planned location: `environment/internal/walio/frame.go`, `environment/pkg/boundary/cutoff.go`, and seeded fixture under `environment/data/fixtures/standby/`
  Why instruction must not reveal it: Stating K or "truncate at mismatch" collapses journal inspection to a single number lookup.

- Discovery: `mkstandalone` refuses until `sidealign` rewrites the SHM header page-size and checkpoint sequence to match the truncated WAL salt.
  Planned location: `environment/cmd/mkstandalone/main.go`, `environment/pkg/header/merge_hdr.go`, `environment/internal/shmio/header.go`
  Why instruction must not reveal it: Revealing align-before-materialize ordering turns the task into a three-step recipe without byte reasoning.

### Anti-trivialization verdict

| # | Check | Verdict | Reasoning |
|---|-------|---------|-----------|
| 1 | Disclosure-collapse | PASS | Symptoms-only brief omits cutoff index and tool order. |
| 2 | Hidden-instance | PASS | Fixed topology, not hunt-the-broken-manifest. |
| 3 | Single-artifact repair | PASS | WAL trim + SHM align + materialize must all succeed. |
| 4 | Generalization | PASS | Tests use computed SQL expectations, not one magic offset in prompt. |
| 5 | Prompt-honesty | PASS | Honest prompt does not name faulty module. |
| 6 | Cheating-vs-difficulty | PASS | Read-only verification is not the difficulty source. |
| 7 | Mechanical-fix filter | PASS | Not a deps/timeout task. |
| 8 | Localized-fix | PASS | Three module roots on fix path. |
| 9 | Oracle-locality | PASS | Multi-step CLI oracle, not one-file rewrite. |
| 10 | Small declarative-cluster | PASS | Not a single config knob. |
| 11 | Grep-collapse | PASS | Instruction nouns banned from code symbols. |
| 12 | Pre-factored-helper | PASS | Opaque names (apply_cutoff, merge_hdr_q). |
| 13 | Recipe-discount | PASS | Misleading sizecheck + partial frames defeat textbook checkpoint order. |
| 14 | Security-aura discount | PASS | Ops/storage framing only. |
| 15 | Orthogonal-checklist | PASS | Order-dependent coupled steps. |
| 16 | Harness-discount | PASS | Fixtures add realism, not difficulty. |
| 17 | One-pass solvability | PASS | 20+ files + false-green probe block one-pass solve. |
| 18 | Hard-only gate | PASS | Residual reasoning is hard under Edition 2 profile. |
| 19 | Discovery budget test | PASS | Three discoveries listed above. |
| 20 | Instruction specificity test | PASS | symptoms-only level. |
| 21 | Topology distribution test | PASS | Three topologies below, each ≥3 locations. |

### Topology enumeration (3 candidate fix topologies)

**Topology A — Truncate-at-boundary first:** `environment/pkg/boundary/cutoff.go`, `environment/internal/walio/truncate.go`, `environment/cmd/mkstandalone/main.go`. Truncation without walscope-derived index leaves torn frames; mkstandalone cannot repair unaligned SHM alone.

**Topology B — Header-align before materialize:** `environment/pkg/header/merge_hdr.go`, `environment/internal/shmio/align.go`, `environment/cmd/sidealign/main.go`. Aligning before WAL trim propagates stale counters; materializing before align fails writable tests.

**Topology C — Ops-first via wrappers:** `environment/scripts/mkstandalone-wrapper.sh`, `environment/cmd/walscope/main.go`, `environment/internal/dbkit/open.go`. Skipping walscope leaves cutoff unknown; premature open triggers negative reorder failure.

### Rubric axes

- **Verifiable:** PASS — SQL + PRAGMA + audit JSON + negative reorder + snapshot checksum.
- **Well-specified:** PASS — Output paths and audit fields documented in instruction; elevation vocabulary is standard.
- **Solvable:** PASS — Expert DBA can finish in hours with bundled tools.
- **Difficult:** PASS — WAL/SHM byte work plus false-green probe exceeds undergrad scope.
- **Interesting:** PASS — Real warm-standby cutover pattern.
- **Outcome-verified:** PASS — Grades DB contents, not command transcript.

### Hardness axes

- **Discover:** PASS — Agent must read sizecheck source and walscope output for facts not in instruction.md.
- **Synthesize:** PASS — CLIs, fixtures, and SHM/WAL bytes form one coupled system.
- **Diagnose:** PASS — Instruction gives refusal and counter skew symptoms only.
- **Navigate coupling:** PASS — Wrong order corrupts or refuses elevation; steps constrain each other.
- **Reason beyond training:** PASS — Partial-frame fixture and lying probe require ops-specific sequencing beyond generic SQLite tutorials.

### Instruction completeness test

Can the agent solve this by reading ONLY instruction.md without deeply engaging with the codebase? **No.** The safe frame cutoff index, sizecheck's length-only comparison, and mkstandalone preflight ordering are only visible via walscope runtime output and Go CLI sources.

## Reviewer Appendix

### Implementation plan

Build a Go CLI lab installed under `/opt/lab/bin` with opaque tool names. Seed a broken replica trio under `/data/standby/` where WAL frames are partially integrated and SHM checkpoint counters disagree with the main file. `sizecheck` intentionally compares only WAL file sizes. The agent inspects journals with `walscope`, determines the truncate boundary, trims WAL via `apply_cutoff`, runs `sidealign` to `merge_hdr_q`, then `mkstandalone` `finalize_copy` to emit `/data/standby/live.db` and writes `elevation_audit.json`. Difficulty survives because the green probe misleads, decoy `legacy_cutoff` offers a wrong trim, and tests punish destructive reordering.

### Proposed file inventory

```
tasks/hot-standby-promotion-sequence/
  task.toml
  instruction.md
  tests/test.sh, test_outputs.py
  solution/solve.sh
  environment/
    Dockerfile, .dockerignore, go.mod, go.sum, config/lab.toml
    cmd/walscope/main.go          # journal decoder CLI
    cmd/sidealign/main.go         # SHM align CLI
    cmd/mkstandalone/main.go      # finalize_copy materializer
    cmd/sizecheck/main.go         # misleading length-only probe
    internal/walio/{reader,frame,truncate}.go
    internal/shmio/{header,align}.go
    internal/dbkit/open.go
    internal/audit/record.go
    pkg/boundary/{cutoff,legacy_cutoff}.go
    pkg/header/{merge_hdr,probe_hdr}.go
    scripts/{standby-readonly,elevate-standby,mkstandalone-wrapper}.sh
    data/fixtures/{primary,standby,snapshot}/...
```

(34 environment-relative paths; 20+ substantive files excluding Docker-only.)

### Oracle notes

`solve.sh` runs: `walscope --json` on replica WAL to parse last valid frame index K; pipes WAL through `apply_cutoff` at K (via helper or inline Go one-shot); writes trimmed WAL; `sidealign` with salt from walscope; `mkstandalone` to `/data/standby/live.db`; appends audit steps to `elevation_audit.json`. Must not copy snapshot over standby. Negative test is satisfied by not re-running destructive sequence post-success.

### Collapse audit

Stage: implementation-plan

**Smallest plausible successful patch:** Run walscope to learn K, truncate WAL at K, sidealign SHM to matching salt, mkstandalone to live.db — four coupled ops across three Go packages plus audit JSON write.

**Likely editable frontier:**
- Agent does not edit Go; frontier is CLI invocation order and interpreting walscope JSON.
- Oracle touches `apply_cutoff`, `merge_hdr_q`, `finalize_copy`.

**Requirement-to-file map:**
- Golden queries → promoted `live.db` (outcome of full chain)
- schema_version → depends on correct truncate + align
- Audit JSON → `internal/audit/record.go` writer invoked by agent or mkstandalone
- False-green probe → `cmd/sizecheck/main.go` (read-only discovery)
- Frame boundary → `internal/walio/frame.go` + fixture bytes

**Oracle estimated complexity:** ~45–70 lines of bash + CLI flags (walscope parse, temp WAL write, sidealign, mkstandalone, audit append).

**Red flags:**
- SQLite WAL ops are documented — mitigated by misleading sizecheck and partial-frame seed.

**Residual hardness:**
Agent must distrust green probe, extract K from walscope, and order truncate → align → materialize without instruction naming those steps.

**Collapse verdict:** PASS

### Naming-pass record

**Instruction nouns extracted:**
standby, elevation, readiness, journal, inspection, checkpoint, frames, snapshot, promotion, audit, warm-copy, main-file, change-counter, sidecar, shared-memory, write-ahead, probe, database, primary, copy

**Renames during drafting:**
- `promote` → `mkstandalone`: instruction promotion/elevation family
- `readiness-shim` → `sizecheck`: readiness/probe overlap
- `journalctl-sql` → `walscope`: journal inspection overlap
- `merge_hdr` → `merge_hdr_q`: opacity suffix
- flipping path `merge_hdr_q.go` → `merge_hdr.go`: keep filename neutral

**Test names audited:**
- test_k9_row_bundle
- test_m4_schema_marker
- test_p2_trace_fields
- test_q7_writable_mode
- test_r1_order_guard
- test_s3_seed_preserved

**Concentration math:**
- Total tests: 6
- A (`environment/pkg/boundary/cutoff.go`): 2/6 = 0.333
- B (`environment/pkg/header/merge_hdr.go`): 2/6 = 0.333
- C (`environment/cmd/mkstandalone/main.go`): 2/6 = 0.333
- Cap: 0.5. Max ratio: 0.333. Status: PASS

### Per-test feasibility pre-check

- **test_k9_row_bundle** — Golden SELECT counts on live.db. Valid approaches: 1 (must produce correct DB). Chain-dependent: yes, on truncate+align+materialize. Risk: LOW.
- **test_m4_schema_marker** — PRAGMA schema_version integer. Valid approaches: 1. Chain-dependent: yes. Risk: LOW.
- **test_p2_trace_fields** — Audit JSON keys/order. Valid approaches: 2+ (agent may write JSON manually or via tool). Chain-dependent: no. Risk: LOW.
- **test_q7_writable_mode** — INSERT commit proves standalone. Valid approaches: 1. Chain-dependent: yes. Risk: LOW.
- **test_r1_order_guard** — Negative reorder check. Valid approaches: 1. Chain-dependent: yes (post-success). Risk: MEDIUM (oracle must not trip guard).
- **test_s3_seed_preserved** — Snapshot checksum. Valid approaches: 2+ (any path that avoids mutating snapshot). Chain-dependent: no. Risk: LOW.
