### Decision
GO - Attempt 1.
- Builds a Java recovery-console task around distributed log reconciliation and saga rollback planning.
- Uses three scenario bundles and a distributed fix surface so the task is not solved by a single policy table.

### Metadata
- version: 2
- Task name: in-doubt-transaction-recovery
- Title: In-Doubt Recovery
- Category: system-administration
- Languages: ["Java"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["java", "transactions", "recovery", "logs", "sagas"]
- Milestones: 0

## Authoring Brief
This file is the only drafting input for Step 2b. Do NOT include reviewer-only analysis, oracle steps, exact patch sites, or an exhaustive file tree here.

### Public contract
Create a task where the agent repairs a Java command-line recovery tool. The tool reads crash-drill scenario directories under `/app/scenarios`, writes `/app/output/decisions.json` and `/app/output/compensations.json`, and must bring the reported distributed work and saga clean-up plan into agreement with the durable records in the scenario logs. The public instruction should describe the observed drift and required output paths/schema, but it should not name the internal decision helpers or spell out every fixture answer.

### Failure topology
The visible failures span four interacting domains: coordinator journal rows, member journals, scenario mode metadata, and saga step state. Some cases require honoring durable member-side completion even when the coordinator row is absent, while other cases require treating fully prepared work differently depending on the scenario mode. Saga plans must then consume those decisions and skip already-compensated steps while preserving reverse clean-up order.

### Environment shape
Use a single Java module with a console entry point, parser/reader utilities, neutral engine classes, small model records, and three scenario directories. Scenario data should include coordinator rows, multiple member journals, metadata, and saga files. Names under the fix path must stay neutral and not mirror instruction nouns.

### Required artifacts
Create a standard single-step task with `instruction.md`, `task.toml`, `output_contract.toml`, `environment/Dockerfile`, `environment/.dockerignore`, Java sources, scenario log files, `solution/solve.sh`, `tests/test.sh`, and `tests/test_outputs.py`. The environment must contain at least 20 files excluding the Dockerfile.

### Test plan
- `test_north_member_completion_survives_gap`: verifies a member-side completed record keeps an unflushed transaction durable.
- `test_north_prepared_only_falls_back`: verifies prepared-only records in the default scenario do not become durable work.
- `test_harbor_full_prepared_set`: verifies a full prepared set in the alternate scenario becomes durable work.
- `test_harbor_partial_prepared_set`: verifies an incomplete prepared set in the alternate scenario is not promoted.
- `test_vault_flushed_rows_still_win`: verifies flushed coordinator rows remain authoritative.
- `test_abort_cleanups_are_reverse_and_filtered`: verifies clean-up actions are reverse ordered and already completed clean-up is not repeated.
- `test_commit_cleanups_are_empty`: verifies durable saga work is not compensated.
- `test_outputs_cover_every_scenario`: verifies both artifacts have all scenario keys and no unexpected top-level shape.

### Drafting guardrails
Do not use file names or symbols like transaction, participant, coordinator, commit, abort, saga, compensation, presumed, recovery, or reconcile on the oracle-touched code path. Keep scenario files realistic records, not answer keys. Tests may embed expected outcomes but should derive the need for those outcomes from records visible in the environment, not from a hidden golden file.

### Triviality Ledger
- Naive abort-on-gap is blocked because one scenario contains a member-side completed record for an unflushed row and tests require that durable state to survive.
- A single literal mode table is blocked because the alternate-mode cases need both full-set promotion and partial-set rejection.
- A compensation-only patch is blocked because compensation tests depend on the decision artifact semantics for the same scenarios.
- A decisions-only patch is blocked because saga tests require reverse filtering over step state rather than a blanket rollback.

### Per-gate Pitfall Inventory
- RC1/RC7/GX3: oracle must patch several Java methods with substantive logic, not overwrite one short table or add cosmetic diff.
- RC2/CR7: fix-path symbols and test names use neutral names and avoid direct instruction nouns.
- RC3/RC4/RC5: expected values live in verifier code; environment files are input records, not golden outputs.
- RC6/GX9/GX10: instruction should give the output contract and symptom but avoid enumerating scenario-by-scenario answers or contradictory polarity prose.
- Static checks: include `[environment] allow_internet = false`, a standard offline `test.sh`, `output_contract.toml`, and `environment/.dockerignore`.

### Initial Draft Commitments
- `tasks/in-doubt-transaction-recovery/instruction.md`
- `tasks/in-doubt-transaction-recovery/task.toml`
- `tasks/in-doubt-transaction-recovery/output_contract.toml`
- `tasks/in-doubt-transaction-recovery/environment/Dockerfile`
- `tasks/in-doubt-transaction-recovery/environment/.dockerignore`
- `tasks/in-doubt-transaction-recovery/environment/README.md`
- `tasks/in-doubt-transaction-recovery/environment/build.sh`
- `tasks/in-doubt-transaction-recovery/environment/scenarios/north/meta.properties`
- `tasks/in-doubt-transaction-recovery/environment/scenarios/north/coordinator.log`
- `tasks/in-doubt-transaction-recovery/environment/scenarios/north/member-bank.log`
- `tasks/in-doubt-transaction-recovery/environment/scenarios/north/member-inventory.log`
- `tasks/in-doubt-transaction-recovery/environment/scenarios/north/member-shipping.log`
- `tasks/in-doubt-transaction-recovery/environment/scenarios/north/saga.plan`
- `tasks/in-doubt-transaction-recovery/environment/scenarios/harbor/meta.properties`
- `tasks/in-doubt-transaction-recovery/environment/scenarios/harbor/coordinator.log`
- `tasks/in-doubt-transaction-recovery/environment/scenarios/harbor/member-ledger.log`
- `tasks/in-doubt-transaction-recovery/environment/scenarios/harbor/member-customs.log`
- `tasks/in-doubt-transaction-recovery/environment/scenarios/harbor/member-carrier.log`
- `tasks/in-doubt-transaction-recovery/environment/scenarios/harbor/saga.plan`
- `tasks/in-doubt-transaction-recovery/environment/scenarios/vault/meta.properties`
- `tasks/in-doubt-transaction-recovery/environment/scenarios/vault/coordinator.log`
- `tasks/in-doubt-transaction-recovery/environment/scenarios/vault/member-ledger.log`
- `tasks/in-doubt-transaction-recovery/environment/scenarios/vault/member-catalog.log`
- `tasks/in-doubt-transaction-recovery/environment/scenarios/vault/member-escrow.log`
- `tasks/in-doubt-transaction-recovery/environment/scenarios/vault/saga.plan`
- `tasks/in-doubt-transaction-recovery/environment/src/main/java/com/acme/ops/Console.java`
- `tasks/in-doubt-transaction-recovery/environment/src/main/java/com/acme/ops/io/LineReader.java`
- `tasks/in-doubt-transaction-recovery/environment/src/main/java/com/acme/ops/io/JsonWriter.java`
- `tasks/in-doubt-transaction-recovery/environment/src/main/java/com/acme/ops/model/Bundle.java`
- `tasks/in-doubt-transaction-recovery/environment/src/main/java/com/acme/ops/model/UnitRecord.java`
- `tasks/in-doubt-transaction-recovery/environment/src/main/java/com/acme/ops/model/ActionRecord.java`
- `tasks/in-doubt-transaction-recovery/environment/src/main/java/com/acme/ops/model/OutcomeRecord.java`
- `tasks/in-doubt-transaction-recovery/environment/src/main/java/com/acme/ops/model/RepairRecord.java`
- `tasks/in-doubt-transaction-recovery/environment/src/main/java/com/acme/ops/store/EventTape.java`
- `tasks/in-doubt-transaction-recovery/environment/src/main/java/com/acme/ops/store/TraceReader.java`
- `tasks/in-doubt-transaction-recovery/environment/src/main/java/com/acme/ops/engine/A1.java`
- `tasks/in-doubt-transaction-recovery/environment/src/main/java/com/acme/ops/engine/B2.java`
- `tasks/in-doubt-transaction-recovery/environment/src/main/java/com/acme/ops/engine/C3.java`
- `tasks/in-doubt-transaction-recovery/environment/src/main/java/com/acme/ops/engine/D4.java`
- `tasks/in-doubt-transaction-recovery/environment/src/main/java/com/acme/ops/engine/E5.java`
- `tasks/in-doubt-transaction-recovery/solution/solve.sh`
- `tasks/in-doubt-transaction-recovery/tests/test.sh`
- `tasks/in-doubt-transaction-recovery/tests/test_outputs.py`

### Construction manifest (BLOCKING - Step 2b must follow this verbatim)

#### symbol_table
```
- path: src/main/java/com/acme/ops/engine/A1.java
  symbol: fold
  kind: function
  signature: public Map<String, String> fold(Bundle x)
  purpose: Reduces scenario records into durable outcome strings.
- path: src/main/java/com/acme/ops/engine/B2.java
  symbol: choose
  kind: function
  signature: public String choose(String a, java.util.List<String> b, String c, int d)
  purpose: Selects one outcome from journal fragments and scenario mode.
- path: src/main/java/com/acme/ops/engine/C3.java
  symbol: collect
  kind: function
  signature: public Map<String, java.util.List<String>> collect(Bundle x)
  purpose: Builds per-id member fragments from raw rows.
- path: src/main/java/com/acme/ops/engine/D4.java
  symbol: make
  kind: function
  signature: public java.util.List<RepairRecord> make(Bundle x, Map<String, String> y)
  purpose: Converts step records and outcomes into clean-up records.
- path: src/main/java/com/acme/ops/engine/E5.java
  symbol: emit
  kind: function
  signature: public void emit(java.nio.file.Path a, java.util.Map<String, Map<String, String>> b, java.util.Map<String, java.util.List<RepairRecord>> c) throws java.io.IOException
  purpose: Writes both JSON artifacts.
```

#### flipping_point_contract
```
locations:
  - id: A
    path: src/main/java/com/acme/ops/engine/A1.java
    controls_tests: [test_north_member_completion_survives_gap, test_vault_flushed_rows_still_win]
  - id: B
    path: src/main/java/com/acme/ops/engine/B2.java
    controls_tests: [test_north_prepared_only_falls_back, test_harbor_full_prepared_set, test_harbor_partial_prepared_set]
  - id: C
    path: src/main/java/com/acme/ops/engine/C3.java
    controls_tests: [test_outputs_cover_every_scenario]
  - id: D
    path: src/main/java/com/acme/ops/engine/D4.java
    controls_tests: [test_abort_cleanups_are_reverse_and_filtered, test_commit_cleanups_are_empty]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest
```
- path: src/main/java/com/acme/ops/store/EventTape.java
  kind: helper
  rhymes_with: fold
  non_fix_purpose: Normalizes input rows by source file.
- path: src/main/java/com/acme/ops/io/JsonWriter.java
  kind: helper
  rhymes_with: emit
  non_fix_purpose: Escapes and formats nested JSON values.
- path: src/main/java/com/acme/ops/model/OutcomeRecord.java
  kind: helper
  rhymes_with: choose
  non_fix_purpose: Holds a scenario/id/value tuple for output sorting.
```

#### code_forbidden_tokens
```
code_forbidden_tokens: [console, crash, drills, durable, work, scenario, directories, output, decisions, compensations, json, distributed, records, saga, clean, up, plan, schema, object, scenarios, transactions, decision, commit, abort, sagas, actions, repair, member, coordinator, journal, mode, transaction, participant, presumed, recovery, reconciliation]
```
