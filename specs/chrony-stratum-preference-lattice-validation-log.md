# Validation Log: chrony-stratum-preference-lattice

## Attempt 1
- Derived score: 15 FAILs, 0 WARNs
- Evidence: chrony-stratum-preference-lattice-attempt-1-evidence.json
- Evidence errors:
  - Schema validation failed at $.naming_pass.concentration_math: 'per_location' is a required property
  - Schema validation failed at $.naming_pass.concentration_math: 'total_tests' is a required property
  - Schema validation failed at $.naming_pass.concentration_math: Additional properties are not allowed ('concentration_cap', 'max_ratio', 'passes_cap', 'per_location_ratios' were unexpected)
  - Schema validation failed at $.topology_enumeration[0]: 'id' is a required property
  - Schema validation failed at $.topology_enumeration[0]: 'summary' is a required property
  - Schema validation failed at $.topology_enumeration[0]: 'why_no_single_location_suffices' is a required property
  - Schema validation failed at $.topology_enumeration[0]: Additional properties are not allowed ('name', 'why_single_insufficient' were unexpected)
  - Schema validation failed at $.topology_enumeration[1]: 'id' is a required property
  - Schema validation failed at $.topology_enumeration[1]: 'summary' is a required property
  - Schema validation failed at $.topology_enumeration[1]: 'why_no_single_location_suffices' is a required property
  - Schema validation failed at $.topology_enumeration[1]: Additional properties are not allowed ('name', 'why_single_insufficient' were unexpected)
  - Schema validation failed at $.topology_enumeration[2]: 'id' is a required property
  - Schema validation failed at $.topology_enumeration[2]: 'summary' is a required property
  - Schema validation failed at $.topology_enumeration[2]: 'why_no_single_location_suffices' is a required property
  - Schema validation failed at $.topology_enumeration[2]: Additional properties are not allowed ('name', 'why_single_insufficient' were unexpected)
- Blocking evidence failures:
  - Schema validation failed at $.naming_pass.concentration_math: 'per_location' is a required property
  - Schema validation failed at $.naming_pass.concentration_math: 'total_tests' is a required property
  - Schema validation failed at $.naming_pass.concentration_math: Additional properties are not allowed ('concentration_cap', 'max_ratio', 'passes_cap', 'per_location_ratios' were unexpected)
  - Schema validation failed at $.topology_enumeration[0]: 'id' is a required property
  - Schema validation failed at $.topology_enumeration[0]: 'summary' is a required property
  - Schema validation failed at $.topology_enumeration[0]: 'why_no_single_location_suffices' is a required property
  - Schema validation failed at $.topology_enumeration[0]: Additional properties are not allowed ('name', 'why_single_insufficient' were unexpected)
  - Schema validation failed at $.topology_enumeration[1]: 'id' is a required property
  - Schema validation failed at $.topology_enumeration[1]: 'summary' is a required property
  - Schema validation failed at $.topology_enumeration[1]: 'why_no_single_location_suffices' is a required property
  - Schema validation failed at $.topology_enumeration[1]: Additional properties are not allowed ('name', 'why_single_insufficient' were unexpected)
  - Schema validation failed at $.topology_enumeration[2]: 'id' is a required property
  - Schema validation failed at $.topology_enumeration[2]: 'summary' is a required property
  - Schema validation failed at $.topology_enumeration[2]: 'why_no_single_location_suffices' is a required property
  - Schema validation failed at $.topology_enumeration[2]: Additional properties are not allowed ('name', 'why_single_insufficient' were unexpected)

## Attempt 2
- Derived score: 0 FAILs, 0 WARNs
- Evidence: chrony-stratum-preference-lattice-attempt-2-evidence.json

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 0
- count of run_static_checks.py WARN-only exits before approval: 0
- count of collapse_check.py FAIL exits before first PASS: 0
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 0.55s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 401.89s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null
