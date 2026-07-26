### Decision
GO — Attempt 1. Go batch reconciliation across `anchor/`, `propagate/`, and `gate/` subsystem roots with sterile-processing fixtures and property-based verifier checks.

### Metadata
- version: 2
- Task name: hospital-sterile-tray-recall-reconciliation
- Title: Sterile Tray Recall
- Category: data-processing
- Languages: ["go", "bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["go", "healthcare", "sterile-processing", "recall", "traceability", "compliance"]
- Milestones: 0

## Authoring Brief

### Public contract
Go batch at `/opt/csp/scripts/run-case.sh --case <name> --root /data/fixtures` ingests scan feeds, cycle boards, lot notices, OR manifests, and quarantine snapshots; writes `quarantine_ledger.jsonl`, `tray_disposition.json`, and `recall_audit.tsv` under `/data/out/<case>/`. Cases `case_c0412`–`case_c0416`.

### Failure topology
Symptoms span four coupled clusters: notice-to-case propagation (recalled lots still releasable), zone-wide over-blocking (clean trays blocked), autoclave chronology (post-close scans read sterile), split-set parent/child drift, and rerun inflation in audit counts. No single feed is authoritative; reconciliation must weave scan timing, cycle windows, notice effective times, set catalog edges, and quarantine snapshots.

### Environment shape
`/opt/csp` Go module with `anchor/` (scan-to-cycle alignment), `propagate/` (notice activation and zone pick), `gate/` (disposition mux), `internal/ingest/*` readers, `internal/core/` orchestration, fixture builder under `/data/fixtures/cases/`, verifier harness in `tests/`.

### Required artifacts
Standard TB3 layout: `instruction.md`, `task.toml`, `output_contract.toml`, `environment/` (35+ files), `solution/solve.sh`, `tests/{test.sh,test_outputs.py}`, `construction_manifest.json`.

### Test plan
Nine tests: recall hold, clean release, sterile gap, child propagation, rerun stability, audit counts, contract fields, dual-tray hidden case. Each independently passable; expected values embedded in test code.

### Drafting guardrails
Symptoms-only instruction; opaque fix-path symbols; oracle distributed across `anchor/`, `propagate/`, `gate/`; no golden answers in environment.

### Triviality Ledger
- Naive zone-wide block passes recall cases but fails clean-tray release (`gate/mux_q` + `holdpick` coupling).
- Fixing only notice curve passes direct recall but fails split-set child (`linkgate` parent walk).
- Fixing only cycle fold passes chronology but leaves audit inflation (`rankgate` rerun guard).

### Per-gate Pitfall Inventory
- RC6/GX6: instruction uses observation clauses, not causal chains.
- CR8: `rowgate.DecideQ` concentrates disposition logic away from orchestrator.
- CR1: `PickL` renamed `FetchZ` to avoid `lot` substring collision.
- GX4: broken `linkgate` stubbed; oracle rewrites working body.

### Initial Draft Commitments
- `tasks/hospital-sterile-tray-recall-reconciliation/{instruction.md,task.toml,output_contract.toml,construction_manifest.json}`
- `environment/{Dockerfile,.dockerignore,go.mod,cmd/cspd/main.go,config/site.toml,scripts/*}`
- `environment/{anchor,propagate,gate,internal}/**`
- `solution/solve.sh`, `tests/{test.sh,test_outputs.py}`
- `scripts/gen_hospital_sterile_tray_recall.py`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

See `tasks/hospital-sterile-tray-recall-reconciliation/construction_manifest.json`.
