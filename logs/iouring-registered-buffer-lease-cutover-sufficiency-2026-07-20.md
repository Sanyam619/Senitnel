# iouring-registered-buffer-lease-cutover — instruction sufficiency (2026-07-20)

Artifact: `difficulty_check_artifact (21).zip`

## Platform result

- Difficulty: HARD
- Agents: Opus 0/5, GPT-5.5 0/5 (all reward 0.0)
- Oracle: 100% (3/3), NOP: 0%
- Instruction Sufficiency: FAIL

## What failed

All 10 agent trials passed 5/6 tests and failed only `test_n4_quartz`.
Agents seated broker markers and set `mnt_ns=broker` but left pre-existing
host markers under `/data/lab/mnt/host/ten/`. The test requires those host
paths absent. Instruction said "bound into the broker mount namespace" but
never stated host markers must be removed.

## Lesson (same family as fanotify host-omit / AGENTS.md §10)

Do not put a graded end-state (host tree empty after seating) only in the
test. State the dual residency outcome in `instruction.md`. Hardness stays
in lease/seal/preflight coupling, not in an undocumented cleanup.

## Fix shipped

Added an explicit seating sentence: broker markers present, host markers
under `/data/lab/mnt/host/ten/` gone after cutover.
