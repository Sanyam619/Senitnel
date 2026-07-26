Seat the forecasting backtest evaluation so `/app/scripts/run_forecast_eval.sh`
writes `/output/forecast-eval.json` inside the metric bands documented under
`/app/docs/forecast_bands.md`. Desk layout notes live in `/app/docs/desk_notes.md`.
Frozen series sit under `/app/data/series/` and split definitions under
`/app/data/splits/`; evaluation preference and tip binding live under
`/app/calib/`.

The report carries a top-level schema_tag, a windows array, and an eval_ok
flag; field layout and the required window set are documented in
`/app/docs/forecast_bands.md`. For each rolling window, smape and mase must
reflect strictly causal features. split_tip must equal the durable
walk-forward tip rather than a live all-data tip. scaler must follow the
train-only preference bound from that tip. Trial evaluation selection
refreshes seating surfaces on every engine build, so surface edits alone do
not stick. `/app/tools/fcprobe` may print a stable-looking status line during
an unhealthy run. The verifier rebuilds `/app/eng` and re-runs the eval on
both the shipped materials and novel sealed tips; hand-written reports fail.
Two consecutive runs must be byte-identical.
