# iouring-registered-buffer-lease-cutover — reviewer: bin stand-in bypass (2026-07-22)

## Feedback

1. Main blocker: replacing `/opt/ingest/bin` with bash stand-ins passed 6/6
   without touching `/app` sources. Re-entry did not catch them.
2. Category questionable for pure C/Go patching under `system-administration`.
3. `task.toml` difficulty=hard but platform measured medium.

## Fix (complexity unchanged: same three loci)

1. `tests/test.sh` rebuilds from `/app` into `/var/lib/verifier/ingest-bin`,
   ELF-checks helpers, exports `IOURING_VERIFIER_BIN`. Tests exercise only
   that path.
2. Instruction: ops-first lab surfaces; graded path is rebuild under `/app`;
   `/opt/ingest/bin` alone is not enough. Tags ops-flavored; difficulty=medium.
3. Keep `system-administration`: primary outcomes are live unit/lease/mount/
   journal cutover under `/data/lab` (debugging category is blocked).
