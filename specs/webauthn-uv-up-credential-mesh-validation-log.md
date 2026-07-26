# webauthn-uv-up-credential-mesh — Step 2b/3b WARN justifications

## Collapse WARN

1. **RC8 frontier concentration (50% nest)** — Two Java authenticator loci (`OpA`/`OpB`) plus two Rust RP loci (`fold_w`/`slot_v`) is intentional language split matching the idea (Java emulator × Rust RP). Max flipping-point share is 33% under the 0.5 cap.

2. **CR1 undeclared helper structs** — Oracle rewrites function bodies that share files with `RowW`/`SlotW`/`RowV`/`SlotV`/`OpA`/`OpB` types. Declared fix symbols remain the four decision functions; expanding the table to every struct tripped CR8 orchestration scans in drafting.

3. **GX3 edit distance 60** — Borderline but above the 30 floor; four coupled decision bodies with real logic (not flag flips).

4. **GX6 causal connectives** — Instruction uses “after/still/while” for hold/presence and cutover symptoms required for Instruction Sufficiency (SoftHSM stale/revoked lesson). Not a fix recipe.

## Static WARN

- Instruction length slightly over preferred paragraph guidance — needed to document graded polarities (`stale_cred`/`revoked`, hold vs revoke presence, pack-over-mark) without becoming a checklist.

## Evidence

- `./scripts/check-task.sh` preflight PASS (collapse WARN)
- `harbor run -a oracle` → Mean **1.000** (jobs/2026-07-20__18-29-10)
- `harbor run -a nop` → Mean **0.000** (jobs/2026-07-20__18-30-55)
- `approve_task.py --skip-verifier-health` → Approval gate PASS

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 1
- count of run_static_checks.py WARN-only exits before approval: 3
- count of collapse_check.py FAIL exits before first PASS: 1
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 103.30s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 464.10s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 1
- count of run_static_checks.py WARN-only exits before approval: 3
- count of collapse_check.py FAIL exits before first PASS: 1
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 103.30s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 490.87s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 2
- count of run_static_checks.py WARN-only exits before approval: 7
- count of collapse_check.py FAIL exits before first PASS: 3
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 103.30s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 173856.75s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 2
- count of run_static_checks.py WARN-only exits before approval: 10
- count of collapse_check.py FAIL exits before first PASS: 4
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 103.30s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 265714.10s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 3
- count of run_static_checks.py WARN-only exits before approval: 12
- count of collapse_check.py FAIL exits before first PASS: 4
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 103.30s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 349274.18s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 3
- count of run_static_checks.py WARN-only exits before approval: 14
- count of collapse_check.py FAIL exits before first PASS: 4
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 103.30s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 354711.39s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 3
- count of run_static_checks.py WARN-only exits before approval: 15
- count of collapse_check.py FAIL exits before first PASS: 4
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 103.30s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 358869.73s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 3
- count of run_static_checks.py WARN-only exits before approval: 16
- count of collapse_check.py FAIL exits before first PASS: 4
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 103.30s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 363731.37s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 3
- count of run_static_checks.py WARN-only exits before approval: 17
- count of collapse_check.py FAIL exits before first PASS: 4
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 103.30s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 416140.43s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 3
- count of run_static_checks.py WARN-only exits before approval: 18
- count of collapse_check.py FAIL exits before first PASS: 4
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 103.30s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 419286.93s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 3
- count of run_static_checks.py WARN-only exits before approval: 20
- count of collapse_check.py FAIL exits before first PASS: 5
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 0
- wall-clock time from first preflight to first preflight PASS: 103.30s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 424210.53s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 3
- count of run_static_checks.py WARN-only exits before approval: 21
- count of collapse_check.py FAIL exits before first PASS: 5
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 1
- wall-clock time from first preflight to first preflight PASS: 103.30s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 428123.66s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 3
- count of run_static_checks.py WARN-only exits before approval: 23
- count of collapse_check.py FAIL exits before first PASS: 5
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 1
- wall-clock time from first preflight to first preflight PASS: 103.30s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 504051.17s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 3
- count of run_static_checks.py WARN-only exits before approval: 24
- count of collapse_check.py FAIL exits before first PASS: 5
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 1
- wall-clock time from first preflight to first preflight PASS: 103.30s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 510327.03s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null

## Per-task authoring metrics

- count of run_static_checks.py FAIL exits before first PASS: 3
- count of run_static_checks.py WARN-only exits before approval: 24
- count of collapse_check.py FAIL exits before first PASS: 5
- count of dirty-flag triggers (approve_task.py refused due to checksum mismatch): 1
- wall-clock time from first preflight to first preflight PASS: 103.30s
- wall-clock time from first Step 2b PASS to approve_task.py exit 0: 510407.67s
- list of CNI references that fired during the authoring: []
- whether the spec's Initial Draft Commitments matched the final file set (draft_commitments_diff): null
