# Validation Log: ceph-osd-crush-reweight-seating

## Attempt 1
- Derived score: 1 FAILs, 1 WARNs
- Evidence: ceph-osd-crush-reweight-seating-attempt-1-evidence.json
- Evidence errors:
  - naming_pass.concentration_math disagrees with computed values: location 'B' ratio supplied=0.333 computed=0.333333; location 'C' ratio supplied=0.167 computed=0.166667; location 'E' ratio supplied=0.417 computed=0.416667
- Blocking evidence failures:
  - naming_pass.concentration_math disagrees with computed values: location 'B' ratio supplied=0.333 computed=0.333333; location 'C' ratio supplied=0.167 computed=0.166667; location 'E' ratio supplied=0.417 computed=0.416667

## Attempt 2
- Derived score: 0 FAILs, 1 WARNs
- Evidence: ceph-osd-crush-reweight-seating-attempt-2-evidence.json

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 0
- count of run_static_checks.py WARN-only exits before approval: 1
- count of collapse_check.py FAIL exits before first PASS: 0
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 0.63s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 44.33s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 0
- count of run_static_checks.py WARN-only exits before approval: 1
- count of collapse_check.py FAIL exits before first PASS: 0
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 0.63s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 191.70s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null
