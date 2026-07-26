### Decision
GO — Attempt 1. Java cold-chain recall holdback with three distributed fix loci across engine, ingest, and core packages; 38 environment files; symptoms-only instruction.

### Metadata
- version: 2
- Task name: food-recall-cold-chain-holdback
- Title: Food Recall Cold-Chain Holdback
- Category: security
- Languages: ["java", "bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["java", "food-safety", "cold-chain", "recall", "compliance", "batch"]
- Milestones: 0

## Authoring Brief

### Public contract
Run `/opt/distro/scripts/run-cycle.sh --day <distribution-day> --root /data/fixtures` after rebuilding the Java batch processor under `/opt/distro`. For each distribution day the job reads notice feeds, probe feeds, dock feeds, review feeds, signoff feeds, and route maps from `/data/fixtures/days/<day>/`, then writes three artifacts under `/data/out/<day>/`:

1. `holdback_ledger.jsonl` — one JSON object per line with string fields `unit_id`, `state` (`HELD` or `RELEASED`), `reason_code`, and integer `source_day`.
2. `release_auth_audit.json` — JSON object with integer `version` equal to `1` and array `entries`; each entry has string fields `unit_id`, `auth_id`, `decision`, and integer `precedence_rank`.
3. `affected_units.tsv` — header row `unit_id\tstore_id\texposure_class\tqty_cases` followed by data rows sorted by `unit_id`.

The processor must be deterministic across reruns on the same day. Distribution days are named `day_r0412` through `day_r0416` under fixtures.

### Failure topology
After a regional policy rollout the batch job mis-governs physical lot movement. Recalled dairy units still appear releasable where signoff records exist, while unrelated frozen units remain blocked. Temperature-excursion cases that QA already cleared with signoff stay locked. Parent lots split at dock leave sibling child units exposed because lineage propagation is incomplete. Reruns on split-lineage days can inflate affected-unit counts. The failures interact: signoff precedence, probe-window folding, and dock split rebinding must all be correct before containment, clearance, and lineage invariants hold together.

### Environment shape
Maven Java project at `/opt/distro` with packages for configuration loading, CSV/JSON ingest parsers, a rule engine, core unit graph resolution, and output writers. Fixture builder script materializes five distribution days under `/data/fixtures`. Shell wrapper invokes the packaged JAR. Decoy modules mirror fix-path APIs but serve routing validation and legacy export paths.

### Required artifacts
Single-step task: `instruction.md`, `task.toml`, `output_contract.toml`, `environment/{Dockerfile,.dockerignore,pom.xml,config,scripts,src,data}`, `solution/solve.sh`, `tests/{test.sh,test_outputs.py}`.

### Test plan
- `test_k9_active_notice_blocks`: ACTIVE notice unit stays HELD despite GRANT signoff on day_r0412.
- `test_m4_unrelated_release`: unaffected frozen unit RELEASED on day_r0413.
- `test_p2_cleared_excursion`: CLEARED_WITH_SIGNOFF review plus GRANT releases on day_r0414.
- `test_q7_split_lineage`: both dock-split children HELD when parent recalled on day_r0415.
- `test_s3_rerun_stable`: two consecutive runs on day_r0415 produce identical ledger and TSV hashes.
- `test_w2_hidden_day`: day_r0416 containment matches embedded expectations without instruction value recital.

### Drafting guardrails
Instruction stays symptoms-only; no algorithm names, thresholds, or fix locations. Fix-path symbols use opaque names from the construction manifest. Test names avoid instruction nouns. Expected values live in test code only for hidden day_r0416.

### Triviality Ledger
- Global GRANT-wins patch passes signoff cases but fails active-notice containment because PhaseK and ScanC still mis-fold probes and split lineage.
- Widening probe window alone clears excursion holds but leaves split siblings releasable and reruns non-idempotent.
- Mapping only the first dock child blocks one sibling but fails rerun stability and hidden-day cross-store propagation.

### Per-gate Pitfall Inventory
- RC1: solve.sh applies substantive Java patches and rebuilds; not a one-line flag flip.
- RC3: each symptom cluster has a dedicated test with computed domain values.
- RC6: instruction describes observable mis-governance only.
- RC7: oracle patches three classes plus rebuild logic ≥30 LOC.
- GX9: instruction does not recite per-row expected values for test days.
- Static checks: `allow_internet = false`; pytest in Dockerfile; 20+ env files.

### Initial Draft Commitments
- tasks/food-recall-cold-chain-holdback/instruction.md
- tasks/food-recall-cold-chain-holdback/task.toml
- tasks/food-recall-cold-chain-holdback/output_contract.toml
- tasks/food-recall-cold-chain-holdback/environment/Dockerfile
- tasks/food-recall-cold-chain-holdback/environment/.dockerignore
- tasks/food-recall-cold-chain-holdback/environment/pom.xml
- tasks/food-recall-cold-chain-holdback/environment/config/lab.properties
- tasks/food-recall-cold-chain-holdback/environment/scripts/run-cycle.sh
- tasks/food-recall-cold-chain-holdback/environment/scripts/build_fixtures.sh
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/App.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/CycleCmd.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/cfg/PropsLoader.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/cfg/LaneCfg.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/core/k9/Step2.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/core/k9/UnitGraph.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/core/k9/LegacyBind.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/core/r8/Orchestrator.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/core/r8/BatchCtx.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/core/r8/StageGate.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/ingest/m7/ScanC.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/ingest/m7/ProbeRow.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/ingest/m7/CoolFold.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/ingest/d4/DockParser.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/ingest/d4/DockRow.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/ingest/n2/NoticeParser.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/ingest/n2/NoticeRow.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/ingest/s5/SignoffParser.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/ingest/s5/SignoffRow.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/ingest/v6/ReviewParser.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/ingest/v6/ReviewRow.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/ingest/r3/RouteLoader.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/ingest/r3/RouteRow.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/engine/p3/PhaseK.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/engine/p3/RankTable.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/engine/p3/ShadowBlend.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/engine/q1/RulePack.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/engine/q1/EvalCtx.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/model/UnitRef.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/model/OutRow.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/model/AuditEntry.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/io/JsonWriter.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/io/JsonReader.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/io/TsvWriter.java
- tasks/food-recall-cold-chain-holdback/environment/src/main/java/com/distro/io/CsvReader.java
- tasks/food-recall-cold-chain-holdback/solution/solve.sh
- tasks/food-recall-cold-chain-holdback/tests/test.sh
- tasks/food-recall-cold-chain-holdback/tests/test_outputs.py

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table
```
- path: src/main/java/com/distro/engine/p3/PhaseK.java
  symbol: merge_b
  kind: function
  signature: public static String merge_b(com.distro.ingest.n2.NoticeRow a, com.distro.ingest.s5.SignoffRow b, com.distro.ingest.v6.ReviewRow c)
  purpose: Combines notice, signoff, and review rows into HELD or RELEASED state.

- path: src/main/java/com/distro/ingest/m7/ScanC.java
  symbol: fold_a
  kind: function
  signature: public static java.util.List<com.distro.ingest.m7.ProbeRow> fold_a(java.util.List<com.distro.ingest.m7.ProbeRow> rows, long x, long y)
  purpose: Filters probe rows to the in-transit window between hook and dock timestamps.

- path: src/main/java/com/distro/core/k9/Step2.java
  symbol: resolve_d
  kind: function
  signature: public static java.util.List<String> resolve_d(String p, java.util.Map<String, java.util.List<String>> m)
  purpose: Expands a parent unit id to all dock-split child ids.
```

#### flipping_point_contract
```
locations:
  - id: A
    path: src/main/java/com/distro/engine/p3/PhaseK.java
    controls_tests: [test_k9_active_notice_blocks, test_w2_hidden_day]
  - id: B
    path: src/main/java/com/distro/ingest/m7/ScanC.java
    controls_tests: [test_m4_unrelated_release, test_p2_cleared_excursion]
  - id: C
    path: src/main/java/com/distro/core/k9/Step2.java
    controls_tests: [test_q7_split_lineage, test_s3_rerun_stable]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest
```
- path: src/main/java/com/distro/engine/p3/ShadowBlend.java
  kind: module
  rhymes_with: merge_b
  non_fix_purpose: Blends route priority scores for manifest ordering exports.

- path: src/main/java/com/distro/ingest/m7/CoolFold.java
  kind: module
  rhymes_with: fold_a
  non_fix_purpose: Aggregates historical probe medians for archival summaries.

- path: src/main/java/com/distro/core/k9/LegacyBind.java
  kind: module
  rhymes_with: resolve_d
  non_fix_purpose: Maps deprecated warehouse pallet ids for legacy CSV exports.
```

#### code_forbidden_tokens
```
code_forbidden_tokens: [recall, notices, refrigerated, trailer, telemetry, store, receiving, events, QA, temperature, reviews, holdback, release, records, ledger, authorization, audit, trail, affected, inventory, report, dairy, lots, frozen, excursion, policy, rollout, stores, exposure, split, reruns, batch, distribution, regional, grocery, releasable, blocked, cleared, locked, double-count, cold-chain, hold]
```
