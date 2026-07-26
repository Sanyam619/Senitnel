# Validation Log: embedding-bank-temperature-recalibration

## Attempt 1
- Derived score: 6 FAILs, 0 WARNs
- Evidence: embedding-bank-temperature-recalibration-attempt-1-evidence.json
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
- Derived score: 0 FAILs, 0 WARNs
- Evidence: embedding-bank-temperature-recalibration-attempt-2-evidence.json

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 2
- count of run_static_checks.py WARN-only exits before approval: 2
- count of collapse_check.py FAIL exits before first PASS: 1
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 276.24s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 138.48s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 2
- count of run_static_checks.py WARN-only exits before approval: 5
- count of collapse_check.py FAIL exits before first PASS: 1
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 276.24s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 589.54s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 2
- count of run_static_checks.py WARN-only exits before approval: 6
- count of collapse_check.py FAIL exits before first PASS: 1
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 276.24s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 1033.59s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 2
- count of run_static_checks.py WARN-only exits before approval: 10
- count of collapse_check.py FAIL exits before first PASS: 3
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 276.24s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 8567.31s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 2
- count of run_static_checks.py WARN-only exits before approval: 11
- count of collapse_check.py FAIL exits before first PASS: 3
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 276.24s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 8599.21s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null
