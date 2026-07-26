### Decision
GO — Attempt 1. Redesign from build/Cargo lattice to data-processing: multi-lane JSONL + WAL decode, ship co-presence, field solo, conflicting tier watermarks. Primary work is derived roster/rollup emission, not source repair.

### Metadata
- version: 2
- Task name: edge-lane-lattice-rollup
- Title: Edge Lane Lattice Rollup
- Category: system-administration
- Languages: ["Rust"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: ["telemetry", "rollup", "wal", "jsonl", "rust", "lattice"]
- Milestones: 0

## Authoring Brief

### Public contract

Raw edge telemetry dumps under `/app/data/` span per-lane JSONL, binary WAL segments, and tier manifests. Ops matrix notes under `/app/ops/` describe ship/field lane lattices. A surface skim looks complete, but the derived capability roster is wrong for ship co-presence and field solo rules.

**Required outcomes:**
- `/output/cap-roster.json` with integer `version` `1`, array `backends` (each `name` + `status`), and array `epochs` (each integer `id`, string `profile`, integer `accepted`).
- For the active ship window set, `mqtt` and `lora` are both `active` only when co-present after WAL merge and holdback; otherwise both `inactive`.
- For the field window set, `uart` is `active` and `mqtt`/`lora` are `inactive`.
- Epoch `accepted` counts match the filtered merge (not the surface skim).
- `/app/data/fixtures/` unchanged.

### Failure topology

Three interacting data authorities. Lane JSONL alone under-counts because WAL frames carry additional accepted events. Tier manifests disagree on watermarks: a green surface tier marks epochs complete while a stricter tier still holds events. Ship lattice requires mqtt+lora co-presence in the same epoch after merge; treating lanes independently yields a false ship pair. Field lattice forces uart-only actives.

### Environment shape

- Rust `ctl` skim tool (false-green surface path) plus `core` helpers.
- `/app/data/lanes/*.jsonl`, `/app/data/wal/*.bin`, `/app/data/manifests/*.jsonl`.
- `/app/ops/matrix.toml`, profile TOMLs, runbook.
- Dockerfile builds skim binary; agent produces derived JSON from raw dumps.

### Required artifacts

Standard single-step layout under `tasks/edge-lane-lattice-rollup/` with 20+ environment files, Rust-only solver path (no Python ETL in oracle).

### Test plan

- `test_k4_dual_hook_ok` — ship backends mqtt+lora both active after correct merge.
- `test_m8_alt_hook_ok` — field uart active; mqtt/lora inactive.
- `test_q2_window_tally_a` — ship epoch accepted counts match filtered merge.
- `test_t6_window_tally_b` — field epoch accepted counts match uart-only merge.
- `test_w1_green_gap` — roster must not equal surface skim output.
- `test_n9_anchor_digest` — fixtures checksum unchanged.

### Drafting guardrails

Symptoms-only instruction. No WAL checksum recipe, no co-presence algorithm named. Opaque fix-path symbols. Oracle transforms data via Rust, does not sed-fix skim as the whole solution.

### Triviality Ledger

- Skimming JSONL only fails WAL-backed accepted counts.
- Independent lane activation fails ship co-presence.
- Trusting surface tier watermark fails holdback filtering.
- Copying surface skim output fails `test_w1_green_gap`.

### Per-gate Pitfall Inventory

- RC1/RC7: Oracle implements multi-stage Rust merge ≥30 LOC substantive.
- RC3: Tests assert computed statuses and counts.
- RC5: Expected counts embedded in tests.
- RC6: Instruction symptoms-only.
- CR1/CR2: Three loci with ≤50% concentration.
- Static: `allow_internet=false`, `.dockerignore`, absolute paths.

### Initial Draft Commitments

- `tasks/edge-lane-lattice-rollup/task.toml`
- `tasks/edge-lane-lattice-rollup/instruction.md`
- `tasks/edge-lane-lattice-rollup/output_contract.toml`
- `tasks/edge-lane-lattice-rollup/tests/test.sh`
- `tasks/edge-lane-lattice-rollup/tests/test_outputs.py`
- `tasks/edge-lane-lattice-rollup/solution/solve.sh`
- `tasks/edge-lane-lattice-rollup/environment/Dockerfile`
- `tasks/edge-lane-lattice-rollup/environment/.dockerignore`
- `tasks/edge-lane-lattice-rollup/environment/Cargo.toml`
- `tasks/edge-lane-lattice-rollup/environment/core/Cargo.toml`
- `tasks/edge-lane-lattice-rollup/environment/core/src/lib.rs`
- `tasks/edge-lane-lattice-rollup/environment/ctl/Cargo.toml`
- `tasks/edge-lane-lattice-rollup/environment/ctl/src/main.rs`
- `tasks/edge-lane-lattice-rollup/environment/ctl/src/fold_a.rs`
- `tasks/edge-lane-lattice-rollup/environment/ctl/src/sieve_b.rs`
- `tasks/edge-lane-lattice-rollup/environment/ctl/src/emit_c.rs`
- `tasks/edge-lane-lattice-rollup/environment/ctl/src/decoy_fold.rs`
- `tasks/edge-lane-lattice-rollup/environment/ctl/src/decoy_sieve.rs`
- `tasks/edge-lane-lattice-rollup/environment/ops/matrix.toml`
- `tasks/edge-lane-lattice-rollup/environment/ops/runbooks/ctl_usage.md`
- `tasks/edge-lane-lattice-rollup/environment/config/profiles/ship.toml`
- `tasks/edge-lane-lattice-rollup/environment/config/profiles/field.toml`
- `tasks/edge-lane-lattice-rollup/environment/data/lanes/mqtt.jsonl`
- `tasks/edge-lane-lattice-rollup/environment/data/lanes/lora.jsonl`
- `tasks/edge-lane-lattice-rollup/environment/data/lanes/uart.jsonl`
- `tasks/edge-lane-lattice-rollup/environment/data/manifests/tier_a.jsonl`
- `tasks/edge-lane-lattice-rollup/environment/data/manifests/tier_b.jsonl`
- `tasks/edge-lane-lattice-rollup/environment/data/manifests/tier_c.jsonl`
- `tasks/edge-lane-lattice-rollup/environment/data/wal/seg_001.bin`
- `tasks/edge-lane-lattice-rollup/environment/data/wal/seg_002.bin`
- `tasks/edge-lane-lattice-rollup/environment/data/wal/seg_003.bin`
- `tasks/edge-lane-lattice-rollup/environment/data/fixtures/seed.json`
- `tasks/edge-lane-lattice-rollup/environment/data/fixtures/surface_skim.json`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: ctl/src/fold_a.rs
  symbol: fold_a
  kind: function
  signature: fn fold_a(raw: &[u8], mark: u64) -> Vec<(u16, u8, bool)>
  purpose: Decodes WAL bytes into epoch/lane/hold tuples under a watermark.

- path: ctl/src/sieve_b.rs
  symbol: sieve_b
  kind: function
  signature: fn sieve_b(rows: &[(u16, String, bool)], mode: &str) -> Vec<(u16, String)>
  purpose: Applies lattice co-presence or solo rules per profile mode.

- path: ctl/src/emit_c.rs
  symbol: emit_c
  kind: function
  signature: fn emit_c(path: &str, backends: &[(String, String)], epochs: &[(u16, String, u32)]) -> std::io::Result<()>
  purpose: Writes the derived roster JSON object.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: ctl/src/fold_a.rs
    controls_tests: [test_q2_window_tally_a, test_t6_window_tally_b]
  - id: B
    path: ctl/src/sieve_b.rs
    controls_tests: [test_k4_dual_hook_ok, test_m8_alt_hook_ok]
  - id: C
    path: ctl/src/emit_c.rs
    controls_tests: [test_w1_green_gap, test_n9_anchor_digest]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: ctl/src/decoy_fold.rs
  kind: helper
  rhymes_with: fold_a
  non_fix_purpose: JSONL-only counter used by surface skim; ignores WAL bytes.

- path: ctl/src/decoy_sieve.rs
  kind: helper
  rhymes_with: sieve_b
  non_fix_purpose: Per-lane independent activation without co-presence.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [telemetry, rollup, lane, lattice, ship, field, mqtt, lora, uart, watermark, holdback, roster, backends, epochs, accepted, profile, surface, skim, wal, manifest, fixture, version, status, name, active, inactive, cutover, edge, binary, derived, window, pair]
```
