### Decision
GO — Attempt 1. Library circulation domain with distributed Java fix topology across merge, RFID fold, and lineage expand modules.

### Metadata
- version: 2
- Task name: rare-book-quarantine-circulation
- Title: Rare Book Quarantine Circulation
- Category: data-processing
- Languages: ["java", "bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["java", "library", "heritage", "circulation", "conservation", "batch"]
- Milestones: 0

## Authoring Brief

### Public contract
Maven Java batch at `/opt/archives/scripts/run-cycle.sh --day <collection-day> --root /data/fixtures` ingests quarantine, covenant, exhibit, RFID, and circulation feeds plus sweep maps. Writes `loan_decision_ledger.jsonl`, `quarantine_exceptions.json`, and `shelf_custody_audit.tsv` under `/data/out/<day>/`. Collection days `day_c0901`–`day_c0905` plus hidden `day_c0906`. Decision states `ALLOW` and `DENIED_LOAN`. Agent rebuilds `/opt/archives` and reruns all days without editing fixtures.

### Failure topology
Symptoms: active quarantine volumes loanable when covenant grants exist; unrelated volumes blocked; exhibit-cleared volumes stay locked; bound-volume siblings circulate when parent flagged; reruns inflate custody counts. Requires tracing precedence across ingest folds, lineage expansion, and merge engine.

### Environment shape
`/opt/archives` Maven tree with opaque packages (`core`, `ingest`, `engine`, `model`, `io`, `cfg`), fixture builder script, `/data/fixtures/days/<day>/` feeds, decoy helpers rhyming with fix modules.

### Required artifacts
Standard single-step layout: instruction.md, task.toml, output_contract.toml, environment/ (20+ files, Dockerfile, .dockerignore), tests/, solution/solve.sh.

### Test plan
- test_k9_active_flag_blocks — quarantine stays denied despite covenant grant (day_c0901)
- test_m4_unrelated_allow — unrelated volume allows with valid sweep (day_c0902)
- test_p2_cleared_exhibit — exhibit-cleared case allows (day_c0903)
- test_q7_split_lineage — split siblings both denied (day_c0904)
- test_s3_rerun_stable — byte-stable rerun (day_c0904)
- test_w2_hidden_day — hidden day cross-branch denial (day_c0906)

### Drafting guardrails
Symptoms-only instruction; opaque fix-path symbols; no instruction nouns on fix path; expected values in test code; three distributed bugs.

### Triviality Ledger
- Covenant-only patch passes day_c0901 but fails split lineage because parent quarantine must propagate to all children via LineageExpand.
- RFID window-only patch passes day_c0902 but fails exhibit-cleared day_c0903 because merge precedence still inverts quarantine vs exhibit.
- Merge-only patch passes exhibit day but fails day_c0901 donor-precedence cluster.

### Per-gate Pitfall Inventory
- RC1: solve.sh applies three substantive Java edits plus mvn package, not sed deletes.
- RC3: tests assert ALLOW/DENIED_LOAN per volume, not file existence.
- RC6: instruction lists symptoms and output paths only.
- CR1/CR7: fix symbols MergeLane.merge_b, RfidFold.fold_a, LineageExpand.resolve_d avoid instruction nouns.
- GX9: collection day IDs and volume IDs named in instruction where tests assert them.

### Initial Draft Commitments
- tasks/rare-book-quarantine-circulation/instruction.md
- tasks/rare-book-quarantine-circulation/task.toml
- tasks/rare-book-quarantine-circulation/output_contract.toml
- tasks/rare-book-quarantine-circulation/environment/Dockerfile
- tasks/rare-book-quarantine-circulation/environment/.dockerignore
- tasks/rare-book-quarantine-circulation/environment/pom.xml
- tasks/rare-book-quarantine-circulation/environment/config/lab.properties
- tasks/rare-book-quarantine-circulation/environment/scripts/run-cycle.sh
- tasks/rare-book-quarantine-circulation/environment/scripts/build_fixtures.sh
- tasks/rare-book-quarantine-circulation/environment/src/main/resources/lab.properties
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/App.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/CycleCmd.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/cfg/PropsLoader.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/cfg/LaneCfg.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/core/k9/LineageExpand.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/core/k9/VolumeGraph.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/core/k9/LegacyBind.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/core/r8/Orchestrator.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/core/r8/BatchCtx.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/core/r8/StageGate.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/ingest/m7/RfidFold.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/ingest/m7/RfidRow.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/ingest/m7/SignalFold.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/ingest/d4/CirculationParser.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/ingest/d4/CirculationRow.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/ingest/n2/QuarantineParser.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/ingest/n2/QuarantineRow.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/ingest/s5/CovenantParser.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/ingest/s5/CovenantRow.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/ingest/v6/ExhibitParser.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/ingest/v6/ExhibitRow.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/ingest/r3/SweepLoader.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/ingest/r3/SweepRow.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/engine/p3/MergeLane.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/engine/p3/RankTable.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/engine/p3/ShadowBlend.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/engine/q1/RulePack.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/engine/q1/EvalCtx.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/model/VolumeRef.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/model/OutRow.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/model/AuditEntry.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/io/JsonWriter.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/io/JsonReader.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/io/TsvWriter.java
- tasks/rare-book-quarantine-circulation/environment/src/main/java/com/archives/io/CsvReader.java
- tasks/rare-book-quarantine-circulation/tests/test.sh
- tasks/rare-book-quarantine-circulation/tests/test_outputs.py
- tasks/rare-book-quarantine-circulation/solution/solve.sh

### Construction manifest

#### symbol_table
- path: environment/src/main/java/com/archives/engine/p3/MergeLane.java
  symbol: merge_b
  kind: function
  signature: public static String merge_b(QuarantineRow a, CovenantRow b, ExhibitRow c)
  purpose: combines three feed rows into ALLOW or DENIED_LOAN
- path: environment/src/main/java/com/archives/ingest/m7/RfidFold.java
  symbol: fold_a
  kind: function
  signature: public static List<RfidRow> fold_a(List<RfidRow> rows, long x, long y)
  purpose: filters RFID rows to sweep window
- path: environment/src/main/java/com/archives/core/k9/LineageExpand.java
  symbol: resolve_d
  kind: function
  signature: public static List<String> resolve_d(String p, Map<String, List<String>> m)
  purpose: expands parent volume id to bound-volume children

#### flipping_point_contract
locations:
  - id: A
    path: environment/src/main/java/com/archives/engine/p3/MergeLane.java
    controls_tests: [test_k9_active_flag_blocks, test_p2_cleared_exhibit]
  - id: B
    path: environment/src/main/java/com/archives/ingest/m7/RfidFold.java
    controls_tests: [test_m4_unrelated_allow]
  - id: C
    path: environment/src/main/java/com/archives/core/k9/LineageExpand.java
    controls_tests: [test_q7_split_lineage, test_s3_rerun_stable, test_w2_hidden_day]
no_single_location_flips_majority: true
concentration_cap: 0.5

#### decoy_manifest
- path: environment/src/main/java/com/archives/ingest/m7/SignalFold.java
  kind: helper
  rhymes_with: fold_a
  non_fix_purpose: averages signal strength samples for reporting-only path
- path: environment/src/main/java/com/archives/engine/p3/ShadowBlend.java
  kind: helper
  rhymes_with: merge_b
  non_fix_purpose: picks first sweep route code for legacy export
- path: environment/src/main/java/com/archives/core/k9/LegacyBind.java
  kind: helper
  rhymes_with: resolve_d
  non_fix_purpose: maps legacy shelf codes to warehouse ids

#### code_forbidden_tokens
code_forbidden_tokens: [quarantine, circulation, conservation, exhibit, loan, manifest, rfid, shelf, sweep, donor, covenant, restriction, custody, patron, slip, ledger, exception, audit, collection, volume, branch, archives, rare, book]
