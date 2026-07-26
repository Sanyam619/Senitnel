# backup-restore-reconstruction — category feedback (2026-07-19)

## Platform block

Declared `system-administration` was not justified: graded activity was
rewrite Rust + JSON reconcile vs oracle (debugging / data-processing).
No live host ops; entrypoint was cargo build + run; knit_a epoch / borrow
tiebreak / `run.stamp` underspecified; rubric paste described a prior
fieldday/labs/repair.json variant.

## Fix (complexity preserved)

- **Broken surfaces:** `ops/weave_k.sh`, `bag/pull_m.sh`, `rim/mark_t.sh`,
  `deck/bind_v.sh` — live `/etc/fleet`, `/var/lib/fleet`, `/var/run/fleet`.
- **Correct prebuilt** `fleetctl` / `yarder` / `fleetpeek` in image
  (`/app/bin`, restore under `/usr/lib/fleet/bin`).
- **Volume attach:** same-inode hardlink (no SYS_ADMIN `mount --bind`).
- **Service:** `fleetd` pidfile required for reconcile.
- **Instruction:** documents seal-epoch fence, borrow rule, `run.stamp`,
  admin paths; no fieldday/labs/repair.json wording.
- **α–ε semantic layers unchanged** (roster fence, sealed lease, sealed
  payload, seal-ordinal fragments, exact policy + quarantine).

## Local evidence

- `./scripts/check-task.sh` — PASS (collapse WARN only)
- harbor oracle — Mean **1.0** (13/13 tests) — `jobs/2026-07-19__14-25-50`
- harbor nop — Mean **0.0** — `jobs/2026-07-19__14-26-38`
- `approve_task.py` — PASS
- zip: `Task_Ready_To_Submit/backup-restore-reconstruction.zip`
