### Decision
GO — Attempt 2. 0F/0W structured evidence. Symptoms-only instruction; five-location flipping contract across three roots (max share 0.44); build-authority gate (ops/prefer.toml) rematerializes two rank sources so source-only patches are undone on the verifier rebuild; scale value made load-bearing via score fusion + soft-assignment agreement so it cannot be cosmetically pinned.

### Metadata
- version: 2
- Task name: embedding-bank-temperature-recalibration
- Title: Embedding Bank Recalibration
- Category: machine-learning
- Languages: ["rust", "bash"]
- Difficulty: hard
- Codebase size: small (20-200 files under environment/ excl. Docker files)
- Subcategories: []
- Tags: ["embeddings", "temperature", "calibration-bank", "checkpoint-resume", "recall-at-k", "inference-eval"]
- Milestones: 0

## Authoring Brief

### Public contract

- Entry point: `/app/scripts/run_embed_eval.sh` rebuilds the engine workspace under `/app/eng` and writes `/output/embed-eval.json`.
- Report schema: `schema_tag` = `"embed-eval/v2"` (string); `scenarios` = array with exactly the ids `cold_a`, `resume_a`, `cold_b`, `resume_b`, `mix_c`, `mix_d`, each entry carrying `recall_at_10` (number), `nmi` (number), `temperature` (number), `bank_epoch` (integer); `bands_ok` (boolean).
- For each pair, `cold_*.recall_at_10` and `resume_*.recall_at_10` must agree within `1e-4` (a resumed job retrieves exactly like its cold twin).
- Every scenario's `bank_epoch` must equal the durable tip of the calibration bank, not the live tip.
- Every `temperature` must sit inside the per-scenario band published in `/app/docs/embed_bands.md`; `recall_at_10` and `nmi` must sit inside their published per-scenario bands as well; `bands_ok` is true only when every cell is in band.
- Frozen inputs under `/app/data/banks/` and `/app/data/checkpoints/` (and the ledger + sheet data) must not be rewritten.
- `/app/data/fixtures/surface_ok.json` is an untrustworthy surface probe: it can look healthy while `bands_ok` is false.
- Hand-written reports fail: verification rebuilds the engine from the `/app/eng` sources into a verifier-owned staging dir and reruns it; the rebuilt values must match the shipped report. Two consecutive runs of the entrypoint must produce byte-identical `/output/embed-eval.json`.
- The engine also exposes a trace mode (`emit` binary, second subcommand) that streams per-cell events; verification reconstructs the report aggregates from that stream.

The instruction.md itself is symptoms-only: published-band drift after a training restart, resumed cells no longer retrieving like their cold twins, mixed cells disagreeing with the documentation, and every row pinning the wrong calibration generation. It states the output contract and the constraints above. It must NOT name any module, config file (other than the entrypoint, docs, data roots given above), cause, or fix location, and must not list expected numeric values for any cell (GX9).

### Failure topology

Four semantic defects plus one authority gate interact so that no single edit greens the report. The blob decoder drops the per-block scale frames that only resumed checkpoints carry, so resumed query vectors come out with wrong norms and the cold/resume retrieval parity breaks — and because the fused score also feeds the soft-assignment agreement statistic, the same defect drags `nmi` out of band for resumed and mixed cells. The ledger binder selects the newest ledger line of any state instead of the newest committed line, so every cell reports the live tip as `bank_epoch` and — because the scale sheet row is keyed by the bound index — also poisons `temperature`. The scale resolver reads the bait sheet family that tracks the working line instead of the committed family, so even a corrected binding still yields out-of-band `temperature` until the resolver is fixed too. The composed-cell assembler concatenates every segment present on disk instead of honoring the ledger's composition roster, so `mix_c`/`mix_d` include withdrawn segments and miss their bands even when everything upstream is fixed. Finally, a build-authority config gates a build-script rematerialization: while the binding mode stays on the working line, the two rank sources are rewritten from seed templates on every cargo build, so an agent that patches the sources but never discovers the gate loses its fixes exactly when the verifier rebuilds. Nothing in the instruction names these sites; the coupling (binding → sheet row → scale → fused score → both metrics; roster → mixed cells; gate → rebuilt sources) forces a multi-pass diagnosis.

