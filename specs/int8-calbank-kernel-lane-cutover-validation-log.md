# Validation log — int8-calbank-kernel-lane-cutover

## Attempt 1 — GO

- Category: machine-learning (INT8 cal-bank × kernel-lane cutover; C + Rust)
- Framing: cutover/eval outcomes — not repair/debug checklist
- Loci: knit_q (durable tip), fold_w (live-mask), slot_v (resume rebind)
- Local docker: broken defaults wrong ledger; oracle → 8/8 pytest PASS

## Notes

- Surface probe / surface_ok.json is false-green bait
- Graded top1 values documented in instruction for sufficiency
- Spec: specs/int8-calbank-kernel-lane-cutover.md

## Step 2b evidence (2026-07-19)

- `./scripts/check-task.sh` — PASS (collapse WARN: RC7/RC8/GX3 borderline, GX7 path literals)
- harbor oracle 1x — Mean **1.000** (`jobs/2026-07-19__20-12-20/`)
- harbor nop — Mean **0.000** (`jobs/2026-07-19__20-13-34/`)
- Not yet: oracle 10x, `approve_task.py`, submission zip (Step 4)

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 3
- count of run_static_checks.py WARN-only exits before approval: 15
- count of collapse_check.py FAIL exits before first PASS: 5
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 86.51s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 517303.87s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 3
- count of run_static_checks.py WARN-only exits before approval: 16
- count of collapse_check.py FAIL exits before first PASS: 5
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 86.51s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 517885.93s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null
