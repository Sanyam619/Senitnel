### Decision
GO — Attempt 1. SoftHSM-class cross-encoder rerank calibration desk under
`machine-learning`: trial→serving + tip_bind × dual rematerialize × fusion/
temperature/tip_epoch coupling across IR slices. No repair/debug framing;
primary activity is held-out rerank evaluation against nDCG/MRR bands.

### Metadata
- version: 2
- Task name: cross-encoder-rerank-calibration
- Title: Cross-Encoder Rerank Calibration
- Category: machine-learning
- Languages: ["rust"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: [rerank, cross-encoder, ndcg, score-fusion, tip-epoch, inference-eval]
- Milestones: 0

## Authoring Brief

### Public contract
- Entrypoint `/app/scripts/run_rerank_eval.sh` writes `/output/rerank-eval.json`
- Schema: `schema_tag` = `rerank-eval-v1`; `slices` array with
  `id`, `ndcg_at_10`, `mrr`, `temperature`, `fusion`, `tip_epoch`; `eval_ok`
- Slice ids (order): cold_a, resume_a, cold_b, resume_b, mix_c, mix_d
- Bands in `/app/docs/rerank_bands.md`; schema in `/app/docs/report_schema.md`
- Frozen: `/app/data/pools/`, `/app/data/qrels/`, packs, schedules, tip journal
- `rerankprobe` may false-green (first-stage only)
- Verifier rebuilds `/app/eng`, re-invokes entrypoint; consecutive runs
  byte-identical; novel durable tip moves epoch/temperature/fusion/mix

### Failure topology
Agents see healthy first-stage probe + trial rematerialize undoing naive
source edits. Tip resolution must ignore live tip and retired newest-durable
(tip_g9). Schedule sheet must follow the bound tip (a7 → temperature 0.125 +
`rrf`), not live w2 (`linear` bait). Resume packs need correct CKP2 unpack;
mix slices need tip wefts, not fold-all. Wrong fusion with right nDCG on one
slice still fails distant MRR/fusion/epoch cells.

### Environment shape
- `/app/eng/{core,rank,emit}` Rust workspace with dual dissimilar `build.rs`
- `/app/calib/` trial_pref + tip_bind + trace dial
- `/app/data/{pools,packs,qrels,feature_registry,sched,fixtures,ledger}`
- `/app/docs/`, `/app/eval/runbooks/`, `/app/scripts/`, `/app/tools/rerankprobe`

### Required artifacts
Standard layout: instruction, task.toml, output_contract, environment,
solution/solve.sh, tests/{test.sh,test_outputs.py}, ≥20 environment files.

### Test plan
- Frozen digests (pools/packs/qrels/journal/bands)
- Schema/types/fusion vocabulary
- Resume↔cold parity
- Durable temperature + rrf fusion
- tip_epoch = 6; not 8/9
- Exact engine metrics per cold/resume/mix pair
- Band membership + eval_ok
- Not surface fixture / not linear fusion; probe still greens first-stage
- Byte-identical republish ×2
- Novel tip inject moves epoch + temperature + fusion + mix metrics

### Drafting guardrails
Symptoms-only instruction; no tip resolution recipe; no intent comments on
seeds; no `/app/ops/` cutover nouns; ML tags lead; dual dissimilar build.rs;
EXPECTED only in tests.

### Triviality Ledger
- Independent polarity stubs without rematerialize → blocked by serving×bind gate
- Grep tip_g7 from 4-row journal → blocked by interleaved live + retired tip_g9
- Copy surface_ok → blocked by bait metrics + linear fusion assert
- Hardcode tip_g7 table → blocked by novel tip inject

### Per-gate Pitfall Inventory
- SE classifier: avoid ops/cutover/repair vocabulary; keep calib/eval framing
- CR5: rank vs core build.rs parsers must stay structurally dissimilar
- PLR0124/PLW1510: finite range form; explicit check= on subprocess.run

### Initial Draft Commitments
- SoftHSM spine cloned from diffusion, remapped to ndcg/mrr/temperature/fusion
- pools/qrels naming per idea; languages=["rust"]; category machine-learning
