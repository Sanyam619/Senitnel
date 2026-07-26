### Decision
GO — Attempt 1. Distributed Go ramp-accounting bugs across temporal alignment, blend normalization, and retention settlement with opaque symbols and 34+ environment files.

### Metadata
- version: 2
- Task name: airport-deicing-fluid-accountability
- Title: Deicing Fluid Accountability
- Category: system-administration
- Languages: ["go", "bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["go", "airport-ops", "deicing", "compliance", "mass-balance", "telemetry"]
- Milestones: 0

## Authoring Brief

### Public contract
A Go batch at `/opt/ramp/scripts/run-shift.sh --shift <name> --root /data/fixtures` ingests six fixture feeds per shift, writes three artifacts under `/data/out/<shift>/`, and must be rebuilt with `go build` under `/opt/ramp`. Outputs: `fluid_ledger.jsonl` (aircraft_id, pad_id, gallons_applied, fluid_code, seq), `runoff_compliance.json` (version, tanks array with tank_id, gallons_captured, headroom_gal, within_permit bool), `truck_utilization_audit.tsv` (truck_id, active_min, gallons_pumped, efficiency_pct). Five shifts `shift_w1206`–`shift_w1210`. Instruction describes symptom clusters only.

### Failure topology
Ledger credits stand windows that do not overlap pump activity while raw truck totals remain plausible. Type IV effective gallons collapse after passing assay feeds. Retention summaries overshoot permitted headroom when cell-band diversion is active. Utilization reruns double-count pump minutes when multiple stand rows overlap a pulse window. Fixes require rediscovering how minute axes are folded across feeds, how assay percent maps to effective volume per fluid code, and how diverted capture splits across retention nodes—each coupling affects downstream mass-balance closure tests.

### Environment shape
`/opt/ramp` hosts a Go module with cmd entrypoint, opaque ingest packages for six feeds, align/blend/settle stages, core orchestrator, io helpers, decoy modules, config, and shell drivers. `/data/fixtures/shifts/<shift>/` holds per-shift CSV/JSON feeds. Tests invoke the batch driver and assert computed ledger, compliance, and utilization values across five shifts including one held-back scenario.

### Required artifacts
Single-step layout: instruction.md, task.toml, output_contract.toml, environment/{Dockerfile,.dockerignore,go.mod,30+ source/config/fixture files}, solution/solve.sh, tests/{test.sh,test_outputs.py}.

### Test plan
- test_h4_stand_window_credit — ledger gallons attach to correct aircraft/pad window on shift_w1206
- test_m2_type4_curve — Type IV effective gallons match oracle after assays on shift_w1207
- test_p9_retention_headroom — diverted cell-band shift keeps primary tank within_permit on shift_w1209
- test_q1_mass_closure — shift_w1208 total applied gallons equals summed truck pulses within tolerance
- test_s7_rerun_stable — two consecutive runs on shift_w1209 produce identical ledger and TSV bytes
- test_w3_hidden_shift — held-back shift_w1210 blocks impossible pad overlap and reports both retention nodes

### Drafting guardrails
Keep instruction symptoms-only; forbid instruction nouns as code symbols on the fix path; distribute bugs across align/blend/settle; embed expected values only in tests; no golden answers under environment/; decoy modules must perform real non-fix work.

### Triviality Ledger

- Naive removal of the minute offset in fold_k alone passes stand-window tests but fails mass-closure because pulses still duplicate across overlapping stand rows until mux_c settlement dedupes utilization.
- Setting curve_b to identity passes Type IV curve test but fails mass-closure because TYPE1 rows still need percent scaling from assay feeds.
- Zeroing diversion in mux_c alone passes retention headroom but fails hidden shift where alternate node must receive diverted gallons.

### Per-gate Pitfall Inventory

- RC1: solve.sh must patch three functions with substantive logic, not wholesale file replacement.
- RC3: every test asserts computed gallons/bools, not existence-only.
- RC6/GX9: instruction must not recite per-shift expected gallon totals.
- CR7: fold_k, curve_b, mux_c must not appear as words in instruction.md.
- GX3: oracle solve.sh must exceed 30 LOC of substantive edits plus rebuild loop.
- Static checks: allow_internet=false, .dockerignore present, verifier deps in Dockerfile only.

### Initial Draft Commitments

- tasks/airport-deicing-fluid-accountability/instruction.md
- tasks/airport-deicing-fluid-accountability/task.toml
- tasks/airport-deicing-fluid-accountability/output_contract.toml
- tasks/airport-deicing-fluid-accountability/environment/.dockerignore
- tasks/airport-deicing-fluid-accountability/environment/Dockerfile
- tasks/airport-deicing-fluid-accountability/environment/go.mod
- tasks/airport-deicing-fluid-accountability/environment/cmd/rampd/main.go
- tasks/airport-deicing-fluid-accountability/environment/config/site.toml
- tasks/airport-deicing-fluid-accountability/environment/scripts/run-shift.sh
- tasks/airport-deicing-fluid-accountability/environment/scripts/build_fixtures.sh
- tasks/airport-deicing-fluid-accountability/environment/internal/model/types.go
- tasks/airport-deicing-fluid-accountability/environment/internal/io/csvr.go
- tasks/airport-deicing-fluid-accountability/environment/internal/io/jsonw.go
- tasks/airport-deicing-fluid-accountability/environment/internal/io/tsvw.go
- tasks/airport-deicing-fluid-accountability/environment/internal/ingest/pulsefeed/reader.go
- tasks/airport-deicing-fluid-accountability/environment/internal/ingest/pulsefeed/row.go
- tasks/airport-deicing-fluid-accountability/environment/internal/ingest/standboard/reader.go
- tasks/airport-deicing-fluid-accountability/environment/internal/ingest/standboard/row.go
- tasks/airport-deicing-fluid-accountability/environment/internal/ingest/assayfeed/reader.go
- tasks/airport-deicing-fluid-accountability/environment/internal/ingest/assayfeed/row.go
- tasks/airport-deicing-fluid-accountability/environment/internal/ingest/cellband/reader.go
- tasks/airport-deicing-fluid-accountability/environment/internal/ingest/cellband/doc.go
- tasks/airport-deicing-fluid-accountability/environment/internal/ingest/slotboard/reader.go
- tasks/airport-deicing-fluid-accountability/environment/internal/ingest/slotboard/row.go
- tasks/airport-deicing-fluid-accountability/environment/internal/ingest/retaingauge/reader.go
- tasks/airport-deicing-fluid-accountability/environment/internal/ingest/retaingauge/row.go
- tasks/airport-deicing-fluid-accountability/environment/internal/align/clockfold.go
- tasks/airport-deicing-fluid-accountability/environment/internal/align/window.go
- tasks/airport-deicing-fluid-accountability/environment/internal/blend/normcurve.go
- tasks/airport-deicing-fluid-accountability/environment/internal/blend/table.go
- tasks/airport-deicing-fluid-accountability/environment/internal/settle/drainmux.go
- tasks/airport-deicing-fluid-accountability/environment/internal/settle/permit.go
- tasks/airport-deicing-fluid-accountability/environment/internal/core/shiftctx.go
- tasks/airport-deicing-fluid-accountability/environment/internal/core/orchestrator.go
- tasks/airport-deicing-fluid-accountability/environment/internal/core/stage.go
- tasks/airport-deicing-fluid-accountability/environment/internal/decoy/rangefold.go
- tasks/airport-deicing-fluid-accountability/environment/internal/decoy/blendproxy.go
- tasks/airport-deicing-fluid-accountability/solution/solve.sh
- tasks/airport-deicing-fluid-accountability/tests/test.sh
- tasks/airport-deicing-fluid-accountability/tests/test_outputs.py

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: internal/align/clockfold.go
  symbol: fold_k
  kind: function
  signature: func fold_k(a int, b int, c int) int
  purpose: maps pump minute into stand window axis

- path: internal/blend/normcurve.go
  symbol: curve_b
  kind: function
  signature: func curve_b(a float64, b string) float64
  purpose: scales raw gallons by assay percent and fluid code

- path: internal/settle/drainmux.go
  symbol: mux_c
  kind: function
  signature: func mux_c(a float64, b float64, c float64) (float64, float64)
  purpose: splits captured gallons between primary and alternate retention nodes
```

#### flipping_point_contract

```
locations:
  - id: A
    path: internal/align/clockfold.go
    controls_tests: [test_h4_stand_window_credit, test_q1_mass_closure]
  - id: B
    path: internal/blend/normcurve.go
    controls_tests: [test_m2_type4_curve, test_q1_mass_closure]
  - id: C
    path: internal/settle/drainmux.go
    controls_tests: [test_p9_retention_headroom, test_w3_hidden_shift]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: internal/decoy/rangefold.go
  kind: helper
  rhymes_with: fold_k
  non_fix_purpose: computes UI display range labels for stand boards without affecting ledger

- path: internal/decoy/blendproxy.go
  kind: helper
  rhymes_with: curve_b
  non_fix_purpose: proxy table for historical archive blends not used in live shift path
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [regional, hub, ramp, operations, batch, scripts, shift, root, fixtures, truck, pulse, feeds, stand, assignment, boards, mix, assay, weather, cell, bands, departure, slot, retention, gauge, fluid, ledger, runoff, compliance, utilization, audit, winter, policy, pack, volumes, aircraft, totals, rows, credit, windows, types, mixes, reports, lab, summaries, exceed, headroom, diversions, capture, deliveries, permit, reruns, inflate, rebuild, unchanged, names, gallons, pad, type]
```
