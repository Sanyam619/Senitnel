### Decision
GO — Attempt 1. Dual-language (Rust + Go) promotion-replay drift task with fix locus split across hop binding, subject resolution, and epoch frontier evaluation; security-relevant consistency work, not checklist hardening.

### Metadata
- version: 2
- Task name: container-attestation-drift-ledger
- Title: Attestation Drift Ledger
- Category: security
- Languages: ["Rust", "Go", "bash"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: ["containers", "attestation", "supply-chain", "rust", "go", "security"]
- Milestones: 0

## Authoring Brief
This file is the only drafting input for Step 2b. Do NOT include reviewer-only analysis, oracle steps, exact patch sites, or an exhaustive file tree here.

### Public contract

A single-container lab under `/app` replays a promotion journal for several container images. After replay, the digest ledger, attestation checks, and runtime policy gate disagree on which images may run. Surface status can look healthy while admit decisions and ledger rows diverge across stages.

**Symptoms the agent sees (instruction.md level):**
- Replaying the promotion journal leaves attestations disagreeing with the digest ledger and the runtime policy gate.
- Some promoted images are admitted while ledger rows mark them stale; others are denied even though manifests and attestation files are present.
- Surface status can look healthy while the three views diverge across stages.

**Required outcomes:**
- `/output/drift-report.json` exists with integer `version` `1`.
- Array `images`: each object has string `ref`, string `digest`, string `stage`, boolean `admit`.
- Array `mismatches`: each object has string `ref` and string `reason` (empty after a correct repair).
- Fresh replay yields one consistent admit set across ledger, attestation checks, and policy gate for all fixture images.
- Files under `/data/fixtures/anchors/` unchanged (checksum guard in tests).

**Constraints:**
- `[environment] allow_internet = false`; verifier deps in Dockerfile.
- No multi-container layout; no UI building.
- Agent repairs Rust and Go sources and reruns bundled CLIs; do not ship golden answers under `environment/`.

### Failure topology

Three symptom clusters interact. First, promotion hops record the wrong content identity: journal `dest` fields often hold an OCI index digest after tag push, while the lab’s arch filter expects the platform-manifest child. Second, attestation subject checks verify the index digest (or the source-registry subject) without walking to the same platform child the ledger tracks, so admit/deny flips independently of ledger rows. Third, after replay renumbers epochs, the policy gate still compares string stage labels from the pre-replay roots file, admitting stale rows while denying current ones.

The task is hard because no single tool documents the full identity rule. Surface status can stay green (journal line counts, header dumps) while the three views diverge. Local fixes break distant invariants: correcting only the ledger leaves false admits; correcting only subjects leaves epoch-stale admits; correcting only the frontier leaves digest mismatches in the report.

### Environment shape

- `environment/Dockerfile` + `.dockerignore` — Rust + Go toolchains, python3/pytest, offline.
- `environment/crates/alpha/` — Rust digest hop/store/journal library; `cmd/digctl` CLI.
- `environment/go/wire/` — attestation subject/bundle helpers; `go/eval/` frontier and join.
- `environment/go/cmd/{provcheck,polgate,replayctl}/` — opaque CLIs for check, gate, replay.
- `environment/scripts/` — surface-status and replay-stub wrappers (false-green path lives here).
- `environment/config/` — lab paths and arch filter only.
- `environment/data/journal/`, `data/store/`, `data/attest/`, `data/policy/`, `data/fixtures/anchors/` — seeded promotion state.

### Required artifacts

- Standard task layout: `instruction.md`, `task.toml`, `output_contract.toml`, `environment/**`, `solution/solve.sh`, `tests/test.sh`, `tests/test_outputs.py`.
- 25+ meaningful files under `environment/` excluding Dockerfile/docker-compose (see Initial Draft Commitments).
- Oracle patches substantive logic in the three fix-path files (≥30 non-boilerplate LOC across the frontier).

### Test plan

- `test_k4_shape_bundle` — Report schema and required image refs present; multiple valid repair approaches exist; not chain-dependent on oracle path.
- `test_m8_slot_matrix` — Per-image `admit` booleans match converged expectation for fixture set; 2+ approaches; depends on subject+frontier agreement.
- `test_p2_hash_align` — Per-image `digest` equals platform-manifest content digest (computed in tests from store fixtures); 2+ approaches; depends on hop binding.
- `test_r6_delta_list` — `mismatches` empty after repair; 2+ approaches; depends on three-view agreement.
- `test_t1_tier_frontier` — `stage` values and admit set respect post-replay frontier; 2+ approaches; depends on hop+epoch coupling.
- `test_w3_cross_agree` — Re-running replay+report yields identical admit set; ledger/check/gate views agree; depends on full fix.

### Drafting guardrails

Instruction stays symptoms-only: disagreeing views and healthy surface status, no algorithm names, no fix-file pointers, no numeric epoch recipe. Use construction-manifest symbols verbatim (`op_a`, `fold_b`, `phase_c`). Do not embed instruction nouns in fix-path symbols, parameters, or test names. Decoys (`scan.rs`, `probe.go`) must do real non-fix work. Do not hide the operational contract in environment READMEs. Expected digests/admits live in test code, not golden files under `environment/`.

### Triviality Ledger

- Naive trust of journal `dest` index digests passes surface status but fails `test_p2_hash_align` because platform children differ.
- Verifying attestation subjects at index level can green a subset of admits but fails `test_m8_slot_matrix` when platform children diverge.
- String stage-label policy compare admits stale rows after renumber and fails `test_t1_tier_frontier` / `test_r6_delta_list`.
- Patching only one of hop / subject / frontier leaves majority of cross-view tests failing (flipping-point contract).
- Copying anchor fixtures over live store fails `test_w3_cross_agree` integrity expectations and does not repair logic.

### Per-gate Pitfall Inventory

- RC1: Oracle must edit substantive Rust/Go logic — not `sed` out BUG markers or restore golden report.
- RC2/CR7: Opaque fix-path names; instruction nouns banned from symbols on the fix path.
- RC3: Tests assert computed digests and admit booleans, not format/existence alone.
- RC4/RC5: No answer-shaped goldens under `environment/`; expectations embedded in tests.
- RC6/GX9/GX10: Symptoms-only instruction; no per-image answer recital; no polarity contradictions in one sentence.
- RC7/GX3: Oracle LOC across three files ≥30 substantive; no heredoc padding.
- CR1/CR2: Follow symbol_table and flipping_point_contract verbatim; concentration ≤0.5.
- CR8: No single driver importing all three fix symbols; distribute CLI entrypoints.
- CR9: Report field names (`version`, `images`, `ref`, `digest`, `stage`, `admit`, `mismatches`, `reason`) appear in instruction.md.
- Static checks: `allow_internet = false`, `.dockerignore` present, absolute `/app` and `/output` paths.

### Initial Draft Commitments

- `instruction.md`
- `task.toml`
- `output_contract.toml`
- `environment/.dockerignore`
- `environment/Dockerfile`
- `environment/Cargo.toml`
- `environment/crates/alpha/Cargo.toml`
- `environment/crates/alpha/src/lib.rs`
- `environment/crates/alpha/src/hop.rs`
- `environment/crates/alpha/src/scan.rs`
- `environment/crates/alpha/src/journal.rs`
- `environment/crates/alpha/src/store.rs`
- `environment/cmd/digctl/main.rs`
- `environment/go.mod`
- `environment/go/wire/subject.go`
- `environment/go/wire/probe.go`
- `environment/go/wire/bundle.go`
- `environment/go/eval/phase.go`
- `environment/go/eval/join.go`
- `environment/go/cmd/provcheck/main.go`
- `environment/go/cmd/polgate/main.go`
- `environment/go/cmd/replayctl/main.go`
- `environment/scripts/status-surface.sh`
- `environment/scripts/replay-stub.sh`
- `environment/config/lab.toml`
- `environment/config/arch-filter.toml`
- `environment/data/fixtures/anchors/manifest.sha256`
- `environment/data/journal/promo-001.jsonl`
- `environment/data/journal/promo-002.jsonl`
- `environment/data/store/img-a/index.json`
- `environment/data/store/img-a/platform.json`
- `environment/data/store/img-b/index.json`
- `environment/data/store/img-b/platform.json`
- `environment/data/store/img-c/index.json`
- `environment/data/store/img-c/platform.json`
- `environment/data/attest/img-a.json`
- `environment/data/attest/img-b.json`
- `environment/data/attest/img-c.json`
- `environment/data/policy/roots.toml`
- `solution/solve.sh`
- `tests/test.sh`
- `tests/test_outputs.py`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: environment/crates/alpha/src/hop.rs
  symbol: op_a
  kind: function
  signature: pub fn op_a(a: &HopIn, b: &ArchSel) -> DigestOut
  purpose: Computes the content digest recorded for one promotion hop.

- path: environment/go/wire/subject.go
  symbol: fold_b
  kind: function
  signature: func fold_b(a string, b string) (string, error)
  purpose: Resolves an attestation subject string to the tracked content digest.

- path: environment/go/eval/phase.go
  symbol: phase_c
  kind: function
  signature: func phase_c(a string, b int64) (bool, error)
  purpose: Returns whether a candidate clears the active frontier check.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: environment/crates/alpha/src/hop.rs
    controls_tests: [test_p2_hash_align, test_t1_tier_frontier]
  - id: B
    path: environment/go/wire/subject.go
    controls_tests: [test_m8_slot_matrix, test_k4_shape_bundle]
  - id: C
    path: environment/go/eval/phase.go
    controls_tests: [test_r6_delta_list, test_w3_cross_agree]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: environment/crates/alpha/src/scan.rs
  kind: helper
  rhymes_with: op_a
  non_fix_purpose: Counts journal lines for surface status; does not bind hop digests.

- path: environment/go/wire/probe.go
  kind: helper
  rhymes_with: fold_b
  non_fix_purpose: Dumps attestation header fields for diagnostics; does not resolve subjects.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [promotion, journal, container, image, attestations, digest, ledger, runtime, policy, gate, images, manifests, surface, status, views, stages, replay, admit, report, mismatches, reason, fixtures, anchors, drift, attestation, rows, stage, ref, files]
```