### Environment shape

- `core/` — Rust crate: fixture/ledger IO, blob decoding, composed-cell assembly, query batching, metric computation.
- `rank/` — Rust crate with a build script and seed templates: ledger binding and per-cell scale resolution; the build script consults the ops config.
- `emit/` — Rust binary crate: CLI with a report subcommand and a trace subcommand; canonical deterministic JSON emission.
- Workspace `Cargo.toml`/`Cargo.lock` tie the three crates together; Docker copies them to `/app/eng`.
- `ops/` — build-authority config (`prefer.toml`), a rhyming non-graded config (`pin.toml`), and a short runbook describing the binding vocabulary as outcomes (no fix recipe).
- `data/` — frozen banks (two families, several binary segments each), four checkpoints (two cold, two resumed with block-scale framing), the ledger JSONL (committed/working/withdrawn marks, sheet-family references), two sheet families under `data/sched/`, and the bait `fixtures/surface_ok.json`.
- `docs/` — `embed_bands.md` publishing per-scenario bands (outcome tables only; no knob checklist, no file map).
- `scripts/` — the entrypoint shell script.
- Fixture bytes are generated by a committed helper under `build_helpers/` (task root, not shipped in the image) with fixed seeds.

### Required artifacts

- `instruction.md` — symptoms-only, public contract above, one plain-language opening sentence before any domain jargon.
- `task.toml` — version 1.0 single-step, `category = "machine-learning"`, `difficulty = "hard"`, languages `["rust","bash"]`, tags as in Metadata, `[environment] allow_internet = false`.
- `output_contract.toml` — report path + schema fields as the structured contract.
- `environment/Dockerfile` — single container; Rust toolchain pinned; stub-then-`cargo fetch`-then-real-src layer order; pytest installed from a hashed `environment/requirements.txt` with `--require-hashes` (comment the word pytest for the local static gate; `RUN rm` on its own line); no hidden-path COPY; `environment/.dockerignore` present.
- `tests/test.sh` + `tests/test_outputs.py` — pytest suite per the Test plan; every `subprocess.run` with explicit `check=`; no `v == v` NaN idioms; frozen-input checksums pinned from a linux/amd64 build.
- `solution/solve.sh` — oracle that edits exactly the five contract locations (semantic rewrites, no wholesale file replacement), then runs the entrypoint.
- 20+ files under `environment/` (the Initial Draft Commitments list below is authoritative).

### Test plan

1. `test_j2_pyrite` — frozen inputs (banks, checkpoints, ledger, sheets) hash-match pinned checksums after the solve; multiple approaches irrelevant (pure integrity); not chain-dependent.
2. `test_k4_agate` — report exists, parses, carries `schema_tag`, `bands_ok`, exactly the six ids, and well-typed fields in sane ranges; any valid fix passes; not chain-dependent.
3. `test_p7_jasper` — for both pairs, the two paired `recall_at_10` values agree within `1e-4`; multiple valid decoder implementations pass; chain-dependent on the decoder fix.
4. `test_r3_garnet` — first-pair cells sit inside the published `recall_at_10`/`nmi` bands; chain-dependent on decoder + scale resolution.
5. `test_t6_beryl` — second-pair cells sit inside the published bands; same chain as 4 on the second data family.
6. `test_m5_onyx` — composed cells sit inside their bands AND match values recomputed by the verifier from the rebuilt engine (blocks hardcoding); chain-dependent on decoder + roster + binding.
7. `test_w1_topaz` — every `temperature` sits inside its published band and equals the committed sheet row for the bound index (read from data, not from the report); chain-dependent on binder + resolver + gate.
8. `test_v8_lazuli` — every `bank_epoch` equals the committed ledger index computed independently by the verifier from the ledger; chain-dependent on binder + gate.
9. `test_d9_quartz` — two consecutive entrypoint runs produce byte-identical reports; any deterministic implementation passes.
10. `test_e2_opal` — verifier copies `/app/eng` + `/app/ops` to a staging dir, rebuilds with cargo, reruns, and requires the rebuilt report to equal the shipped one (numeric tolerance 1e-9); kills hand-written JSON and un-flipped gates; chain-dependent on all five locations.
11. `test_h3_zircon` — the trace subcommand's event stream reconstructs the per-cell aggregates in the report (counts + partial sums); kills report-only tampering; chain-dependent on the engine being the real producer.
12. `test_g6_flint` — `bands_ok` is true AND the report's cell values differ from the bait `surface_ok.json` values (blocks copying the bait); chain-dependent on real fixes.
13. `test_s4_coral` — re-entry: verifier hashes the two rank sources, reruns the entrypoint, and requires (a) the sources unchanged across the rebuild and (b) the fresh report equal to the shipped one — proving the binding authority is committed rather than the sources being one-shot patched around the gate; chain-dependent on the gate flip.
14. `test_n8_umber` — the trace stream's per-cell corpus row counts for the composed cells equal the sizes the verifier recomputes from the sealed ledger roster and segment headers; chain-dependent on the assembler fix.

