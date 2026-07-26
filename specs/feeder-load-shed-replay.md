### Decision
GO — Attempt 1. Dual-language (Rust ledger + Go topology inspector) shed-replay stale-availability design with generation-pin barrier, adjacency cascade, and MW-threshold probe decoy; three-location flipping contract at 2/6 each.

### Metadata
- version: 2
- Task name: feeder-load-shed-replay
- Title: Feeder Load-Shed Replay
- Category: system-administration
- Languages: ["Rust", "Go"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: ["ops", "rust", "go", "topology", "ledger", "infrastructure"]
- Milestones: 0

## Authoring Brief

### Public contract

A single-container distribution control lab under `/app` pairs a Rust event ledger (`/app/bin/ledctl`) with a Go topology inspector (`/app/bin/topoprobe`). Seeded fixtures live under `/app/data/` (journal segments, topology graph, load-state store, availability bitmap, generation pin).

**Symptoms the agent sees (instruction.md level):**
- Operators replay feeder shed events from the ledger into the live load-state store.
- After replay, load totals for shed feeders match the journal.
- Topology dumps still list the expected feeder-to-circuit edges.
- Circuit availability probes nevertheless still report those circuits as available for new load.
- Re-running replay leaves availability unchanged.

**Required outcomes:**
- Deterministic probes report shed circuits unavailable and MW totals aligned with journal expectations (values embedded in tests).
- `/output/reconcile-report.json` matches the schema fields documented by `topoprobe --schema` (field names also stated in instruction.md).
- Second replay is idempotent: availability and report digests unchanged after a successful first pass.
- Unaffected feeders/circuits remain available; topology edge set unchanged from seed.

**Constraints:**
- `[environment] allow_internet = false`; verifier deps in Dockerfile.
- No multi-container layout; no UI building.
- Agent may patch Rust/Go sources under `/app` and rebuild via provided Makefiles/`cargo`/`go build` wrappers; may also invoke `ledctl` / `topoprobe`.
- Standard non-milestone `task.toml` (no `workdir` key).

### Failure topology

Three symptom clusters interact. First, load accounting looks healthy: Rust apply writes MW deltas and advances the ledger cursor, so quantity probes pass. Second, topology dumps remain correct because the adjacency graph was never the broken artifact. Third, availability stays stale because the bitmap is keyed by a topology generation pin that replay does not bump, feeder-level marks do not cascade to child circuits, and the inspector exposes an MW-threshold fast path that can look green without reading the bitmap. Wrong local fixes (cursor-only, feeder-bit-only, or fast-path seal) each satisfy a subset of observations and fail the coupled suite.

### Environment shape

- `environment/Dockerfile` + `.dockerignore` — multi-stage Rust + Go builders, Debian runtime with tmux/asciinema/pytest.
- `environment/ledger/` — Rust workspace: journal IO, apply/fold path, cursor, pin state, `ledctl` CLI.
- `environment/topo/` — Go module: graph load, walk/cascade, seal/report, `topoprobe` CLI, decoy fast helpers.
- `environment/data/` — fixtures: journal segments, topology JSON, load-state, availability bitmap, gen pin.
- `environment/scripts/` — thin rebuild/replay wrappers (no hidden solver steps).
- `environment/config/` — path map only (no answer knobs).

### Required artifacts

- `tasks/feeder-load-shed-replay/task.toml` with `allow_internet = false`.
- `tasks/feeder-load-shed-replay/instruction.md` — symptoms-only prose from naming pass; includes output path and report field names.
- `tasks/feeder-load-shed-replay/tests/test.sh`, `tests/test_outputs.py` — ≥6 tests per plan.
- `tasks/feeder-load-shed-replay/solution/solve.sh` — oracle patches + rebuild + replay (≥30 LOC substantive).
- `tasks/feeder-load-shed-replay/environment/**` — 20+ non-Docker files per Initial Draft Commitments.
- Local-only `output_contract.toml` allowed during authoring; banned from submission zip.

### Test plan

- `test_k2_slot_bundle` — After replay, availability slots for shed circuits are unavailable (computed expectations in test code).
- `test_m8_qty_align` — Load MW totals for shed feeders match journal-derived expectations.
- `test_p3_link_stable` — Topology edge set checksum matches seed (regression: graph not rewritten).
- `test_q1_fan_pair` — Multi-depth cascade: child circuits under two feeders both unavailable; sibling feeder unaffected.
- `test_r6_out_shape` — `/output/reconcile-report.json` has required keys and digest fields from `topoprobe --schema`.
- `test_t4_twice_ok` — Second `ledctl replay` leaves availability bitmap digest and report digest unchanged.

Multiple valid approaches: agent may fix producers then rebuild, or adjust seal+producers equivalently if outcomes match. Chain-dependent: slot/fan/report tests depend on a successful replay after code fixes.

### Drafting guardrails

Do not embed instruction nouns (feeder, shed, availability, replay, topology, ledger, probe, circuit, journal, edges, load, report, …) in fix-path function names, parameters, directories, or test function names. Instruction.md may use standard distribution-ops language freely. Do not hide the operational contract in environment README files. Decoy helpers (`apply_legacy`, `walk_fast`, `seal_qty`) must do real non-fix work. Fixtures must encode multi-feeder cascade depth without HINT comments naming the generation pin or walk order.

### Triviality Ledger

- Patching only Rust cursor/MW apply passes `test_m8_qty_align` but fails `test_k2_slot_bundle` because the generation pin and bitmap stay stale.
- Marking only feeder node ids via `walk_fast` decoy passes shallow single-node checks but fails `test_q1_fan_pair` (children remain available).
- Using `seal_qty` MW-threshold path can fabricate unavailable-looking reports for low MW yet fails `test_r6_out_shape` digest coupling and `test_t4_twice_ok` when bitmap never updates.
- Advancing cursor before publishing invalidation makes second replay a no-op; `test_t4_twice_ok` fails if the first pass never rebuilt bits.
- Rewriting topology edges to “fix” availability fails `test_p3_link_stable`.

### Per-gate Pitfall Inventory

- RC1: Oracle must add real apply/cascade/seal logic — not delete BUG markers or restore golden bitmaps wholesale.
- RC3: Tests assert computed availability and MW integers, not mere file existence.
- RC5: Golden expectations live in test code, not under `environment/data/golden/`.
- RC6: Instruction stays symptoms-only — do not name `fold_q7`, `walk_r4`, `seal_n2`, or barrier order.
- RC7: `solve.sh` patches three locations + rebuild + replay with error handling ≥30 LOC.
- CR1/CR2: Use construction manifest symbols verbatim; flipping-point revert splits tests 2+2+2.
- CR7/GX9: Report field names appear in instruction.md; numeric MW/availability expectations are not recited per scenario in prose.
- GX10: Do not state both polarities for the same circuit in one sentence (available vs unavailable).
- Static checks: `allow_internet = false`, `.dockerignore` present, absolute paths in instruction, verifier deps in Dockerfile.
- Docker: digest-pinned sanctioned bases; tmux+asciinema in runtime before COPY; no `workdir` in non-milestone `task.toml`.

### Initial Draft Commitments

- `tasks/feeder-load-shed-replay/task.toml`
- `tasks/feeder-load-shed-replay/output_contract.toml`
- `tasks/feeder-load-shed-replay/instruction.md`
- `tasks/feeder-load-shed-replay/tests/test.sh`
- `tasks/feeder-load-shed-replay/tests/test_outputs.py`
- `tasks/feeder-load-shed-replay/solution/solve.sh`
- `tasks/feeder-load-shed-replay/environment/Dockerfile`
- `tasks/feeder-load-shed-replay/environment/.dockerignore`
- `tasks/feeder-load-shed-replay/environment/config/paths.toml`
- `tasks/feeder-load-shed-replay/environment/scripts/rebuild.sh`
- `tasks/feeder-load-shed-replay/environment/scripts/run_replay.sh`
- `tasks/feeder-load-shed-replay/environment/ledger/Cargo.toml`
- `tasks/feeder-load-shed-replay/environment/ledger/Cargo.lock`
- `tasks/feeder-load-shed-replay/environment/ledger/src/lib.rs`
- `tasks/feeder-load-shed-replay/environment/ledger/src/journal.rs`
- `tasks/feeder-load-shed-replay/environment/ledger/src/cursor.rs`
- `tasks/feeder-load-shed-replay/environment/ledger/src/apply.rs`
- `tasks/feeder-load-shed-replay/environment/ledger/src/apply_legacy.rs`
- `tasks/feeder-load-shed-replay/environment/ledger/src/pinstate.rs`
- `tasks/feeder-load-shed-replay/environment/ledger/src/bin/ledctl.rs`
- `tasks/feeder-load-shed-replay/environment/topo/go.mod`
- `tasks/feeder-load-shed-replay/environment/topo/go.sum`
- `tasks/feeder-load-shed-replay/environment/topo/cmd/topoprobe/main.go`
- `tasks/feeder-load-shed-replay/environment/topo/internal/graph/load.go`
- `tasks/feeder-load-shed-replay/environment/topo/internal/graph/types.go`
- `tasks/feeder-load-shed-replay/environment/topo/internal/walk/walk_r4.go`
- `tasks/feeder-load-shed-replay/environment/topo/internal/walk/walk_fast.go`
- `tasks/feeder-load-shed-replay/environment/topo/internal/seal/seal_n2.go`
- `tasks/feeder-load-shed-replay/environment/topo/internal/seal/seal_qty.go`
- `tasks/feeder-load-shed-replay/environment/topo/internal/bitmap/codec.go`
- `tasks/feeder-load-shed-replay/environment/data/journal/seg_001.bin`
- `tasks/feeder-load-shed-replay/environment/data/journal/seg_002.bin`
- `tasks/feeder-load-shed-replay/environment/data/topo/grid.json`
- `tasks/feeder-load-shed-replay/environment/data/state/load.json`
- `tasks/feeder-load-shed-replay/environment/data/state/avail.bin`
- `tasks/feeder-load-shed-replay/environment/data/state/gen_pin.json`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: environment/ledger/src/apply.rs
  symbol: fold_q7
  kind: function
  signature: pub fn fold_q7(a: &Batch, b: &mut PinState) -> Result<(), Error>
  purpose: Applies journal batch deltas into load-state and updates pin/cursor barrier fields.

- path: environment/topo/internal/walk/walk_r4.go
  symbol: walk_r4
  kind: function
  signature: func walk_r4(g *Graph, s []byte, k uint32) ([]byte, error)
  purpose: Writes availability bitmap bytes for nodes reachable from marked roots under key k.

- path: environment/topo/internal/seal/seal_n2.go
  symbol: seal_n2
  kind: function
  signature: func seal_n2(v View, b []byte, k uint32) (Report, error)
  purpose: Builds probe report from bitmap view under key k rather than quantity thresholds.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: environment/ledger/src/apply.rs
    controls_tests: [test_k2_slot_bundle, test_m8_qty_align]
  - id: B
    path: environment/topo/internal/walk/walk_r4.go
    controls_tests: [test_q1_fan_pair, test_p3_link_stable]
  - id: C
    path: environment/topo/internal/seal/seal_n2.go
    controls_tests: [test_r6_out_shape, test_t4_twice_ok]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: environment/ledger/src/apply_legacy.rs
  kind: helper
  rhymes_with: fold_q7
  non_fix_purpose: Legacy quantity-only batch fold used by diagnostics; advances cursor without pin updates.

- path: environment/topo/internal/walk/walk_fast.go
  kind: helper
  rhymes_with: walk_r4
  non_fix_purpose: Marks only explicitly listed node ids without adjacency expansion; used by dry-run tooling.

- path: environment/topo/internal/seal/seal_qty.go
  kind: helper
  rhymes_with: seal_n2
  non_fix_purpose: MW-threshold report builder for capacity planning dashboards; ignores bitmap keys.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [distribution, control, lab, Rust, event, ledger, Go, topology, inspector, operators, replay, feeder, shed, events, live, load-state, store, load, totals, journal, dumps, edges, circuit, availability, probes, circuits, available, consistent, deterministic, reconcile-report, fields, schema, flag, bin, output, report]
```
