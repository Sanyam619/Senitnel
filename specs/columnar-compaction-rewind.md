### Decision
GO — Attempt 2. Added variant-ladder anchor decoy, tri-file recovery config split, and dual read-path trap beyond standard LSM rewind recipes.

### Metadata
- version: 2
- Task name: columnar-compaction-rewind
- Title: Columnar Compaction Rewind
- Category: data-processing
- Languages: [Rust]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [lsm, columnar, operational-recovery, manifest, wal, secondary-index]
- Milestones: 0

## Authoring Brief

### Public contract
An embedded columnar LSM-style store (`/app/store`) serves time-travel queries via a shipped operator CLI (`/app/bin/ctl`). Fixture data under `/app/data/` includes seeded SST segments, tiered manifest chains, WAL segments, and secondary-index sidecars for two keyspaces (`events`, `metrics`).

**Symptoms (instruction.md):** After a background merge job, point lookups and range scans for the `events` keyspace return rows that should not be visible at the queried timestamps. Rollup counts for `events` still match expectations. `metrics` is unaffected. The agent must restore correct query results without modifying Rust engine source.

**Constraints:**
- Rust-only environment codebase (25+ non-Docker files under `environment/`).
- Agent may edit recovery configuration under `/app/config/recovery/` and invoke `/app/bin/ctl` subcommands only.
- No internet at runtime (`allow_internet = false`).
- Produce `/output/rewind-report.json` with: `restored_generation` (int), `events` and `metrics` objects each containing `visible_segments` (int) and `sidecar_digest` (hex string).

**Docker & task.toml contract (non-milestone — mandatory at Step 2b):**
- Standard task (`number_of_milestones = 0`): do **not** set `workdir` under `[environment]` in `task.toml`. `workdir = "/app"` is milestone-only per `task-creation.mdc`.
- `task.toml` uses top-level `[agent]` and `[verifier]` blocks plus `[environment]` with `allow_internet = false`, realistic `cpus` / `memory_mb` / `storage_mb` / `build_timeout_sec` (see Dockerfile & Image Best Practices §14).
- **Builder stage** `FROM` (digest-pinned): `public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36` — compile `ctl` with `cargo build --release --locked`.
- **Final runtime stage** `FROM` (digest-pinned): `public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d` — copy release binary + fixtures only; no Rust toolchain in runtime.
- Single consolidated `apt-get` layer in runtime: `tmux`, `asciinema`, `ca-certificates`, `python3`, `python3-pip` with `--no-install-recommends` and `rm -rf /var/lib/apt/lists/*` in the same layer (agent runtime requires tmux + asciinema).
- **Install tmux + asciinema in the runtime stage before any `COPY` layers** — platform agent runs crash when these are missing or installed too late. Pin Debian bookworm versions: `asciinema=2.2.0-1`, `tmux=3.3a-3`.
- Set `ENV TERM=xterm-256color` after the apt layer (prevents tmux session crashes in headless agent runs).
- Build-time smoke check: `RUN tmux -V && asciinema --version` immediately after apt install so a broken image fails at build, not at agent runtime.
- Verifier deps (`pytest`, `pytest-json-ctrf`) pinned and installed in Dockerfile — **not** in `tests/test.sh`.
- `environment/.dockerignore` required; narrow `COPY` (no `COPY . /app`); exclude `solution/`, `tests/`, `**/target/`, build caches.
- Dockerfile sets `WORKDIR /app` (container CWD for agent + test.sh guard); this is separate from the forbidden `task.toml` `workdir` field.
- Do not copy `solution/`, `tests/`, or answer-shaped golden vectors into the image. Expected values live in `tests/test_outputs.py` only (RC5).
- Layer order: base + apt → pip deps → manifests (`Cargo.toml`/`Cargo.lock`) → `cargo build` in builder → copy binary + `data/` + `config/` + `store` sources (read-only) into runtime → `WORKDIR /app`.

**Opus-strong justification:** Exploits multi-source-of-truth trap (manifest head vs WAL replay cursor vs sidecar generation stamps), destructive-if-repeated rewind phase, and premature-completion bait where aggregate rollups pass while point-resolution path still serves stale column stripes.

