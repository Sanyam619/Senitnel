# Platform TRIVIAL — int8-calbank-kernel-lane-cutover (2026-07-19)

Artifact: `difficulty_check_artifact (17).zip`

## Numbers
- Opus 100% (5/5), GPT-5.5 100% (5/5); oracle 100%; NOP 0%
- All 8 tests 10/10

## Collapse (from GPT/Opus trajectories)
1. **Three polarity stubs** — `knit_q` always live tip, `fold_w` always lane 0, `slot_v` always checkpoint epoch. GPT ep3: patch all three in one heredoc (~same class as signed-plugin / capsule `fold_q`/`gate_r`/`slot_w`).
2. **Answer-key instruction** — exact lanes, modes, and top1 floats for every scenario plus durable-vs-live tip spelled as the checklist.
3. **`score_u` lookup table** — graded metrics already embedded; once epoch/lane/mode flipped, table emitted the answer.
4. **Primary activity = debugging three sites**, not INT8 cal-bank × inference authority reconstruction.

## Redesign shipped (2026-07-20)
- Correct C/Rust helpers (no three polarity stubs)
- `score_u` reads scale blobs (no answer lookup table)
- Coupled authority: seal fence × journal `active_scale` × profile hot fold × resume rebase stamp
- Broken preflight always copies e3 until fixed to honor journal
- Preflight rematerializes tips every `run_eval` (naive tip JSON edits undone)
- Local: check-task PASS (collapse WARN), oracle 1.0, NOP 0.0
- Zip: `Task_Ready_To_Submit/int8-calbank-kernel-lane-cutover.zip`
