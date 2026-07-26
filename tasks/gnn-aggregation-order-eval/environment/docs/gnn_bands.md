# Published evaluation health bands

These bands were measured for the current frozen graphs and checkpoints when
the desk was bound to a durable feature-registry tip. A healthy report has
every scenario inside its row and `bands_ok = true`.

Columns: accuracy low/high, macro_f1 low/high.

| scenario | a_lo   | a_hi   | f_lo   | f_hi   |
|----------|--------|--------|--------|--------|
| cold_a   | 0.600  | 0.640  | 0.970  | 1.001  |
| resume_a | 0.600  | 0.640  | 0.970  | 1.001  |
| cold_b   | 0.600  | 0.640  | 0.990  | 1.001  |
| resume_b | 0.600  | 0.640  | 0.990  | 1.001  |
| mix_c    | 0.640  | 0.675  | 0.990  | 1.001  |
| mix_d    | 0.560  | 0.605  | 0.990  | 1.001  |

Resume parity is graded on top of the bands: each `resume_*` scenario must
reproduce its `cold_*` scenario's `accuracy` and `macro_f1` within `1e-4`.

`tip_epoch` and `agg` are not banded; they must equal the generation and
aggregation mode of the bound durable feature-registry tip.

## Degree seating

Before neighbor aggregation, each node feature row is seated according to the
bound tip's `norm` preference:

- When `norm` is `degree`, node `i` with raw feature row `x_i` and undirected
  degree `d_i` (each undirected edge counted once at each endpoint; a self-loop
  counted once) is replaced by `x_i / sqrt(d_i + 1)`, applied elementwise.
- When `norm` is `raw`, seated features equal the raw feature rows.

## Metric definitions

`accuracy` is the mean, over labeled nodes, of the softmax probability of the
true class under the linear classifier applied to the aggregated node states.
`macro_f1` is the unweighted mean of per-class F1 on argmax predictions.
Published numeric cells must match this faithful evaluation of the frozen
graphs and checkpoints under the bound tip (within `1e-5`), not only the band
windows above.