### Drafting guardrails

Do not leak fix sites through names, comments, docs, or fixtures: no instruction noun may appear in any fix-path symbol, path token, or test name (construction manifest below is binding); no intent comments at defect sites; `embed_bands.md` publishes outcome bands only (never a file/knob map, never per-cell expected values that saturate GX9); the ops runbook describes the binding vocabulary (`skim`/`anchor`) as operational outcomes without saying which mode is correct or that a build script rewrites sources; seeds under `rank/seeds/` carry no comments referencing bugs; the bait sheet and bait surface fixture must look as plausible as the committed ones; decoys must do genuine work and stay off the fix path.

### Triviality Ledger

- Hardcoding six cell values into the report writer passes `test_k4_agate` but fails `test_e2_opal` (rebuilt-engine equality), `test_m5_onyx` (verifier-recomputed composed cells), and `test_h3_zircon` (trace reconstruction), because the verifier reruns the real engine and recomputes aggregates independently.
- Patching only the two rank sources (binder + resolver) without discovering `ops/prefer.toml` greens a local run but fails `test_e2_opal`/`test_s4_coral`: the verifier rebuild triggers the build script, which rematerializes both sources from broken seeds while the binding mode is `skim`.
- Flipping `ops/prefer.toml` alone changes nothing green: the shipped sources are already the broken bodies, so all band/parity tests stay red until the four semantic sites are actually fixed.
- Copying `surface_ok.json` numbers into the report fails `test_g6_flint` explicitly and `test_e2_opal` implicitly.
- Fixing the decoder but not the roster leaves `mix_c`/`mix_d` out of band (`test_m5_onyx`); fixing the roster but not the decoder leaves resumed-query mixes out of parity (`test_p7_jasper`, `test_m5_onyx`) — the mixed cells sit at the intersection, so neither half-fix collapses the other.
- Pinning `temperature` to a constant inside the band fails `test_w1_topaz`, which independently reads the committed sheet row for the bound index from data.
- Grep-for-nouns fails: every instruction noun is banned from fix-path symbols; decoys `braid.rs`/`dial.rs`/`pin.toml` rhyme with the fix-path shapes and do real non-fix work.

### Per-gate Pitfall Inventory

