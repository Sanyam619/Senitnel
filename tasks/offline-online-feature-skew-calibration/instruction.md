The model evaluation pipeline under `/app` scores a tabular serving model
against held-out inference slices. Offline training features and online
serving features disagree enough that AUC, Brier, and feature-skew bands
fail. Recalibrate the serving evaluation so the published health report is
inside those bands.

Publish by running `/app/scripts/run_feature_eval.sh`, which writes
`/output/feature-eval.json`. Metric bands live in
`/app/docs/calibration_bands.md`. Evaluation notes live in
`/app/eval/runbooks/eval_notes.md`.

The schema_tag value joins feature-eval and v1 with a slash. The features
array contains rows with name, offline_mean, online_mean, skew, and source.
Feature names appear in this order: f_amt, f_age, f_zip, f_chn, f_risk. The
slices array contains id, auc, and brier for retail, corporate, mobile, and
holdout in that order. The top-level calibration_ok value is a boolean.

Correct output has calibration_ok true, absolute feature skew inside each
published bound, and slice metrics inside their bands. Each source names the
durable online tip used for serving. Each skew is online_mean minus
offline_mean. Repeated runs produce byte-identical output.
`/app/tools/feathealth` is only a surface probe and may show aligned for an
invalid report. Keep `/app/data/` and `/app/docs/calibration_bands.md`
frozen. The selected feature snapshot and its calibration lineage must
survive a clean evaluation rerun; trial-only state is not publishable. See
the evaluation notes.
