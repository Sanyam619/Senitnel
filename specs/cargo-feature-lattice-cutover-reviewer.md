### Decision
GO — Attempt 1. Distributed fix across build.rs probe, proc-macro gate, and cargo-config cfg roots; opaque symbols; default-green false acceptance trap; ship/field matrix coupling.

### Metadata
- Task name: cargo-feature-lattice-cutover
- Title: Cargo Feature Lattice Cutover
- Category: build-and-dependency-management
- Languages: ["Rust"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: ["tool_specific"]
- Tags: ["cargo", "rust", "features", "workspace", "proc-macro", "linker"]
- Milestones: 0

### Discovery budget
- Discovery: `probe_slot_a` still emits omit-cfg when mqtt is on, causing compile_error when lora is also requested (legacy mutex).
  Planned location: `p7/build.rs` plus lora/compile gates in `p7/src/main.rs`
  Why instruction must not reveal it: Naming the mutex probe collapses the ship matrix to a one-line build.rs delete.

- Discovery: `expand_gate_b` expands uart registration under old token `legacy_uart` and marks mqtt/lora active even on default features.
  Planned location: `g4/src/lib.rs`
  Why instruction must not reveal it: Naming the proc-macro token mismatch turns the task into a string-replace recipe.

- Discovery: `.cargo/config.toml` injects `--cfg hook_legacy_only`, which compile_error's the field/uart lane and swaps ship hook tags to omitted markers.
  Planned location: `.cargo/config.toml` + backend tag modules
  Why instruction must not reveal it: Pointing at the rustflags line removes cfg/lattice coupling reasoning.

### Anti-trivialization verdict
All 21 checks PASS for this cutover design: not hidden-instance, not single-manifest flip, not disclosure-complete, discovery budget ≥3, topology ≥3, hard-only gate PASS, symptoms-only instruction.

### Topology enumeration (3 candidate fix topologies)
1. **Probe-first lattice** — coordinate `p7/build.rs`, `p7/Cargo.toml` features, `bk-lora` compile gates. No single file restores ship compile + dual active roster.
2. **Macro-first roster** — coordinate `g4/src/lib.rs`, `p7/src/roster.rs`, feature names in `p7/Cargo.toml`. Macro-only fix leaves field blocked by config cfg.
3. **Config-first cfg** — coordinate `.cargo/config.toml`, backend hook tags, field uart gate. Config-only fix leaves ship mutex and wrong macro tokens.

### Rubric axes
- Verifiable: PASS — cargo builds + JSON roster + binary strings.
- Well-specified: PASS — ship/field/default outcomes clear.
- Solvable: PASS — expert Cargo engineer in a few hours.
- Difficult: PASS — feature lattice + proc-macro + cfg coupling.
- Interesting: PASS — real mid-cutover workspace work.
- Outcome-verified: PASS — grades builds and capability roster, not patch transcript.

### Hardness axes
- Discover: PASS — must read ops matrix, build.rs, macro expansion, config rustflags.
- Synthesize: PASS — features, cfg, macro, config must agree.
- Diagnose: PASS — symptoms are green-default vs broken matrices, not named causes.
- Navigate coupling: PASS — fixing mutex without features/config still fails field/symbols.
- Reason beyond training: PASS — not a single Cargo.toml flip; lattice + proc-macro + cfg.

### Instruction completeness test
No — instruction alone does not name omit-cfg, legacy_uart token, or hook_legacy_only rustflags; solver must engage the workspace.

## Reviewer Appendix

### Implementation plan
Broken mid-cutover Rust workspace: default features compile; ship hits mutex compile_error; field hits legacy cfg compile_error; macros mis-register capabilities; config strips hook tags. Oracle reconciles build.rs, macro, config, and feature tables, then builds ship and emits `/output/cap-roster.json`.

### Proposed file inventory
Matches authoring spec Initial Draft Commitments (25+ env files).

### Oracle notes
solve.sh: clear hook_legacy_only from `.cargo/config.toml`; rewrite `probe_slot_a` to stop omit-cfg on mqtt; rewrite `expand_gate_b` to use mqtt/lora/uart feature tokens and default-inactive; fix `p7/Cargo.toml` ship/field feature deps; cargo build ship; run caps to `/output/cap-roster.json`.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
Must touch build probe, macro gate, and cargo config (plus feature table) — not one file.

Likely editable frontier:
- p7/build.rs, g4/src/lib.rs, .cargo/config.toml, p7/Cargo.toml

Requirement-to-file map:
- ship compile -> build.rs + features
- field compile -> config.toml + features
- roster statuses -> macros + roster
- hook tags -> config.toml + backends

Oracle estimated complexity: 80-120 lines substantive

Red flags:
- none if instruction stays cutover/symptoms-only

Residual hardness:
Default-green trap plus three-way feature/cfg/macro coupling remains after tree is visible.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
agent, cutover, feature, crate, lattice, edition, bump, default-features, build, ship, field, matrix, binary, backend, profile, ops, notes, linker, material, fixtures, state, pulse-agent, roster, caps, subcommand, mqtt, lora, uart, pair, active, inactive, backends

**Renames during drafting:**
- [`agent/` → `p7/`: path token matched instruction noun agent]
- [`macros/` → `g4/`: avoid generic telegraph; distinct root]
- [`test_q2_primary_hook_pair` → `test_q2_primary_hook_both`: pair is instruction noun]

**Test names audited:**
- test_k4_dual_lane_ok
- test_m8_alt_lane_ok
- test_q2_primary_hook_both
- test_t6_alt_hook_solo
- test_w1_baseline_gap
- test_n9_sym_presence

**Concentration math:**
- Total tests across `flipping_point_contract`: 6
- Per location:
  - L1 (`p7/build.rs`): 2/6 = 0.333
  - L2 (`g4/src/lib.rs`): 2/6 = 0.333
  - L3 (`.cargo/config.toml`): 2/6 = 0.333
- Cap: 0.5. Max ratio observed: 0.333. Status: PASS

### Per-test feasibility pre-check
- Test: test_k4_dual_lane_ok — Checks ship release build exit 0 — Valid approaches: 2+ — Chain-dependent: no — Feasibility: LOW
- Test: test_m8_alt_lane_ok — Checks field release build exit 0 — Valid approaches: 2+ — Chain-dependent: no — Feasibility: LOW
- Test: test_q2_primary_hook_both — Checks ship roster mqtt+lora active — Valid approaches: 2+ — Chain-dependent: needs ship binary — Feasibility: MEDIUM
- Test: test_t6_alt_hook_solo — Checks field roster uart-only active — Valid approaches: 2+ — Chain-dependent: needs field binary — Feasibility: MEDIUM
- Test: test_w1_baseline_gap — Checks default roster lacks ship pair — Valid approaches: 2+ — Chain-dependent: needs default binary — Feasibility: LOW
- Test: test_n9_sym_presence — Checks ship binary hook tag strings — Valid approaches: 2+ — Chain-dependent: needs ship binary — Feasibility: LOW
