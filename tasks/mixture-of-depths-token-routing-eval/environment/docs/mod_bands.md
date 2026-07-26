# Mixture-of-depths evaluation bands

`schema_tag` must be `mod-eval-v1`.

## Scenarios

`scenarios` is an array. Required ids, each present once:

`cold_a`, `resume_a`, `cold_b`, `resume_b`, `mix_c`, `mix_d`

Each scenario object carries `id` (string), `perplexity` (number),
`avg_depth` (number), `capacity` (number), and `tip_epoch` (integer).

## Router tip and capacity

`tip_epoch` for every scenario must equal the selected durable router tip
epoch drawn from materials under `/app/data/routers/`. Retired tip ids are
not selected. Tip sheets kept beside the journal are operator mirrors and
are not the selection authority.

`capacity` for every scenario must equal that durable tip's capacity.
The live full-depth sheet is not the capacity authority.

## Depth schedule

Average routed depth is computed from the depth schedule under
`/app/data/routers/depth_schedule.json` keyed by the effective routing
capacity. Only the top capacity-fraction of tokens by router score are
routed deep; the rest stay shallow. Ledger copies of that schedule are
operator conveniences and are not authoritative.

## Avg-depth bands

Every scenario's `avg_depth` must lie in `[4.35, 4.65]`.

## Perplexity

Cold/resume partners that share a pair must agree on `perplexity` within
`1e-4`. Perplexity bands:

| id | min | max |
| -- | --- | --- |
| cold_a | 4.155 | 4.325 |
| resume_a | 4.155 | 4.325 |
| cold_b | 5.075 | 5.282 |
| resume_b | 5.075 | 5.282 |
| mix_c | 3.648 | 3.798 |
| mix_d | 4.732 | 4.925 |

## bands_ok

`bands_ok` is true only when every required scenario satisfies its
avg-depth band, its perplexity band, cold/resume perplexity agreement,
and the durable tip capacity / epoch outcomes above. A healthy-looking
fixture under `/app/data/fixtures/surface_ok.json` or a green
`/app/tools/modprobe` print is not sufficient.

## Tip binding

Serving evaluation selection under `/app/calib/` requires a tip binding
record in the same tree. The record is `key = value` lines naming the
selected tip id, epoch, and capacity. A mismatched or missing record
keeps trial refresh behavior.

## Idempotence

Two consecutive runs of the eval driver must write byte-identical
`/output/mod-eval.json`.
