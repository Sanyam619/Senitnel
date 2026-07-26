# Fairness revise — battery-pack-thermal-conservation (2026-07-24)

Platform artifact `(22).zip`: HARD, agents 0%/0%, Instruction Sufficiency FAIL.
Nearly all residual tests 10/10; sole blockers `test_m8_obsidian` (0/10) and
`test_s4_opal` (5/10) on undocumented `cutover.ok` / `overlay.live` deletion.

## Changes
- Document sealed outcomes in `instruction.md` + `thermal_bands.md` + `thermal.spec`:
  `cutover.ok` present, `overlay.live` absent, rebuild must not rematerialize scratch.
- `rebuild.sh`: when sealed, `rm -f overlay.live` (not only skip copy).
- Tests: m8/s4 assert documented seal end-state; r1/w9/t6/k3/n5 coupled to
  rebuild survival / band residuals / ship≠fleet so free structural cells are weaker.

## Local Step 2b
- Preflight PASS (collapse WARN)
- Oracle 1.0 (`jobs/2026-07-24__18-47-23`)
- NOP 0.0 (`jobs/2026-07-24__18-47-41`)
- Zip refreshed under `Task_Ready_To_Submit/battery-pack-thermal-conservation.zip`
