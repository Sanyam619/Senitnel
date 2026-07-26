# Inference calibration evaluation notes

The inference calibration pass rebuilds the scoring engine under `/app/eng`
and emits `/output/feature-eval.json`. The surface probe reads a stale
display fixture and can print aligned despite serving scores outside the
published AUC, Brier, and feature-skew bands.

More than one candidate feature snapshot is available under
`/app/data/online/`. The model-evaluation registry under
`/app/data/feature_registry/` records which snapshots reached
production-eligible (durable) status and which stayed trial (live). A
separate registry record, `/app/data/feature_registry/retired_tips.jsonl`,
lists snapshots later retired. A retired snapshot must not serve even if its
durable mark is newer.

Publishing takes more than choosing the evaluation selection: the stored
calibration lineage must also name the serving snapshot it stands behind.
A lineage naming a snapshot the registry does not support does not hold
across a clean evaluation rerun, and trial-only state is not publishable.
