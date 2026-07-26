### Decision
GO — Attempt 1. Build-unification only (no source repair/debug of service logic): three language codegen pin/resolver roots must converge on one wire ABI under yank+mirror pressure; false-green per-language healthchecks; opaque fold/sieve/emit symbols.

### Metadata
- version: 2
- Task name: wire-contract-codegen-unify
- Title: Wire Contract Codegen Unify
- Category: build-and-dependency-management
- Languages: ["Go", "Rust", "Java"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: ["tool_specific"]
- Tags: ["protobuf", "codegen", "gomod", "cargo", "maven", "wire-abi"]
- Milestones: 0

## Authoring Brief

### Public contract

A single-container monorepo under `/app/` generates stubs from one shared IDL through three language build pipelines (Go module + `protoc-gen-go` pin path, Rust `prost`/`build.rs` pin path, Java Maven protobuf plugin pin path). After a registry yank and a mirror pin, each language health check still compiles alone. Cross-language integration disagrees on the wire: field numbers, oneof arms, optional presence, and JSON names diverge across stub sets.

**Symptoms the agent sees (instruction.md level):**
- Per-language health checks stay green in isolation.
- Cross-language integration binaries / probes disagree on wire layout and JSON names.
- Registry yank + mirror pin leave each resolver looking locally consistent.

**Required outcomes:**
- `/output/wire-unify.json` exists with integer `schema_version` `1`, hex string `contract_digest`, and arrays `go_rows`, `rust_rows`, `java_rows` of objects with string `slot`, integer `tag`, string `kind`, string `json_key`.
- The three layout arrays agree row-for-row on `slot`/`tag`/`kind`/`json_key` (same ordered slots).
- `/app/bin/xlink` binary and JSON round-trip probes both report `status` `ok`.
- `/app/bin/lanehealth` remains green for go, rust, and java after unification.
- IDL under `/app/idl/` and yank/mirror fixtures under `/app/data/registry/` unchanged (verifier integrity ledger).

**Constraints:**
- `[environment] allow_internet = false`; verifier deps in Dockerfile.
- No multi-container layout.
- Agent work is build-graph / pin / codegen unification across Go, Rust, and Java — not debugging service business logic.
- Languages: Go, Rust, Java.

### Failure topology

Three interacting clusters. First, false-green surface: `lanehealth` only compiles each language alone and ignores cross-language wire ABI. Second, pin/mirror skew: a yanked transitive codegen plugin still wins through a mirror overlay for one language while the others pin a different owner for field tags / presence / JSON names. Third, dual-path drift: binary wire tags and JSON name options are owned by different plugin pins, so aligning only binary tags leaves JSON round-trips broken (and vice versa).

Hard because each language build can be locally “correct” while the shared wire contract is wrong, and no single pin file documents which plugin owns which layout dimension.

### Environment shape

- `environment/Dockerfile` + `.dockerignore` — Go + Rust + JDK/Maven + pytest; offline registries.
- `environment/idl/` — shared IDL fixtures (immutable to agent for integrity).
- `environment/data/registry/` — yank windows, mirror overlays, plugin metadata.
- `environment/gox/` — Go module, health entry, opaque fold path + decoy skim.
- `environment/rsx/` — Rust workspace, prost-style build pin path, opaque sieve + decoy.
- `environment/jvx/` — Maven project, protobuf plugin BOM path, opaque emit.
- `environment/xlink/` — cross-language probe/report CLI (orchestrates layouts; must not call >2 fix-path symbols from one file — distribute via thin wrappers).
- `environment/ops/` — runbooks and policy notes (no fix recipes).
- `environment/config/` — lane matrix / field notes only.

### Required artifacts

- `tasks/wire-contract-codegen-unify/task.toml` with `allow_internet = false`, `category = "build-and-dependency-management"`, languages Go/Rust/Java.
- `instruction.md` — symptoms-only; names output path and JSON fields.
- `tests/test.sh`, `tests/test_outputs.py` — six opaque hard tests (no existence-only / schema-only tests).
- `solution/solve.sh` — unifies pins/resolvers across three roots (≥30 substantive LOC).
- `environment/**` — 25+ non-Docker files per Initial Draft Commitments.
- `output_contract.toml` — authoring metadata.

### Test plan

- `test_k3_zircon` — binary field `tag` values agree across `go_rows`/`rust_rows`/`java_rows` for every `slot`.
- `test_m8_obsidian` — `kind` values for oneof-class slots agree across the three arrays.
- `test_p2_garnet` — optional-presence `kind`/`tag` pairs agree (proto3 optional dimension).
- `test_q7_topaz` — `json_key` values agree across languages for every `slot`.
- `test_r1_onyx` — `contract_digest` is a non-empty hex digest identical to the digest recomputed from the agreed layout rows.
- `test_t6_amber` — `schema_version == 1`; binary and JSON round-trip probes both `ok`; IDL/registry fixtures unchanged.

Multiple valid pin-alignment sequences allowed if outcomes match. Not chain-dependent on a single ordered recipe beyond needing a coherent unified contract for digest/round-trip tests.

### Drafting guardrails

Do not embed instruction nouns in fix-path symbols, parameters, or test names. Instruction may use standard build/codegen domain language. No HINT/STEP walkthroughs. `lanehealth` must genuinely implement shallow per-language compile checks. Do not frame the task as bug-hunting in service logic. No golden answer files under `environment/`.

### Triviality Ledger

- Aligning only Go pins leaves Rust/Java layouts drifting → `test_k3_zircon` / `test_q7_topaz` fail.
- Aligning binary tags without JSON name options passes tag tests but fails `test_q7_topaz` and JSON round-trip in `test_t6_amber`.
- Following decoy `skim_fold` / `skim_sieve` (mirror-local “preferred” plugin) keeps `lanehealth` green but leaves cross-lang disagreement.
- Rewriting IDL or registry fixtures fails integrity checks inside `test_t6_amber`.
- Emitting a hand-written `/output/wire-unify.json` without going through `/app/bin/xlink report` fails probe coupling / digest checks.

### Per-gate Pitfall Inventory

- RC1: Oracle edits resolver/pin logic across three roots — never delete-bug or wholesale restore golden.
- RC3: Tests assert tag/kind/json_key agreement and digest/round-trip — not mere file existence.
- RC5: Expected layout invariants live in test code + instruction field names, not golden under environment/.
- RC6: Instruction symptoms-only — no fold_a / sieve_b / emit_c / plugin version numbers.
- RC7: solve.sh substantive LOC ≥ 30 across three language roots.
- CR1/CR2: Construction manifest symbols verbatim; 2+2+2 flip split under concentration_cap 0.5.
- CR7/GX9: JSON field names in instruction; exact per-slot values only discoverable at runtime.
- CR8: xlink orchestration must not reference more than 2 fix-path symbols from one file.
- Static: allow_internet=false, .dockerignore, absolute paths, category build-and-dependency-management.

### Initial Draft Commitments

- `tasks/wire-contract-codegen-unify/task.toml`
- `tasks/wire-contract-codegen-unify/instruction.md`
- `tasks/wire-contract-codegen-unify/output_contract.toml`
- `tasks/wire-contract-codegen-unify/tests/test.sh`
- `tasks/wire-contract-codegen-unify/tests/test_outputs.py`
- `tasks/wire-contract-codegen-unify/solution/solve.sh`
- `tasks/wire-contract-codegen-unify/environment/Dockerfile`
- `tasks/wire-contract-codegen-unify/environment/.dockerignore`
- `tasks/wire-contract-codegen-unify/environment/idl/events.proto`
- `tasks/wire-contract-codegen-unify/environment/idl/options.proto`
- `tasks/wire-contract-codegen-unify/environment/data/registry/yanks.jsonl`
- `tasks/wire-contract-codegen-unify/environment/data/registry/mirror_index.jsonl`
- `tasks/wire-contract-codegen-unify/environment/data/registry/plugin_meta.json`
- `tasks/wire-contract-codegen-unify/environment/data/state/runtime.json`
- `tasks/wire-contract-codegen-unify/environment/config/l7/k9.toml`
- `tasks/wire-contract-codegen-unify/environment/config/l7/m2.toml`
- `tasks/wire-contract-codegen-unify/environment/config/l7/p7.toml`
- `tasks/wire-contract-codegen-unify/environment/ops/runbooks/xlink_usage.md`
- `tasks/wire-contract-codegen-unify/environment/ops/runbooks/lane_health.md`
- `tasks/wire-contract-codegen-unify/environment/ops/scripts/digest_util.py`
- `tasks/wire-contract-codegen-unify/environment/gox/go.mod`
- `tasks/wire-contract-codegen-unify/environment/gox/go.sum`
- `tasks/wire-contract-codegen-unify/environment/gox/cmd/lanehealth/main.go`
- `tasks/wire-contract-codegen-unify/environment/gox/cmd/foldctl/main.go`
- `tasks/wire-contract-codegen-unify/environment/gox/internal/k3/fold_a.go`
- `tasks/wire-contract-codegen-unify/environment/gox/internal/k3/skim_fold.go`
- `tasks/wire-contract-codegen-unify/environment/gox/pkg/frame/doc.go`
- `tasks/wire-contract-codegen-unify/environment/rsx/Cargo.toml`
- `tasks/wire-contract-codegen-unify/environment/rsx/Cargo.lock`
- `tasks/wire-contract-codegen-unify/environment/rsx/core/Cargo.toml`
- `tasks/wire-contract-codegen-unify/environment/rsx/core/src/lib.rs`
- `tasks/wire-contract-codegen-unify/environment/rsx/core/src/sieve_b.rs`
- `tasks/wire-contract-codegen-unify/environment/rsx/core/src/skim_sieve.rs`
- `tasks/wire-contract-codegen-unify/environment/rsx/sievectl/Cargo.toml`
- `tasks/wire-contract-codegen-unify/environment/rsx/sievectl/src/main.rs`
- `tasks/wire-contract-codegen-unify/environment/jvx/pom.xml`
- `tasks/wire-contract-codegen-unify/environment/jvx/src/main/java/org/lab/p7/EmitC.java`
- `tasks/wire-contract-codegen-unify/environment/jvx/src/main/java/org/lab/p7/SkimEmit.java`
- `tasks/wire-contract-codegen-unify/environment/jvx/src/main/java/org/lab/p7/LaneMain.java`
- `tasks/wire-contract-codegen-unify/environment/xlink/go.mod`
- `tasks/wire-contract-codegen-unify/environment/xlink/cmd/xlink/main.go`
- `tasks/wire-contract-codegen-unify/environment/xlink/internal/m4/probe.go`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: environment/gox/internal/k3/fold_a.go
  symbol: FoldA
  kind: function
  signature: func FoldA(a string, b string) ([]Row, error)
  purpose: Resolves Go codegen pin against yank/mirror and emits binary tag/oneof rows.

- path: environment/rsx/core/src/sieve_b.rs
  symbol: sieve_b
  kind: function
  signature: pub fn sieve_b(a: &str, b: &str) -> Result<Vec<Row>, String>
  purpose: Resolves Rust prost/build.rs pin path and emits optional-presence and json_key rows.

- path: environment/jvx/src/main/java/org/lab/p7/EmitC.java
  symbol: EmitC
  kind: class
  signature: public static List<Row> apply(String a, String b)
  purpose: Resolves Maven protobuf plugin pin and emits java layout rows plus digest material.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: environment/gox/internal/k3/fold_a.go
    controls_tests: [test_k3_zircon, test_m8_obsidian]
  - id: B
    path: environment/rsx/core/src/sieve_b.rs
    controls_tests: [test_p2_garnet, test_q7_topaz]
  - id: C
    path: environment/jvx/src/main/java/org/lab/p7/EmitC.java
    controls_tests: [test_r1_onyx, test_t6_amber]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: environment/gox/internal/k3/skim_fold.go
  kind: helper
  rhymes_with: FoldA
  non_fix_purpose: Mirror-preferred plugin reader used by lanehealth diagnostics; keeps local Go compile green without cross-lang tag ownership.

- path: environment/rsx/core/src/skim_sieve.rs
  kind: helper
  rhymes_with: sieve_b
  non_fix_purpose: Yank-window skim helper for sievectl diagnostics; does not honor optional-presence vs json_key split.

- path: environment/jvx/src/main/java/org/lab/p7/SkimEmit.java
  kind: helper
  rhymes_with: EmitC
  non_fix_purpose: Maven BOM skim used by Java lanehealth; emits locally consistent rows that ignore mirror yank winners.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [monorepo, stubs, IDL, Go, Rust, Java, build, pipelines, registry, yank, mirror, pin, language, health, check, integration, binaries, wire, field, numbers, oneof, arms, optional, presence, JSON, names, stub, sets, codegen, graphs, contract, verifier, integrity, ledger, bytes, output, schema_version, contract_digest, layout, arrays, go_rows, rust_rows, java_rows, slot, tag, kind, json_key, entries, Binary, round-trip, probes, status, lane, tool, lanehealth, unification, xlink, report]
```
