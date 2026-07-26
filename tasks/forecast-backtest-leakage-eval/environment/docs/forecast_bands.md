# Forecast evaluation bands

`schema_tag` must be `forecast-eval-v1`.

## Tip resolution

`split_tip` and `horizon` for every window row must match the selected
durable walk-forward tip drawn from materials under
`/app/data/feature_registry/`. Sheets kept under `/app/data/ledger/` are
operator mirrors and are not the selection authority. Retired tip ids are
not selected.

## Windows

Each entry in `windows[]` has `id`, `smape`, `mase`, `horizon`, `split_tip`,
and `scaler`.

- `split_tip`, `horizon`, and `scaler` are identical across every window row.
- `scaler` must reflect train-only fitting for the bound tip.
- Series under `/app/data/series/` and splits under `/app/data/splits/`
  participate in scoring.

### sMAPE bands

| window id | min | max |
| --------- | --- | --- |
| w_alpha   | 0.136 | 0.148 |
| w_beta    | 0.150 | 0.162 |
| w_gamma   | 0.162 | 0.174 |
| w_delta   | 0.128 | 0.140 |
| w_epsilon | 0.145 | 0.157 |

### MASE bands

| window id | min | max |
| --------- | --- | --- |
| w_alpha   | 0.870 | 0.890 |
| w_beta    | 0.900 | 0.920 |
| w_gamma   | 0.935 | 0.955 |
| w_delta   | 0.850 | 0.870 |
| w_epsilon | 0.885 | 0.905 |

## eval_ok

`eval_ok` is true only when every window lands inside its band and the run's
internal invariants hold. A shallow print from `/app/tools/fcprobe` is not
sufficient evidence of a healthy run.

## Idempotence

Two consecutive runs of the eval driver must write byte-identical
`/output/forecast-eval.json`.
