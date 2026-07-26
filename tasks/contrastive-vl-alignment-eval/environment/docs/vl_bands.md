# Published contrastive VL retrieval evaluation bands

These bands were measured for the current frozen image banks, caption query
frames, and tip materials when the desk was bound to a sealed durable tip and
the durable logit-scale / negative-pool schedule pair. A healthy report has
every slice inside its row and `eval_ok = true`.

Columns: recall@5 low/high, recall@10 low/high. Temperature is shared across
slices because a run binds exactly one schedule row; the published
temperature band is 0.118–0.131. The durable negative-pool preference for
that row is `hardmine`.

| slice    | r5_lo | r5_hi | r10_lo | r10_hi |
|----------|-------|-------|--------|--------|
| cold_a   | 0.900 | 0.970 | 0.910  | 0.970  |
| resume_a | 0.900 | 0.970 | 0.910  | 0.970  |
| cold_b   | 0.900 | 0.970 | 0.910  | 0.970  |
| resume_b | 0.900 | 0.970 | 0.910  | 0.970  |
| mix_c    | 0.760 | 0.860 | 0.800  | 0.870  |
| mix_d    | 0.760 | 0.860 | 0.800  | 0.870  |

Resume parity is graded on top of the bands: each `resume_*` slice must
reproduce its `cold_*` twin's `recall_at_5` and `recall_at_10` within `1e-4`.

`tip_epoch` is not banded; it must equal the generation of the bound durable
tip. `temperature` and `pool` must match the durable schedule pair for that
generation.
