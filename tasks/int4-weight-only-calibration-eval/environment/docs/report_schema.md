# Report shape

`/app/scripts/run_int4_eval.sh` publishes `/output/int4-eval.json`.

```json
{
  "schema_tag": "int4-eval-v1",
  "scenarios": [
    {"id": "cold_a", "perplexity": 0.0, "top1": 0.0, "group_size": 0, "tip_epoch": 0}
  ],
  "bands_ok": false
}
```

- `schema_tag` — string, `int4-eval-v1`.
- `scenarios` — one object per line of `data/eval/roster.txt`, in roster order.
  - `id` — string, the roster name.
  - `perplexity` — number.
  - `top1` — number in `[0, 1]`.
  - `group_size` — integer, the grouping width the pass quantized under.
  - `tip_epoch` — integer, the number of the generation the pass scored under.
- `bands_ok` — boolean, true only when every scenario is inside its published
  band.

The roster carries `cold_a`, `resume_a`, `cold_b`, `resume_b`, `mix_c` and
`mix_d`. `cold_a`/`resume_a` and `cold_b`/`resume_b` are partners: each pair is
one measurement taken from two starting snapshots over the same evaluation
slice.

Two consecutive publications of an unchanged desk are byte-identical.
