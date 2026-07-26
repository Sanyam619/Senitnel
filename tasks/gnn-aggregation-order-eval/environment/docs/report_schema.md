# Report schema — gnn-eval-v2

The published report at /output/gnn-eval.json carries:

- `schema_tag` (string): exactly `gnn-eval-v2`.
- `scenarios` (array): exactly the ids `cold_a`, `resume_a`, `cold_b`,
  `resume_b`, `mix_c`, `mix_d`, in that order. Each entry carries:
  - `id` (string)
  - `accuracy` (number)
  - `macro_f1` (number)
  - `agg` (string): the bound aggregation mode (`mean`, `sum`, `max`, or
    `pna`)
  - `tip_epoch` (integer)
- `bands_ok` (boolean): true only when every scenario sits inside its
  published band (see gnn_bands.md).

Metric values are printed with six decimals. `tip_epoch` is the journal
generation the run binds to; `agg` is the aggregation mode resolved for that
generation and is identical across scenarios within one run.
