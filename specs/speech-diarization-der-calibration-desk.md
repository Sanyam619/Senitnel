### Decision
GO — Attempt 1. SoftHSM-class ML diarization desk: clustering tip × embedding-bank tip × DER/JER bands; oracle-count probe bait; rematerialize until serving + tip bind; languages rust+bash; category machine-learning.

### Metadata
- version: 2
- Task name: speech-diarization-der-calibration-desk
- Title: Speech Diarization DER Desk
- Category: machine-learning
- Languages: ["rust", "bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["diarization", "der", "jer", "clustering-tip", "tip-epoch", "inference-eval"]
- Milestones: 0

## Authoring Brief

### Public contract
Seat the speaker-diarization evaluation so `/app/scripts/run_diar_eval.sh` emits `/output/diar-eval.json` with `schema_tag` (string), `slices` (array of `{id:string, der:number, jer:number, clustering:string, tip_epoch:integer}`), and `eval_ok` (boolean). Frozen audio under `/app/data/audio/`, RTTM refs under `/app/data/rttm/`. For each required slice in `/app/docs/diar_bands.md`, `der` and `jer` must meet bands; `clustering` must equal the durable method tip (`ahc`|`spectral`|`nme` — not the live decoy); `tip_epoch` must equal the sealed embedding-bank tip epoch as a number. `/app/tools/diarprobe` may report low DER while `eval_ok` is false (oracle speaker count). Verifier rebuilds `/app/eng` and re-runs; two runs byte-identical. Novel sealed tips move the report.

### Failure topology
Broken desk picks live/retired tips, scores oracle-count or stale-method columns, and leaves trial preference so rebuilds rematerialize seating. Correct seating couples embed-registry sealed-max non-retired tip epoch with cluster-registry durable method (`ahc`), looks up DER/JER from method×epoch sheets (not oracle, not ledger mirror), writes serving preference + `key=value` tip bind, and gates `eval_ok` on unsupervised durable clustering plus in-band metrics.

### Environment shape
`/app/eng` Rust binary; opaque seating modules under seat/flag/mix/score/gate; `/app/calib` trial preference + tip bind; `/app/data/{audio,rttm,embed_registry,cluster_registry,ledger,fixtures}`; docs bands/schema/notes; scripts + diarprobe.

### Required artifacts
Standard task layout: instruction, task.toml, output_contract, Dockerfile, .dockerignore, hashed requirements, solve.sh, test.sh, test_outputs.py, ≥20 environment files.

### Test plan
- Fixtures digest pin
- Schema / slice order / field types (tip_epoch integer; clustering string)
- tip_epoch = sealed non-retired embed tip; not retired sealed-max; not live
- clustering = durable method tip; not live spectral decoy
- der/jer match method×epoch sheets (not oracle, not obs, not ledger mirror)
- All slices in bands + eval_ok
- Not surface_ok bait
- Rebuild + byte-identical republish
- Novel sealed embed tip moves tip_epoch and metrics
- tip_bind.accept key=value names resolved tip/epoch/clustering/method

### Drafting guardrails
Symptoms-only instruction (no fix recipes). Opaque seating symbols. No answer-shaped surface_ok with correct tip. Document tip_epoch as number and tip_bind `key=value` receipt. Lead with ML diarization outcomes — no repair/cutover/ops framing. Rematerialize until serving + bind. Hard tests only (recompute EXPECTED; novel inject).

### Triviality Ledger
- Grep flip of five stubs blocked by build.rs rematerialize until calib seated
- Oracle-count low DER blocked by eval_ok + clustering durable method requirement
- Newest-any / sealed-max tip blocked by retired ledger
- Live spectral decoy blocked by cluster registry durable resolution + band coupling
- Hand-written report blocked by verifier rebuild from /app/eng

### Per-gate Pitfall Inventory
- RC1/RC7: oracle rewrites ≥5 seating bodies + calib, not delete-only
- RC2: mineral test names; no broken_/golden_ paths
- RC3/RC5: tests recompute from fixtures; EXPECTED in test code
- RC6: symptoms instruction; bands in docs not as fix checklist of sites
- CR1–CR9: opaque pick_t/bit_z/mix_w/score_u/gate_y; no instruction nouns on fix path
- GX9/GX10: do not enumerate per-slice expected der/jer in instruction

### Initial Draft Commitments
- instruction.md, task.toml, output_contract.toml
- solution/solve.sh, tests/test.sh, tests/test_outputs.py
- environment/Dockerfile, .dockerignore, requirements.txt
- environment/eng/{Cargo.toml,Cargo.lock,build.rs,stub_main.rs,seeds/s1..s5.rs.in,src/*}
- environment/{seat,flag,mix,score,gate}/*.rs
- environment/calib/{trial_pref.toml,trace_pref.toml}
- environment/data/audio/*.json, data/rttm/*.rttm
- environment/data/embed_registry/{tip_journal,retired_tips}.jsonl
- environment/data/cluster_registry/{tip_journal,retired_tips}.jsonl
- environment/data/ledger/method_mirror.json, data/fixtures/surface_ok.json, data/fixtures.sha256
- environment/docs/{diar_bands,desk_notes,report_schema}.md
- environment/scripts/{run_diar_eval,verify_fixtures}.sh
- environment/tools/{diarprobe,probe_calc.py}

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table
```
- path: seat/knit_b.rs
  symbol: pick_t
  kind: function
  signature: pub fn pick_t(a: &str, b: &str, c: &str) -> TipPick
  purpose: select sealed non-retired max-epoch embed tip
- path: flag/xv_c.rs
  symbol: bit_z
  kind: function
  signature: pub fn bit_z(a: &str, b: i64, c: &str) -> String
  purpose: resolve durable clustering method label from cluster tip
- path: mix/ward_d.rs
  symbol: mix_w
  kind: function
  signature: pub fn mix_w(a: &ChanSet, b: &str, c: i64) -> f64
  purpose: lookup DER column for method×epoch
- path: score/helm_e.rs
  symbol: score_u
  kind: function
  signature: pub fn score_u(a: &ChanSet, b: &str, c: i64) -> f64
  purpose: lookup JER column for method×epoch
- path: gate/emit_f.rs
  symbol: gate_y
  kind: function
  signature: pub fn gate_y(ders: &[f64], jers: &[f64], methods: &[String], rows_ok: bool) -> bool
  purpose: deep eval_ok over unsupervised durable methods and finite in-band metrics
```

#### flipping_point_contract
```
locations:
  - id: A
    path: seat/knit_b.rs
    controls_tests: [test_c1_biotite, test_d9_epidote, test_f5_dolomite, test_l7_dunite]
  - id: B
    path: flag/xv_c.rs
    controls_tests: [test_e2_scoria, test_f5_dolomite, test_i6_marl, test_n8_basalt]
  - id: C
    path: mix/ward_d.rs
    controls_tests: [test_f5_dolomite, test_g8_feldspar, test_i6_marl]
  - id: D
    path: score/helm_e.rs
    controls_tests: [test_f5_dolomite, test_g8_feldspar, test_n8_basalt]
  - id: E
    path: gate/emit_f.rs
    controls_tests: [test_g8_feldspar, test_h4_gneiss]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest
```
- path: eng/src/decoy_p.rs
  kind: helper
  rhymes_with: pick_t
  non_fix_purpose: weighted roll of DER vector for probe-adjacent telemetry
- path: eng/src/decoy_q.rs
  kind: helper
  rhymes_with: gate_y
  non_fix_purpose: histogram summary of JER vector
- path: data/ledger/method_mirror.json
  kind: config-reader
  rhymes_with: bit_z
  non_fix_purpose: stale clustering method map that lands metrics out of band
- path: data/fixtures/surface_ok.json
  kind: helper
  rhymes_with: mix_w
  non_fix_purpose: oracle-count bait report that diarprobe greens
```

#### code_forbidden_tokens
```
code_forbidden_tokens: [seat, speaker, diarization, der, jer, clustering, tip, epoch, embedding, bank, audio, rttm, eval, report, schema, slices, probe, durable, method, spectral, ahc, nme, oracle, band, rebuild, preference, bind, receipt, serving, trial, journal, retired, live, sealed]
```
