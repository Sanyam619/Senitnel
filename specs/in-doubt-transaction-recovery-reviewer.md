### Decision
GO - Attempt 1. Distributed Java recovery console with three scenario bundles and a four-location fix surface.

### Metadata
- Task name: in-doubt-transaction-recovery
- Title: In-Doubt Recovery
- Category: system-administration
- Languages: ["Java"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["java", "transactions", "recovery", "logs", "sagas"]
- Milestones: 0

### Discovery budget
- Discovery: member-side completed rows override a missing coordinator row.
  Planned location: scenario journals and neutral reducer code.
  Why instruction must not reveal it: naming this directly makes the hardest in-doubt case a rule transcription.
- Discovery: alternate scenario mode promotes only a full prepared set, not a partial set.
  Planned location: `meta.properties`, member journals, and neutral engine classes.
  Why instruction must not reveal it: spelling the condition makes the task a finite state-table repair.
- Discovery: saga cleanup uses the recovered outcome and step status, not the raw saga file alone.
  Planned location: saga plan files plus Java planning code.
  Why instruction must not reveal it: direct prose would point to the exact filter and order.
- Discovery: output writing must preserve all scenarios and stable nested object shape.
  Planned location: console/output writer integration.
  Why instruction must not reveal it: this is integration behavior that should be found by running the tool.

### Anti-trivialization verdict
All 21 checks pass at idea level. The concept is verifiable, deterministic, and not a multi-container or UI task. It avoids hidden-instance difficulty by requiring a general multi-scenario recovery behavior. It is not a single-artifact repair because outcome selection, fragment collection, saga planning, and output emission coordinate. Instruction will stay symptoms-only and avoid scenario answer recital.

### Topology enumeration (3 candidate fix topologies)
1. Reducer-centered topology: record reader, outcome selector, saga planner, and writer coordinate. No single component can pass both decision and compensation tests.
2. Planner-centered topology: selector, step parser, plan filter, and JSON emission coordinate. This can pass saga cases only if recovered outcomes are correct.
3. Parser-centered topology: metadata parsing, member-row grouping, flushed-row map, and planner order coordinate. Parsing alone cannot infer durable outcomes or clean-up order.

### Rubric axes
- Verifiable: Pass. Exact JSON values and post-cleanup equivalence are deterministic.
- Well-specified: Pass. The instruction can describe outputs and observed drift without answer keys.
- Solvable: Pass. A Java-capable expert can reason through logs and patch a small module.
- Difficult: Pass. It requires distributed transaction and saga reasoning across files.
- Interesting: Pass. Enterprise transaction recovery has real operational value.
- Outcome-verified: Pass. Tests grade output artifacts, not implementation choices.

### Hardness axes
- Discover: The agent must read logs, metadata, and code behavior beyond instruction.md.
- Synthesize: Outcomes require combining coordinator, member, mode, and saga inputs.
- Diagnose: The prompt describes wrong recovered artifacts, not the underlying reducer defects.
- Navigate coupling: A local outcome change affects compensation planning and output shape.
- Reason beyond training: The edge cases are enterprise recovery predicates, not a common single-file recipe.

### Instruction completeness test
No, an agent cannot solve from instruction.md alone. It must inspect the scenario records, discover how the Java tool models them, and repair cross-component behavior.

## Reviewer Appendix

### Implementation plan
Build a Java CLI that scans `/app/scenarios`, parses scenario metadata, coordinator rows, member journals, and saga plans, then writes two JSON artifacts. The baseline intentionally over-trusts flushed coordinator rows and blanket-compensates aborted saga work. The oracle patches the neutral engine classes to respect durable member completion, scenario-mode prepared sets, and reverse filtered cleanup.

### Proposed file inventory
See the authoring spec's Initial Draft Commitments. It contains 31 environment files excluding the Dockerfile, enough for `small`.

### Oracle notes
The oracle should patch four neutral engine files. It should not hardcode scenario answers; it should implement general row grouping, outcome selection, saga filtering, and stable emission.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
A real solution must coordinate at least the reducer, selector, fragment collector, and cleanup planner. A one-line "abort all gaps" or "commit all prepared" patch fails opposing cases.

Likely editable frontier:
- `engine/A1.java`
- `engine/B2.java`
- `engine/C3.java`
- `engine/D4.java`
- `engine/E5.java`

Requirement-to-file map:
- Recovered durable outcomes -> reducer/selector/collector.
- Saga clean-up plan -> planner plus recovered outcomes.
- JSON artifacts -> writer/emitter integration.

Oracle estimated complexity: 100+ lines of non-boilerplate logic.

Red flags:
- Standard 2PC terminology could make the instruction too rule-like if overused.

Residual hardness:
The environment exposes enough domain records to solve, but the agent still has to infer which records are authoritative and how the saga planner depends on the recovered outcomes.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
console, crash, drills, durable, work, scenario, directories, output, decisions, compensations, json, distributed, records, saga, clean, up, plan, schema, object, scenarios, transactions, decision, commit, abort, sagas, actions, repair, member, coordinator, journal, mode, transaction, participant, presumed, recovery, reconciliation

**Renames during drafting:**
- `RecoveryEngine` -> `A1`: avoids direct noun match.
- `DecisionPolicy` -> `B2`: avoids direct noun match.
- `SagaPlanner` -> `D4`: avoids direct noun match.

**Test names audited:**
- test_north_member_completion_survives_gap
- test_north_prepared_only_falls_back
- test_harbor_full_prepared_set
- test_harbor_partial_prepared_set
- test_vault_flushed_rows_still_win
- test_abort_cleanups_are_reverse_and_filtered
- test_commit_cleanups_are_empty
- test_outputs_cover_every_scenario

**Concentration math:**
- Total tests across `flipping_point_contract`: 8
- A: 2/8 = 0.25
- B: 3/8 = 0.375
- C: 1/8 = 0.125
- D: 2/8 = 0.25
- Cap: 0.5. Max ratio observed: 0.375. Status: PASS

### Per-test feasibility pre-check
- Test: test_north_member_completion_survives_gap
  Checks: member-side completion survives a missing coordinator row.
  Valid approaches: 2+
  Chain-dependent: no
  Feasibility risk: LOW
- Test: test_north_prepared_only_falls_back
  Checks: prepared-only rows in default mode are rejected.
  Valid approaches: 2+
  Chain-dependent: no
  Feasibility risk: LOW
- Test: test_harbor_full_prepared_set
  Checks: full prepared set in alternate mode is promoted.
  Valid approaches: 2+
  Chain-dependent: no
  Feasibility risk: LOW
- Test: test_harbor_partial_prepared_set
  Checks: incomplete prepared set is rejected.
  Valid approaches: 2+
  Chain-dependent: no
  Feasibility risk: LOW
- Test: test_vault_flushed_rows_still_win
  Checks: flushed rows remain authoritative.
  Valid approaches: 2+
  Chain-dependent: no
  Feasibility risk: LOW
- Test: test_abort_cleanups_are_reverse_and_filtered
  Checks: cleanup action order and filtering.
  Valid approaches: 2+
  Chain-dependent: yes, depends on recovered outcome, but this is domain coupling rather than test order coupling.
  Feasibility risk: LOW
- Test: test_commit_cleanups_are_empty
  Checks: durable saga work is not compensated.
  Valid approaches: 2+
  Chain-dependent: yes, depends on recovered outcome.
  Feasibility risk: LOW
- Test: test_outputs_cover_every_scenario
  Checks: stable output coverage.
  Valid approaches: 2+
  Chain-dependent: no
  Feasibility risk: LOW
