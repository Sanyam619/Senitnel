### Decision
GO — Attempt 3. Renamed telegraphic CLI nouns (promote, readiness-shim, journalctl-sql), distributed fix across walio/shm/header/mkstandalone roots, and replaced audit/snapshot test-name collisions with opaque identifiers.

### Metadata
- version: 2
- Task name: hot-standby-promotion-sequence
- Title: Hot-Standby Promotion Sequence
- Category: system-administration
- Languages: ["Go", "bash"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: ["sqlite", "wal", "ops", "go", "storage", "elevation"]
- Milestones: 0

## Authoring Brief

### Public contract

A single-container SQLite warm-copy lab lives under `/data`. The primary file is `/data/primary/source.db`; replica artifacts are under `/data/standby/`. Operators can read the replica in read-only mode, but elevation to a standalone writable database at `/data/standby/live.db` keeps failing.

**Symptoms the agent sees (instruction.md level):**
- Read-only queries against the replica succeed for recent rows.
- `elevate-standby.sh` (wrapper around `mkstandalone`) exits non-zero with a generic "not ready" message.
- `/opt/lab/bin/sizecheck` reports green despite repeated elevation failures.
- Journal inspection via `walscope` shows the replica main-file change-counter and SHM checkpoint counter disagree; the write-ahead sidecar appears partially integrated.
- Re-running elevation after a failed attempt can make the replica unreadable until restored from `/data/fixtures/snapshot/`.

**Required outcomes:**
- `/data/standby/live.db` exists, opens read-write, returns golden SQL query results embedded in tests, and `PRAGMA schema_version` matches the promoted expectation.
- `/data/standby/elevation_audit.json` records an ordered list of steps the agent took (tool name + short action label per step); schema fields are defined in tests, not a hidden hints file.
- Seeded snapshot under `/data/fixtures/snapshot/` remains intact (checksum guard in tests).
- Negative test: repeating elevation steps in a destructive order after success must fail or leave `live.db` invalid.

**Constraints:**
- `[environment] allow_internet = false`; verifier deps in Dockerfile.
- No multi-container layout.
- Agent performs ops reconciliation using bundled CLIs — not Go source patching.
- Avoid vocabulary from existing tasks: no "lease" or "replay" in code symbols, paths, or comments on the fix path.

### Failure topology

Three symptom clusters interact. First, a false-green readiness path: `sizecheck` compares WAL byte lengths between primary and replica, so operators believe the replica is caught up even while SHM checkpoint counters diverge. Second, partial integration in the WAL sidecar: some frames were applied into the main file but later frames have salt/checksum mismatches, so blind truncation at EOF or a naive checkpoint leaves torn pages. Third, elevation preflight in `mkstandalone` requires SHM header fields (page size, checkpoint sequence, salt) to match the post-truncate WAL state; running materialization before realigning SHM or before trimming at the correct frame boundary produces generic refusal or corruption.

The task is hard because no single tool documents the full order. `walscope` exposes byte-level facts, `sidealign` mutates SHM, WAL truncation is a separate primitive, and `mkstandalone` only succeeds when all preconditions align. Wrong ordering does not always fail immediately — it can pass `sizecheck` yet break schema_version or trigger the negative reorder test.

### Environment shape

- `environment/Dockerfile` + `.dockerignore` — Go 1.22+ build, sqlite3 CLI, seeded fixtures copied into `/data`.
- `environment/cmd/` — four opaque CLIs: `walscope` (journal decoder), `sidealign` (SHM rewriter), `mkstandalone` (standalone materializer), `sizecheck` (misleading readiness).
- `environment/internal/walio/` — WAL frame parsing, salt checks, truncate helper used by CLIs.
- `environment/internal/shmio/` — SHM header read/write primitives.
- `environment/internal/dbkit/` — safe open helpers and pragma readers for CLIs.
- `environment/internal/audit/` — JSON trace writer for elevation_audit.json.
- `environment/pkg/boundary/` — `apply_cutoff` fix-path symbol + `legacy_cutoff` decoy.
- `environment/pkg/header/` — `merge_hdr_q` fix-path symbol + `probe_hdr` decoy.
- `environment/scripts/` — `standby-readonly.sh`, `elevate-standby.sh`, thin wrappers.
- `environment/data/fixtures/` — primary seed, broken standby trio (db, wal, shm), pristine snapshot tree.
- `environment/config/lab.toml` — paths only (no answer knobs).

### Required artifacts

- `tasks/hot-standby-promotion-sequence/task.toml` with `allow_internet = false`.
- `tasks/hot-standby-promotion-sequence/instruction.md` — symptoms-only prose from naming pass; includes output paths and audit JSON field names tests will check.
- `tasks/hot-standby-promotion-sequence/tests/test.sh`, `tests/test_outputs.py` — ≥6 tests per plan below.
- `tasks/hot-standby-promotion-sequence/solution/solve.sh` — oracle CLI chain (≥30 LOC substantive).
- `tasks/hot-standby-promotion-sequence/environment/**` — 20+ non-Docker files per Initial Draft Commitments.
- No `output_contract.toml` in submission zip.

### Test plan

- `test_k9_row_bundle` — Opens `/data/standby/live.db` read-only; asserts golden SELECT results for seeded inventory rows (computed expectations in test code).
- `test_m4_schema_marker` — Asserts `PRAGMA schema_version` on `live.db` matches promoted value.
- `test_p2_trace_fields` — Parses `/data/standby/elevation_audit.json`; asserts required keys, ordered steps array, and tool labels present.
- `test_q7_writable_mode` — Opens `live.db` read-write, runs INSERT in a transaction, verifies commit (proves standalone not WAL-attached).
- `test_r1_order_guard` — Negative guard: if solution re-runs materialize before align after success, expects failure or invalid schema_version.
- `test_s3_seed_preserved` — Compares checksum of `/data/fixtures/snapshot/**` against embedded hash list.

Multiple valid approaches: agent may call CLIs directly or via bash wrappers if equivalent. Chain-dependent: row bundle + schema + writable tests depend on correct prior WAL/SHM steps.

### Drafting guardrails

Do not embed instruction nouns (standby, elevation, readiness, journal, checkpoint, frames, snapshot, promotion, audit, etc.) in fix-path function names, parameters, directories, or test function names. Instruction.md may use standard SQLite ops language freely. Do not hide the operational contract in environment README files. `sizecheck` must genuinely implement length-only logic visible in source. Seeded fixture must encode partial-frame state without a HINT comment naming the cutoff index.

### Triviality Ledger

- Naive `mkstandalone` first passes `sizecheck` green but fails `test_m4_schema_marker` because SHM checkpoint counters still diverge from the trimmed WAL salt.
- EOF WAL truncate passes length parity but fails `test_k9_row_bundle` due to torn page at the partial-frame boundary; only `apply_cutoff` at walscope-reported index succeeds.
- Running `sidealign` before truncate updates SHM to stale checkpoint numbers and fails `test_q7_writable_mode` even when `sizecheck` stays green.
- `legacy_cutoff` decoy implements length-only trim; using it fails schema tests, blocking grep-to-single-helper collapse.
- Re-ordered elevation after success trips `test_r1_order_guard`, blocking one-shot recipe scripts.

### Per-gate Pitfall Inventory

- RC1: Oracle must execute real CLI sequence with computed cutoff — not delete broken bytes or restore golden files wholesale.
- RC3: Tests assert computed row counts and schema_version integers, not mere file existence.
- RC5: Golden SQL expected values live in test code, not under `environment/data/golden/`.
- RC6: Instruction stays symptoms-only — do not name `apply_cutoff`, `merge_hdr_q`, or step order.
- RC7: `solve.sh` chains walscope parse + truncate + sidealign + mkstandalone with error handling ≥30 LOC.
- CR1/CR2: Use construction manifest symbols verbatim; flipping-point revert must split tests 2+2+2.
- CR7/GX9: Audit JSON field names appear in instruction.md; cutoff index K appears only in walscope runtime output.
- GX10: Instruction must not state both polarities of a binary field for one case (e.g., do not say "checkpoint must match" and "checkpoint may differ").
- Static checks: `allow_internet = false`, `.dockerignore` present, absolute paths in instruction.

### Initial Draft Commitments

- `tasks/hot-standby-promotion-sequence/task.toml`
- `tasks/hot-standby-promotion-sequence/instruction.md`
- `tasks/hot-standby-promotion-sequence/tests/test.sh`
- `tasks/hot-standby-promotion-sequence/tests/test_outputs.py`
- `tasks/hot-standby-promotion-sequence/solution/solve.sh`
- `tasks/hot-standby-promotion-sequence/environment/Dockerfile`
- `tasks/hot-standby-promotion-sequence/environment/.dockerignore`
- `tasks/hot-standby-promotion-sequence/environment/go.mod`
- `tasks/hot-standby-promotion-sequence/environment/go.sum`
- `tasks/hot-standby-promotion-sequence/environment/config/lab.toml`
- `tasks/hot-standby-promotion-sequence/environment/cmd/walscope/main.go`
- `tasks/hot-standby-promotion-sequence/environment/cmd/sidealign/main.go`
- `tasks/hot-standby-promotion-sequence/environment/cmd/mkstandalone/main.go`
- `tasks/hot-standby-promotion-sequence/environment/cmd/sizecheck/main.go`
- `tasks/hot-standby-promotion-sequence/environment/internal/walio/reader.go`
- `tasks/hot-standby-promotion-sequence/environment/internal/walio/frame.go`
- `tasks/hot-standby-promotion-sequence/environment/internal/walio/truncate.go`
- `tasks/hot-standby-promotion-sequence/environment/internal/shmio/header.go`
- `tasks/hot-standby-promotion-sequence/environment/internal/shmio/align.go`
- `tasks/hot-standby-promotion-sequence/environment/internal/dbkit/open.go`
- `tasks/hot-standby-promotion-sequence/environment/internal/audit/record.go`
- `tasks/hot-standby-promotion-sequence/environment/pkg/boundary/cutoff.go`
- `tasks/hot-standby-promotion-sequence/environment/pkg/boundary/legacy_cutoff.go`
- `tasks/hot-standby-promotion-sequence/environment/pkg/header/merge_hdr.go`
- `tasks/hot-standby-promotion-sequence/environment/pkg/header/probe_hdr.go`
- `tasks/hot-standby-promotion-sequence/environment/scripts/standby-readonly.sh`
- `tasks/hot-standby-promotion-sequence/environment/scripts/elevate-standby.sh`
- `tasks/hot-standby-promotion-sequence/environment/scripts/mkstandalone-wrapper.sh`
- `tasks/hot-standby-promotion-sequence/environment/data/fixtures/snapshot/source.db`
- `tasks/hot-standby-promotion-sequence/environment/data/fixtures/standby/replica.db`
- `tasks/hot-standby-promotion-sequence/environment/data/fixtures/standby/replica.db-wal`
- `tasks/hot-standby-promotion-sequence/environment/data/fixtures/standby/replica.db-shm`
- `tasks/hot-standby-promotion-sequence/environment/data/fixtures/primary/source.db`
- `tasks/hot-standby-promotion-sequence/environment/data/fixtures/primary/source.db-wal`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: environment/pkg/boundary/cutoff.go
  symbol: apply_cutoff
  kind: function
  signature: func apply_cutoff(wal []byte, idx int) ([]byte, error)
  purpose: Returns WAL bytes truncated after frame index idx.

- path: environment/pkg/header/merge_hdr.go
  symbol: merge_hdr_q
  kind: function
  signature: func merge_hdr_q(shm []byte, salt uint32) ([]byte, error)
  purpose: Rewrites SHM header checkpoint and page-size fields to match salt.

- path: environment/cmd/mkstandalone/main.go
  symbol: finalize_copy
  kind: function
  signature: func finalize_copy(src string, dst string) error
  purpose: Materializes standalone writable DB after preflight gates pass.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: environment/pkg/boundary/cutoff.go
    controls_tests: [test_k9_row_bundle, test_m4_schema_marker]
  - id: B
    path: environment/pkg/header/merge_hdr.go
    controls_tests: [test_p2_trace_fields, test_q7_writable_mode]
  - id: C
    path: environment/cmd/mkstandalone/main.go
    controls_tests: [test_r1_order_guard, test_s3_seed_preserved]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: environment/pkg/boundary/legacy_cutoff.go
  kind: helper
  rhymes_with: apply_cutoff
  non_fix_purpose: Deprecated length-only WAL trim used by diagnostic scripts, not the elevation path.

- path: environment/pkg/header/probe_hdr.go
  kind: helper
  rhymes_with: merge_hdr_q
  non_fix_purpose: Read-only SHM header dumper for walscope; does not mutate alignment.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [standby, elevation, readiness, journal, inspection, checkpoint, frames, snapshot, promotion, audit, warm-copy, main-file, change-counter, sidecar, shared-memory, write-ahead, probe, database, primary, copy]
```
