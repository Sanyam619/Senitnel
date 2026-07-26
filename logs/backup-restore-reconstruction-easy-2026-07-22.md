# backup-restore-reconstruction — platform EASY + sufficiency FAIL (2026-07-22)

Artifact: `difficulty_check_artifact (9).zip`

## Result

- Difficulty ❌ EASY (need ≥ MEDIUM)
- Opus 80% (4/5), GPT-5.5 80% (4/5)
- Oracle 100%, NOP 0%
- Near-miss: 16/17 — only `test_runtime_holds_match_sealed_cutover`
- Instruction Sufficiency FAIL on both near-miss trials

## Collapse

Agents correctly repaired helpers / drop-in / cutover, then set
`PAYLOAD_LINEAGE=seal` (journal mode / `attach.intent` token) instead of
volume directory name `sealed`. Docs emphasized `attach.intent` raw token
`seal` and never stated that `PAYLOAD_LINEAGE` must be the subdirectory
name under `volumes/<episode>/`.

## Redesign (this session)

1. Document vocabulary split in `reconcile_contract.md` / `journal_format.md`
   / architecture (`seal` vs `sealed`).
2. Add abort rematerialize authority (`fold_d` + `ops/abort.d`) gated on
   durable `/var/lib/fleet/state/cutover.ok`.
3. fleetd rematerializes by copy when `PAYLOAD_LINEAGE` is not `sealed`
   (misarmed journal mode undoes hardlinks).
4. New test `test_cutover_receipt_suppresses_abort_residue`.
5. Recovery order: axle → fold_d → weave → pull → mark → bind.