### Failure topology
A destructive background merge advanced the manifest head and compacted away superseded column stripes, but the incremental read path for one keyspace still resolves through a sidecar index bound to pre-merge segment IDs while the aggregate rollup path reads merged column statistics from the newest manifest tier. Tombstone windows that should hide rows at queried timestamps are visible through the point path only. The operator must discover which manifest generation is the safe rollback anchor (not simply the highest or lowest), which WAL segments must be retained through the barrier, and that secondary-index rebuild must follow manifest rollback — rebuilding indexes first leaves dangling pointers that still fail point tests.

### Environment shape
- `environment/store/` — Rust workspace: column reader, merge scheduler, manifest journal, WAL replayer, sidecar builder, ctl CLI (25+ modules across `src/`, `ctl/`, `ops/`, `index/`, `manifest/`, `wal/`).
- `environment/data/` — Offline fixtures: tiered manifest JSONL chains, column SST files, WAL segments, sidecar blobs, golden visibility vectors.
- `environment/config/recovery/` — Operator-editable TOML: phase ordering table, barrier sequence anchors, per-keyspace rebuild gates (values initially wrong/incomplete).
- `environment/ops/runbooks/` — Non-fix shell helpers documenting ctl invocations (no hidden solver steps).
- `tests/` — Python verifier comparing golden vectors, manifest monotonicity, sidecar digests, report schema.

### Required artifacts
- `tasks/columnar-compaction-rewind/task.toml` — standard shape: `[agent]`, `[verifier]`, `[environment]` with `allow_internet = false`; **no** `workdir` key (non-milestone)
- `tasks/columnar-compaction-rewind/output_contract.toml`
- `tasks/columnar-compaction-rewind/instruction.md` (symptoms-only)
- `tasks/columnar-compaction-rewind/environment/Dockerfile` — multi-stage; canonical Rust builder + Debian bookworm-slim runtime; tmux + asciinema + pinned pytest
- `tasks/columnar-compaction-rewind/environment/.dockerignore`
- `tasks/columnar-compaction-rewind/environment/store/` (full Rust workspace, prebuilt `ctl` binary)
- `tasks/columnar-compaction-rewind/environment/data/` (fixtures)
- `tasks/columnar-compaction-rewind/environment/config/recovery/` (editable recovery TOML)
- `tasks/columnar-compaction-rewind/tests/test.sh`, `tests/test_outputs.py` (≥8 tests)
- `tasks/columnar-compaction-rewind/solution/solve.sh` (oracle: config edits + ordered ctl invocations)

### Test plan
- `test_golden_vector_alpha` — fixture key visibility vector A matches golden after recovery.
- `test_golden_vector_beta` — fixture key visibility vector B and ordering match golden.
- `test_absent_marker_at_window` — deleted fixture key absent at queried time window.
- `test_aggregate_totals_stable` — aggregate totals still match golden (regression guard).
- `test_output_json_schema_valid` — `/output/rewind-report.json` schema and required fields.
- `test_chain_order_invariant` — restored chain generation monotonic and ≤ pre-merge head.
- `test_digest_checksum_match` — rebuilt index digest matches column stripe checksums.
- `test_secondary_namespace_stable` — unaffected namespace vectors unchanged from baseline.

### Drafting guardrails
Do not name the stale manifest tier, safe rollback generation number, WAL barrier sequence, or rebuild ordering in instruction.md, test names, comments, or fixture filenames. Recovery TOML keys must use opaque identifiers (`phase_table`, `barrier_seq`, `tier_anchor`) not matching instruction nouns on the fix path. Decoy ctl subcommands and index helpers must look structurally similar to the real rollback path. Avoid disclosing the dual read-path divergence in instruction prose.

### Triviality Ledger

- Naive "rewind to highest manifest gen" passes monotonicity test but fails point vectors because the safe anchor is two generations behind the head; `test_chain_order_invariant` coupled with `test_golden_vector_alpha` blocks this.
- Rebuilding sidecars before manifest rollback passes digest on stale stripes but fails point lookups; `test_digest_checksum_match` plus `test_absent_marker_at_window` require correct phase order.
- Truncating WAL to latest segment only passes aggregate test (`test_aggregate_totals_stable`) but leaves tombstone window wrong; `test_absent_marker_at_window` requires barrier seq from compaction journal.
- Editing only one recovery TOML without ctl invocations leaves on-disk state inconsistent; chain-dependent tests fail without full workflow.
- Variant ladder: journals contain two plausible anchor generations; wrong anchor (decoy head for secondary namespace) passes `test_chain_order_invariant` for wrong namespace but fails `test_secondary_namespace_stable` and `test_golden_vector_alpha`.
- Recovery values are split across `phase_table.toml`, `anchors.toml`, and `barrier.toml` with cross-field validation in ctl; no single TOML block is sufficient.

