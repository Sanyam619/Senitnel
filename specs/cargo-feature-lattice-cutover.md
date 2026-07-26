### Decision
GO — Attempt 1. Distributed fix across build.rs probe, proc-macro gate, and Cargo/config lattice roots; opaque symbols; default-green false acceptance trap; ship/field matrix coupling.

### Metadata
- version: 2
- Task name: cargo-feature-lattice-cutover
- Title: Cargo Feature Lattice Cutover
- Category: build-and-dependency-management
- Languages: ["Rust"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: ["tool_specific"]
- Tags: ["cargo", "rust", "features", "workspace", "proc-macro", "linker"]
- Milestones: 0

## Authoring Brief

### Public contract

A Rust workspace under `/app/` is mid-cutover from a monolithic agent into a feature-gated crate lattice. After an edition bump, default-features builds look green while the ship and field matrices do not both land, and a green default binary omits backends the ship profile must expose.

**Symptoms the agent sees (instruction.md level):**
- Default-features `cargo` build of `pulse-agent` succeeds.
- Ship and field feature sets do not both produce a coherent release binary.
- Caps roster from a default-features binary omits the ship backend pair.
- Ops matrix notes under `/app/ops/` describe intended ship/field capability sets without naming the broken gate sites.

**Required outcomes:**
- Ship feature set builds `pulse-agent` release binary successfully.
- Field feature set builds `pulse-agent` release binary successfully.
- `/output/cap-roster.json` from a ship binary lists `mqtt` and `lora` under `backends` with `status` `active`.
- A field binary's roster lists `uart` as `active` and `mqtt`/`lora` as `inactive`.
- A default-features binary must not report the ship backend pair as both `active`.
- Ship binary contains required backend hook tag strings documented in `/app/link/`.

**Constraints:**
- `[environment] allow_internet = false`; verifier deps in Dockerfile.
- No multi-container layout.
- Agent edits workspace manifests, build scripts, proc-macro, and cargo config — not hand-written golden JSON.
- Rust-only environment sources (plus ops notes / fixtures).

### Failure topology

Three coupled cutover remnants interact. First, `probe_slot_a` in the agent `build.rs` still emits an omit-cfg when mqtt is enabled (legacy mutual exclusion from the monolith), so ship builds that need mqtt+lora together hit a compile_error on the lora path. Second, `expand_gate_b` in the proc-macro still expands registration arms against old feature token names, so field uart stays inactive in the roster and default builds falsely mark the ship pair active. Third, `.cargo/config.toml` still injects a legacy rustc `--cfg` that blocks the field lane and strips ship hook tags, while workspace feature tables remain mid-migration on optional backend deps.

The task is hard because a green default-features build is a false acceptance signal, mutual-exclusion vs required-together is encoded across build.rs and features, and proc-macro expansion plus cfg/link selection must agree with the Cargo feature lattice.

### Environment shape

- `environment/Dockerfile` + `.dockerignore` — Rust toolchain, offline cargo cache, pytest.
- `environment/` workspace root with crates: core, wire, macros, three backends, agent binary.
- `environment/.cargo/config.toml` — rustflags / cfg injection (fix locus C).
- `environment/link/` — hook tag notes (correct + decoy).
- `environment/ops/` — matrix notes and runbook (discovery, not instruction-by-reference for ops contract).
- `environment/config/` — profile TOML decoys.
- `environment/data/fixtures/` — checksum-guarded fixtures.

### Required artifacts

- `tasks/cargo-feature-lattice-cutover/task.toml` with `allow_internet = false`.
- `tasks/cargo-feature-lattice-cutover/instruction.md` — symptoms-only cutover prose (not repair/debug framing).
- `tasks/cargo-feature-lattice-cutover/tests/test.sh`, `tests/test_outputs.py` — six hard tests; session-cached builds.
- `tasks/cargo-feature-lattice-cutover/solution/solve.sh` — oracle patches ≥3 loci (≥30 LOC substantive).
- `tasks/cargo-feature-lattice-cutover/environment/**` — 25+ non-Docker files per Initial Draft Commitments.

### Test plan

- `test_k4_dual_lane_ok` — Ship feature set `cargo build -p pulse-agent --release` succeeds (exit 0).
- `test_m8_alt_lane_ok` — Field feature set release build succeeds.
- `test_q2_primary_hook_both` — Ship caps roster has mqtt+lora both `active`.
- `test_t6_alt_hook_solo` — Field roster has uart `active` and mqtt/lora `inactive`.
- `test_w1_baseline_gap` — Default-features roster does not have both mqtt and lora `active`.
- `test_n9_sym_presence` — Ship binary contains required hook tag strings from `/app/link/`.

Chain-dependent: roster tests need successful builds; session fixture builds once per lane. Multiple valid approaches exist (any coherent feature/cfg/macro/config reconciliation that satisfies outcomes).

### Drafting guardrails

Do not embed instruction nouns in fix-path function names, parameters, or test names. Instruction uses standard Cargo/feature language freely. Do not frame as bug-hunt or repair checklist. Do not hide the operational contract in environment README files — ops notes may describe matrix intent the solver discovers. No HINT/STEP walkthroughs in environment/.

### Triviality Ledger

- Enabling only mqtt on ship passes a naive compile check but fails `test_q2_primary_hook_both` and/or `test_n9_sym_presence` because lora must be required-together.
- Fixing Cargo.toml features alone leaves `probe_slot_a` omit-cfg and fails ship lora activation.
- Fixing build.rs alone leaves proc-macro old tokens and fails roster tests.
- Fixing macros alone leaves wrong linker rustflags and fails `test_n9_sym_presence` / ship link.
- Treating default-features green as done fails `test_w1_baseline_gap` and ship/field lane tests.
- Hand-writing `/output/cap-roster.json` without a real binary fails symbol and rebuild-from-sources checks.

### Per-gate Pitfall Inventory

- RC1: Oracle must reconcile features/cfg/macro/config — not delete omit lines only or copy a golden roster.
- RC3: Tests assert build success, computed roster statuses, and symbol presence — not file existence alone.
- RC5: Expected backend names/statuses live in test code and instruction; no golden JSON under environment/.
- RC6: Instruction stays symptoms-only cutover language — do not name `probe_slot_a`, `expand_gate_b`, or exact broken knobs.
- RC7: `solve.sh` edits ≥3 loci with substantive logic ≥30 LOC.
- CR1/CR2: Use construction manifest symbols verbatim; flipping-point 2+2+2.
- CR7/GX9: Roster field names appear in instruction; do not recite per-test answer triples beyond contract.
- Static checks: `allow_internet = false`, `.dockerignore`, absolute paths, timeout coherence with cached builds.

### Initial Draft Commitments

- `tasks/cargo-feature-lattice-cutover/task.toml`
- `tasks/cargo-feature-lattice-cutover/instruction.md`
- `tasks/cargo-feature-lattice-cutover/output_contract.toml`
- `tasks/cargo-feature-lattice-cutover/tests/test.sh`
- `tasks/cargo-feature-lattice-cutover/tests/test_outputs.py`
- `tasks/cargo-feature-lattice-cutover/solution/solve.sh`
- `tasks/cargo-feature-lattice-cutover/environment/Dockerfile`
- `tasks/cargo-feature-lattice-cutover/environment/.dockerignore`
- `tasks/cargo-feature-lattice-cutover/environment/Cargo.toml`
- `tasks/cargo-feature-lattice-cutover/environment/Cargo.lock`
- `tasks/cargo-feature-lattice-cutover/environment/.cargo/config.toml`
- `tasks/cargo-feature-lattice-cutover/environment/link/hooks.toml`
- `tasks/cargo-feature-lattice-cutover/environment/link/legacy.toml`
- `tasks/cargo-feature-lattice-cutover/environment/ops/matrix.toml`
- `tasks/cargo-feature-lattice-cutover/environment/ops/runbooks/ctl_usage.md`
- `tasks/cargo-feature-lattice-cutover/environment/config/profiles/ship.toml`
- `tasks/cargo-feature-lattice-cutover/environment/config/profiles/field.toml`
- `tasks/cargo-feature-lattice-cutover/environment/data/fixtures/seed.json`
- `tasks/cargo-feature-lattice-cutover/environment/core/Cargo.toml`
- `tasks/cargo-feature-lattice-cutover/environment/core/src/lib.rs`
- `tasks/cargo-feature-lattice-cutover/environment/wire/Cargo.toml`
- `tasks/cargo-feature-lattice-cutover/environment/wire/src/lib.rs`
- `tasks/cargo-feature-lattice-cutover/environment/g4/Cargo.toml`
- `tasks/cargo-feature-lattice-cutover/environment/g4/src/lib.rs`
- `tasks/cargo-feature-lattice-cutover/environment/g4/src/preview.rs`
- `tasks/cargo-feature-lattice-cutover/environment/bk-mqtt/Cargo.toml`
- `tasks/cargo-feature-lattice-cutover/environment/bk-mqtt/src/lib.rs`
- `tasks/cargo-feature-lattice-cutover/environment/bk-lora/Cargo.toml`
- `tasks/cargo-feature-lattice-cutover/environment/bk-lora/src/lib.rs`
- `tasks/cargo-feature-lattice-cutover/environment/bk-uart/Cargo.toml`
- `tasks/cargo-feature-lattice-cutover/environment/bk-uart/src/lib.rs`
- `tasks/cargo-feature-lattice-cutover/environment/p7/Cargo.toml`
- `tasks/cargo-feature-lattice-cutover/environment/p7/build.rs`
- `tasks/cargo-feature-lattice-cutover/environment/p7/src/main.rs`
- `tasks/cargo-feature-lattice-cutover/environment/p7/src/sheet.rs`
- `tasks/cargo-feature-lattice-cutover/environment/p7/src/probe_legacy.rs`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: p7/build.rs
  symbol: probe_slot_a
  kind: function
  signature: fn probe_slot_a(a: &str, b: &str) -> bool
  purpose: Emits rustc-cfg tokens from feature environment probes during build.

- path: g4/src/lib.rs
  symbol: expand_gate_b
  kind: function
  signature: fn expand_gate_b(primary: TokenStream) -> TokenStream
  purpose: Expands capability registration arms for optional backend hooks.

- path: p7/src/sheet.rs
  symbol: emit_sheet_c
  kind: function
  signature: fn emit_sheet_c(path: &str, rows: &[(String, String)]) -> std::io::Result<()>
  purpose: Writes the caps roster JSON object to the output path.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: p7/build.rs
    controls_tests: [test_k4_dual_lane_ok, test_q2_primary_hook_both]
  - id: B
    path: g4/src/lib.rs
    controls_tests: [test_t6_alt_hook_solo, test_w1_baseline_gap]
  - id: C
    path: .cargo/config.toml
    controls_tests: [test_m8_alt_lane_ok, test_n9_sym_presence]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: p7/src/probe_legacy.rs
  kind: helper
  rhymes_with: probe_slot_a
  non_fix_purpose: Read-only diagnostic that prints feature env vars for ops scripts; not invoked by release builds.

- path: g4/src/preview.rs
  kind: helper
  rhymes_with: expand_gate_b
  non_fix_purpose: Dry-run token pretty-printer used by local docs generation; not linked into pulse-agent.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [agent, cutover, feature, crate, lattice, edition, bump, default-features, compile, ship, field, matrix, binary, backend, profile, ops, notes, linker, material, fixtures, pulse-agent, roster, caps, subcommand, mqtt, lora, uart, pair, active, inactive, backends, version, status, name]
```
