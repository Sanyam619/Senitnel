# Validation Log: landlock-seccomp-notify-admission-mesh

## Attempt 1
- Derived score: 9 FAILs, 0 WARNs
- Evidence: landlock-seccomp-notify-admission-mesh-attempt-1-evidence.json
- Evidence errors:
  - Schema validation failed at $.topology_enumeration[0]: 'summary' is a required property
  - Schema validation failed at $.topology_enumeration[0]: 'why_no_single_location_suffices' is a required property
  - Schema validation failed at $.topology_enumeration[0]: Additional properties are not allowed ('name', 'why_single_location_insufficient' were unexpected)
  - Schema validation failed at $.topology_enumeration[1]: 'summary' is a required property
  - Schema validation failed at $.topology_enumeration[1]: 'why_no_single_location_suffices' is a required property
  - Schema validation failed at $.topology_enumeration[1]: Additional properties are not allowed ('name', 'why_single_location_insufficient' were unexpected)
  - Schema validation failed at $.topology_enumeration[2]: 'summary' is a required property
  - Schema validation failed at $.topology_enumeration[2]: 'why_no_single_location_suffices' is a required property
  - Schema validation failed at $.topology_enumeration[2]: Additional properties are not allowed ('name', 'why_single_location_insufficient' were unexpected)
- Blocking evidence failures:
  - Schema validation failed at $.topology_enumeration[0]: 'summary' is a required property
  - Schema validation failed at $.topology_enumeration[0]: 'why_no_single_location_suffices' is a required property
  - Schema validation failed at $.topology_enumeration[0]: Additional properties are not allowed ('name', 'why_single_location_insufficient' were unexpected)
  - Schema validation failed at $.topology_enumeration[1]: 'summary' is a required property
  - Schema validation failed at $.topology_enumeration[1]: 'why_no_single_location_suffices' is a required property
  - Schema validation failed at $.topology_enumeration[1]: Additional properties are not allowed ('name', 'why_single_location_insufficient' were unexpected)
  - Schema validation failed at $.topology_enumeration[2]: 'summary' is a required property
  - Schema validation failed at $.topology_enumeration[2]: 'why_no_single_location_suffices' is a required property
  - Schema validation failed at $.topology_enumeration[2]: Additional properties are not allowed ('name', 'why_single_location_insufficient' were unexpected)

## Attempt 2
- Derived score: 1 FAILs, 0 WARNs
- Evidence: landlock-seccomp-notify-admission-mesh-attempt-2-evidence.json
- Evidence errors:
  - naming_pass.concentration_math disagrees with computed values: location 'A' ratio supplied=0.2857 computed=0.285714; location 'B' ratio supplied=0.2857 computed=0.285714; location 'C' ratio supplied=0.4286 computed=0.428571
- Blocking evidence failures:
  - naming_pass.concentration_math disagrees with computed values: location 'A' ratio supplied=0.2857 computed=0.285714; location 'B' ratio supplied=0.2857 computed=0.285714; location 'C' ratio supplied=0.4286 computed=0.428571

## Attempt 3
- Derived score: 0 FAILs, 0 WARNs
- Evidence: landlock-seccomp-notify-admission-mesh-attempt-3-evidence.json

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 1
- count of run_static_checks.py WARN-only exits before approval: 12
- count of collapse_check.py FAIL exits before first PASS: 4
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 150.11s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 354595.14s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 1
- count of run_static_checks.py WARN-only exits before approval: 13
- count of collapse_check.py FAIL exits before first PASS: 4
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 150.11s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 438163.93s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 1
- count of run_static_checks.py WARN-only exits before approval: 14
- count of collapse_check.py FAIL exits before first PASS: 4
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 150.11s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 440427.30s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 2
- count of run_static_checks.py WARN-only exits before approval: 17
- count of collapse_check.py FAIL exits before first PASS: 5
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 150.11s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 527906.24s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 2
- count of run_static_checks.py WARN-only exits before approval: 18
- count of collapse_check.py FAIL exits before first PASS: 5
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 150.11s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 540554.44s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 2
- count of run_static_checks.py WARN-only exits before approval: 19
- count of collapse_check.py FAIL exits before first PASS: 5
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 150.11s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 540590.16s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 2
- count of run_static_checks.py WARN-only exits before approval: 20
- count of collapse_check.py FAIL exits before first PASS: 5
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 150.11s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 540608.93s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 2
- count of run_static_checks.py WARN-only exits before approval: 21
- count of collapse_check.py FAIL exits before first PASS: 5
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 150.11s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 546766.14s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null