### Per-gate Pitfall Inventory

- RC1 (instruction audit): instruction must stay symptoms-only — no manifest tier or generation hints.
- RC6 (grep collapse): fix-path Rust symbols must not contain instruction nouns; use `exec_m9`, `apply_k2`, `TIER_C`.
- GX3 (oracle size): substantive ordered ctl workflow in solve.sh, not cosmetic sed.
- GX9 (NOP): broken initial recovery config ensures NOP scores 0.
- GX10 (flipping point): three distinct revert locations each control <50% of tests.
- Static checks: `allow_internet = false`, verifier deps in Dockerfile, no `workdir` in `task.toml`, digest-pinned canonical `FROM` lines, `dockerfile_copy_sources` PASS.
- Docker CI: `check_pinned_images`, `check_sanctioned_base_images`, `check_build_context_size` (env ≤100 MiB, no file >50 MiB).
- Agent infra: tmux + asciinema must be present and verified at image build — missing either causes GPT-5.x infrastructure failures (0% solvability score unrelated to task difficulty).
- Collapse audit A1: no single manifest JSON patch passes all tests.
- Collapse audit A4: decoy compact/rebuild modules prevent one-file grep solve.

### Initial Draft Commitments

- `tasks/columnar-compaction-rewind/task.toml`
- `tasks/columnar-compaction-rewind/output_contract.toml`
- `tasks/columnar-compaction-rewind/instruction.md`
- `tasks/columnar-compaction-rewind/environment/Dockerfile`
- `tasks/columnar-compaction-rewind/environment/.dockerignore`
- `tasks/columnar-compaction-rewind/environment/store/Cargo.toml`
- `tasks/columnar-compaction-rewind/environment/store/Cargo.lock`
- `tasks/columnar-compaction-rewind/environment/store/src/lib.rs`
- `tasks/columnar-compaction-rewind/environment/store/src/column_reader.rs`
- `tasks/columnar-compaction-rewind/environment/store/src/merge_scheduler.rs`
- `tasks/columnar-compaction-rewind/environment/store/src/rollup.rs`
- `tasks/columnar-compaction-rewind/environment/store/manifest/src/journal.rs`
- `tasks/columnar-compaction-rewind/environment/store/manifest/src/tier.rs`
- `tasks/columnar-compaction-rewind/environment/store/wal/src/replayer.rs`
- `tasks/columnar-compaction-rewind/environment/store/wal/src/segment.rs`
- `tasks/columnar-compaction-rewind/environment/store/index/src/sidecar.rs`
- `tasks/columnar-compaction-rewind/environment/store/index/src/rebuild_fast.rs`
- `tasks/columnar-compaction-rewind/environment/store/index/src/rebuild_full.rs`
- `tasks/columnar-compaction-rewind/environment/store/ctl/src/main.rs`
- `tasks/columnar-compaction-rewind/environment/store/ctl/src/subcmd_roll.rs`
- `tasks/columnar-compaction-rewind/environment/store/ctl/src/subcmd_compact.rs`
- `tasks/columnar-compaction-rewind/environment/store/ctl/src/subcmd_query.rs`
- `tasks/columnar-compaction-rewind/environment/store/ops/src/barrier.rs`
- `tasks/columnar-compaction-rewind/environment/store/ops/src/phase.rs`
- `tasks/columnar-compaction-rewind/environment/config/recovery/phase_table.toml`
- `tasks/columnar-compaction-rewind/environment/config/recovery/barrier.toml`
- `tasks/columnar-compaction-rewind/environment/config/recovery/anchors.toml`
- `tasks/columnar-compaction-rewind/environment/data/manifests/tier_a.jsonl`
- `tasks/columnar-compaction-rewind/environment/data/manifests/tier_b.jsonl`
- `tasks/columnar-compaction-rewind/environment/data/manifests/tier_c.jsonl`
- `tasks/columnar-compaction-rewind/environment/data/wal/seg_001.bin`
- `tasks/columnar-compaction-rewind/environment/data/wal/seg_002.bin`
- `tasks/columnar-compaction-rewind/environment/data/columns/events_*.col`
- `tasks/columnar-compaction-rewind/environment/data/columns/metrics_*.col`
- `tasks/columnar-compaction-rewind/environment/data/sidecars/events.idx`
- `tasks/columnar-compaction-rewind/environment/data/sidecars/metrics.idx`
- `tasks/columnar-compaction-rewind/environment/ops/runbooks/ctl_usage.md`
- `tasks/columnar-compaction-rewind/tests/test.sh`
- `tasks/columnar-compaction-rewind/tests/test_outputs.py`
- `tasks/columnar-compaction-rewind/solution/solve.sh`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: environment/store/ctl/src/subcmd_roll.rs
  symbol: exec_m9
  kind: function
  signature: fn exec_m9(data_root: &Path, anchor: u64, ks: &str) -> Result<RollReport>
  purpose: Applies manifest rollback to anchor generation for one namespace

