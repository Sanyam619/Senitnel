Bring the mixture-of-depths model evaluation into its published metric
bands, so that running `/app/scripts/run_mod_eval.sh` writes the
evaluation report `/output/mod-eval.json`. The report's field layout and
required scenario set are documented in `/app/docs/mod_bands.md`, with
background evaluation notes in `/app/docs/eval_notes.md`. Frozen model
checkpoints live under `/app/data/ckpt/`, router materials under
`/app/data/routers/`, held-out evaluation slices under `/app/data/eval/`,
and evaluation calibration state under `/app/calib/`.

The report carries a top-level schema_tag, a scenarios array, and a
bands_ok flag. Cold-start and checkpoint-resume partners must agree on
perplexity within `1e-4`. Every scenario's average routed depth must land
in the published band. Routing capacity must follow the durable router tip
rather than the live full-depth sheet, and tip_epoch must follow that same
durable tip.

Evaluation selection ships in trial mode and restores the evaluation
sources from the trial seed set on every rebuild of the evaluation engine.
Results hold across rebuilds only once the calibration preference and the
tip binding record under `/app/calib/` both agree with the registry-resolved
durable tip. `/app/data/fixtures/surface_ok.json` may look healthy during an
unhealthy evaluation, and `/app/tools/modprobe` may print a stable-looking
depth line during one too. The verifier rebuilds `/app/eng` and reruns the
evaluation on the shipped materials and on novel sealed tips, so
transcribed reports fail. Two consecutive runs must write byte-identical
reports.
