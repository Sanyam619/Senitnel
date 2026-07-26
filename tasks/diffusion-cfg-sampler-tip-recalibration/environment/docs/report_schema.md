# Report schema — diff-eval-v2

The published report at /output/diff-eval.json carries:

- `schema_tag` (string): exactly `diff-eval-v2`.
- `scenarios` (array): exactly the ids `cold_a`, `resume_a`, `cold_b`,
  `resume_b`, `mix_c`, `mix_d`, in that order. Each entry carries:
  - `id` (string)
  - `fid` (number)
  - `clip_score` (number)
  - `cfg_scale` (number)
  - `sampler` (string)
  - `tip_epoch` (integer)
- `bands_ok` (boolean): true only when every scenario sits inside its
  published band (see diff_bands.md).

Metric values are printed with six decimals. `tip_epoch` is the tip
generation the run binds to; `cfg_scale` and `sampler` are the schedule
pair resolved for that generation and are identical across scenarios
within one run.
