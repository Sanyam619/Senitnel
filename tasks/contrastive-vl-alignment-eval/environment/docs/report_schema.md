# Report schema — vl-eval-v1

The published report at /output/vl-eval.json carries:

- `schema_tag` (string): exactly `vl-eval-v1`.
- `slices` (array): exactly the ids `cold_a`, `resume_a`, `cold_b`,
  `resume_b`, `mix_c`, `mix_d`, in that order. Each entry carries:
  - `id` (string)
  - `recall_at_5` (number)
  - `recall_at_10` (number)
  - `temperature` (number)
  - `tip_epoch` (integer)
  - `pool` (string): one of `inbatch`, `hardmine`
- `eval_ok` (boolean): true only when every slice sits inside its published
  band (see vl_bands.md).

Metric values are printed with six decimals. `tip_epoch` is the tip
generation the run binds to; `temperature` and `pool` are the schedule
pair resolved for that generation and are identical across slices within
one run.
