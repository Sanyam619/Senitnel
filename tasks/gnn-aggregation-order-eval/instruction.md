The model evaluation pipeline under /app runs graph neural net inference on
frozen held-out graphs and checkpoints. Accuracy and macro_f1 disagree with
the published bands across cold, resume, and mixed slices. Recalibrate the
aggregation-order evaluation so the published health report lands inside those
bands.

Publish by running /app/scripts/run_gnn_eval.sh, which writes
/output/gnn-eval.json with schema_tag, a scenarios array, and bands_ok.
Metric bands live in /app/docs/gnn_bands.md. Field layout and the required
scenario set live in /app/docs/report_schema.md. Evaluation notes live in
/app/eval/runbooks/eval_notes.md. Evaluation helpers under /app/eval/
including /app/eval/ref_score.py can reconstruct scenario metrics from the
frozen graphs and checkpoints under the published seating rule. Evaluation
selection lives in /app/calib/trial_pref.toml and tip binding in
/app/calib/tip_bind.accept. Graphs, checkpoints, the feature registry, and
aggregation sheets under /app/data/ are frozen inputs.

Every scenario must sit inside its published band with bands_ok true. Each
resume scenario reproduces its cold twin: accuracy and macro_f1 match within
1e-4. Resume checkpoints store block-packed classifier frames; unpacking must
reproduce the cold-run decision geometry. Aggregation mode and tip_epoch follow
the durable feature-registry tip that the evaluation binds for the run.
Retired tips and live sweep tips are not the bound tip. Degree-normalized
features follow that tip's durable preference under the seating rule in
gnn_bands.md. Mixed scenarios are scored against the graph composition that
tip declares. Metric values must match a faithful message-passing evaluation
of the frozen inputs under that bound tip, not merely land inside the band
windows.

Publishable evaluation keeps seating surfaces durable across rebuilds.
Trial-only preference or an unpublished tip binding causes a rebuild to restore
desk seed seating, so surface edits alone do not stick. The verifier re-runs
the entrypoint and requires the re-published report to be byte-identical to
/output/gnn-eval.json; hand-written or template reports fail. Two consecutive
entrypoint runs must be byte-identical. The verifier also injects novel durable
registry tips and expects aggregation mode, tip_epoch, and per-scenario metrics
to move with each tip.

Everything under /app/data/ is frozen input. /app/docs/gnn_bands.md is the
published contract and is also frozen. Display fixtures under
/app/data/fixtures/ are not the published report. Alternate ledgers under
/app/data/ledger/ are not the feature-registry authority the evaluation binds
against.
