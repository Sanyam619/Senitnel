# backup-restore-reconstruction — verifier isolation + borrow polarity (2026-07-25)

Platform / author feedback on `Task_Ready_To_Submit/backup-restore-reconstruction.zip`:

1. Grading suite recomputes EXPECTED then runs agent `run_recovery.sh` while
   `/tests` is readable as root → grade-time import of `expected_for` / dump
   into `/output`.
2. Prebuilt bins restored only when missing → agent stand-ins survive.
3. `difficulty = "medium"` while measured runs are hard.
4. Rubric positive for leaving data/fleetpeek byte-identical (pays for absence).
5. Beta leases: sealed winner was also earliest-`ts` among all live claims, so
   earliest-alone greened every borrow cell.

## Fix (complexity unchanged)

- `conftest.py`: move `/tests` children aside before each recovery pass; always
  `copy2` from `/usr/lib/fleet/bin`; unseal in `finally`.
- Beta: earlier unsealed `atlas@50` + sealed `ridge@100` + later sealed
  `mesa@200` so seal-first and min-among-sealed diverge from min-among-all /
  max-among-sealed.
- `difficulty = "hard"`; drop absence +2; keep mutation `-5`.
- AUTHORING_RIGHTS_AND_WRONGS.md lessons appended.

## Local evidence

- Preflight PASS (collapse WARN justified: CR1/CR7/GX1/GX7 residual).
- Oracle 1.0 (`jobs/2026-07-25__18-27-33`).
- NOP 0.0 (`jobs/2026-07-25__18-28-32`).
- `approve_task.py` PASS.
