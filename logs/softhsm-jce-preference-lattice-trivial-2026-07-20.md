# softhsm-jce-preference-lattice — platform TRIVIAL (2026-07-20)

Artifact: `difficulty_check_artifact (23).zip` (referenced by author; local copy
may be absent). Platform: Difficulty ❌ TRIVIAL (need ≥ MEDIUM).

## Scores

- terminus-claude-opus-4-8: **100% (5/5)**
- terminus-gpt5-5: **100% (5/5)**
- oracle: 100% (3/3)
- nop: 0% (0/1)
- All 10 unit tests: **10/10**

## Prior round

HARD with 0% agents: Instruction Sufficiency FAIL on `stale_slot` vs
`revoked` polarity (agents inverted k4/p9).

## Collapse mechanism

1. Sufficiency “fix” pasted a full host reason-code recipe into
   `instruction.md` (wrong_pack ranking, mode-only, unmarked, root, stale,
   revoked).
2. Hardness remained three textbook-empty polarity stubs (`knit_xv` always
   green, `op_b` always clear, `op_c` always genOk) plus a bait
   `window.toml`.
3. Frontier agents transcribed the recipe into the stubs in one short loop —
   same class as signed-plugin / capsule / INT8 three-stub TRIVIAL.

## Do not repeat

Never answer Instruction Sufficiency by shipping an answer-key decision
table next to empty polarity bodies. Scenario prose for stale vs revoked is
fair; a checklist + stubs is TRIVIAL.

## Redesign shipped (this pass)

- Correct decision bodies (`knit_xv`, `OpB`, `OpC`).
- Wrong `FluxK`/`NestK`/`ForgeK` vs sealed fingerprint.
- JNI pack/mode byte swap in `desk_jni.c` (oracle sed, not whole-file rewrite).
- AssembleY prefers surface window + live-as-durable bind.
- `desk-reload.sh` rematerializes `NestK` from the surface window (undoes
  naive sheet edits).
- Instruction: symptoms + short stale/revoked scenario prose only (no full
  reason ranking checklist).
- Local evidence after redesign: oracle **1.0** / NOP **0.0**;
  `approve_task.py` PASS (WARN-only collapse/static).
  Zip: `Task_Ready_To_Submit/softhsm-jce-preference-lattice.zip`.

## 2026-07-22 instruction quality revise (complexity unchanged)

Platform review: instruction too long / hinting (surface window + desk-reload
rewrite), under-specified band bounds and wrong_pack-vs-stale precedence,
bare `desk-reload.sh` path. Difficulty labeled HARD while measuring Medium —
do not harden loci; tighten instruction only.

Shipped: short human-style prompt; band 4–9 inclusive; pack/mode outranks
revoke marking; absolute `/app/scripts/desk-reload.sh`; removed authority-bait
and reload rematerialize recipe.

