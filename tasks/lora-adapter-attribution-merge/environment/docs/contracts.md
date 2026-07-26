# Pipeline component contracts

The merge pipeline stages adapters through three internal packages before the
driver writes the report. Downstream evaluators and the driver assume the
contracts below. This note records intent and observables, not a worked
implementation.

## Base snapshot conventions

Each base under `/app/data/bases/` is JSON with `id`, `vocab_size`,
`embed_dim`, `embedding`, `mlp_weight`, `rms_eps`, and `cal_mean_sq`.

`rms_eps` is the constant inside the residual-block normalizer. `cal_mean_sq`
is the calibration statistic recorded when the snapshot was frozen; tooling
that rebases adapters across snapshots is expected to treat it as the
reference energy the normalizer was designed around.

Observed drift:

- `S1 -> S2`: vocabulary grew. Shared-token embedding rows match; new rows
  were appended. Other fields match.
- `S2 -> S3`: `rms_eps` dropped and `cal_mean_sq` was revised downward when
  the residual-block normalizer was retuned. Embeddings and MLP weights
  match.

## Adapter conventions

Each adapter under `/app/data/adapters/` carries factored low-rank factors
(`embed_A`/`embed_B`, `mlp_A`/`mlp_B`) against its `source_snapshot`. The
dense effective embedding delta is `embed_B @ embed_A`; the dense effective
MLP delta is `mlp_B @ mlp_A`.

## Forward-pass reference

For tokens under base `B` with applied dense deltas `(dE, dM)`:

```
y = sum_t (B.embedding[t] + dE[t])
scale = 1 / sqrt( (sum(y^2) / embed_dim) + B.rms_eps )
h = scale * y
z = (B.mlp_weight + dM) @ h
```

Task score is `-mean((z - expected)^2)`.

## Base-alignment

An adapter fit on `S_src` must be expressed against `S_tgt` so that:

- Every `S_tgt` token id indexes a well-defined embedding-delta row. Tokens
  that already existed under `S_src` keep their original effective rows;
  tokens introduced after `S_src` contribute zero.
- The residual-block contribution the adapter would have made under `S_src`
  is preserved when the same shared-token inputs are evaluated under
  `S_tgt`, accounting for how the normalizer's scale changes between the
  two snapshots' recorded calibration energy and `rms_eps`. Same-snapshot
  rebase is a no-op on the dense deltas.

Getting the second bullet wrong shows up as downstream score regressions
even when vocab resizing is correct.

## State-fusion

Aligned adapters against one target are combined into a fused state that
exposes both the total dense delta and a per-source share for every
adapter. The total must equal the sum of the shares. Shares are dense
effective deltas (not the factored A/B pairs). Attribution and single-source
removal both read those shares.

## Attribution-projection

Removing one adapter from a fused state must leave a state equivalent to
fusing the other adapters from scratch. Re-adding the stored share of the
removed adapter must reconstruct the original fused deltas. Approximations
that rescale the whole merge by a head-count factor do not satisfy this.

## Attribution completeness

After subtracting every stored per-source share from the fused deltas, the
residual Frobenius norm must sit at numerical noise for the shapes used
here (see report schema).
