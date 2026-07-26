# backup-restore-reconstruction — HARD 0% + sufficiency FAIL (2026-07-24)

Artifact: `difficulty_check_artifact (30).zip`

## Result

- Difficulty ✅ HARD
- Agents 0%/0% (Opus/GPT); every trial 17/18
- Sole miss: `test_cutover_receipt_suppresses_abort_residue`
- Instruction Sufficiency FAIL

## Collapse

“Suppress abort rematerialize” was read as delete live `90-local.conf`.
Fold still matched site standard from `10-core`/`40-lab`. One trial used
JSON `cutover.ok` vs `key=value`.

## Fairness revise (this session)

- Document: receipt is `key=value`; matching receipt skips abort copy;
  live `90-local.conf` must stay present with site-standard tokens
- Couple `test_dropin_fold_matches_site_standard` to require that file
- No complexity add; no answer-key checklist in instruction.md
