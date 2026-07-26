# iouring-registered-buffer-lease-cutover — MEDIUM + sufficiency on fold (2026-07-21)

## Platform result

- Difficulty: MEDIUM ✅
- Agents: Opus 40% (2/5), GPT-5.5 80% (4/5)
- Oracle 100%, NOP 0%
- Instruction Sufficiency FAIL
- Near-miss cluster: 3/4 failed trials at 5/6 — only `test_w3_beryl`

## Root cause

Agents fixed harbor→fleet, rebuilt helpers, but left `emit_c` `fold` as no-op and
put PrivateMounts repair in `seat`/`nsbind`. Spec never said `--fold` owns
isolation repair. One trial also guessed dash-separated `buf_slot`.

`k8`/`n4`/`r2` at 10/10 were mostly genuine once rebuild worked; `k8` was
static-only (weak).

## Fix shipped

1. Instruction + field-notes: `ledgerout --fold` clears PrivateMounts drift on
   live unit + every drop-in; seating alone does not count; `buf_slot` is
   colon-joined prefix:tenant:epoch matching ring slot bodies.
2. Move fold-only re-entry to `test_k8_fluorite` (seat-only repairs fail).
3. `test_w3_beryl` grades seating + emit + preflight (no fold coupling).
4. `test_n4_quartz` adds nsbind host-bait re-entry (snapshot/restore).
