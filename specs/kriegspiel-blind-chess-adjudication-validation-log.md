# Validation Log: kriegspiel-blind-chess-adjudication

## Attempt 1
- Derived score: 6 FAILs, 1 WARNs
- Evidence: kriegspiel-blind-chess-adjudication-attempt-1-evidence.json
- Evidence errors:
  - hardness_axes is missing required ids: discover, synthesize, diagnose, navigate_coupling, reason_beyond_training.
  - hardness_axes contains unexpected ids: H1, H2, H3, H4, H5.
  - anti_trivialization_checks is missing required ids: disclosure_collapse, hidden_instance, single_artifact_repair, generalization, prompt_honesty, cheating_vs_difficulty, mechanical_fix_filter, localized_fix, oracle_locality, small_declarative_cluster, grep_collapse, pre_factored_helper, recipe_discount, security_aura_discount, orthogonal_checklist, harness_discount, one_pass_solvability, hard_only_gate, discovery_budget_test, instruction_specificity_test, topology_distribution_test.
  - anti_trivialization_checks contains unexpected ids: AT1, AT2, AT3, AT4, AT5, AT6, AT7, AT8, AT9, AT10, AT11, AT12, AT13, AT14, AT15, AT16, AT17, AT18, AT19, AT20, AT21.
  - rubric_axes is missing required ids: verifiable, well_specified, solvable, difficult, interesting, outcome_verified.
  - rubric_axes contains unexpected ids: R1, R2, R3, R4, R5, R6.
- Blocking evidence failures:
  - hardness_axes is missing required ids: discover, synthesize, diagnose, navigate_coupling, reason_beyond_training.
  - hardness_axes contains unexpected ids: H1, H2, H3, H4, H5.
  - anti_trivialization_checks is missing required ids: disclosure_collapse, hidden_instance, single_artifact_repair, generalization, prompt_honesty, cheating_vs_difficulty, mechanical_fix_filter, localized_fix, oracle_locality, small_declarative_cluster, grep_collapse, pre_factored_helper, recipe_discount, security_aura_discount, orthogonal_checklist, harness_discount, one_pass_solvability, hard_only_gate, discovery_budget_test, instruction_specificity_test, topology_distribution_test.
  - anti_trivialization_checks contains unexpected ids: AT1, AT2, AT3, AT4, AT5, AT6, AT7, AT8, AT9, AT10, AT11, AT12, AT13, AT14, AT15, AT16, AT17, AT18, AT19, AT20, AT21.
  - rubric_axes is missing required ids: verifiable, well_specified, solvable, difficult, interesting, outcome_verified.
  - rubric_axes contains unexpected ids: R1, R2, R3, R4, R5, R6.

## Attempt 2
- Derived score: 3 FAILs, 0 WARNs
- Evidence: kriegspiel-blind-chess-adjudication-attempt-2-evidence.json
- Evidence errors:
  - Schema validation failed at $: 'construction_manifest' is a required property
  - Schema validation failed at $: 'topology_enumeration' is a required property
  - Schema validation failed at $.naming_pass: Additional properties are not allowed ('recomputed_concentration' was unexpected)
- Blocking evidence failures:
  - Schema validation failed at $: 'construction_manifest' is a required property
  - Schema validation failed at $: 'topology_enumeration' is a required property
  - Schema validation failed at $.naming_pass: Additional properties are not allowed ('recomputed_concentration' was unexpected)

## Attempt 3
- Derived score: 0 FAILs, 1 WARNs
- Evidence: kriegspiel-blind-chess-adjudication-attempt-3-evidence.json

## Attempt 4
- Derived score: 2 FAILs, 0 WARNs
- Evidence: kriegspiel-blind-chess-adjudication-attempt-4-evidence.json
- Evidence errors:
  - Schema validation failed at $: 'construction_manifest' is a required property
  - Schema validation failed at $: 'topology_enumeration' is a required property
- Blocking evidence failures:
  - Schema validation failed at $: 'construction_manifest' is a required property
  - Schema validation failed at $: 'topology_enumeration' is a required property

## Attempt 5
- Derived score: 0 FAILs, 0 WARNs
- Evidence: kriegspiel-blind-chess-adjudication-attempt-5-evidence.json

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 0
- count of run_static_checks.py WARN-only exits before approval: 4
- count of collapse_check.py FAIL exits before first PASS: 0
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 0.63s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 264.74s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 0
- count of run_static_checks.py WARN-only exits before approval: 5
- count of collapse_check.py FAIL exits before first PASS: 0
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 0.63s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 1014.55s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 0
- count of run_static_checks.py WARN-only exits before approval: 7
- count of collapse_check.py FAIL exits before first PASS: 0
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 0.63s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 1560.98s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 0
- count of run_static_checks.py WARN-only exits before approval: 8
- count of collapse_check.py FAIL exits before first PASS: 0
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 0.63s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 73215.78s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 0
- count of run_static_checks.py WARN-only exits before approval: 9
- count of collapse_check.py FAIL exits before first PASS: 0
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 0.63s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 95502.66s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null
