# Validation Log: cgroup-v2-hierarchy-cutover

## Attempt 1
- Derived score: 2 FAILs, 0 WARNs
- Evidence: cgroup-v2-hierarchy-cutover-attempt-1-evidence.json
- Evidence errors:
  - test name 'test_x3_layout_shape' contains forbidden instruction noun 'layout'.
  - naming_pass.concentration_math disagrees with computed values: location 'A' ratio supplied=0.333 computed=0.333333; location 'B' ratio supplied=0.333 computed=0.333333; location 'C' ratio supplied=0.333 computed=0.333333
- Blocking evidence failures:
  - test name 'test_x3_layout_shape' contains forbidden instruction noun 'layout'.
  - naming_pass.concentration_math disagrees with computed values: location 'A' ratio supplied=0.333 computed=0.333333; location 'B' ratio supplied=0.333 computed=0.333333; location 'C' ratio supplied=0.333 computed=0.333333

## Attempt 2
- Derived score: 0 FAILs, 0 WARNs
- Evidence: cgroup-v2-hierarchy-cutover-attempt-2-evidence.json

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 4
- count of run_static_checks.py WARN-only exits before approval: 0
- count of collapse_check.py FAIL exits before first PASS: 5
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 285.27s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 1141.04s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null
