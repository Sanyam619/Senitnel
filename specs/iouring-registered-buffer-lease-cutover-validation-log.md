# Validation Log: iouring-registered-buffer-lease-cutover

## Attempt 1
- Derived score: 1 FAILs, 0 WARNs
- Evidence: iouring-registered-buffer-lease-cutover-attempt-1-evidence.json
- Evidence errors:
  - naming_pass.concentration_math disagrees with computed values: location 'A' ratio supplied=0.333 computed=0.333333; location 'B' ratio supplied=0.333 computed=0.333333; location 'C' ratio supplied=0.333 computed=0.333333
- Blocking evidence failures:
  - naming_pass.concentration_math disagrees with computed values: location 'A' ratio supplied=0.333 computed=0.333333; location 'B' ratio supplied=0.333 computed=0.333333; location 'C' ratio supplied=0.333 computed=0.333333

## Attempt 2
- Derived score: 3 FAILs, 0 WARNs
- Evidence: iouring-registered-buffer-lease-cutover-attempt-2-evidence.json
- Evidence errors:
  - Schema validation failed at $: 'construction_manifest' is a required property
  - Schema validation failed at $: 'topology_enumeration' is a required property
  - Schema validation failed at $.naming_pass: Additional properties are not allowed ('recomputed_concentration' was unexpected)
- Blocking evidence failures:
  - Schema validation failed at $: 'construction_manifest' is a required property
  - Schema validation failed at $: 'topology_enumeration' is a required property
  - Schema validation failed at $.naming_pass: Additional properties are not allowed ('recomputed_concentration' was unexpected)

## Attempt 3
- Derived score: 0 FAILs, 0 WARNs
- Evidence: iouring-registered-buffer-lease-cutover-attempt-3-evidence.json

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 0
- count of run_static_checks.py WARN-only exits before approval: 0
- count of collapse_check.py FAIL exits before first PASS: 1
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 0.46s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 194478.47s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 0
- count of run_static_checks.py WARN-only exits before approval: 3
- count of collapse_check.py FAIL exits before first PASS: 2
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 0.46s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 198825.76s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 0
- count of run_static_checks.py WARN-only exits before approval: 3
- count of collapse_check.py FAIL exits before first PASS: 2
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 0.46s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 198844.58s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 0
- count of run_static_checks.py WARN-only exits before approval: 3
- count of collapse_check.py FAIL exits before first PASS: 3
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 0.46s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 263705.27s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 2
- count of run_static_checks.py WARN-only exits before approval: 3
- count of collapse_check.py FAIL exits before first PASS: 5
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 0.46s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 349860.14s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 3
- count of run_static_checks.py WARN-only exits before approval: 6
- count of collapse_check.py FAIL exits before first PASS: 6
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 0.46s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 360255.32s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 3
- count of run_static_checks.py WARN-only exits before approval: 6
- count of collapse_check.py FAIL exits before first PASS: 6
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 0.46s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 360299.73s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 3
- count of run_static_checks.py WARN-only exits before approval: 8
- count of collapse_check.py FAIL exits before first PASS: 6
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 0.46s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 438154.01s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null
