# Validation Log: thin-lto-archive-visibility-lattice

## Attempt 1
- Derived score: 14 FAILs, 0 WARNs
- Evidence: thin-lto-archive-visibility-lattice-attempt-1-evidence.json
- Evidence errors:
  - Schema validation failed at $.naming_pass.concentration_math: 'per_location' is a required property
  - Schema validation failed at $.naming_pass.concentration_math: Additional properties are not allowed ('A', 'B', 'C', 'D', 'cap' were unexpected)
  - Schema validation failed at $.naming_pass.renames_during_drafting[0]: 'original' is a required property
  - Schema validation failed at $.naming_pass.renames_during_drafting[0]: 'renamed_to' is a required property
  - Schema validation failed at $.naming_pass.renames_during_drafting[0]: Additional properties are not allowed ('from', 'to' were unexpected)
  - Schema validation failed at $.naming_pass.renames_during_drafting[1]: 'original' is a required property
  - Schema validation failed at $.naming_pass.renames_during_drafting[1]: 'renamed_to' is a required property
  - Schema validation failed at $.naming_pass.renames_during_drafting[1]: Additional properties are not allowed ('from', 'to' were unexpected)
  - Schema validation failed at $.naming_pass.renames_during_drafting[2]: 'original' is a required property
  - Schema validation failed at $.naming_pass.renames_during_drafting[2]: 'renamed_to' is a required property
  - Schema validation failed at $.naming_pass.renames_during_drafting[2]: Additional properties are not allowed ('from', 'to' were unexpected)
  - Schema validation failed at $.naming_pass.renames_during_drafting[3]: 'original' is a required property
  - Schema validation failed at $.naming_pass.renames_during_drafting[3]: 'renamed_to' is a required property
  - Schema validation failed at $.naming_pass.renames_during_drafting[3]: Additional properties are not allowed ('from', 'to' were unexpected)
- Blocking evidence failures:
  - Schema validation failed at $.naming_pass.concentration_math: 'per_location' is a required property
  - Schema validation failed at $.naming_pass.concentration_math: Additional properties are not allowed ('A', 'B', 'C', 'D', 'cap' were unexpected)
  - Schema validation failed at $.naming_pass.renames_during_drafting[0]: 'original' is a required property
  - Schema validation failed at $.naming_pass.renames_during_drafting[0]: 'renamed_to' is a required property
  - Schema validation failed at $.naming_pass.renames_during_drafting[0]: Additional properties are not allowed ('from', 'to' were unexpected)
  - Schema validation failed at $.naming_pass.renames_during_drafting[1]: 'original' is a required property
  - Schema validation failed at $.naming_pass.renames_during_drafting[1]: 'renamed_to' is a required property
  - Schema validation failed at $.naming_pass.renames_during_drafting[1]: Additional properties are not allowed ('from', 'to' were unexpected)
  - Schema validation failed at $.naming_pass.renames_during_drafting[2]: 'original' is a required property
  - Schema validation failed at $.naming_pass.renames_during_drafting[2]: 'renamed_to' is a required property
  - Schema validation failed at $.naming_pass.renames_during_drafting[2]: Additional properties are not allowed ('from', 'to' were unexpected)
  - Schema validation failed at $.naming_pass.renames_during_drafting[3]: 'original' is a required property
  - Schema validation failed at $.naming_pass.renames_during_drafting[3]: 'renamed_to' is a required property
  - Schema validation failed at $.naming_pass.renames_during_drafting[3]: Additional properties are not allowed ('from', 'to' were unexpected)

## Attempt 2
- Derived score: 0 FAILs, 0 WARNs
- Evidence: thin-lto-archive-visibility-lattice-attempt-2-evidence.json


## Step 2b evidence (2026-07-20)

- Preflight: `./scripts/check-task.sh` PASS (collapse WARN only)
- GX7 WARN justification: orphan path literals `harness.sha256` / `ledgers` are verifier ledger paths inside `tests/`, not graded agent contract tokens.
- Oracle 1x: Mean **1.000** (`jobs/2026-07-20__18-26-47`)
- NOP: Mean **0.000** (`jobs/2026-07-20__18-27-20`)
- Not READY/SUBMIT: oracle 10x + `approve_task.py` still required for Step 4.

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 0
- count of run_static_checks.py WARN-only exits before approval: 0
- count of collapse_check.py FAIL exits before first PASS: 4
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 97.77s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 177022.03s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 5
- count of run_static_checks.py WARN-only exits before approval: 8
- count of collapse_check.py FAIL exits before first PASS: 9
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 97.77s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 266788.56s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null
