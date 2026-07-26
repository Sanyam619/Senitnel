# Report schema — embed-eval-v2

The published report at /output/embed-eval.json carries:

- `schema_tag` (string): exactly `embed-eval-v2`.
- `scenarios` (array): exactly the ids `cold_a`, `resume_a`, `cold_b`,
  `resume_b`, `mix_c`, `mix_d`, in that order. Each entry carries:
  - `id` (string)
  - `recall_at_10` (number)
  - `nmi` (number)
  - `temperature` (number)
  - `bank_epoch` (integer)
- `bands_ok` (boolean): true only when every scenario sits inside its
  published band (see embed_bands.md).

Metric values are printed with six decimals. `bank_epoch` is the ledger
generation the run binds to; `temperature` is the scale row resolved for
that generation and is identical across scenarios within one run.
