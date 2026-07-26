# Report schema — rerank-eval-v1

The published report at /output/rerank-eval.json carries:

- `schema_tag` (string): exactly `rerank-eval-v1`.
- `slices` (array): exactly the ids `cold_a`, `resume_a`, `cold_b`,
  `resume_b`, `mix_c`, `mix_d`, in that order. Each entry carries:
  - `id` (string)
  - `ndcg_at_10` (number)
  - `mrr` (number)
  - `temperature` (number)
  - `fusion` (string): one of `rrf`, `linear`, `learned`
  - `tip_epoch` (integer)
- `eval_ok` (boolean): true only when every slice sits inside its published
  band (see rerank_bands.md).

Metric values are printed with six decimals. `tip_epoch` is the tip
generation the run binds to; `temperature` and `fusion` are the schedule
pair resolved for that generation and are identical across slices within
one run.
