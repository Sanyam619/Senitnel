# iouring-registered-buffer-lease-cutover — HARD 0% after re-entry harden (2026-07-21)

## Platform result

- Difficulty: HARD ✅
- Agents: Opus 0% (0/5), GPT-5.5 0% (0/5)
- Oracle 100%, NOP 0%
- All 6 tests 0/10; Instruction Sufficiency FAIL

## Why every test was 0/10

Agents hand-fixed `/data/lab` + ledger correctly (~80–90% progress) but did not
rebuild broken helpers. Re-entry checks then:

1. Failed the re-entry assertion, and
2. **Poisoned shared lab state** (leasectl → harbor epoch 3; fold left
   PrivateMounts=yes; bufreg left gen=0), so later static tests also failed.

`lab.toml` `active_profile` was a red herring — unused by tools.

## Fix shipped

1. Instruction: helpers must keep fleet plane on re-invoke; soft rebuild under
   `/app`; no `make` recipe / no symbol checklist / no lab.toml recipe.
2. Static-scoring tests (`n4`, `k8`, `y6`, plus static halves of others) so
   correct lab state can score ~1–3/6 without rebuild.
3. Re-entry suites snapshot/restore so failed re-entry cannot zero unrelated tests.
4. Hardness remains in fixing `fold_a` / `SieveB` / `emit_c` for p7/r2/w3 re-entry.
