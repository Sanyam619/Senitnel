# Validation Log: battery-pack-thermal-conservation

## Attempt 1
- Derived score: 4 FAILs, 0 WARNs
- Evidence: battery-pack-thermal-conservation-attempt-1-evidence.json
- Provided score: 0 FAILs, 0 WARNs
- Score mismatch: Provided score was 0F/0W but the loop derived 4F/0W from structured evidence.
- Evidence errors:
  - test name 'test_m8_rebuild' contains forbidden instruction noun 'rebuild'.
  - test name 'test_p2_hotspot' contains forbidden instruction noun 'hotspot'.
  - test name 'test_q7_fleet' contains forbidden instruction noun 'fleet'.
  - test name 'test_v4_energy' contains forbidden instruction noun 'energy'.
- Blocking evidence failures:
  - test name 'test_m8_rebuild' contains forbidden instruction noun 'rebuild'.
  - test name 'test_p2_hotspot' contains forbidden instruction noun 'hotspot'.
  - test name 'test_q7_fleet' contains forbidden instruction noun 'fleet'.
  - test name 'test_v4_energy' contains forbidden instruction noun 'energy'.

## Attempt 2
- Derived score: 0 FAILs, 0 WARNs
- Evidence: battery-pack-thermal-conservation-attempt-2-evidence.json
- Provided score: 0 FAILs, 0 WARNs

## Step 3b / Step 4 (2026-07-23)
- Step 3b: `logs/battery-pack-thermal-conservation-step3b-2026-07-23.md` — WARN justifications RC1/RC7/RC8/GX3; no task edits.
- Oracle 10x: 10/10 Mean 1.000 (`jobs/2026-07-23__22-49-14`)
- NOP: 0.0 (`jobs/2026-07-23__21-10-56`)
- Zip: `Task_Ready_To_Submit/battery-pack-thermal-conservation.zip`
- `approve_task.py`: PASS (collapse WARN documented)
- Verdict: ACCEPT WITH NOTES — see `logs/battery-pack-thermal-conservation-step4-2026-07-23.md`

## Redesign Attempt 3 (2026-07-23 evening) — taxonomy / no-repair
- Aligned to idea category `scientific-computing` + languages `python`/`bash`.
- Dropped three-stub repair framing: instruction is operate-the-desk / bands (idea paste); hardness = FV conservation×hotspot under dual profiles + policy overlay rematerialize.
- Plausible-wrong physics (uniform contact, positive-only fold, fixed-step ignore CFL) + sealed cutover vs overlay.seed.
- Hard tests: 12 domain residual / independent recompute / overlay-authority / ship↔fleet dt polarity cells (not schema-only).
- Step 2b re-entry: preflight PASS (collapse WARN); oracle 1.0; NOP 0.0. Prior Step 4 zip/APPROVE are stale until Step 3b→4 rerun.

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 2
- count of run_static_checks.py WARN-only exits before approval: 0
- count of collapse_check.py FAIL exits before first PASS: 0
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 0.38s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 6085.12s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 3
- count of run_static_checks.py WARN-only exits before approval: 0
- count of collapse_check.py FAIL exits before first PASS: 1
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 0.38s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 6830.56s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 3
- count of run_static_checks.py WARN-only exits before approval: 1
- count of collapse_check.py FAIL exits before first PASS: 1
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 0.38s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 77973.46s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 4
- count of run_static_checks.py WARN-only exits before approval: 1
- count of collapse_check.py FAIL exits before first PASS: 2
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 0.38s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 79022.99s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 4
- count of run_static_checks.py WARN-only exits before approval: 1
- count of collapse_check.py FAIL exits before first PASS: 4
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 0.38s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 79768.42s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 4
- count of run_static_checks.py WARN-only exits before approval: 1
- count of collapse_check.py FAIL exits before first PASS: 4
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 0.38s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 79820.64s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null
