# Published cross-encoder rerank evaluation bands

These bands were measured for the current frozen candidate pools, score packs,
and qrels when the desk was bound to a durable tip and the durable
temperature/fusion schedule pair. A healthy report has every slice inside its
row and `eval_ok = true`.

Columns: nDCG@10 low/high, MRR low/high. Temperature is shared across slices
because a run binds exactly one schedule row; the published temperature band
is 0.118–0.131. The durable fusion mode for that row is `rrf`.

| slice    | n_lo  | n_hi  | m_lo  | m_hi  |
|----------|-------|-------|-------|-------|
| cold_a   | 0.910 | 0.970 | 0.512 | 0.556 |
| resume_a | 0.910 | 0.970 | 0.512 | 0.556 |
| cold_b   | 0.910 | 0.970 | 0.483 | 0.528 |
| resume_b | 0.910 | 0.970 | 0.483 | 0.528 |
| mix_c    | 0.800 | 0.870 | 0.501 | 0.547 |
| mix_d    | 0.800 | 0.870 | 0.470 | 0.514 |

Resume parity is graded on top of the bands: each `resume_*` slice must
reproduce its `cold_*` twin's `ndcg_at_10` and `mrr` within `1e-4`.

`tip_epoch` is not banded; it must equal the generation of the bound durable
tip. `temperature` and `fusion` must match the durable schedule pair for that
generation.
