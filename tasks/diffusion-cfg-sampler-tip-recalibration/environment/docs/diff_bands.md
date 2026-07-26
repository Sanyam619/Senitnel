# Published diffusion evaluation health bands

These bands were measured for the current frozen banks and checkpoints when
the desk was bound to a durable tip and the durable CFG/sampler schedule
pair. A healthy report has every scenario inside its row and
`bands_ok = true`.

Columns: FID low/high, CLIP score low/high. CFG scale is shared across
scenarios because a run binds exactly one schedule row; the published CFG
band is 7.40–7.60. The durable sampler for that row is `dpmpp_2m`.

| scenario | f_lo  | f_hi  | c_lo  | c_hi  |
|----------|-------|-------|-------|-------|
| cold_a   | 5.000 | 8.000 | 0.512 | 0.556 |
| resume_a | 5.000 | 8.000 | 0.512 | 0.556 |
| cold_b   | 5.000 | 8.000 | 0.483 | 0.528 |
| resume_b | 5.000 | 8.000 | 0.483 | 0.528 |
| mix_c    | 15.000 | 20.000 | 0.501 | 0.547 |
| mix_d    | 15.000 | 20.000 | 0.470 | 0.514 |

Resume parity is graded on top of the bands: each `resume_*` scenario must
reproduce its `cold_*` scenario's `fid` and `clip_score` within `1e-4`.

`tip_epoch` is not banded; it must equal the generation of the bound durable
tip. `cfg_scale` and `sampler` must match the durable schedule pair for that
generation.
