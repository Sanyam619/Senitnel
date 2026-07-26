### Decision
GO — Attempt 1. Machine-learning INT8 calibration-bank × kernel-lane cutover (C kernels + Rust orchestrator). No repair/debug framing: graded work is binding the durable bank tip, respecting live lane masks, and rebinding resume so golden eval scenarios pass. Surface probe uses a different reduction and can stay green while deep eval fails.

### Metadata
- Task name: int8-calbank-kernel-lane-cutover
- Title: INT8 Calbank Lane Cutover
- Category: machine-learning
- Languages: ["C", "Rust"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: ["int8", "calibration", "inference", "kernel-lanes", "checkpoint-resume"]
- Milestones: 0

### Discovery budget
- Discovery: Sealed durable tip epoch is 7; live tip epoch is 3; deep eval must bind 7.
  Planned location: `data/banks/tip_durable.json` (`sealed: true`) vs `tip_live.json`; `knit_q` reads sealed flag.
  Why instruction must not reveal it: Naming “always prefer durable epoch 7” collapses tip authority to transcription.

- Discovery: Live-mask bit `0x01` on roster rows selects lanes k1/k0/k2; ignoring mask defaults to k0 and breaks mix_c.
  Planned location: `data/lanes/roster.jsonl` + `n4/fold_w.c`.
  Why instruction must not reveal it: Publishing the bit/lane table turns lane selection into a checklist.

- Discovery: Resume pack stores stale epoch 3; `slot_v` must rebind to the deep-bound tip or resume top1 diverges.
  Planned location: `data/checkpoints/resume_pack.json` + `q7/src/slot_v.rs`.
  Why instruction must not reveal it: “On resume replace checkpoint epoch with tip” is the cause, not a symptom.

- Discovery: Surface probe uses mean-abs via decoy_fold/decoy_tip and reports inflated top1 in surface_ok.json.
  Planned location: `surf/surfprobe.c`, `decoy_*`, `data/fixtures/surface_ok.json`.
  Why instruction must not reveal it: Telling agents to ignore surface removes the false-green trap that catches ledger copy.

### Anti-trivialization verdict
All 21 checks PASS for this design: symptoms-only cutover framing; multi-locus tip×mask×resume coupling; opaque symbols; verifier-owned EXPECTED; not blank-canvas training; not LoRA/spec-decode; not three polarity stubs alone — each locus interacts with distant eval cells.

### Topology enumeration (3 candidate fix topologies)
1. **Tip-first then mask then resume:** `knit_q` → `fold_w` → `slot_v`. Tip alone cannot fix lane matrix or resume equality.
2. **Mask-first scoring path:** Correct `fold_w` with wrong tip still fails durable epoch and graded top1; resume still stale.
3. **Resume-centric emit path:** Correct `slot_v` with wrong tip/mask yields matching-but-wrong resume pairs or wrong lanes — still fails zircon/obsidian/topaz.

### Rubric axes
- Verifiable: PASS — deterministic JSON ledger + fixture checksum.
- Well-specified: PASS — schema and graded outcomes in instruction.
- Solvable: PASS — expert can recover tip/mask/resume from data+code in hours.
- Difficult: PASS — cross-language authority coupling outside textbook INT8 recipes.
- Interesting: PASS — real INT8 cal-bank cutover failure mode.
- Outcome-verified: PASS — grades ledger metrics, not process.

### Hardness axes
- Discover: PASS — durable vs live, mask bit, stale resume epoch not in instruction as causes.
- Synthesize: PASS — C kernels + Rust orch + banks + checkpoints + surface bait.
- Diagnose: PASS — symptoms are failed eval under resume/mixed/bank drift.
- Navigate coupling: PASS — local tip fix fails resume/lanes; local mask fix fails epoch/top1.
- Reason beyond training: PASS — not blank training loop; cal-bank tip × lane mask × resume rebind.

### Instruction completeness test
No — instruction states cutover symptoms and graded outcome numbers but does not name which tip is authoritative, how live-mask bytes select lanes, or that resume must discard checkpoint epoch. Solver must read banks/roster/checkpoint code paths.

## Reviewer Appendix

### Implementation plan
Ship a Rust orchestrator that loads tips, roster, checkpoints, and calls C `fold_w`/`score_u` to emit `/output/eval-ledger.json`. Broken defaults prefer live tip, ignore live-mask, and keep checkpoint epoch on resume. Surface probe links decoys and writes a false-green fixture. Oracle corrects `knit_q`, `fold_w`, and `slot_v`, rebuilds, and runs deep eval.

### Proposed file inventory
Matches Authoring Brief Initial Draft Commitments (35+ environment paths including banks, lanes, eval, fixtures, kernels, orch, ops, surf).

### Oracle notes
Rewrite `knit_q` to return durable epoch when sealed flag set; rewrite `fold_w` to scan live-mask bit; rewrite `slot_v` to return tip epoch when resume flag set; rebuild via `scripts/build_all.sh`; run `ops/run_eval.sh`.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
Three coordinated body rewrites across Rust tip bind, C lane fold, and Rust resume rebind — not a single config flip.

Likely editable frontier:
- q7/src/knit_q.rs, q7/src/slot_v.rs, n4/fold_w.c

Requirement-to-file map:
- durable bank_epoch -> knit_q
- lane matrix / mixed mode -> fold_w
- resume equality -> slot_v

Oracle estimated complexity: 80–120 non-boilerplate LOC including rebuild/run.

Red flags:
- none if instruction stays cutover-framed and symbols stay opaque

Residual hardness:
Even with file tree visible, agent must infer sealed-tip precedence, mask semantics, and resume rebind from behavior and data — surface probe remains a trap.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
INT8, inference, cutover, calibration, banks, kernel, lanes, surface, accuracy, bands, probe, evaluation, scenarios, checkpoint, resume, mixed-precision, fallback, bank-epoch, durable, tip, ledger, version, bank_epoch, id, lane, mode, top1, cold_a, resume_a, cold_b, resume_b, mix_c, mix_d, fixtures

**Renames during drafting:**
- None — first-pass naming used knit_q / fold_w / slot_v against the forbidden list

**Test names audited:**
- test_k7_zircon
- test_m3_obsidian
- test_p9_garnet
- test_q2_topaz
- test_r5_onyx
- test_t8_amber
- test_w4_jade
- test_n6_quartz

**Concentration math:**
- Total tests across flipping_point_contract: 8
- Per location:
  - L1 (q7/src/knit_q.rs): 2/8 = 0.25
  - L2 (n4/fold_w.c): 2/8 = 0.25
  - L3 (q7/src/slot_v.rs): 4/8 = 0.50
- Cap: 0.5. Max ratio observed: 0.50. Status: PASS

### Per-test feasibility pre-check
- Test: test_k7_zircon — Checks durable bank_epoch — Valid approaches: 2+ — Chain-dependent: no — Feasibility: LOW
- Test: test_m3_obsidian — Checks lane matrix — Valid approaches: 2+ — Chain-dependent: no — Feasibility: LOW
- Test: test_p9_garnet — Checks resume=cold top1 — Valid approaches: 2+ — Chain-dependent: no — Feasibility: LOW
- Test: test_q2_topaz — Checks graded top1 — Valid approaches: 1 (correct bind) — Chain-dependent: no — Feasibility: LOW
- Test: test_r5_onyx — Checks modes — Valid approaches: 2+ — Chain-dependent: no — Feasibility: LOW
- Test: test_t8_amber — Checks surface gap — Valid approaches: 2+ — Chain-dependent: no — Feasibility: LOW
- Test: test_w4_jade — Checks fixtures+schema — Valid approaches: 2+ — Chain-dependent: no — Feasibility: LOW
- Test: test_n6_quartz — Checks re-run stability — Valid approaches: 2+ — Chain-dependent: no — Feasibility: LOW
