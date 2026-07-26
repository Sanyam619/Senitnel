# openldap-syncrepl-consumer-tip-lattice — validation log

## Decision
GO — system-administration OpenLDAP syncrepl consumer seating lattice.

## Step 2b evidence (2026-07-25)

| Gate | Result |
|------|--------|
| `run_static_checks.py` | PASS (WARN on solve.sh local vars JOURNAL/PREF_D/… as false-positive build-knob scan) |
| `collapse_check.py` | 0 FAIL / 3 WARN (CR1/CR7 bash `name()` parse; GX1 false-positive on `]] && continue`) |
| `./scripts/check-task.sh` | Preflight PASS |
| harbor oracle 1x | **1.000** (`jobs/2026-07-25__18-51-37`) |
| harbor NOP | **0.000** (`jobs/2026-07-25__18-51-52`) |

## WARN justifications
- **CR1/CR7**: Fix-path symbols are bash `mesh_x()`/`axle_y()`/`skim_z()`/`helm_w()`/`emit_q()` functions; the checker’s AST pass does not extract them (same class as autofs seating). Symbols are present at file roots declared in the construction manifest.
- **GX1**: Diff noise on `]] && continue` / loop guards — not intent comments narrating the fix.

## Category
`system-administration` — live `/etc/ldap` + `/var/lib/ldap` seating via bash ops; languages=`["bash"]`; no repair/debug framing.