- path: environment/store/ops/src/barrier.rs
  symbol: apply_k2
  kind: function
  signature: fn apply_k2(wal_dir: &Path, cutoff: u64) -> Result<BarrierState>
  purpose: Truncates WAL replay window at sequence cutoff

- path: environment/store/index/src/rebuild_full.rs
  symbol: run_p4
  kind: function
  signature: fn run_p4(data_root: &Path, ks: &str, after_barrier: u64) -> Result<Digest>
  purpose: Rebuilds secondary sidecar from column stripes post-barrier

- path: environment/config/recovery/anchors.toml
  symbol: TIER_C
  kind: constant
  signature: tier_c = <u64>
  purpose: Recovery anchor generation consumed by ctl roll subcommand

- path: environment/config/recovery/barrier.toml
  symbol: SEQ_CUTOFF
  kind: constant
  signature: seq_cutoff = <u64>
  purpose: WAL barrier sequence for apply_k2
```

#### flipping_point_contract

```
locations:
  - id: A
    path: environment/config/recovery/anchors.toml
    controls_tests: [test_golden_vector_alpha, test_golden_vector_beta, test_chain_order_invariant]
  - id: B
    path: environment/config/recovery/barrier.toml
    controls_tests: [test_absent_marker_at_window, test_digest_checksum_match]
  - id: C
    path: solution/solve.sh
    controls_tests: [test_output_json_schema_valid, test_aggregate_totals_stable, test_secondary_namespace_stable]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: environment/store/ctl/src/subcmd_compact.rs
  kind: module
  rhymes_with: exec_m9
  non_fix_purpose: Runs live forward compaction against current head; unsafe after partial merge

- path: environment/store/index/src/rebuild_fast.rs
  kind: helper
  rhymes_with: run_p4
  non_fix_purpose: Incremental sidecar patch from head manifest without WAL barrier

- path: environment/store/manifest/src/tier.rs
  kind: module
  rhymes_with: TIER_C
  non_fix_purpose: Tier promotion for forward merges; does not roll back
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [production, columnar, storage, time-travel, queries, embedded, engine, background, merge, point, lookups, range, scans, events, keyspace, rows, timestamps, rollup, counts, keyspaces, visibility, operator, tooling, recovery, configuration, manifest, generation, segment, statistics, rewind]
```

### Dockerfile runtime template (BLOCKING — copy verbatim into `environment/Dockerfile` runtime stage)

Step 2b must place this block immediately after the final `FROM debian:bookworm-slim@sha256:…` line and **before** any `COPY` instructions:

```dockerfile
# Agent runtime requires tmux and asciinema before COPY layers below.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        tmux=3.3a-3 \
        ca-certificates=20230311+deb12u1 \
        python3=3.11.2-1+b1 \
        python3-pip=23.0.1+dfsg-1 \
    && rm -rf /var/lib/apt/lists/*

ENV TERM=xterm-256color

RUN tmux -V && asciinema --version

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest==8.4.1 \
    pytest-json-ctrf==0.3.5
```

Do not omit tmux or asciinema. Do not defer them to a later layer or to `tests/test.sh`.
