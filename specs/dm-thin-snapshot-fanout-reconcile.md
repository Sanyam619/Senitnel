### Decision
GO — Attempt 1. Hard system-administration reconcile: sealed activation journal undoes ledger-only edits; origin-vs-tip preference coupled to epoch; decoy stamp-match bait; concurrent lease races. Go orchestrator + C ioctl helper. No repair/debug framing — primary activity is thin-pool fanout state reconciliation after mid-roll crash.

### Metadata
- version: 2
- Task name: dm-thin-snapshot-fanout-reconcile
- Title: Thin Snapshot Fanout
- Category: system-administration
- Languages: ["go", "c"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["device-mapper", "thin-pool", "snapshot", "activation", "leases", "state-reconciliation"]
- Milestones: 0

## Authoring Brief
This file is the only drafting input for Step 2b. Do NOT include reviewer-only analysis, oracle steps, exact patch sites, or an exhaustive file tree here.

### Public contract
A lab thin pool under `/data/pool` fans snapshots into per-drill volumes. After a mid-roll crash, `/output/drills/<name>/payload.bin` is wrong or empty and `/output/fanout-report.json` is missing or inconsistent. Surface checks under `/opt/pool/bin/` may still print OK. The agent must reconcile pool state so every drill named in `/opt/pool/config/drill.roster` materializes a correct `payload.bin` and a coherent report. The report is JSON with a `drills` array; each entry has `name`, `tip_id`, `origin_kind`, and `order_index`. `origin_kind` is either `live` or `cow`. Shelves under `/data/pool/origins/` must stay byte-identical. A second materialize pass and two concurrent materialize jobs on the same roster must leave matching payloads and no torn lease files under `/data/pool/leases/`. Tooling and sources live under `/opt/pool/`.

### Failure topology
Symptoms cross four authority layers: sealed activation journal (generation-capped), mutable ledger/meta that disagree after partial roll, origin vs snapshot tip preference bound to epoch floors, and per-tip leases under concurrent restore. Surface `dmhealth` only checks roster presence and path existence. Decoy origin blobs stamp-match live origins so naive stamp-scan materialization prefers them when seal handling is wrong. Preflight that correctly honors the seal wipes naive ledger edits on every materialize.

### Environment shape
Go module under `/opt/pool/src` with opaque packages for journal fold, haul/materialize, lease hold, report emit, catalog, and stamp helpers. C shared helper for tip/origin preference ioctl simulation. Config (seal + roster), pool fixtures (journal, origins, decoys, snaps, leases, meta), ops wrappers, layout docs that describe normal layout only (no repair checklist or numeric answer memos). Surface `dmhealth` binary that false-greens.

### Required artifacts
Standard layout: `instruction.md`, `task.toml`, `output_contract.toml`, `environment/` (Dockerfile, `.dockerignore`, Go+C sources, fixtures, ops), `solution/solve.sh`, `tests/{test.sh,test_outputs.py}`. Environment must have 20+ substantive files. No golden payloads under environment. Expected digests live only in tests.

### Test plan
- `test_k3_zircon`: alpha drill payload matches tip-authoritative bytes after partial-roll tip disagreement; multiple approaches; independent.
- `test_m8_obsidian`: beta drill uses live origin when tip epoch is below floor; multiple approaches; independent.
- `test_p2_garnet`: gamma drill rejects stamp-matching decoy; multiple approaches; independent.
- `test_q7_topaz`: report drills array covers roster with correct tip_id / origin_kind / order_index; multiple approaches; independent.
- `test_r1_onyx`: origins shelf checksums unchanged; multiple approaches; independent.
- `test_t6_amber`: second materialize pass is byte-identical; multiple approaches; independent.
- `test_v4_jade`: concurrent double materialize leaves clean leases and matching payloads; multiple approaches; independent.
- `test_w9_quartz`: naive ledger tip rewrite is undone by sealed preflight on next materialize; multiple approaches; guards authority coupling.
- `test_x2_flint`: surface dmhealth OK does not imply correct payloads (payloads still required); multiple approaches; independent.

### Drafting guardrails
Symptoms-only instruction: no “fix ioctl”, no seal-generation algorithm, no epoch-floor formula, no named fix modules. Fix-path symbols opaque (`phase_k`, `phase_m`, `op_q`). Docs must not enumerate mutable knobs or answer-shaped tip ids. Tests re-invoke materialize for authority coupling; EXPECTED only in test code.

### Triviality Ledger
- Editing only ledger/meta tip pointers fails because sealed fold preflight rewrites them from the journal on every materialize.
- Preferring stamp-matched decoy origins greens local stamp checks but fails gamma payload and origin_kind assertions.
- Fixing only Go haul without C preference still emits wrong live/cow bytes on epoch-boundary drills.
- Fixing preference without clearing the decoy shelf substitution still materializes stamp-matched decoy bytes for gamma.
- Skipping lease serialization passes sequential payload checks but fails concurrent double-materialize and second-pass lease cleanliness.

### Per-gate Pitfall Inventory
- RC1/RC7: oracle must rewrite substantive Go+C bodies (≥80 LOC semantic), not delete flags.
- RC6: instruction stays symptoms-only (no seal formula, no epoch floor numbers as recipes).
- RC3/RC5: tests assert payload digests and report fields computed in test code, not env goldens.
- GX9/GX10: do not recite per-drill digests or contradictory live/cow polarity in one sentence.
- CR7: fix-path symbols avoid instruction nouns; tests use opaque mineral names.
- Static: `allow_internet = false`, pinned Dockerfile digests, `.dockerignore`, anonymous author, 20+ env files.

### Initial Draft Commitments
- `instruction.md`
- `task.toml`
- `output_contract.toml`
- `environment/.dockerignore`
- `environment/Dockerfile`
- `environment/Makefile`
- `environment/go.mod`
- `environment/cmd/matfan/main.go`
- `environment/cmd/dmhealth/main.go`
- `environment/internal/fold/fold.go`
- `environment/internal/hold/hold.go`
- `environment/internal/pull/pull.go`
- `environment/internal/skim/skim.go`
- `environment/internal/emit/emit.go`
- `environment/internal/catalog/catalog.go`
- `environment/internal/stamp/stamp.go`
- `environment/internal/wire/wire.go`
- `environment/c/ioctl_a.h`
- `environment/c/ioctl_a.c`
- `environment/c/ioctl_b.c`
- `environment/c/ioctl_b.h`
- `environment/config/pool.seal`
- `environment/config/drill.roster`
- `environment/docs/layout.md`
- `environment/docs/operator-notes.md`
- `environment/ops/run_materialize.sh`
- `environment/ops/check_surface.sh`
- `environment/data/build_fixtures.py`
- `environment/data/pool/journal/act.wal`
- `environment/data/pool/meta/activation.toml`
- `environment/data/pool/origins/o_alpha.bin`
- `environment/data/pool/origins/o_beta.bin`
- `environment/data/pool/origins/o_gamma.bin`
- `environment/data/pool/decoys/d_gamma.bin`
- `environment/data/pool/snaps/t_alpha.meta`
- `environment/data/pool/snaps/t_beta.meta`
- `environment/data/pool/snaps/t_gamma.meta`
- `environment/data/pool/snaps/t_delta.meta`
- `environment/data/pool/snaps/payloads/t_alpha.bin`
- `environment/data/pool/snaps/payloads/t_beta.bin`
- `environment/data/pool/snaps/payloads/t_gamma.bin`
- `environment/data/pool/snaps/payloads/t_delta.bin`
- `environment/data/pool/leases/.keep`
- `solution/solve.sh`
- `tests/test.sh`
- `tests/test_outputs.py`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table
```yaml
- path: internal/fold/fold.go
  symbol: phase_k
  kind: function
  signature: func phase_k(root string, capGen uint64) error
  purpose: replays capped journal lines into runtime activation state and clears disagreeing meta rows
- path: internal/hold/hold.go
  symbol: phase_m
  kind: function
  signature: func phase_m(leaseDir string, key string) (func() error, error)
  purpose: takes an exclusive lease for one tip key and returns a release closure
- path: c/ioctl_a.c
  symbol: op_q
  kind: function
  signature: int op_q(const uint8_t *a, size_t an, const uint8_t *b, size_t bn, uint32_t e, uint32_t f, uint8_t *out, size_t *outn)
  purpose: selects between two candidate byte buffers using epoch compare inputs
- path: internal/skim/skim.go
  symbol: shelf_x
  kind: function
  signature: func shelf_x(root, drill, origin string, live []byte) ([]byte, error)
  purpose: returns the live-shelf candidate bytes for the preference helper
```

#### flipping_point_contract
```yaml
locations:
  - id: A
    path: internal/fold/fold.go
    controls_tests: [test_k3_zircon, test_q7_topaz, test_w9_quartz]
  - id: B
    path: c/ioctl_a.c
    controls_tests: [test_m8_obsidian, test_p2_garnet, test_x2_flint]
  - id: C
    path: internal/hold/hold.go
    controls_tests: [test_r1_onyx, test_t6_amber, test_v4_jade]
  - id: D
    path: internal/skim/skim.go
    controls_tests: [test_p2_garnet]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest
```yaml
- path: internal/catalog/catalog.go
  kind: module
  rhymes_with: phase_k
  non_fix_purpose: lists roster names and counts snaps for inventory commands
- path: c/ioctl_b.c
  kind: helper
  rhymes_with: op_q
  non_fix_purpose: checksums a buffer for surface diagnostics without preference logic
- path: internal/stamp/stamp.go
  kind: helper
  rhymes_with: phase_m
  non_fix_purpose: computes 8-byte stamp prefixes used by dmhealth path presence checks
```

#### code_forbidden_tokens
```yaml
code_forbidden_tokens: [lab, thin, pool, fans, snapshots, per-drill, volumes, crash, mid-roll, drills, payloads, fanout-report, surface, checks, roster, materialize, report, drills, array, name, tip_id, origin_kind, order_index, live, cow, shelves, origins, lease, leases, tooling, sources, correct, coherent, matching, torn]
```
