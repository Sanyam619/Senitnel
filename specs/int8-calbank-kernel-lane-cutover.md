### Decision
GO — Attempt 1. Machine-learning INT8 calibration-bank × kernel-lane cutover (C kernels + Rust orchestrator). No repair/debug framing: graded work is binding the durable bank tip, respecting live lane masks, and rebinding resume so golden eval scenarios pass. Surface probe uses a different reduction and can stay green while deep eval fails.

### Metadata
- version: 2
- Task name: int8-calbank-kernel-lane-cutover
- Title: INT8 Calbank Lane Cutover
- Category: machine-learning
- Languages: ["C", "Rust"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: ["int8", "calibration", "inference", "kernel-lanes", "checkpoint-resume"]
- Milestones: 0

## Authoring Brief

### Public contract

An INT8 inference cutover is underway under `/app`. Calibration banks and kernel-lane materials live under `/app/data/`. After the cutover, surface accuracy bands from the bundled surface probe look healthy, but golden evaluation scenarios fail under checkpoint resume, mixed-precision fallback, and bank-epoch drift away from the durable tip.

**Required outcomes:**
- `/output/eval-ledger.json` produced via `/app/ops/run_eval.sh` with integer `version` `1`, integer `bank_epoch`, and array `scenarios`.
- Each scenario object has string `id`, string `lane`, string `mode` (`int8` or `mixed`), and number `top1`.
- Required scenario ids: `cold_a`, `resume_a`, `cold_b`, `resume_b`, `mix_c`, `mix_d`.
- `cold_a.top1` equals `resume_a.top1`; `cold_b.top1` equals `resume_b.top1` (resume rebinds to the durable tip).
- `bank_epoch` equals the sealed durable tip epoch under `/app/data/banks/` (not the live tip).
- Lane assignments: `cold_a`/`resume_a` → `k1`; `cold_b`/`resume_b` → `k0`; `mix_c` → `k2` with `mode` `mixed`; `mix_d` → `k1` with `mode` `int8`.
- Graded `top1` values (verifier-owned, also stated for sufficiency): `cold_a`/`resume_a` = `0.91`; `cold_b`/`resume_b` = `0.87`; `mix_c` = `0.84`; `mix_d` = `0.89`.
- Deep ledger must disagree with `/app/data/fixtures/surface_ok.json` on at least one shared scenario `top1`.
- `/app/data/fixtures/` unchanged.

**Constraints:**
- `[environment] allow_internet = false`; verifier deps in Dockerfile.
- Languages: C (kernels) + Rust (runtime/orchestrator).
- Instruction is cutover/eval outcomes — not a repair/debug checklist and not a cargo/make recipe as the task.
- No multi-container / UI.

### Failure topology

Three coupled authorities. (1) Bank tip: live tip and durable tip disagree on epoch; surface probe binds live; deep eval must bind sealed durable. (2) Kernel-lane mask: roster rows carry a live-mask bit; lane pick that ignores the bit greens surface averages while distant scenarios land on the wrong kernel. (3) Resume: checkpoint stores a stale bank epoch; without rebind to the durable tip, resume `top1` diverges from cold-start even when cold looks correct. Mixed-precision fallback (`mix_c`) only stays in-band when the selected lane and durable scales agree. Greening any one locus fails distant eval cells.

### Environment shape

- Rust workspace `orch/` — orchestrator, tip bind, resume rebind, ledger emit; decoy tip helper used only by surface probe.
- C `n4/` — lane fold with live-mask, INT8 score kernels, decoy fold used by surface probe.
- `/app/data/banks/` — tip_live / tip_durable + per-epoch scale blobs.
- `/app/data/lanes/roster.jsonl` — lane ids + live-mask bits.
- `/app/data/checkpoints/` — resume payloads with stale epoch.
- `/app/data/eval/` — scenario tensors/labels.
- `/app/data/fixtures/` — seed + surface_ok bait.
- `/app/ops/run_eval.sh` — deep eval entry; surface probe is separate bait.
- Dockerfile builds C shared objects + Rust `runtime` binary; toolchains remain for agent rebuild.

### Required artifacts

Standard single-step layout under `tasks/int8-calbank-kernel-lane-cutover/` with 20+ environment files (excl. Docker), C+Rust sources, tests with ≥6 hard outcome checks, oracle `solve.sh` that corrects the three loci and reruns eval (≥30 substantive LOC).

### Test plan

- `test_k7_zircon` — `bank_epoch` equals durable tip epoch; not live tip.
- `test_m3_obsidian` — lane matrix for all six scenarios matches required assignments.
- `test_p9_garnet` — resume/cold `top1` pairs equal for a and b.
- `test_q2_topaz` — graded `top1` values match verifier EXPECTED for all six scenarios.
- `test_r5_onyx` — modes: mix_c is `mixed`, others `int8` as specified.
- `test_t8_amber` — deep ledger disagrees with surface_ok on a shared scenario `top1`.
- `test_w4_jade` — fixtures seed checksum unchanged; ledger schema version 1.
- `test_n6_quartz` — re-invoke `run_eval.sh` after a no-op and require identical ledger (stability).

Multiple approaches OK if outcomes match. Not chain-dependent beyond needing a complete ledger file.

### Drafting guardrails

Symptoms-only instruction (cutover/eval language). No “fix knit_q / fold_w / slot_v”. Opaque fix-path symbols. No answer-shaped tip preference in ops notes. Surface probe must remain a real false-green path. EXPECTED metrics live in tests (and graded values restated in instruction for sufficiency, not as a patch recipe). Forbidden instruction tokens must not appear as fix-path symbol names.

### Triviality Ledger

- Binding live tip greens surface but fails `test_k7_zircon` and graded top1.
- Ignoring live-mask still may pass one cold scenario but fails the lane matrix (`test_m3_obsidian`) and mix_c.
- Fixing tip without resume rebind fails `test_p9_garnet` (resume keeps stale epoch).
- Hand-writing eval-ledger.json fails rebuild/stability and surface-gap checks that re-run the binary.
- Copying surface_ok into the ledger fails `test_t8_amber`.

### Per-gate Pitfall Inventory

- RC1/RC7: Oracle patches three loci with substantive logic (≥30 LOC), not sed deletes.
- RC2: Opaque names (`knit_q`, `fold_w`, `slot_v`); no broken_/fix_me_ paths.
- RC3: Tests assert computed top1/lanes/epoch, not format alone.
- RC4/RC5: EXPECTED in test code; no golden under environment answering the ledger.
- RC6: Instruction symptoms-only cutover framing; no algorithm checklist.
- GX9: Graded top1 stated once per scenario with clear binding (sufficiency), not a dense answer recital window for every field.
- GX10: No polarity contradictions (durable vs live separated into distinct sentences).
- CR1–CR9: symbol_table / flipping_point / decoys / forbidden tokens enforced.
- Static: `allow_internet=false`, `.dockerignore`, absolute paths, pinned deps, no COPY of hidden build-context dirs.

### Initial Draft Commitments

- `tasks/int8-calbank-kernel-lane-cutover/task.toml`
- `tasks/int8-calbank-kernel-lane-cutover/instruction.md`
- `tasks/int8-calbank-kernel-lane-cutover/output_contract.toml`
- `tasks/int8-calbank-kernel-lane-cutover/tests/test.sh`
- `tasks/int8-calbank-kernel-lane-cutover/tests/test_outputs.py`
- `tasks/int8-calbank-kernel-lane-cutover/solution/solve.sh`
- `tasks/int8-calbank-kernel-lane-cutover/environment/Dockerfile`
- `tasks/int8-calbank-kernel-lane-cutover/environment/.dockerignore`
- `tasks/int8-calbank-kernel-lane-cutover/environment/Cargo.toml`
- `tasks/int8-calbank-kernel-lane-cutover/environment/Cargo.lock`
- `tasks/int8-calbank-kernel-lane-cutover/environment/orch/Cargo.toml`
- `tasks/int8-calbank-kernel-lane-cutover/environment/q7/src/main.rs`
- `tasks/int8-calbank-kernel-lane-cutover/environment/q7/src/knit_q.rs`
- `tasks/int8-calbank-kernel-lane-cutover/environment/q7/src/slot_v.rs`
- `tasks/int8-calbank-kernel-lane-cutover/environment/q7/src/emit_z.rs`
- `tasks/int8-calbank-kernel-lane-cutover/environment/q7/src/decoy_tip.rs`
- `tasks/int8-calbank-kernel-lane-cutover/environment/q7/src/run_a.rs`
- `tasks/int8-calbank-kernel-lane-cutover/environment/q7/src/run_b.rs`
- `tasks/int8-calbank-kernel-lane-cutover/environment/q7/src/run_c.rs`
- `tasks/int8-calbank-kernel-lane-cutover/environment/orch/build.rs`
- `tasks/int8-calbank-kernel-lane-cutover/environment/n4/Makefile`
- `tasks/int8-calbank-kernel-lane-cutover/environment/n4/fold_w.c`
- `tasks/int8-calbank-kernel-lane-cutover/environment/n4/fold_w.h`
- `tasks/int8-calbank-kernel-lane-cutover/environment/n4/score_u.c`
- `tasks/int8-calbank-kernel-lane-cutover/environment/n4/score_u.h`
- `tasks/int8-calbank-kernel-lane-cutover/environment/n4/decoy_fold.c`
- `tasks/int8-calbank-kernel-lane-cutover/environment/n4/include/rt_abi.h`
- `tasks/int8-calbank-kernel-lane-cutover/environment/ops/run_eval.sh`
- `tasks/int8-calbank-kernel-lane-cutover/environment/ops/run_surface.sh`
- `tasks/int8-calbank-kernel-lane-cutover/environment/ops/field_notes.md`
- `tasks/int8-calbank-kernel-lane-cutover/environment/config/runtime.toml`
- `tasks/int8-calbank-kernel-lane-cutover/environment/scripts/build_all.sh`
- `tasks/int8-calbank-kernel-lane-cutover/environment/surf/surfprobe.c`
- `tasks/int8-calbank-kernel-lane-cutover/environment/data/banks/tip_live.json`
- `tasks/int8-calbank-kernel-lane-cutover/environment/data/banks/tip_durable.json`
- `tasks/int8-calbank-kernel-lane-cutover/environment/data/banks/scales_e3.bin`
- `tasks/int8-calbank-kernel-lane-cutover/environment/data/banks/scales_e7.bin`
- `tasks/int8-calbank-kernel-lane-cutover/environment/data/lanes/roster.jsonl`
- `tasks/int8-calbank-kernel-lane-cutover/environment/data/checkpoints/resume_pack.json`
- `tasks/int8-calbank-kernel-lane-cutover/environment/data/eval/scenarios.json`
- `tasks/int8-calbank-kernel-lane-cutover/environment/data/fixtures/seed.json`
- `tasks/int8-calbank-kernel-lane-cutover/environment/data/fixtures/surface_ok.json`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: q7/src/knit_q.rs
  symbol: knit_q
  kind: function
  signature: pub fn knit_q(a: u32, b: u32, c: u8) -> u32
  purpose: Selects which bank epoch integer to bind for deep evaluation given two tip epochs and a sealed flag byte.

- path: n4/fold_w.c
  symbol: fold_w
  kind: function
  signature: int fold_w(const unsigned char *a, int b, int c)
  purpose: Chooses a kernel lane index from a live-mask byte vector with a fallback index.

- path: q7/src/slot_v.rs
  symbol: slot_v
  kind: function
  signature: pub fn slot_v(a: u32, b: u32, c: u8) -> u32
  purpose: Chooses the epoch used after checkpoint resume given checkpoint epoch, bound tip epoch, and a resume flag.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: q7/src/knit_q.rs
    controls_tests: [test_k7_zircon, test_q2_topaz]
  - id: B
    path: n4/fold_w.c
    controls_tests: [test_m3_obsidian, test_r5_onyx]
  - id: C
    path: q7/src/slot_v.rs
    controls_tests: [test_p9_garnet, test_t8_amber, test_w4_jade, test_n6_quartz]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: q7/src/decoy_tip.rs
  kind: helper
  rhymes_with: knit_q
  non_fix_purpose: Always returns the live tip epoch; used only by surfprobe path.

- path: n4/decoy_fold.c
  kind: helper
  rhymes_with: fold_w
  non_fix_purpose: Picks lane 0 unconditionally for surface mean-abs reduction; ignores live-mask.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [calibration, bank, epoch, durable, live, tip, kernel, lane, mask, resume, checkpoint, mixed, precision, fallback, inference, int8, top1, scenario, ledger, surface, probe, cutover, orchestrator, eval, accuracy, bind, rebind, scale, roster, golden]
```
