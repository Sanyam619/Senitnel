# backup-restore-reconstruction — abort.d polarity + episode pin (2026-07-24)

Platform feedback on `Task_Ready_To_Submit/backup-restore-reconstruction.zip`
(post HARD-0% fairness revise):

1. Abort residue check required synonym tokens on
   `/var/lib/fleet/ops/abort.d/90-local.conf` while docs said “rewrite abort
   synonyms in place” (agents read that as fix the abort package).
2. `test_episode_inputs_immutable` only checked existence; expectations
   recomputed from writable `/app/data/episodes`.
3. Ops docs named grader staging (`/logs/verifier`, recovery-pass logs);
   rubric rewarded “does not treat fleethealth as done”; measured medium.

## Fix

- Docs: live drop-in rewrite vs forensic abort.d synonyms polarity.
- Pin `/app/packaging/episodes.sha256` at image build; session + immutability
  checks.
- Verifier staging under `/var/log/fleet/` (ops log tree); strip private
  grader path names from packaging README.
- Rubric: fleethealth-as-done → negative; abort.d rewrite → negative.
- `difficulty = "medium"`.

## Local evidence

- Preflight PASS (collapse WARN RC2/CR1/CR7/GX1 only).
- Oracle 1.0 / NOP 0.0.
