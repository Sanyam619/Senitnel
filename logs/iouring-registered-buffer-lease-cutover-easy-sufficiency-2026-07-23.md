# iouring-registered-buffer-lease-cutover — EASY + sufficiency FAIL (artifact 18)

## Feedback (2026-07-23)

- Difficulty ❌ EASY (Opus 80% / GPT 100%)
- Instruction Sufficiency ❌ FAIL on near-miss: correct end-state via direct
  file edits; helpers unrepaired → every `_run_cutover()` fails
- Successful agents still finished by rewriting the five polarity bash scripts

## Redesign (v2.1)

1. Fair sufficiency: durable recovery must survive re-invocation of
   `/app/ops/run_cutover.sh`; hand-applied state undone by the next pass does
   not count. No helper filename checklist.
2. Seal-cap WAL tip (`fleet.seal` + `act.wal`) as durable authority; drifted
   `fleet.toml` (epoch 9 / drift) and harbor are bait.
3. pref.d fold → seal-bound preference; cutover.ok receipt; abort.d
   rematerialize unless receipt matches.
4. ringfan/preflight require WAL tip + pref + receipt + abort open.
5. Oracle repairs helpers across ops/mesh/seat/arm/rim.
