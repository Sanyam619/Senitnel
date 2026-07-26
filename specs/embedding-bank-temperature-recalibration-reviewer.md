### Decision
GO — Attempt 2. 0F/0W structured evidence. Symptoms-only instruction; five-location flipping contract across three roots (max share 0.44); build-authority gate (ops/prefer.toml) rematerializes two rank sources so source-only patches are undone on the verifier rebuild; scale value made load-bearing via score fusion + soft-assignment agreement so it cannot be cosmetically pinned.

### Metadata
- Task name: embedding-bank-temperature-recalibration
- Title: Embedding Bank Recalibration
- Category: machine-learning
- Languages: ["rust", "bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["embeddings", "temperature", "calibration-bank", "checkpoint-resume", "recall-at-k", "inference-eval"]
- Milestones: 0

### Discovery budget

- Discovery: The ledger JSONL distinguishes committed (sealed) lines from working lines; every cell must bind to the newest committed index while the binder currently takes the newest line of any state.
  Planned location: `data/ledger/journal.jsonl` marks + `rank/src/knot.rs` behavior.
  Why instruction must not reveal it: naming the sealed-marker rule turns the generation fix into a one-line transcription; the instruction only says the committed generation ("durable tip, not live tip") must be reported.
- Discovery: Resumed checkpoint blobs carry per-block scale frames that the decoder drops, silently changing vector norms and breaking cold/resume retrieval parity (and, through score fusion, NMI).
  Planned location: binary framing of `data/checkpoints/resume_*.ckpt` + `core/src/lens.rs`.
  Why instruction must not reveal it: stating that resumed blobs are block-scaled is the diagnosis; the instruction only states the parity symptom.
- Discovery: `ops/prefer.toml` holds a binding mode; while it stays on the working line (`skim`), the rank crate's build script rematerializes both rank sources from seed templates on every build, so naive source-only fixes are undone when the verifier rebuilds.
  Planned location: `ops/prefer.toml`, `rank/build.rs`, `rank/seeds/*.rs.in`.
  Why instruction must not reveal it: this is the authority-coupling discovery; revealing it reduces the task to a config flip plus edits.
- Discovery: Composed cells must be assembled from the ledger's composition roster, excluding withdrawn segments; the assembler currently concatenates every segment present on disk.
  Planned location: `core/src/weave.rs` + withdrawal marks in the ledger.
  Why instruction must not reveal it: naming the withdrawal rule turns mixed-cell repair into transcription.
- Discovery: The scale sheet family is keyed by generation and only one family is committed (referenced from sealed ledger lines); the resolver currently reads the bait family that tracks the working line.
  Planned location: `data/sched/table_a7.toml` vs `data/sched/table_w2.toml` + `rank/src/facet.rs`.
  Why instruction must not reveal it: pointing at the correct sheet file is the answer; the instruction only requires the value to sit inside the published band.

### Anti-trivialization verdict

| # | Check | Verdict | Reasoning |
|---|-------|---------|-----------|
| 1 | Disclosure-collapse | PASS | Honest statement of every graded outcome reveals no fix site; the gate/rematerialization and data semantics stay hidden. |
| 2 | Hidden-instance | PASS | All six cells are wrong in the shipped state; difficulty is coupling, not instance search. |
| 3 | Single-artifact repair | PASS | Five locations across three roots; max test share 0.44. |
| 4 | Generalization | PASS | Six cells over two data families + two compositions grade the same code paths; per-cell hardcoding fails rebuild/recompute tests. |
| 5 | Prompt-honesty | PASS | The prompt already names all ids and outcomes; nothing positional leaks. |
| 6 | Cheating-vs-difficulty | PASS | Tamper gates (rebuild, trace, byte-identity, checksums) are not the claimed hardness. |
| 7 | Mechanical-fix filter | PASS | No dep/timeout/footer issues in the design. |
| 8 | Localized-fix | PASS | Fix spans two crates + config; prompt names none of them. |
| 9 | Oracle-locality | PASS | Oracle edits four function bodies + one key; no wholesale file replacement. |
| 10 | Small declarative-cluster | PASS | The single config key only matters because the build script enforces it; the rest is semantic code. |
| 11 | Grep-collapse | PASS | Naming pass bans all 32 instruction nouns from fix-path symbols/paths/test names. |
| 12 | Pre-factored-helper | PASS | Decoys rhyme with fix-path symbols and do genuine non-fix work. |
| 13 | Recipe-discount | PASS | Sealed-ledger binding, block-scale decoding, roster filtering are not textbook recipes. |
| 14 | Security-aura discount | PASS | No security aura claimed; hardness argued from ML-eval semantics. |
| 15 | Orthogonal-checklist | PASS | Requirements couple: binding→sheet→scale→both metrics; decoder+roster intersect at mixed cells; gate spans all rebuilt-report tests. |
| 16 | Harness-discount | PASS | Single container; no harness complexity claimed as hardness. |
| 17 | One-pass solvability | PASS | Decoys defeat shape-scanning; the first source-only patch is reverted by the rebuild, forcing a second discovery loop. |
| 18 | Hard-only gate | PASS | Five coupled loci, authority gate, numeric parity/band outcomes on six cells — above medium. |
| 19 | Discovery budget (BLOCKING) | PASS | Five non-trivial discoveries enumerated above. |
| 20 | Instruction specificity | PASS | Symptoms-only. |
| 21 | Topology distribution (BLOCKING) | PASS | Three topologies below, each ≥3 coordinated locations. |

### Topology enumeration (3 candidate fix topologies)

1. **T1 (chosen): binding-authority gate over two rank resolvers plus two core data-path fixes.** Locations: `ops/prefer.toml`, `rank/src/knot.rs`, `rank/src/facet.rs`, `core/src/lens.rs`, `core/src/weave.rs`. No single location suffices: the config flip alone leaves broken bodies; fixed bodies alone are reverted on rebuild; core fixes alone leave generation/scale cells red.
2. **T2: resolvers folded into the emit binary, blob decoding split into a codec module, ledger parsing in base.** Locations: `emit/src/main.rs`, `core/src/base.rs`, `core/src/codec.rs`, `ops/prefer.toml`. Binding, decoding, and sheet lookup live in three modules feeding one report; fixing any one leaves cells governed by the others wrong.
3. **T3: a ledger compaction tool materializes the committed view; engine binds to the materialized view; a sheet materializer regenerates the committed family.** Locations: `tools/compact/src/main.rs`, `rank/src/knot.rs`, sheet materializer under `scripts/`, `core/src/weave.rs`. Compactor, binder, and materializer must agree on the committed index; mixed cells still need the roster fix.

### Rubric axes

- Verifiable — PASS: fixed seeds, pinned fixtures, canonical JSON, numeric bands/tolerances, byte-identity.
- Well-specified — PASS: two-paragraph contract; two readers produce equivalent verifiers.
- Solvable — PASS: bounded function-level edits + one config key; hours for an expert.
- Difficult — PASS: practitioner-level resume-parity/calibration-lifecycle reasoning plus an authority gate that reverts naive edits.
- Interesting — PASS: restoring an embedding eval stack to published bands after a botched resume/calibration rollout is paid ML work.
- Outcome-verified — PASS: grades the report, rebuilt agreement, determinism; no process dictated.

### Hardness axes

- Discover — Ledger seal semantics, block-scale framing, gate rematerialization, withdrawal roster, committed sheet family: all live only in tree/runtime.
- Synthesize — Two crates, a build script, a config, ledger data, and sheet data must be modeled together; no single file holds the solution.
- Diagnose — Instruction gives parity/band/generation symptoms; causes must be inferred from behavior diffs and binary framing.
- Navigate coupling — Source fixes are undone by the gate on rebuild; scale depends on binding; mixed cells depend on decoder AND roster.
- Reason beyond training — Scale enters score fusion + soft-assignment agreement (not the textbook monotone-softmax case); bespoke framing/ledger semantics resist pattern matching.

### Instruction completeness test

No. The instruction gives the output contract and symptoms but not the ledger semantics, the checkpoint framing, the sheet family layout, the withdrawal roster, or the binding-gated rematerialization. Implementing only what it says (emit a six-cell report) fails rebuild-equality, parity, band, and generation tests.

## Reviewer Appendix

### Implementation plan

The environment ships a three-crate Rust workspace (core: IO/decoding/assembly/metrics; rank: ledger binding + scale resolution with a build script; emit: CLI + canonical JSON), an ops config pair, frozen binary banks/checkpoints, a ledger JSONL with sealed/working/withdrawn marks, two sheet families, published bands docs, and a bash entrypoint. Four semantic defects (dropped block-scale frames, newest-line binding, bait-sheet lookup, roster-ignoring assembly) plus a build-authority gate (working-line mode causes the build script to rematerialize both rank sources from broken seeds) leave all six report cells out of band. The agent must diagnose from symptoms, fix the four sites, and discover/flip the gate so fixes survive the verifier rebuild. Hardness: coupled propagation (binding→sheet→scale→metrics), intersection cells (mix depends on decoder AND roster), and the gate forcing a second discovery loop after the first "green" local patch.

### Proposed file inventory

See "Initial Draft Commitments" in the authoring spec — that list is authoritative (51 paths; 47 under environment/ + data, comfortably over the 20-file floor). One-line roles: workspace + three crates (10 source files incl. 2 decoys + build.rs + 2 seeds), ops configs + runbook (3), entrypoint (1), docs bands (1), ledger + 2 sheets (3), 8 bank segments, 4 checkpoints, bait fixture (1), Docker/requirements/dockerignore (3), tests (3), oracle (1), instruction/task/output-contract/manifest (4), fixture generator (1).

### Oracle notes

solve.sh applies five edits: (1) `core/src/lens.rs` — parse the per-block frame header when present and apply block scales while decoding rows; (2) `rank/src/knot.rs` — filter ledger lines to the committed state and take the newest such index; (3) `rank/src/facet.rs` — key the committed sheet family by the bound index instead of reading the working-line family; (4) `core/src/weave.rs` — build composed collections from the ledger roster, skipping withdrawn segments; (5) `ops/prefer.toml` — set `[bind] mode = "anchor"` so the build script stops rematerializing the rank sources. Then run the entrypoint once (tests run it again for byte-identity). Edits are body rewrites via targeted patches, not file swaps.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
Approximately 60-90 lines of semantic change across five files: frame parsing + application in the decoder; state filtering in the binder; keyed committed-family lookup in the resolver; roster filtering in the assembler; one config key flip that only helps once the two rank sources are also correct.

Likely editable frontier:
- core/src/lens.rs
- core/src/weave.rs
- rank/src/knot.rs
- rank/src/facet.rs
- ops/prefer.toml

Requirement-to-file map:
- cold/resume recall parity -> core/src/lens.rs
- bank_epoch = committed index -> rank/src/knot.rs (+ ops/prefer.toml survival)
- temperature in band / committed sheet row -> rank/src/facet.rs (+ knot_r binding, + ops/prefer.toml survival)
- mix cells in band -> core/src/weave.rs (+ lens_unfold)
- rebuilt report equality / re-entry -> ops/prefer.toml

Oracle estimated complexity: 60-90 non-boilerplate lines

Red flags:
- none

Residual hardness:
Even with the tree visible, the solver must reverse the block-scale frame layout from binary fixtures, infer sealed-vs-working ledger semantics from data plus outcome docs, realize the sheet family is generation-keyed and which family is committed, discover the rematerialization by observing its own edits reverted on rebuild, and keep six cells plus determinism green simultaneously.

Collapse verdict: PASS

### Naming-pass record

**Instruction nouns extracted:**
embedding, retrieval, evaluation, band, report, engine, metric, schema, scenario, recall, nmi, temperature, bank, epoch, cold, resume, twin, pair, mix, calibration, generation, durable, tip, live, checkpoint, surface, probe, entrypoint, fixture, verification, restart, documentation

**Renames during drafting:**
- `pick_epoch` → `knot_r`: 'epoch' is an instruction noun; the binder must be opaque to it.
- `temp_sheet_lookup` → `facet_q`: 'temperature' is an instruction noun and 'temp' telegraphs it.
- `unpack_resume_blocks` → `lens_unfold`: 'resume' is an instruction noun.
- `mix_roster` → `weave_m`: 'mix' is an instruction noun.
- prefer.toml values `live`/`durable` → `skim`/`anchor`: 'live' and 'durable' are instruction nouns; config vocabulary made opaque.

**Test names audited:**
- test_j2_pyrite
- test_k4_agate
- test_p7_jasper
- test_r3_garnet
- test_t6_beryl
- test_m5_onyx
- test_w1_topaz
- test_v8_lazuli
- test_d9_quartz
- test_e2_opal
- test_h3_zircon
- test_g6_flint
- test_s4_coral

**Concentration math:**
- Total tests across `flipping_point_contract`: 9
- Per location:
  - A (`ops/prefer.toml`): 4/9 = 0.444
  - B (`rank/src/knot.rs`): 4/9 = 0.444
  - C (`rank/src/facet.rs`): 3/9 = 0.333
  - D (`core/src/lens.rs`): 4/9 = 0.444
  - E (`core/src/weave.rs`): 3/9 = 0.333
- Cap: 0.5. Max ratio observed: 0.444. Status: PASS

### Per-test feasibility pre-check

- Test: test_j2_pyrite — Checks: frozen inputs hash-match pins. Valid approaches: n/a (integrity). Chain-dependent: no. Feasibility risk: LOW (regenerate pins from linux/amd64).
- Test: test_k4_agate — Checks: report shape/ids/types. Valid approaches: 2+. Chain-dependent: no. Feasibility risk: LOW.
- Test: test_p7_jasper — Checks: paired recall agreement 1e-4. Valid approaches: 2+ (any correct decode). Chain-dependent: yes (decoder). Feasibility risk: LOW (fixtures constructed so correct decode gives exact parity).
- Test: test_r3_garnet / test_t6_beryl — Checks: per-family band membership. Valid approaches: 2+. Chain-dependent: yes (decoder + scale). Feasibility risk: MEDIUM — bands must be generated from the oracle engine with margin; mitigate by deriving bands from oracle values ± comfortable widths during fixture generation.
- Test: test_m5_onyx — Checks: composed cells in band and equal to verifier recompute. Valid approaches: constrained by recompute (equivalent implementations still match since inputs/algorithm contract fixed). Chain-dependent: yes (decoder + roster + binding). Feasibility risk: MEDIUM — verifier recompute must use the rebuilt engine, not a parallel Python reimplementation, to avoid double-implementation drift.
- Test: test_w1_topaz — Checks: scale equals committed sheet row and in band. Valid approaches: 2+. Chain-dependent: yes (binder + resolver + gate). Feasibility risk: LOW.
- Test: test_v8_lazuli — Checks: generation equals verifier-computed committed index. Valid approaches: 2+. Chain-dependent: yes (binder + gate). Feasibility risk: LOW.
- Test: test_d9_quartz — Checks: byte-identical double run. Valid approaches: 2+ (any deterministic emitter). Chain-dependent: no. Feasibility risk: LOW (canonical JSON writer, no timestamps).
- Test: test_e2_opal — Checks: staged rebuild + rerun equals shipped report. Valid approaches: 2+. Chain-dependent: yes (all five locations). Feasibility risk: MEDIUM — staging copy must include ops/ and seeds; cargo offline build in verifier must be warm (vendor or pre-fetched registry).
- Test: test_h3_zircon — Checks: trace stream reconstructs aggregates. Valid approaches: 2+. Chain-dependent: yes (engine is real producer). Feasibility risk: LOW.
- Test: test_g6_flint — Checks: bands_ok true and values differ from bait fixture. Valid approaches: 2+. Chain-dependent: yes. Feasibility risk: LOW (bait values chosen off the oracle values).
- Test: test_s4_coral — Checks: re-entry rebuild stays green/identical. Valid approaches: 2+. Chain-dependent: yes (gate). Feasibility risk: MEDIUM — build script must be deterministic and not dirty the report when mode is anchor.
