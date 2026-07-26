# Firmware recovery policy

Fleet recovery is driven by `/opt/abdev/config/active_policy.toml` and executed through `/opt/abdev/bin/recover` (via `/opt/abdev/ops/reconcile_field.sh`). The policy file controls rule precedence and whether staging commits are permitted.

## Policy file keys

- `rule_order` — comma-separated rule names evaluated top to bottom; the first matching rule wins.
- `allow_commit` — when `true`, the commit rule may promote a verified staging copy; when `false`, commit is skipped.

Rule names:

| Name | Action when matched |
|------|---------------------|
| `rollback_staging_b` | `rollback` when pending copy B is staging and fails integrity |
| `repoint_live_b_fail` | `repoint` when live copy B fails integrity but copy A is live |
| `commit_staging_a` | `commit` when pending copy A is verified staging and copy B is not integrity-clean |
| `rollback_live_b_fail` | `rollback` when pending copy B fails integrity and copy A is live |
| `hold` | `hold` — default finalize with mirror reconciliation only |

Canonical precedence: `rollback_staging_b,repoint_live_b_fail,commit_staging_a,rollback_live_b_fail,hold` with `allow_commit=true`.

## Rollout environment (`recover.env`)

`/opt/abdev/ops/reconcile_field.sh` sources `/opt/abdev/config/recover.env` before invoking recover. Keys:

- `AB_POLICY_FILE` — path to the active policy TOML passed to `recover --policy`.
- `AB_DATA_ROOT` — directory containing read-only scenario images.
- `AB_OUT_ROOT` — directory for corrected images (`fixed_<case>.img`).
- `AB_REPORT` — path for the JSON recovery report.
- `AB_VERIFY_BOOTSIM` — when set to `1`, post-reconcile bootsim checks are expected in field runbooks.
- `AB_PRESERVE_INPUTS` — when set to `1`, scenario images under `AB_DATA_ROOT` must not be modified.

## Mirror selection

For each copy (A or B), read both redundant `slot_hdr_t` mirrors. A mirror is usable when its header CRC32 validates. If only one mirror validates, use it. If both validate, keep the one with the higher `generation` field.

Read both `boot_ldr_t` control-sector mirrors (sectors 4 and 5). Use the first mirror whose CRC32 validates and whose `guard` equals `AB_GUARD_WORD`. Treat `pending_idx == AB_NO_PENDING` (0xFF) as no pending copy.

## Slot integrity view

For each copy, after picking metadata:

- Walk the existing digest-chain sectors (do not rewrite them) and verify they match the picked header's `root_hash`.
- `verity_ok` is true only when that walk succeeds.
- `a_live` / `b_live`: phase is live and `verity_ok`.
- `a_ok` / `b_ok`: `verity_ok` and phase is not retired.

Payload sectors and digest-chain sectors are preserved byte-for-byte from the input image. Recovery only reconciles metadata mirrors and the control-sector pair.

## Finalize writes

1. Copy the full input image into the work buffer.
2. Apply any phase changes from the matched action to the in-memory slot views.
3. For each copy, pack a fresh `slot_hdr_t` using the reconciled phase and `boot_ok`, but reuse `boot_count`, `generation`, `payload_bytes`, and `root_hash` from the picked input header. Recompute `hdr_crc32`. Write the same packed header to both metadata mirrors for that copy.
4. Pack a fresh `boot_ldr_t` with reconciled `live_idx` and `pending_idx` (or `AB_NO_PENDING`), `swap_phase = AB_SWAP_IDLE`, `guard = AB_GUARD_WORD`, and `commit_gen` equal to the picked input control record's `commit_gen` plus one. Recompute `bl_crc32`. Write identical bytes to both control-sector mirrors.
5. Set bootable flags when the reconciled copy is live-phase with passing integrity.

The report's `bootloader_hex` is the lowercase hex of the first control-sector mirror (sector 4) after finalize.
