# Validation log — pacemaker-fence-history-seating-lattice

## Step 2a
- Category: `system-administration` (open; matches idea "System / Environment Setup & Configuration")
- Languages: `["bash"]` (ops entrypoint seating; no repair/debug framing)
- Spec: `specs/pacemaker-fence-history-seating-lattice.md` (GO)

## Step 2b evidence
- `run_static_checks.py --version edition_2`: PASS (WARNs only on discoverability of bash locals / packaging pin)
- `collapse_check.py`: 0 FAIL / 6 WARN / 17 PASS (CR1 symbol parse WARN; GX1/GX6/GX7/GX9 borderline — justified: opaque bash helpers, symptoms instruction, EXPECTED in tests from durable fixtures)
- `./scripts/check-task.sh`: Preflight PASS
- Harbor oracle 1x: **1.000** (`jobs/2026-07-25__17-13-33`)
- Harbor NOP: **0.000** (`jobs/2026-07-25__17-14-17`)

## Collapse WARN justification
- CR1/CR7: bash `name()` helpers not AST-parsed as symbols (same class as autofs seating).
- GX1: oracle replaces helper bodies; no BUG/FIXME intent comments on fix path.
- GX6/GX9: seating schema outcomes named honestly; no per-resource answer-key recital.
- GX7: packaging digest path is internal harness; fixtures integrity stated in instruction.

## Not yet claimed
- Oracle 10x (Step 4)
- `approve_task.py` / submission zip packaging for upload
