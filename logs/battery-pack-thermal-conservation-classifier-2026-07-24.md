# Classifier retheme — battery-pack-thermal-conservation (2026-07-24)

## CodeBuild fail

`[category_classifier]` predicted blocked `software-engineering` at 0.95
while `task.toml` declared `scientific-computing`. `[instruction_check]`
PASS. Pip lockfile line was WARN only (template `flask==…` example).

## Root cause

Instruction-only residual prose was not enough. Solver-visible tree still
smelled like an ops cutover desk: `/app/ops/`, `cutover.ok`, `overlay.live`,
rebuild/refresh helpers next to Python module repair.

## Fix

SPH-style scientific surface:
- `/app/scripts/{prep_eval,run_thermal_eval}.sh`
- `/app/data/policy/{handoff.accept,trial_pref.seed,trial_pref.live,handoff.spec}`
- Residual-first instruction + bands doc (handoff outcomes stated)
- Scientific tags unchanged

## Local evidence (post-retheme)

| Gate | Result |
| --- | --- |
| `./scripts/check-task.sh` | PASS (collapse 0 FAIL / 8 WARN) |
| Harbor oracle 1x | **1.0** (`jobs/2026-07-24__19-19-02`) |
| Harbor NOP | **0.0** (`jobs/2026-07-24__19-19-18`) |
| `approve_task.py --skip-verifier-health` | PASS |
| Zip | `Task_Ready_To_Submit/battery-pack-thermal-conservation.zip` (mtime after retheme) |

Lessons appended to `AGENTS.md` and `AUTHORING_RIGHTS_AND_WRONGS.md`.
