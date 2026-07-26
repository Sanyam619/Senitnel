# MoE evaluation bands

`schema_tag` must be `moe-eval-v1`.

## Router temperature

`router_temp` for every slice must match the selected durable router tip drawn
from materials under `/app/data/routers/`. Tip sheets kept beside the journal
are operator mirrors and are not the selection authority. Retired tip ids are
not selected.

## Holds

Hold and release state is epoch-scoped against the selected tip. Coarse roster
summaries are operator conveniences and are not authoritative. Held experts
stay in the expert array with `active == false` and `load_share == 0`.

## Experts

Each entry in `experts[]` has `id`, `load_share`, and `active`.

- Across entries with `active == true`, `load_share` values must sum to `1.0`
  within `1e-6`.
- Aggregate load shares are the mean of per-slice seated weights.
- Expert capacity sheets under `/app/data/experts/` participate in seating.
  An archived seating sample from a healthy pass is kept under
  `/app/data/eval/audit/` for calibration reference.

## Slices

Each entry in `slices[]` has `id`, `perplexity`, `expert_entropy`, and
`router_temp`.

- `expert_entropy` is the Shannon entropy of that slice's seated weight vector
  (natural log).
- `perplexity` is `exp(expert_entropy)` under the seated weights.

### Perplexity bands

| slice id | min | max |
| -------- | --- | --- |
| s_alpha  | 2.693562 | 2.860174 |
| s_beta   | 1.853196 | 1.967826 |
| s_gamma  | 2.091763 | 2.221150 |
| s_delta  | 2.602896 | 2.763900 |

## eval_ok

`eval_ok` is true only when the expert load invariants hold and every graded
slice satisfies its perplexity band. A surface balance print from
`/app/tools/moeprobe` is not sufficient.

## Idempotence

Two consecutive runs of the eval driver must write byte-identical
`/output/moe-eval.json`.