- RC1 (oracle simplification): risk that solve.sh replaces whole files; countermeasure — oracle applies function-body edits at the five contract sites only, keeping surrounding code identical.
- RC2 (oracle predictability): risk that fix sites are the only "weird-looking" code; countermeasure — decoys with the same shape (braid/dial/pin) and broken bodies that read as plausible defaults, no polarity-stub `return true` shapes.
- RC3 (verifier shallowness): risk of schema-only tests; countermeasure — verifier recomputes ledger index, sheet row, and composed-cell values from data and rebuilds/reruns the engine.
- RC4 (tamper surface): risk that `/output` can be hand-written; countermeasure — rebuild-equality, trace reconstruction, byte-identity double run, frozen-input checksums.
- RC5 (reference artifacts): risk of shipping expected outputs; countermeasure — no oracle report or expected JSON anywhere in `environment/` or `tests/` (verifier recomputes; tolerances/bands live in tests and docs only as bands).
- RC6 (instruction specificity): risk of cause-revealing prose; countermeasure — instruction states symptoms + contract only; no module/config names beyond the public paths.
- RC7 (oracle triviality): risk of <30 non-boilerplate oracle lines; countermeasure — four semantic rewrites (frame parsing, state filtering, keyed lookup, roster filtering) total well above the floor.
- RC8 (frontier concentration): risk of one-file frontier; countermeasure — five locations across `core/`, `rank/`, `ops/` with max test share 0.44.
- CR1 (symbol-table compliance): risk of drafter renaming; countermeasure — Step 2b uses the symbol table verbatim.
- CR2 (flipping-point contract): risk of same-root concentration; countermeasure — three distinct roots; contract below is the commitment.
- CR7 (grep resistance): risk of noun-stem symbols; countermeasure — opaque names audited in the naming pass; config vocabulary `skim`/`anchor` instead of live/durable.
- CR8 (no central orchestration): risk of one dispatcher function owning all fixes; countermeasure — fixes live in four separate modules across two crates plus a config.
- CR9 (test-contract traceability): risk of tests asserting fields the contract never names; countermeasure — output_contract.toml enumerates every graded field.
- GX1 (comment leakage): no comments at defect sites; seeds comment-free.
- GX3 (oracle edit distance): edits are body rewrites inside existing functions, not file swaps; no-op rewrites forbidden.
- GX5/GX9 (token provenance / contract saturation): instruction names fields and ids but never per-cell values; bands live in `docs/embed_bands.md` as ranges, and tests read them from there, keeping saturation low.
- GX10 (polarity contradiction): `bands_ok` polarity appears once, in one sentence, one scenario scope; the surface-probe sentence keeps "healthy"/"false" in separate clauses with an explicit subject each.
- Static checks (ruff PLW1510/PLR0124, hashed pip, dockerignore, amd64 checksums): enforced in Required artifacts; run `ruff check tests/ --select PLR0124,PLW1510` before zip; regenerate checksum ledgers from a linux/amd64 build.

### Initial Draft Commitments

- instruction.md
- task.toml
- output_contract.toml
- construction_manifest.json
- environment/Dockerfile
- environment/.dockerignore
- environment/requirements.txt
- environment/Cargo.toml
- environment/Cargo.lock
- environment/core/Cargo.toml
- environment/core/src/lib.rs
- environment/core/src/base.rs
- environment/core/src/lens.rs
- environment/core/src/weave.rs
- environment/core/src/braid.rs
- environment/core/src/gauge.rs
- environment/rank/Cargo.toml
- environment/rank/build.rs
- environment/rank/src/lib.rs
- environment/rank/src/knot.rs
- environment/rank/src/facet.rs
- environment/rank/src/dial.rs
- environment/rank/seeds/knot_seed.rs.in
- environment/rank/seeds/facet_seed.rs.in
- environment/emit/Cargo.toml
- environment/emit/src/main.rs
- environment/ops/prefer.toml
- environment/ops/pin.toml
- environment/ops/runbooks/eval_notes.md
- environment/scripts/run_embed_eval.sh
- environment/docs/embed_bands.md
- environment/data/ledger/journal.jsonl
- environment/data/sched/table_a7.toml
- environment/data/sched/table_w2.toml
- environment/data/banks/bank_a/seg_01.bin
- environment/data/banks/bank_a/seg_02.bin
- environment/data/banks/bank_a/seg_03.bin
- environment/data/banks/bank_a/seg_04.bin
- environment/data/banks/bank_b/seg_01.bin
- environment/data/banks/bank_b/seg_02.bin
- environment/data/banks/bank_b/seg_03.bin
- environment/data/banks/bank_b/seg_04.bin
- environment/data/checkpoints/cold_a.ckpt
- environment/data/checkpoints/resume_a.ckpt
- environment/data/checkpoints/cold_b.ckpt
- environment/data/checkpoints/resume_b.ckpt
- environment/data/fixtures/surface_ok.json
- build_helpers/gen_data.py
- tests/test.sh
- tests/test_outputs.py
- tests/ledgers/inputs.sha256
- solution/solve.sh

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: rank/src/knot.rs
  symbol: knot_r
  kind: function
  signature: pub fn knot_r(marks: &[Mark]) -> u32
  purpose: Selects the ledger index the whole emission binds to.
