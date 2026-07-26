### Decision

GO — Attempt 1. Speech-recognition evaluation seating with a decoder-tip lattice:
the bound registry tip drives decode path, fusion weight, and the reported epoch
at once, so a slice metric can only land inside its published band when all three
resolve together.

### Metadata

- version: 2
- Task name: asr-blank-collapse-eval
- Title: ASR Blank Collapse Eval
- Category: machine-learning
- Languages: [rust]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [asr, ctc, transducer, wer, blank-collapse, tip-epoch]
- Milestones: 0

## Authoring Brief

### Public contract

`/app/scripts/run_asr_eval.sh` rebuilds the evaluation workspace under `/app/eng`
and publishes `/output/asr-eval.json` carrying:

- `schema_tag` (string)
- `slices` (array of objects with `id` string, `wer` number, `cer` number,
  `blank_mode` string, `lm_weight` number, `tip_epoch` integer)
- `eval_ok` (boolean)

Six slice ids in fixed order. Every slice must land inside the published word- and
character-error bands, `blank_mode` must be the decode path the bound durable
decoder tip declares, `lm_weight` must be the fusion row the bound tip resolves,
`tip_epoch` must be the bound tip generation, and `eval_ok` must be true. Audio
posteriors, alignments, the lexicon, the fusion tables, the decoder registry, and
the published bands doc are frozen inputs. Two consecutive entrypoint runs must be
byte-identical, and the verifier re-runs the entrypoint plus injects a novel sealed
registry tip.

### Failure topology

The published report disagrees with the bands. Three interacting authorities decide
every number: which registry tip a run binds (sealed rows minus the retired ledger,
not newest-any), which fusion sheet and row that tip resolves (shallow-fusion weight
feeds the decode search, not only the report), and which decode path the tip declares
(blank-collapse ordering for the CTC path, prediction-state conditioning for the
transducer path). Getting the tip wrong moves the epoch, the sheet, the weight, and
the mode together, so a slice cannot be brought into band one field at a time. On top
of that, evaluation selection and the tip bind receipt gate the workspace rebuild: any
source seating that is not published together with selection and binding is restored
from the desk seed set on the next rebuild, so a source-only pass does not survive the
entrypoint. A surface probe reports a healthy status because it decodes greedily
without fusion, and a stale sweep fixture shows healthy-looking numbers that the desk
never reads.

### Environment shape

- A Rust evaluation workspace with three crates: shared decode/scoring primitives,
  a binding/resolution crate, and the report emitter binary. Two of the crates carry
  build-time seating logic driven by evaluation selection and the tip bind receipt.
- Frozen data domains: frame posteriors per slice, reference alignments, a token
  lexicon, a bigram fusion table, a prediction-state bias table, per-sheet fusion rows,
  a decoder tip journal plus a retired-tip ledger, a stale sweep fixture, and a legacy
  sweep ledger.
- Published docs: metric bands and report schema. Operational runbook notes.
- Entrypoint script and a surface probe tool.

### Required artifacts

`instruction.md`, `task.toml`, `output_contract.toml`, `environment/` (Dockerfile,
`.dockerignore`, hashed `requirements.txt`, Rust workspace, data domains, docs, ops,
scripts, tools; 20+ files excluding Docker files), `solution/solve.sh`,
`tests/{test.sh, test_outputs.py, data.sha256}`.

### Test plan

1. Frozen-input digests unchanged.
2. Schema tag, slice id set/order, field types and ranges.
3. `blank_mode` equals the bound tip's declared path on every slice.
4. `tip_epoch` equals the bound sealed generation.
5. `tip_epoch` is neither the retired sealed tip nor the newest live tip.
6. `lm_weight` equals the bound fusion row and sits in the published band.
7-9. Per-slice-family `wer`/`cer` equal faithful-engine values on the frozen fixtures
   (three tests, split by family).
10. Every slice inside its published band and `eval_ok` true.
11. Published numbers are not copied from the stale sweep fixture.
12. Two entrypoint republishes are byte-identical with the published report.
13. A novel sealed registry tip moves epoch, mode, weight, and the metrics together.

All tests are independently achievable from the published report plus the entrypoint;
none require the oracle's exact edit sequence.

### Drafting guardrails

Instruction stays symptoms-only: no decode recipe, no tip id, no fusion row value, no
band numbers, no file-level fix location. Code symbols on the fix path stay opaque and
must not reuse instruction nouns. No intent comments on fix-path files. The stale sweep
fixture and the legacy ledger must not be answer-shaped for the graded values.

### Triviality Ledger

- Flipping the decode collapse order alone leaves epoch/weight/mode wrong, so band and
  tip tests still fail.
- Editing sources without publishing selection plus the bind receipt is undone by the
  build-time seating restore on the next entrypoint rebuild, which the verifier drives.
- Hardcoding the resolved tip, weight, or hypotheses is caught by the novel-sealed-tip
  injection, which shifts sheet, row, mode, and metrics at once.
- Copying the surface probe's healthy status or the stale sweep numbers fails the band,
  parity, and anti-copy tests.

### Per-gate Pitfall Inventory

- RC1: oracle adds resolution logic (sealed-minus-retired selection, sheet-by-bound-row
  lookup, prediction-state decode) rather than deleting flags.
