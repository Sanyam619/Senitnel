### Decision
GO — Attempt 1. Build-unification only (no source repair/debug of service logic): three language codegen pin/resolver roots must converge on one wire ABI under yank+mirror pressure; false-green per-language healthchecks; opaque fold/sieve/emit symbols.

### Metadata
- Task name: wire-contract-codegen-unify
- Title: Wire Contract Codegen Unify
- Category: build-and-dependency-management
- Languages: ["Go", "Rust", "Java"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: ["tool_specific"]
- Tags: ["protobuf", "codegen", "gomod", "cargo", "maven", "wire-abi"]
- Milestones: 0

### Discovery budget
- Discovery: A yanked transitive codegen plugin still resolves as the effective owner of binary field tags for one language via the mirror overlay, even when that language's direct pin looks correct.
  Planned location: environment/data/registry/mirror_index.jsonl + environment/gox/internal/k3/fold_a.go
  Why instruction must not reveal it: Naming the yanked-transitive-wins-via-mirror rule collapses diagnose into a one-line pin fix.

- Discovery: Binary wire tags and JSON name options are owned by different plugin pins across languages; aligning only the binary path leaves JSON round-trips and json_key rows divergent.
  Planned location: environment/rsx/core/src/sieve_b.rs and environment/jvx/src/main/java/org/lab/p7/EmitC.java
  Why instruction must not reveal it: Stating the dual-path ownership turns the task into a checklist of two knobs.

- Discovery: lanehealth only compiles each language alone and never compares cross-language layouts; xlink is the only probe that surfaces ABI disagreement.
  Planned location: environment/gox/cmd/lanehealth/main.go and environment/xlink/cmd/xlink/main.go
  Why instruction must not reveal it: Calling lanehealth false-green removes the discoverability tax that makes per-language green builds misleading.

### Anti-trivialization verdict
| # | Check | Verdict | Reasoning |
|---|-------|---------|-----------|
| 1 | Disclosure-collapse | PASS | Symptoms-only; omits which plugin owns which layout dimension |
| 2 | Hidden-instance | PASS | Fixed monorepo topology, not hunt-one-file |
| 3 | Single-artifact repair | PASS | Go+Rust+Java pin/resolver roots must all converge |
| 4 | Generalization | PASS | Tests cover tags, oneof, optional, json_key, digest, round-trip |
| 5 | Prompt-honesty | PASS | Honest prompt does not name FoldA/sieve_b/EmitC |
| 6 | Cheating-vs-difficulty | PASS | Difficulty is cross-lang wire ABI under yank/mirror |
| 7 | Mechanical-fix filter | PASS | Not a deps/timeout task |
| 8 | Localized-fix | PASS | Fix spans gox/, rsx/, jvx/ |
| 9 | Oracle-locality | PASS | Oracle edits three language roots, not one file replace |
| 10 | Small declarative-cluster | PASS | Not a single manifest flip |
| 11 | Grep-collapse | PASS | Opaque FoldA/sieve_b/EmitC |
| 12 | Pre-factored-helper | PASS | Helpers do not mirror unify_wire / fix_codegen |
| 13 | Recipe-discount | PASS | Not textbook single-BOM or single-go.mod MVS |
| 14 | Security-aura discount | PASS | Category is build-and-dependency-management |
| 15 | Orthogonal-checklist | PASS | Binary vs JSON ownership and mirror yank couple |
| 16 | Harness-discount | PASS | Single-container realism only |
| 17 | One-pass solvability | PASS | lanehealth green + decoy skim_* mislead one-pass greps |
| 18 | Hard-only gate | PASS | Three codegen pipelines × yank/mirror × dual path |
| 19 | Discovery budget test | PASS | Three named discoveries |
| 20 | Instruction specificity | PASS | symptoms-only |
| 21 | Topology distribution | PASS | Three topologies with ≥3 locations each |

### Topology enumeration (3 candidate fix topologies)
1. **Pin-align topology** — Coordinate `fold_a.go` Go pin resolution, `sieve_b.rs` Rust prost/build.rs pin, and `EmitC.java` Maven plugin pin so all three emit the same tag/kind/json_key rows. No single language pin is sufficient because tests require cross-array agreement.
2. **Regen-authority topology** — Treat IDL as immutable and force each language's codegen ownership function to re-derive layout from the shared registry authority (yank+mirror), coordinating the same three locations. Fixing only regen order in xlink fails because layouts still come from skewed resolvers.
3. **Mirror-winner topology** — Make each resolver reject yanked-transitive mirror winners consistently, coordinating Go fold, Rust sieve, and Java emit against `mirror_index.jsonl`. Aligning only the mirror file without updating the three consumers leaves lanehealth green and xlink red.

### Rubric axes
- Verifiable: PASS — Deterministic JSON layouts, digests, and probe status.
- Well-specified: PASS — Output path and field names stated; outcomes observable.
- Solvable: PASS — Expert can unify pins across three roots in a few hours.
- Difficult: PASS — Cross-lang codegen ABI under yank/mirror and dual binary/JSON ownership.
- Interesting: PASS — Real monorepo wire-contract cutovers pay for this work.
- Outcome-verified: PASS — Grades layouts/probes, not process.

### Hardness axes
- Discover: PASS — Solver must learn which plugin pin owns tags vs json_key and that mirror yank winners override direct pins.
- Synthesize: PASS — Go MVS-like pins, Rust prost/build.rs, and Maven BOM must converge with registry fixtures.
- Diagnose: PASS — Instruction reports per-language green builds and cross-lang disagreement, not causes.
- Navigate coupling: PASS — Fixing one language or only binary tags breaks distant JSON/digest/round-trip invariants.
- Reason beyond training: PASS — Not Go-MVS-only or Java-BOM-only; three codegen pipelines under yank/mirror.

### Instruction completeness test
No — instruction.md alone does not identify which resolver owns which layout dimension, that lanehealth is shallow, or that a yanked transitive still wins via mirror. Solver must engage gox/rsx/jvx and registry fixtures.

## Reviewer Appendix

### Implementation plan
Environment ships a shared IDL, a local registry (yanks + mirror overlays + plugin meta), and three language build trees. Initial FoldA/sieve_b/EmitC implementations follow decoy-local or yanked-transitive pins so each language compiles alone while layouts disagree. Agent must rewrite those three opaque resolvers (and any necessary pin files they read) so xlink emits an agreed contract. Oracle patches the three fix-path files and rebuilds CLIs; no service business-logic debug. Decoy skim_* helpers keep diagnostic paths green.

### Proposed file inventory
Matches Initial Draft Commitments in the authoring spec (≥25 non-Docker environment files): idl/, data/registry/, config/l7/, ops/, gox/, rsx/, jvx/, xlink/.

### Oracle notes
solve.sh patches FoldA, sieve_b, and EmitC to resolve against the non-yanked mirror authority for binary tags, optional presence, and json_key consistently; rebuilds foldctl/sievectl/java lane + xlink; runs xlink report to /output/wire-unify.json. Does not rewrite IDL or registry fixtures. ≥30 substantive LOC.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
Edit three opaque resolver bodies across Go/Rust/Java so each honors the same yank/mirror ownership rules for tags, oneof, optional, and json_key; rebuild and emit report.

Likely editable frontier:
- environment/gox/internal/k3/fold_a.go
- environment/rsx/core/src/sieve_b.rs
- environment/jvx/src/main/java/org/lab/p7/EmitC.java

Requirement-to-file map:
- binary tag / oneof agreement -> fold_a.go
- optional presence / json_key agreement -> sieve_b.rs
- digest / round-trip / java layout close -> EmitC.java

Oracle estimated complexity: 80–150 lines non-boilerplate across three roots + rebuild glue

Red flags:
- none if decoys and lanehealth stay genuinely shallow

Residual hardness:
After the tree is visible, solver still must recover dual-path ownership and yanked-transitive mirror winners from runtime/registry behavior.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
monorepo, stubs, IDL, Go, Rust, Java, build, pipelines, registry, yank, mirror, pin, language, health, check, integration, binaries, wire, field, numbers, oneof, arms, optional, presence, JSON, names, stub, sets, codegen, graphs, contract, verifier, integrity, ledger, bytes, output, schema_version, contract_digest, layout, arrays, go_rows, rust_rows, java_rows, slot, tag, kind, json_key, entries, Binary, round-trip, probes, status, lane, tool, lanehealth, unification, xlink, report

**Renames during drafting:**
- `unify_wire` → `FoldA`: avoided wire/unify nouns on fix path
- `fix_optional` → `sieve_b`: avoided optional/presence nouns
- `emit_digest` → `EmitC`: avoided digest/report telegraphing

**Test names audited:**
- test_k3_zircon
- test_m8_obsidian
- test_p2_garnet
- test_q7_topaz
- test_r1_onyx
- test_t6_amber

**Concentration math:**
- Total tests across flipping_point_contract: 6
- Per location:
  - L1 (fold_a.go): 2/6 = 0.333333
  - L2 (sieve_b.rs): 2/6 = 0.333333
  - L3 (EmitC.java): 2/6 = 0.333333
- Cap: 0.5. Max ratio observed: 0.333333. Status: PASS

### Per-test feasibility pre-check
- Test: test_k3_zircon — Checks: tag agreement — Valid approaches: 2+ — Chain-dependent: no — Feasibility: LOW
- Test: test_m8_obsidian — Checks: oneof kind agreement — Valid approaches: 2+ — Chain-dependent: no — Feasibility: LOW
- Test: test_p2_garnet — Checks: optional presence agreement — Valid approaches: 2+ — Chain-dependent: no — Feasibility: LOW
- Test: test_q7_topaz — Checks: json_key agreement — Valid approaches: 2+ — Chain-dependent: no — Feasibility: LOW
- Test: test_r1_onyx — Checks: contract_digest — Valid approaches: 2+ — Chain-dependent: no (needs coherent layouts but not a prior test) — Feasibility: LOW
- Test: test_t6_amber — Checks: schema + round-trips + fixture integrity — Valid approaches: 2+ — Chain-dependent: no — Feasibility: LOW