- path: rank/src/facet.rs
  symbol: facet_q
  kind: function
  signature: pub fn facet_q(idx: u32, root: &Path) -> f64
  purpose: Resolves the per-cell scale value from the committed sheet family for a bound index.
- path: core/src/lens.rs
  symbol: lens_unfold
  kind: function
  signature: pub fn lens_unfold(blob: &[u8]) -> Vec<Vec<f32>>
  purpose: Decodes a vector blob into row vectors, honoring any per-block frame headers.
- path: core/src/weave.rs
  symbol: weave_m
  kind: function
  signature: pub fn weave_m(marks: &[Mark], lots: &[Lot]) -> Vec<Lot>
  purpose: Assembles the composed collections for the paired composition cells from the ledger roster.
- path: ops/prefer.toml
  symbol: BIND_MODE
  kind: constant
  signature: [bind] mode = "skim" | "anchor"
  purpose: Build-authority binding mode consumed by the rank build script.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: ops/prefer.toml
    controls_tests: [test_s4_coral, test_w1_topaz, test_v8_lazuli, test_g6_flint]
  - id: B
    path: rank/src/knot.rs
    controls_tests: [test_v8_lazuli, test_w1_topaz, test_m5_onyx, test_g6_flint]
  - id: C
    path: rank/src/facet.rs
    controls_tests: [test_w1_topaz, test_r3_garnet, test_t6_beryl]
  - id: D
    path: core/src/lens.rs
    controls_tests: [test_p7_jasper, test_r3_garnet, test_t6_beryl, test_m5_onyx]
  - id: E
    path: core/src/weave.rs
    controls_tests: [test_m5_onyx, test_g6_flint, test_n8_umber]
no_single_location_flips_majority: true
concentration_cap: 0.5

Amendment note (Step 2b, pre-construction): `test_e2_opal` is a pure anti-tamper
gate (staged rebuild vs shipped report); under the ablation protocol (revert one
location, rerun the entrypoint, rerun tests) both sides regenerate identically, so
it cannot sit in any location's controls list. A dedicated composition test
`test_n8_umber` (trace row counts vs verifier-recomputed sealed roster sizes)
takes its place under E, and A's fourth slot is `test_g6_flint`. Union = 9 tests,
max share 4/9 = 0.444.
```

#### decoy_manifest

```
- path: core/src/braid.rs
  kind: module
  rhymes_with: weave_m
  non_fix_purpose: Batches query rows into fixed-width strides for the scorer; genuinely used and correct in all scenarios.
- path: rank/src/dial.rs
  kind: module
  rhymes_with: facet_q
  non_fix_purpose: Resolves display precision and ordering for the trace event stream; correct and unrelated to scoring.
- path: ops/pin.toml
  kind: config-reader
  rhymes_with: BIND_MODE
  non_fix_purpose: Pins trace verbosity and event buffer sizing consumed by the emit binary; flipping it changes nothing graded.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [embedding, retrieval, evaluation, band, report, engine, metric, schema, scenario, recall, nmi, temperature, bank, epoch, cold, resume, twin, pair, mix, calibration, generation, durable, tip, live, checkpoint, surface, probe, entrypoint, fixture, verification, restart, documentation]
```