- RC2/CR7: no `broken_`/`golden_` tokens; fix-path symbols are opaque and disjoint from
  instruction nouns.
- RC3/RC4/RC5: tests assert computed metric values embedded in test code; frozen inputs
  are digest-pinned; no reference report ships under `environment/`.
- RC6/GX6/GX9/GX10: instruction gives observations and outcomes only, names no numeric
  value that tests assert, and never pairs both decode-path names with one slice.
- RC7/GX3: oracle republishes selection, bind receipt, and four seating surfaces with
  substantive logic well above the 80-LOC floor.
- CR5: the two build-time seating gates are written with different structure and helper
  names.
- GX8: verifier imports only test-infra modules.

### Initial Draft Commitments

- `instruction.md`, `task.toml`, `output_contract.toml`
- `build_helpers/gen_data.py`
- `environment/Dockerfile`, `environment/.dockerignore`, `environment/requirements.txt`
- `environment/eng/Cargo.toml`, `environment/eng/Cargo.lock`
- `environment/eng/core/{Cargo.toml,build.rs}`, `environment/eng/core/src/{lib.rs,frame.rs,glyph.rs,collapse.rs,join.rs,tally.rs,span.rs}`,
  `environment/eng/core/seeds/{collapse_seed.rs.in,join_seed.rs.in}`
- `environment/eng/rank/{Cargo.toml,build.rs}`, `environment/eng/rank/src/{lib.rs,epoch.rs,fuse.rs,bind.rs,dial.rs}`,
  `environment/eng/rank/seeds/{epoch_seed.rs.in,fuse_seed.rs.in}`
- `environment/eng/emit/{Cargo.toml,src/main.rs}`
- `environment/calib/{eval_pass.toml,decoder_selection.txt,trace_pref.toml}`
- `environment/data/audio/<six slices>/utt_0N.bin`, `environment/data/align/<six slices>.txt`
- `environment/data/lexicon/tokens.txt`, `environment/data/lm/bigram.bin`, `environment/data/predict/bias.bin`
- `environment/data/fusion/{table_h4.toml,table_k9.toml}`
- `environment/data/decoder_registry/{tip_journal.jsonl,retired_tips.jsonl}`
- `environment/data/fixtures/probe_ok.json`, `environment/data/sweep/legacy_runs.jsonl`
- `environment/docs/{asr_bands.md,report_schema.md}`, `environment/ops/pin.toml`, `environment/ops/runbooks/eval_notes.md`
- `environment/scripts/run_asr_eval.sh`, `environment/tools/asrprobe`
- `solution/solve.sh`, `tests/{test.sh,test_outputs.py,data.sha256}`

### Construction manifest

#### symbol_table

```
- path: eng/core/src/collapse.rs
  symbol: fold_c
  kind: function
  signature: fn fold_c(a: &[Vec<f32>], b: &[Vec<f32>], w: f64) -> Vec<usize>
  purpose: walks per-frame fused argmax and returns the emitted label sequence

- path: eng/core/src/join.rs
  symbol: step_j
  kind: function
  signature: fn step_j(a: &[Vec<f32>], b: &[Vec<f32>], c: &[Vec<f32>], w: f64) -> Vec<usize>
  purpose: walks frames with an emission state and returns the emitted label sequence

- path: eng/rank/src/epoch.rs
  symbol: pick_e
  kind: function
  signature: fn pick_e(rows: &[Row], out: &HashSet<String>) -> u32
  purpose: returns one generation index from the journal rows

- path: eng/rank/src/fuse.rs
  symbol: row_w
  kind: function
  signature: fn row_w(sheet: &str, n: u32, root: &Path) -> f64
  purpose: returns the numeric row a generation resolves in the sheet tables
```

#### flipping_point_contract

```
locations:
  - id: A
    path: eng/core/src/collapse.rs
    controls_tests: [test_read_slices_match_engine_semantics, test_spont_slices_match_engine_semantics, test_far_slices_match_engine_semantics]
  - id: B
    path: eng/core/src/join.rs
    controls_tests: [test_novel_sealed_tip_shifts_decode_path]
  - id: C
    path: eng/rank/src/epoch.rs
    controls_tests: [test_tip_epoch_is_bound_registry_generation, test_tip_epoch_not_retired_or_live_row, test_blank_mode_is_bound_decoder_path]
  - id: D
    path: eng/rank/src/fuse.rs
    controls_tests: [test_lm_weight_matches_bound_fusion_row, test_report_inside_published_bands_and_flagged]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: eng/rank/src/dial.rs
  kind: config-reader
  rhymes_with: row_w
  non_fix_purpose: reads trace stream shaping for the emitter's trace mode

- path: eng/core/src/span.rs
  kind: helper
  rhymes_with: fold_c
  non_fix_purpose: chunks utterance indices for batched scoring

- path: eng/rank/src/bind.rs
  kind: helper
  rhymes_with: pick_e
  non_fix_purpose: assembles the resolved binding tuple for the emitter

- path: eng/core/src/tally.rs
  kind: helper
  rhymes_with: step_j
  non_fix_purpose: word- and character-level edit distance scoring
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [speech, recognition, evaluation, desk, report, slice, band,
blank, mode, decode, decoder, weight, fusion, tip, epoch, registry, generation,
posterior, alignment, transcript, error, rate, selection, receipt, probe, sweep]
```
