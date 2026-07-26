### Decision
GO — Attempt 1. Same as authoring spec.

### Metadata
- Task name: offline-online-feature-skew-calibration
- Title: Offline-online feature skew calibration
- Category: machine-learning
- Languages: ["rust"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["feature-store", "offline-online", "skew", "auc", "brier", "serving-eval"]
- Milestones: 0

### Discovery budget
- Discovery: Journal marks durable tip as `state=durable` tip_g7 while a newer `state=live` tip_live exists; seating must bind durable.
  Planned location: data/ledger/journal.jsonl + rank op_v body
  Why instruction must not reveal it: naming tip ids turns the task into tip transcription.
- Discovery: Graded skew is online_mean − offline_mean; ratio form can look small on some features while failing published abs bounds.
  Planned location: rank delta_q + docs bands
  Why instruction must not reveal it: pasting the operator collapses polarity discovery (outcome may state difference polarity without naming the broken body).
- Discovery: Runtime mesh overlays high-card f_zip from live shadow while prefer mode is skim, so tip-only patches still fail holdout Brier.
  Planned location: core mesh_k + prefer.toml
  Why instruction must not reveal it: would make prefer the single checklist item.

### Anti-trivialization verdict
Checks 1–21 PASS for hard ML calibration with coupled tip×skew×source×mesh×prefer; not implement-from-scratch; not three independent stubs; discovery budget ≥3; topology ≥3.

### Topology enumeration (3 candidate fix topologies)
1. Prefer-anchor + op_v durable + delta_q difference + mark_w tip string + mesh passthrough — no single file sufficient.
2. Engine-only rewrite of emit scoring with hardcoded EXPECTED — fails frozen integrity / republish if data ignored; still needs prefer for rematerialize survival.
3. Replace feathealth + surface fixture as authority — fails engine republish and band tests.

### Rubric axes
- Verifiable: Pass — deterministic JSON + republish.
- Well-specified: Pass — schema and bands documented as outcomes.
- Solvable: Pass — expert hours on feature-store seating.
- Difficult: Pass — coupled seating not checklist.
- Interesting: Pass — real offline/online skew calibration.
- Outcome-verified: Pass — grades report metrics not process.

### Instruction completeness test
Symptoms-only with fair schema/entrypoint/bands outcomes; agent cannot solve from instruction alone without eng+data reasoning.

### Collapse audit notes
Residual hardness in durable tip × difference skew × source × mesh overlay × prefer rematerialize; surface feathealth false-green.
