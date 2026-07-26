# Published evaluation health bands

These bands were measured for the current frozen banks and checkpoints when
the desk was bound to a durable feature-registry tip. A healthy report has
every scenario inside its row and `bands_ok = true`.

Columns: recall@10 low/high, NMI low/high, temperature low/high. The
temperature band is shared by every scenario because a run binds exactly one
scale row.

| scenario | r_lo  | r_hi  | n_lo  | n_hi  | t_lo  | t_hi  |
|----------|-------|-------|-------|-------|-------|-------|
| cold_a   | 0.910 | 0.970 | 0.512 | 0.556 | 0.118 | 0.131 |
| resume_a | 0.910 | 0.970 | 0.512 | 0.556 | 0.118 | 0.131 |
| cold_b   | 0.910 | 0.970 | 0.483 | 0.528 | 0.118 | 0.131 |
| resume_b | 0.910 | 0.970 | 0.483 | 0.528 | 0.118 | 0.131 |
| mix_c    | 0.800 | 0.870 | 0.501 | 0.547 | 0.118 | 0.131 |
| mix_d    | 0.800 | 0.870 | 0.470 | 0.514 | 0.118 | 0.131 |

Resume parity is graded on top of the bands: each `resume_*` scenario must
reproduce its `cold_*` scenario's `recall_at_10` and `nmi` within `1e-4`.

`bank_epoch` is not banded; it must equal the generation of the bound durable
feature-registry tip.
