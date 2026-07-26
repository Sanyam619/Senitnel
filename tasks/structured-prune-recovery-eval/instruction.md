# Recover the pruned model's published bands

The evaluation desk under `/app/eng` scores a structurally pruned classifier and
publishes the accuracy it recovers, the sparsity it reaches, and the multiply
share it still spends. The accuracies it publishes now sit nowhere near the
documented bands, the geometry it reports beside them describes a denser stack
than the one being scored, and the six scenarios do not even agree with each
other on which channel roster they ran on.

Bring the published evaluation into the documented bands.

`/app/scripts/run_prune_eval.sh` publishes `/output/prune-eval.json`, carrying
`schema_tag`, a `scenarios` array, and `bands_ok`; the per-scenario fields are
described in `/app/docs/report_schema.md`. Every required scenario has to land
inside its accuracy band and inside both geometry bands in
`/app/docs/prune_bands.md`, each cold scenario and its resume partner have to
agree to within `1e-4`, and the roster generation a scenario reports has to be
the durable structured generation it was scored under, not an overlay
proposal or an unstructured trial sheet.

The dense snapshots under `/app/data/dense/`, the channel rosters under
`/app/data/masks/`, the registry under `/app/data/mask_registry/`, the
calibration rows under `/app/data/calib/`, the evaluation slices under
`/app/data/eval/` and the published bands are inputs, not outputs. The published
numbers have to come from scoring those snapshots on those slices. Desk notes
sit under `/app/docs/`.

The evaluation workspace under `/app/eng` is rebuilt from its own sources and
the entrypoint is re-run, so a report that only exists as a published file does
not survive. Two consecutive entrypoint runs must publish byte-identical
reports, and a roster generation that has not been seen before must move the
report with it rather than leave the previous numbers standing.

`/app/data/fixtures/surface_ok.json` is a captured sweep. It reports healthy
numbers while the published report is outside its bands.
